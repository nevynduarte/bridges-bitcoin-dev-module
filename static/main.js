/**
 * Frontend logic for the BTC price widget.
 *
 * Responsibilities:
 * - Fetch BTC/USD price from /api/prices/btc-usd
 * - Update price, last-updated time, and source
 * - Show "Live" vs error status pill
 * - Animate price changes up/down for a quick visual cue
 */

const REFRESH_INTERVAL_MS = 60000; // 60 seconds
let lastPrice = null;

console.log("[BTC] main.js loaded");

/**
 * Format a number as USD.
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
 * Update status pill visuals (Live vs Error).
 */
function setStatus(isError) {
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");

  if (!statusDot || !statusText) return;

  if (isError) {
    statusDot.classList.remove("status-dot-live");
    statusDot.classList.add("status-dot-error");
    statusText.textContent = "Offline";
  } else {
    statusDot.classList.remove("status-dot-error");
    statusDot.classList.add("status-dot-live");
    statusText.textContent = "Live";
  }
}

/**
 * Apply a transient animation class based on price movement.
 */
function animatePriceChange(priceEl, newPrice) {
  if (lastPrice === null) {
    lastPrice = newPrice;
    return;
  }

  const goingUp = newPrice > lastPrice;
  const goingDown = newPrice < lastPrice;

  priceEl.classList.remove("price-up", "price-down");

  if (goingUp) {
    priceEl.classList.add("price-up");
  } else if (goingDown) {
    priceEl.classList.add("price-down");
  }

  lastPrice = newPrice;

  // Remove animation class after it finishes so it can retrigger later.
  setTimeout(() => {
    priceEl.classList.remove("price-up", "price-down");
  }, 700);
}

/**
 * Fetch the BTC price from the backend and update the UI.
 */
async function fetchAndRenderPrice() {
  const priceEl = document.getElementById("price");
  const updatedEl = document.getElementById("updated");
  const sourceEl = document.getElementById("source");
  const footerSourceEl = document.getElementById("footer-source");
  const errorEl = document.getElementById("error");

  if (!priceEl || !updatedEl || !sourceEl || !errorEl) {
    console.error("[BTC] Missing DOM elements for rendering.");
    return;
  }

  console.log("[BTC] fetchAndRenderPrice() called");

  // Clear previous error state.
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

    // Render price with animation if it changed.
    const newPrice = Number(data.price);
    priceEl.textContent = formatUsd(newPrice);
    animatePriceChange(priceEl, newPrice);

    // Last updated.
    const updatedText = data.server_last_updated || new Date().toISOString();
    updatedEl.textContent =
      "Last updated: " + new Date(updatedText).toLocaleTimeString();

    // Source text.
    const sourceName = data.source || "Unknown source";
    sourceEl.textContent = "Source: " + sourceName;
    if (footerSourceEl) {
      footerSourceEl.textContent = sourceName;
    }

    // If backend explicitly marks stale, show degraded state but keep cached price.
    const isStale = Boolean(data.stale);
    if (isStale) {
      setStatus(true);
      errorEl.textContent =
        data.warning ||
        "⚠️ Upstream provider is offline. Showing last known price.";
      errorEl.classList.remove("hidden");
    } else {
      setStatus(false);
    }
  } catch (err) {
    console.error("[BTC] Error fetching BTC price:", err);

    errorEl.textContent =
      "⚠️ Unable to fetch live price right now. Retrying automatically...";
    errorEl.classList.remove("hidden");

    // Status → Offline.
    setStatus(true);
  }
}

/**
 * Initialize:
 * - Fetch once immediately
 * - Then refresh at a fixed interval
 */
function init() {
  console.log("[BTC] init() called");
  fetchAndRenderPrice();
  setInterval(fetchAndRenderPrice, REFRESH_INTERVAL_MS);
}

// Run on load (script is at the bottom of <body>, so DOM is ready).
init();
