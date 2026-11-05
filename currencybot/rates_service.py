"""
Exchange rate retrieval service with live API support, persistent local cache,
and graceful offline fallback.
"""

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

CACHE_FILE_PATH = Path(".currency_rates_cache.json")

# Fallback baseline rates relative to USD if no network and no cache exists yet
BASELINE_FALLBACK_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.89,
    "MYR": 4.40,
    "SGD": 1.28,
    "JPY": 155.0,
    "GBP": 0.75,
    "AUD": 1.50,
    "CAD": 1.35,
    "CHF": 0.88,
    "CNY": 7.15,
    "HKD": 7.78,
    "INR": 84.50,
    "KRW": 1380.0,
    "THB": 34.20,
    "IDR": 15700.0,
    "PHP": 58.0,
    "VND": 25300.0,
    "TWD": 32.10,
    "AED": 3.67,
    "SAR": 3.75,
    "NZD": 1.68,
    "BRL": 5.60,
    "MXN": 19.80,
    "ZAR": 17.60,
    "TRY": 34.50,
    "SEK": 10.60,
    "NOK": 10.90,
    "DKK": 6.85,
    "PLN": 3.98,
}


@dataclass
class RateResult:
    source: str
    target: str
    rate: float
    last_updated: str
    is_cached: bool
    source_provider: str
    disclaimer: Optional[str] = None


class RatesService:
    def __init__(self, cache_path: Optional[Path] = None):
        self.cache_path = cache_path or CACHE_FILE_PATH
        self._rates_cache: Dict[str, float] = {}
        self._last_updated_str: str = ""
        self._load_cache_from_disk()

    def _load_cache_from_disk(self) -> bool:
        """Loads cached rates from disk if available."""
        if not self.cache_path.exists():
            return False
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._rates_cache = data.get("rates", {})
                self._last_updated_str = data.get("last_updated", "")
                return bool(self._rates_cache)
        except Exception:
            return False

    def _save_cache_to_disk(self, rates: Dict[str, float], last_updated: str):
        """Saves retrieved rates to local persistent cache."""
        try:
            payload = {
                "base": "USD",
                "last_updated": last_updated,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "rates": rates,
            }
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def _fetch_from_open_er_api(self) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
        """Primary endpoint: Open Exchange Rates API (free, 160+ currencies)."""
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={"User-Agent": "CurrencyBot/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("result") == "success" and "rates" in data:
                rates = data["rates"]
                rates["USD"] = 1.0
                last_updated = data.get("time_last_update_utc", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
                return rates, last_updated
        return None, None

    def _fetch_from_frankfurter(self) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
        """Secondary endpoint: Frankfurter API (ECB reference rates)."""
        url = "https://api.frankfurter.dev/v1/latest?base=USD"
        req = urllib.request.Request(url, headers={"User-Agent": "CurrencyBot/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "rates" in data:
                rates = data["rates"]
                rates["USD"] = 1.0
                last_updated = data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                return rates, last_updated
        return None, None

    def get_all_usd_rates(self, force_refresh: bool = False) -> Tuple[Dict[str, float], str, bool, Optional[str]]:
        """
        Returns (rates_dict, last_updated_string, is_cached, disclaimer).
        """
        if not force_refresh:
            # Attempt to fetch live from primary
            try:
                rates, updated = self._fetch_from_open_er_api()
                if rates and updated:
                    self._rates_cache = rates
                    self._last_updated_str = updated
                    self._save_cache_to_disk(rates, updated)
                    return rates, updated, False, None
            except Exception:
                pass

            # Attempt secondary
            try:
                rates, updated = self._fetch_from_frankfurter()
                if rates and updated:
                    self._rates_cache = rates
                    self._last_updated_str = updated
                    self._save_cache_to_disk(rates, updated)
                    return rates, updated, False, None
            except Exception:
                pass

        # Offline or API failed -> fall back to local disk cache
        if self._rates_cache or self._load_cache_from_disk():
            disclaimer = f"Offline/Fallback: Rates loaded from cached data ({self._last_updated_str})."
            return self._rates_cache, self._last_updated_str, True, disclaimer

        # If disk cache is also unavailable, use built-in baseline rates
        self._rates_cache = BASELINE_FALLBACK_RATES.copy()
        self._last_updated_str = "Baseline Offline Fallback (2026-11-05)"
        disclaimer = "Offline: API unavailable and no prior cache found. Using baseline reference rates."
        return self._rates_cache, self._last_updated_str, True, disclaimer

    def get_rate(self, source: str, target: str) -> RateResult:
        """
        Calculates exchange rate between any two currencies.
        Uses USD base rates table: rate(source -> target) = rate(USD -> target) / rate(USD -> source).
        """
        source = source.upper()
        target = target.upper()

        if source == target:
            return RateResult(
                source=source,
                target=target,
                rate=1.0,
                last_updated=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                is_cached=False,
                source_provider="Direct Identity",
                disclaimer=None,
            )

        rates, updated, is_cached, disclaimer = self.get_all_usd_rates()

        if source not in rates:
            raise ValueError(f"Unsupported or unknown source currency code: '{source}'")
        if target not in rates:
            raise ValueError(f"Unsupported or unknown target currency code: '{target}'")

        usd_to_source = rates[source]
        usd_to_target = rates[target]
        calculated_rate = usd_to_target / usd_to_source

        return RateResult(
            source=source,
            target=target,
            rate=calculated_rate,
            last_updated=updated,
            is_cached=is_cached,
            source_provider="ExchangeRate-API / Frankfurter" if not is_cached else "Local Cache",
            disclaimer=disclaimer,
        )
