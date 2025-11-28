"""
Integration-ish tests for the Flask app routes.

We monkeypatch the Coingecko provider and time module to avoid real network
calls and to control caching behaviour.
"""

import time as std_time

import pytest

import app as btc_app
from price_provider import PriceProviderError


@pytest.fixture(autouse=True)
def reset_cache():
    btc_app._price_cache["data"] = None
    btc_app._price_cache["fetched_at"] = 0.0
    btc_app.app.config.update(TESTING=True)
    yield


@pytest.fixture
def client():
    return btc_app.app.test_client()


@pytest.fixture
def set_time(monkeypatch):
    def _set(value: float):
        monkeypatch.setattr(btc_app.time, "time", lambda: value)
        monkeypatch.setattr(
            btc_app.time,
            "gmtime",
            lambda ts=None: std_time.gmtime(value if ts is None else ts),
        )

    return _set


def test_api_success(monkeypatch, client, set_time):
    sample = {
        "price": 50000.12,
        "source": "coingecko",
        "provider_last_updated": "2023-01-01T00:00:00Z",
    }

    monkeypatch.setattr(btc_app.price_provider, "get_btc_usd_price", lambda: sample)
    set_time(1700000000.0)

    resp = client.get("/api/prices/btc-usd")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["price"] == sample["price"]
    assert data["source"] == "coingecko"
    assert data["stale"] is False


def test_api_provider_failure_returns_502(monkeypatch, client, set_time):
    def failing():
        raise PriceProviderError("coingecko down")

    monkeypatch.setattr(btc_app.price_provider, "get_btc_usd_price", failing)
    set_time(1700000100.0)

    resp = client.get("/api/prices/btc-usd")
    assert resp.status_code == 502
    data = resp.get_json()
    assert "error" in data


def test_cached_response_reused_within_ttl(monkeypatch, client, set_time):
    call_count = {"value": 0}

    def fake_get():
        call_count["value"] += 1
        return {
            "price": 51000.55,
            "source": "coingecko",
            "provider_last_updated": "2023-01-01T00:00:00Z",
        }

    monkeypatch.setattr(btc_app.price_provider, "get_btc_usd_price", fake_get)

    now = [1_700_000_000.0]

    def advance(seconds):
        now[0] += seconds
        set_time(now[0])

    set_time(now[0])
    resp1 = client.get("/api/prices/btc-usd")
    assert resp1.status_code == 200
    assert call_count["value"] == 1

    # Move forward but stay within TTL (default 120s) so cache should be used.
    advance(30)
    resp2 = client.get("/api/prices/btc-usd")
    data2 = resp2.get_json()
    assert resp2.status_code == 200
    assert call_count["value"] == 1  # still only one provider call
    assert data2["stale"] is False
    assert data2["cache_age_seconds"] >= 30


def test_stale_cache_fallback(monkeypatch, client, set_time):
    cached_payload = {
        "symbol": "BTC",
        "currency": "USD",
        "price": 48000.0,
        "source": "coingecko",
        "provider_last_updated": "2023-01-01T00:00:00Z",
        "server_last_updated": "2023-01-01T00:00:00Z",
        "stale": False,
        "cache_age_seconds": 0.0,
    }

    # Seed the cache at time 0.
    set_time(0.0)
    btc_app.update_cache(cached_payload)

    # Move beyond TTL to make cache stale and force provider error.
    set_time(btc_app.app.config["CACHE_TTL_SECONDS"] + 10)

    def failing():
        raise PriceProviderError("coingecko unreachable")

    monkeypatch.setattr(btc_app.price_provider, "get_btc_usd_price", failing)

    resp = client.get("/api/prices/btc-usd")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["price"] == cached_payload["price"]
    assert data["stale"] is True
    assert "warning" in data
    assert data["cache_age_seconds"] > btc_app.app.config["CACHE_TTL_SECONDS"]
