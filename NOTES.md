# NOTES.md

## API Choice

**CoinGecko API**
This implementation uses the CoinGecko API because it:

* Requires no API key
* Supports real-time and historical BTC pricing
* Has a generous free tier with stable uptime
* Returns structured JSON with minimal nesting, which simplifies parsing and fallback logic

CoinMarketCap and CryptoCompare were considered, but both require API keys and rate management from the start, which was unnecessary for this vertical slice.

## Tech Stack

**Python + Flask + Vanilla JS**

This stack was chosen for the following reasons:

* Python is fast to iterate on and ideal for small backend APIs.
* Flask makes it simple to expose both HTML and JSON endpoints.
* Vanilla HTML/JS is sufficient for a single-widget UI and keeps it dependency-free.
* The overall architecture aligns well with how data science or ML teams would wire together API-backed services.

If expanded, this stack can scale easily by:

* Adding Redis for shared caching
* Persisting to Postgres for historical BTC prices
* Swapping in a React/Vue frontend without needing to change the backend

## Design Decisions

* The backend caches prices for 120s and returns stale data if the provider is temporarily down.
* If the provider fails, a warning is shown, but the last valid price is retained.
* Retry logic with exponential backoff was added to handle transient network issues.
* The UI shows status dots, source, and timestamp so the user is always informed.
* GitHub Actions CI runs linting and tests to ensure reliability during changes.

## API Key Handling (If Needed)

While CoinGecko does not require an API key, this implementation is structured to support key-based providers like CoinMarketCap or CryptoCompare.

On platforms like Render, which I used to test/deploy this tool, API keys are stored securely using environment variables (e.g., `API_KEY`, `API_SECRET`). In local development, the same keys can be safely stored using a `.env` file and loaded with `python-dotenv` or similar tooling. These variables are accessed via `os.getenv()` in `config.py`, and never hardcoded or checked into source control.

This approach ensures API secrets remain private while still being usable across environments.

## Summary

This solution is robust, extensible, and cleanly deployable. It was built with real-world engineering tradeoffs in mind, including future integration of multiple data providers.
