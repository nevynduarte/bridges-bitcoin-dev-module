"""
Minimal unit tests for CoingeckoPriceProvider.

In a real project, this would be run via:
    pytest tests/
"""

from price_provider import CoingeckoPriceProvider, PriceProviderError


def test_provider_smoke(monkeypatch):
    """
    Smoke test that ensures the provider:
    - Calls the configured URL
    - Parses the basic response shape
    """

    sample_json = {
        "bitcoin": {
            "usd": 67321.12,
            "last_updated_at": 1700000000,
        }
    }

    class DummyResponse:
        status_code = 200

        def json(self):
            return sample_json

    def fake_get(url, params=None, timeout=None):
        return DummyResponse()

    # Patch requests.get inside the provider module.
    import price_provider as pp

    monkeypatch.setattr(pp.requests, "get", fake_get)

    provider = CoingeckoPriceProvider(base_url="https://dummy-url.example")
    result = provider.get_btc_usd_price()

    assert result["price"] == sample_json["bitcoin"]["usd"]
    assert result["source"] == "coingecko"
    assert "provider_last_updated" in result


def test_provider_bad_status(monkeypatch):
    """Provider should raise PriceProviderError on non-200 responses."""

    class DummyResponse:
        status_code = 500

        def json(self):
            return {}

    def fake_get(url, params=None, timeout=None):
        return DummyResponse()

    import price_provider as pp

    monkeypatch.setattr(pp.requests, "get", fake_get)

    provider = CoingeckoPriceProvider(base_url="https://dummy-url.example")

    try:
        provider.get_btc_usd_price()
    except PriceProviderError:
        assert True
    else:
        assert False, "Expected PriceProviderError to be raised"
