# Bridges BTC Price Module

A minimal, production-minded web app that displays the **live Bitcoin (BTC) price in USD**, updated every 60 seconds. This implementation uses a structured Flask backend with an abstracted price provider layer, a modern JavaScript frontend with cache-aware live updates, and full test coverage with CI integration.

---

## Features

* Real-time BTC/USD price from Coingecko API
* Auto-refresh every 60 seconds with retry/backoff
* "Live" / "Offline" status pill with animation
* Timestamp of last update (or age of stale cache)
* Graceful fallback: stale cached values if API fails
* Configurable via environment: timeouts, cache TTL
* Modern, responsive dark-themed UI
* Structured logs + test coverage + GitHub CI

---

## Live Demo & Source

* **Live App**: [https://bridges-bitcoin-dev-module.onrender.com](https://bridges-bitcoin-dev-module.onrender.com)
* **GitHub Repo**: [https://github.com/nevyn/bridges-bitcoin-dev-module](https://github.com/nevyn/bridges-bitcoin-dev-module)

---

## Tech Stack

This implementation uses:

* **Flask (Python)** backend with Gunicorn for deployment
* **Jinja2 templates** + static JS/CSS for frontend
* **CoinGecko API** as the primary BTC price data source
* **In-memory TTL cache** with stale fallback logic
* **Pytest** + **monkeypatch** for unit/integration tests
* **GitHub Actions** CI pipeline for linting and tests

---

## Setup & Run Locally

```bash
# Clone and enter the project directory
git clone https://github.com/nevyn/bridges-bitcoin-dev-module.git
cd bridges-bitcoin-dev-module

# Create and activate a virtual environment (optional)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
env FLASK_APP=app.py flask run  # http://127.0.0.1:5000
```

---

## Deployment

This implementation uses [Render](https://render.com) to deploy:

* `Procfile`: `web: gunicorn app:app`
* Static assets served from `/static/`
* Configurable via environment:

  * `CACHE_TTL_SECONDS` (default: 120)
  * `REQUEST_TIMEOUT` (default: 3.0)

---

## Testing

```bash
# Run tests
pytest

# Run linter
flake8 .
```

Tests cover:

* Price provider: success, retries, parse errors
* API route: live response, fallback, 502 on failure
* Cache reuse vs refresh timing

---

## CI/CD

This implementation uses GitHub Actions:

`.github/workflows/ci.yml`:

* Runs on push and pull_request
* Installs dependencies
* Runs `flake8` and `pytest`

---

## Architecture Overview

* `app.py` — Flask app: routes, caching, error handling
* `price_provider.py` — CoinGecko integration with retry + validation
* `templates/index.html` — HTML skeleton using `url_for`
* `static/main.js` — JS logic for fetch, status, animation
* `static/styles.css` — Modern dark theme with responsive layout
* `tests/` — Unit/integration test suite using monkeypatch

### Runtime Flow

```
Browser
   ↓ fetch every 60s
/api/prices/btc-usd
   ↓  (from cache or provider)
CoinGecko (external API)
```

---

## Questions & Implementation Notes

**What happens if the API is down?**

* A cached price is returned if available, marked as stale with age metadata.
* The frontend displays "Offline" status and a visual warning.

**How is the API response structured?**

* Standardized JSON:

  ```json
  {
    "symbol": "BTC",
    "currency": "USD",
    "price": 67543.21,
    "source": "coingecko",
    "server_last_updated": "...",
    "stale": false,
    "age_seconds": 12
  }
  ```

**How does the retry/backoff mechanism work?**

* `price_provider.py` wraps all external calls with `try/retry`, timeouts, and detailed error capture.
* Logs show source, latency, HTTP errors, JSON errors, etc.

**How is price movement shown in the UI?**

* Price increases animate green (glow up)
* Price drops animate red (glow down)
* Status dot: green (live), red (offline)

**What if we want to use other APIs?**

* The provider is abstracted; easy to extend:

  * `CryptoCompareProvider`
  * `BinanceProvider`
  * `CoinMarketCapProvider`

**How would this scale?**

* Add Redis for distributed caching
* Store snapshots to Postgres for historical graphs
* Swap frontend to React or embed in a dashboard

**How could this be extended?**

* Support multiple coins/currencies
* Add sparkline charts with last N prices
* Notify or webhook when thresholds are crossed

---

## Roadmap & Next Steps

* Add fallback and multi-provider support: CryptoCompare, CoinMarketCap, Binance
* Abstract provider classes and load from config/env to support chained retries
* Support additional coins and currency pairs: `/api/prices/eth-usd`, `/btc-eur`, etc.
* Log all price fetches to SQLite or PostgreSQL for historical charting
* Add sparkline chart component to frontend using cached or backend snapshot data
* Enable alerts (UI or webhook) for price thresholds
* Add `/health` and `/metrics` endpoints for observability/monitoring
* Deploy to alternate targets like Railway or Fly.io as container

---

## Improvements & Optimizations

This implementation can be further enhanced in several dimensions:

**Performance:**

* Introduce a shared cache layer like Redis to reduce latency under load.
* Batch fetch multiple symbols if expanding to more currencies or coins.

**Reliability:**

* Use multiple providers with fallback or majority-vote aggregation to minimize API outages.
* Add monitoring/alerting for backend exceptions or stale cache thresholds.

**Accuracy:**

* Allow configurable price sources or market exchange filtering.
* Provide weighted or averaged prices across multiple providers for redundancy.

**Frontend UX:**

* Add a mini sparkline or 24h percentage change to provide price context.
* Improve accessibility (e.g., ARIA roles, keyboard navigation) for dashboard usage.

---

## License

MIT License — use, adapt, and extend freely.
