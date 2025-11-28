/**
 * Frontend logic for the BTC price widget.
 *
 * Fetches BTC/USD from /api/prices/btc-usd and updates the DOM.
 * Includes verbose logging so it's easy to debug.
 */

const REFRESH_INTERVAL_MS = 60000; // 60 seconds (no numeric separator to avoid any edge cases)

console.log("[BTC] main.js loaded");

/**
 * Format a number as a USD currency string.
 * Example: 90997 => "$90,997.00"
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
    console.warn("[BTC] formatUsd fallback", e);
    return "$" + value;
  }
}

/**
 * Fetch the BTC price from the backend and update the DOM.
 */
async function fetchAndRenderPrice() {
  const priceEl = document.getElementById("price");
  const updatedEl = document.getElementById("updated");
  const errorEl = document.getElementById("error");

  console.log("[BTC] fetchAndRenderPrice() called");

  // Clear any previous error state.
  errorEl.textContent = "";
  errorEl.classList.add("hidden");

  try {
    const response = await fetch("/api/prices/btc-usd", {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    console.log("[BTC] backend status:", response.status);

    if (!response.ok) {
      throw new Error(`Backend responded with status ${response.status}`);
    }

    const data = await response.json();
    console.log("[BTC] data:", data);

    if (data.error) {
      throw new Error(data.error);
    }

    // Update the price text
    priceEl.textContent = formatUsd(data.price);

    // Prefer server_last_updated if present
    const updatedText = data.server_last_updated || new Date().toISOString();
    updatedEl.textContent =
      "Last updated: " + new Date(updatedText).toLocaleTimeString();
  } catch (err) {
    console.error("[BTC] Error fetching BTC price:", err);

    // Show a user-friendly error but keep last price on screen
    errorEl.textContent =
      "⚠️ Unable to fetch live price right now. Retrying automatically...";
    errorEl.classList.remove("hidden");
  }
}

/**
 * Initialize the page:
 * - Fetch once immediately
 * - Then schedule periodic refreshes
 *
 * We call init() directly because the script is loaded at the bottom of <body>,
 * so the DOM is already available.
 */
function init() {
  console.log("[BTC] init() called");
  fetchAndRenderPrice();
  setInterval(fetchAndRenderPrice, REFRESH_INTERVAL_MS);
}

// Immediately run init when the script loads.
init();
