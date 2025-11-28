"""
Price provider abstraction.

For this assessment:
- We implement a single provider: Coingecko.
- The goal is to show how we'd encapsulate external API logic
  behind a clean, testable interface.

In a larger system we might have:
- Multiple providers (primary + fallback)
- Circuit breakers
- More detailed error codes
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any

import requests

logger = logging.getLogger(__name__)


class PriceProviderError(Exception):
    """Raised when the external price provider fails or returns invalid data."""


@dataclass
class CoingeckoPriceProvider:
    """
    Simple wrapper around Coingecko's "simple price" API.

    Docs: https://www.coingecko.com/en/api/documentation (high-level)

    We only fetch BTC/USD for this assignment, but we still design this as a
    reusable component to demonstrate good API boundaries.
    """

    base_url: str
    timeout_seconds: float = 3.0
    retry_attempts: int = 2
    retry_backoff_seconds: float = 0.3

    def get_btc_usd_price(self) -> Dict[str, Any]:
        """
        Fetch the current BTC price in USD from Coingecko.

        Returns:
            dict with fields:
                - price: float
                - source: str
                - provider_last_updated: str (ISO8601, UTC)

        Raises:
            PriceProviderError on any error (network, HTTP, JSON, schema).
        """
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_last_updated_at": "true",
        }

        last_error: Exception | None = None

        for attempt in range(1, self.retry_attempts + 1):
            response = None
            try:
                response = requests.get(
                    self.base_url, params=params, timeout=self.timeout_seconds
                )
            except requests.RequestException as e:
                last_error = PriceProviderError(
                    f"Network error calling Coingecko: {e}"
                )
            else:
                status_code = response.status_code
                if status_code != 200:
                    # Include a short preview of the body for diagnostics.
                    preview = ""
                    try:
                        preview = response.text[:200]
                    except Exception:
                        preview = "<unavailable>"

                    last_error = PriceProviderError(
                        f"Coingecko returned status {status_code}: {preview}"
                    )
                else:
                    try:
                        data = response.json()
                    except ValueError as e:
                        last_error = PriceProviderError(
                            "Failed to parse JSON from Coingecko"
                        )
                    else:
                        try:
                            bitcoin = data["bitcoin"]
                            price = float(bitcoin["usd"])
                        except (KeyError, TypeError, ValueError):
                            last_error = PriceProviderError(
                                f"Unexpected Coingecko response structure: {data}"
                            )
                        else:
                            ts = bitcoin.get("last_updated_at")
                            if isinstance(ts, (int, float)):
                                provider_last_updated = datetime.fromtimestamp(
                                    ts, tz=timezone.utc
                                ).isoformat()
                            else:
                                # If not present, we still emit *something* consistent.
                                provider_last_updated = datetime.now(
                                    tz=timezone.utc
                                ).isoformat()

                            logger.debug(
                                "Parsed Coingecko response",
                                extra={
                                    "price": price,
                                    "provider_last_updated": provider_last_updated,
                                    "attempt": attempt,
                                },
                            )

                            return {
                                "price": price,
                                "source": "coingecko",
                                "provider_last_updated": provider_last_updated,
                            }

            # If we reach here, attempt failed.
            logger.warning(
                "Coingecko request attempt failed",
                extra={
                    "attempt": attempt,
                    "max_attempts": self.retry_attempts,
                    "error": str(last_error),
                    "status_code": getattr(response, "status_code", None),
                },
            )

            if attempt < self.retry_attempts:
                time.sleep(self.retry_backoff_seconds)

        # Exhausted retries.
        raise last_error or PriceProviderError("Unknown error calling Coingecko")
