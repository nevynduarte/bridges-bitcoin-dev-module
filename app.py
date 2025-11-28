"""
Flask application entrypoint.

Responsibilities:
- Wire up HTTP routes (HTML + JSON APIs)
- Instantiate the price provider
- Apply simple in-memory caching to control external API usage
- Handle errors in a user-friendly but observable way
"""

import logging
import time
from typing import Optional, Dict, Any

from flask import Flask, jsonify, render_template

from config import Config
from price_provider import CoingeckoPriceProvider, PriceProviderError

# ------------------------------------------------------------------------------
# App & Logging Setup
# ------------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

# Configure a simple, structured-ish logger.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Provider Initialization
# ------------------------------------------------------------------------------

# For this assessment we only need BTC/USD via Coingecko, but we wrap it
# in a provider class to show that we can swap it later (e.g., CoinMarketCap).
price_provider = CoingeckoPriceProvider(
    base_url=app.config["COINGECKO_BASE_URL"],
    timeout_seconds=app.config["REQUEST_TIMEOUT"],
)

# ------------------------------------------------------------------------------
# Simple In-Memory Cache
# ------------------------------------------------------------------------------
# This is deliberately minimal: suitable for a single-process demo service.
# In a production environment, this would likely be Redis or another shared cache.

_price_cache: Dict[str, Any] = {
    "data": None,  # last successful price payload
    "fetched_at": 0.0,  # unix timestamp of last fetch
}


def get_cached_price(allow_stale: bool = False) -> Optional[Dict[str, Any]]:
    """
    Return cached BTC price if it is still within TTL.

    If `allow_stale` is True, returns the cached price even when expired so the
    caller can decide whether to serve stale data.
    """
    ttl = app.config["CACHE_TTL_SECONDS"]
    now = time.time()
    if _price_cache["data"] is None:
        return None
    age = now - _price_cache["fetched_at"]
    is_fresh = age <= ttl
    if not is_fresh and not allow_stale:
        return None
    return {
        "data": _price_cache["data"],
        "age_seconds": age,
        "stale": not is_fresh,
    }


def update_cache(data: Dict[str, Any]) -> None:
    """Update the in-memory cache with fresh price data."""
    _price_cache["data"] = data
    _price_cache["fetched_at"] = time.time()


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """
    Render the main HTML page.

    The page itself is mostly static; it loads `main.js`, which calls
    the JSON API (`/api/prices/btc-usd`) to fetch live data.
    """
    return render_template("index.html")


@app.route("/api/prices/btc-usd", methods=["GET"])
def get_btc_price():
    """
    JSON API: Return the current BTC price in USD.

    This is the primary API consumed by the frontend. It:
    - Checks a small in-memory cache.
    - If stale/missing, calls the external provider (Coingecko).
    - Normalizes the response into a consistent JSON shape.
    - Returns appropriate HTTP status codes on error.
    """
    # 1. Check cache first to avoid unnecessary external calls.
    cached = get_cached_price()
    if cached:
        payload = {
            **cached["data"],
            "stale": cached["stale"],
            "cache_age_seconds": round(cached["age_seconds"], 2),
        }
        logger.debug(
            "Serving BTC price from cache",
            extra={
                "provider": "coingecko",
                "cache_age_seconds": cached["age_seconds"],
                "stale": cached["stale"],
            },
        )
        return jsonify(payload), 200

    # 2. Fetch from external provider if cache empty/expired.
    try:
        start = time.time()
        provider_payload = price_provider.get_btc_usd_price()
        duration_ms = round((time.time() - start) * 1000, 2)

        logger.info(
            "Fetched BTC price from provider",
            extra={
                "provider": "coingecko",
                "latency_ms": duration_ms,
                "status": "success",
            },
        )

        # 3. Normalize into final JSON shape consumed by frontend.
        response_payload = {
            "symbol": "BTC",
            "currency": "USD",
            "price": provider_payload["price"],
            "source": provider_payload["source"],
            "provider_last_updated": provider_payload["provider_last_updated"],
            # `server_last_updated` is the time we fetched & returned to the client.
            "server_last_updated": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            ),
            "stale": False,
            "cache_age_seconds": 0.0,
        }

        # 4. Update cache and return.
        update_cache(response_payload)
        return jsonify(response_payload), 200

    except PriceProviderError as e:
        # Known provider-level error (e.g., bad response, JSON parse failure).
        logger.error(
            "Price provider error",
            extra={
                "provider": "coingecko",
                "error": str(e),
                "status": "error",
            },
        )

        # Serve stale cache if available to avoid a hard failure.
        stale_cached = get_cached_price(allow_stale=True)
        if stale_cached:
            payload = {
                **stale_cached["data"],
                "stale": True,
                "cache_age_seconds": round(stale_cached["age_seconds"], 2),
                "warning": "Using stale cached price due to upstream error.",
            }
            logger.warning(
                "Serving stale cached BTC price after provider failure",
                extra={
                    "provider": "coingecko",
                    "cache_age_seconds": stale_cached["age_seconds"],
                    "error": str(e),
                },
            )
            return jsonify(payload), 200

        return (
            jsonify(
                {
                    "error": "Failed to fetch BTC price from upstream provider.",
                    "details": str(e),
                }
            ),
            502,
        )

    except Exception as e:
        # Catch-all for unexpected errors. In a real system, this might trigger
        # an alert or Sentry event.
        logger.exception("Unexpected error while fetching BTC price")
        return (
            jsonify(
                {
                    "error": "Unexpected error while fetching BTC price.",
                    "details": str(e),
                }
            ),
            500,
        )

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


# ------------------------------------------------------------------------------
# Entrypoint Guard
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # For local development only; in production you'd run via gunicorn/uwsgi.
    app.run(host="0.0.0.0", port=5000, debug=True)
