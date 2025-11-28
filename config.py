"""
Application configuration.

In a larger service, this is where we'd centralize:
- Environment variable loading
- Per-environment overrides (Dev/Stage/Prod)
- Feature flags

For this small app, we keep it simple but still structured.
"""

import os


class Config:
    """Base configuration class."""

    # Whether to run Flask in debug mode. In production this would be False.
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # HTTP request timeout when calling the external price API (in seconds).
    REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "3.0"))

    # Base URL for Coingecko's simple price API.
    # We treat this as configuration so it can be swapped easily if needed.
    COINGECKO_BASE_URL = os.getenv(
        "COINGECKO_BASE_URL",
        "https://api.coingecko.com/api/v3/simple/price",
    )

    # TTL for our in-memory cache (seconds).
    # If many users request the price frequently, this prevents excessive
    # calls to the upstream API.
    CACHE_TTL_SECONDS = 30
