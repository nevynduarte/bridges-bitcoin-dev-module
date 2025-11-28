# Bridges BTC Price Module: Architecture & Extension Plan

## Overview
The BTC Price Module is a lightweight Flask-based application that fetches and displays the live price of Bitcoin (BTC) in USD. It is designed with production-minded principles including API abstraction, error tolerance, cache-backed resilience, and test-driven development. The frontend is a clean, responsive single-page layout with real-time updates, status indicators, and graceful error handling.

## Architecture

### Components

#### 1. **Flask Backend** (`app.py`)
- Serves two main routes:
  - `/`: Renders the main UI from a Jinja2 template.
  - `/api/prices/btc-usd`: JSON endpoint that returns the latest BTC/USD price.
- Contains:
  - In-memory cache with TTL (default: 120s)
  - Fallback to stale cache if the provider fails
  - Logging for API call latency, errors, and fallback mode

#### 2. **Price Provider Layer** (`price_provider.py`)
- Abstracts the external API call
- Implements:
  - `get_btc_usd_price()` method with retry/backoff
  - JSON schema parsing and validation
  - Error wrapping into `PriceProviderError`

#### 3. **Frontend** (`templates/index.html`, `static/*.js/css`)
- HTML + CSS for a modern card layout with:
  - Live/Offline status dot
  - Animated price change feedback
  - Source label and update timestamp
- JavaScript fetches price every 60 seconds and updates the UI
- Displays error banner and cache age if provider is unreachable

#### 4. **Tests** (`tests/*.py`)
- Unit and integration tests using `pytest`
- Covers:
  - API success & failure
  - Provider retry logic
  - Cache hit/miss
  - Fallback to stale cache on provider failure

#### 5. **CI Pipeline** (`.github/workflows/ci.yml`)
- GitHub Actions workflow
- On push / PR:
  - Installs dependencies
  - Lints with `flake8`
  - Runs `pytest` for backend validation

---

## Runtime Flow
```text
[User] → [Flask index route] → [HTML template + static assets]
      ↓
[JS fetch every 60s] → [/api/prices/btc-usd] → [Price Provider]
        ↑             ⇣
   [Cache hit] ← [Coingecko API or fallback to stale cache]
```

---

## Deployment
- Hosted on **Render** (free tier)
- Uses Gunicorn (`Procfile`: `web: gunicorn app:app`)
- Static assets served from `/static` and correctly linked via `url_for()`
- Accessible via HTTPS and designed for single-container scalability

---

## Future Extension Plan

### Multi-Source Price Aggregation
The architecture is already designed for extensibility via the `PriceProvider` abstraction. The next iteration will support **multiple data sources** to increase reliability and enable aggregation.

#### Candidate APIs (All have free tiers with rate limits):

| Provider           | Features                                                                 |
|-------------------|--------------------------------------------------------------------------|
| **CoinGecko**      | Real-time price, market cap, and historical data                         |
| **CryptoCompare**  | High-frequency price data, minute/hourly/daily granularity              |
| **CoinMarketCap**  | Market cap, volume, trending; requires API key                          |
| **Binance**        | Real-time exchange data with generous limits                            |
| **BitcoinAverage** | Weighted average price across exchanges                                 |
| **Bitcoincharts**  | CSV historical records, free no-auth API                                |

#### Integration Strategy
- Create a `BaseProvider` interface
- Implement adapters:
  - `CoinGeckoProvider`
  - `CryptoCompareProvider`
  - etc.
- Add fallback chaining logic:
  - Try primary
  - If timeout/error, try backup provider(s)
  - If all fail, fallback to stale cache
- Optional: Median or weighted average from multiple APIs

#### Configuration
- Use `.env` or `config.py` to select:
  - `PRIMARY_PROVIDER = "coingecko"`
  - `FALLBACK_PROVIDERS = ["cryptocompare", "coinmarketcap"]`
  - `API_KEYS = {"coinmarketcap": "..."}`

#### UI Impact
- Show source in footer and tooltip (e.g., "Aggregated from 3 sources")
- Optional: Add trend icon (up/down) or mini chart with historical data

---

## Long-Term Options
- Redis cache for shared data across containers
- PostgreSQL or SQLite to log price snapshots
- React or Vue frontend for modular dashboard widgets
- Alerting or webhook when price crosses thresholds
- International currency support: `/api/prices/btc-eur`, `/btc-inr`, etc.

---

## Conclusion
This project began as a live BTC price viewer and now demonstrates:
- Solid API error handling
- Production-ready deployment
- Modern UI/UX principles
- Fully tested CI-driven workflow

It is well-positioned for extension into a real-time crypto dashboard, trading assistant, or educational tool.

