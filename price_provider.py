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

        try:
            response = requests.get(
                self.base_url, params=params, timeout=self.timeout_seconds
            )
        except requests.RequestException as e:
            # Network-level or timeout-level error.
            raise PriceProviderError(f"Network error calling Coingecko: {e}") from e

        if response.status_code != 200:
            raise PriceProviderError(
                f"Coingecko returned non-200 status: {response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as e:
            # Failed to parse JSON.
            raise PriceProviderError("Failed to parse JSON from Coingecko") from e

        # Expected shape:
        # {
        #   "bitcoin": {
        #       "usd": 67321.12,
        #       "last_updated_at": 1700000000 (optional, unix ts)
        #   }
        # }
        try:
            bitcoin = data["bitcoin"]
            price = float(bitcoin["usd"])
        except (KeyError, TypeError, ValueError) as e:
            raise PriceProviderError(
                f"Unexpected Coingecko response structure: {data}"
            ) from e

        # Coingecko may provide a unix timestamp; we convert to ISO8601 for consistency.
        provider_last_updated = None
        ts = bitcoin.get("last_updated_at")
        if isinstance(ts, (int, float)):
            provider_last_updated = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        else:
            # If not present, we still emit *something* consistent.
            provider_last_updated = datetime.now(tz=timezone.utc).isoformat()

        logger.debug(
            "Parsed Coingecko response",
            extra={"price": price, "provider_last_updated": provider_last_updated},
        )

        return {
            "price": price,
            "source": "coingecko",
            "provider_last_updated": provider_last_updated,
        }
