/**
 * Frontend logic for the BTC price widget.
 *
 * Responsibilities:
 * - Fetch BTC/USD price from /api/prices/btc-usd
 * - Update the DOM with the latest price and timestamps
 * - Show a user-friendly error message if something goes wrong
 * - Automatically refresh the data every 60 seconds
 */

const REFRESH_INTERVAL_MS = 60_000; // 60 seconds

/**
 * Format a number as a USD currency string.
 * Example: 67321.123 => "$67,321.12"
 */
function formatUsd(value) {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  } catch (e) {
    // Fallback in case of unexpected input.
    return `$${value}`;
  }
}

/**
 * Fetch the BTC price from the backend and update the DOM.
 */
async function fetchAndRenderPrice() {
  const priceEl = document.getElementById("price");
  const updatedEl = document.getElementById("updated");
  const errorEl = document.getElementById("error");

  // Clear any previous error state.
  errorEl.textContent = "";
  errorEl.classList.add("hidden");

  try {
    const response = await fetch("/api/prices/btc-usd", {
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
    });

    if (!response.ok) {
      // Example: 502 or 500 from backend.
      throw new Error(`Backend responded with status ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      // Backend may include a structured error payload.
      throw new Error(data.error);
    }

    // Update price text.
    priceEl.textContent = formatUsd(data.price);

    // Prefer server_last_updated for user-facing display.
    const updatedText = data.server_last_updated || "Unknown";
    updatedEl.textContent = `Last updated: ${new Date(updatedText).toLocaleTimeString()}`;
  } catch (err) {
    console.error("Error fetching BTC price:", err);

    // Show a user-friendly error while keeping the last price on-screen.
    errorEl.textContent =
      "⚠️ Unable to fetch live price right now. Retrying automatically...";
    errorEl.classList.remove("hidden");
  }
}

/**
 * Initialize the page:
 * - Fetch once immediately
 * - Then schedule periodic refreshes
 */
function init() {
  fetchAndRenderPrice();
  setInterval(fetchAndRenderPrice, REFRESH_INTERVAL_MS);
}

// Run once the DOM is ready.
document.addEventListener("DOMContentLoaded", init);
