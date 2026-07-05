"""
Weather data scraper for WATT-IF using the Open-Meteo Historical Weather API.

Fetches real daily weather data for Metro Manila (Ninoy Aquino Airport station area)
and aggregates it into the monthly variables expected by the SARIMAX model:
  - avg_temperature    (°C)    — mean of daily mean temperatures
  - avg_humidity       (%)     — mean of daily (max+min)/2 relative humidity
  - total_rainfall_mm  (mm)    — sum of daily precipitation
  - rainy_days_count           — days where precipitation_hours > 0
  - hot_days_count             — days where temperature_2m_max >= 33°C

API:  https://archive-api.open-meteo.com/v1/archive  (free, no API key)
Docs: https://open-meteo.com/en/docs/historical-weather-api

Results are cached in memory keyed by year_month to avoid redundant API calls.
Cache is intentionally not persisted — restarts will re-fetch if needed.
"""

from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Manila coordinates (NAIA area — representative for Metro Manila)
# ---------------------------------------------------------------------------

_LATITUDE = 14.5086
_LONGITUDE = 121.0194
_TIMEZONE = "Asia/Manila"

# Threshold for counting a day as "hot" (°C)
HOT_DAY_THRESHOLD = 33.0

# ---------------------------------------------------------------------------
# Open-Meteo endpoints
# ---------------------------------------------------------------------------

_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Variables requested from the API
_DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "precipitation_hours",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
]

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class MonthlyWeather:
    """Aggregated monthly weather values for one calendar month."""

    year_month: str           # YYYY-MM
    avg_temperature: float    # mean of daily mean temps (°C)
    avg_humidity: float       # mean of daily (rh_max + rh_min) / 2 (%)
    total_rainfall_mm: float  # sum of daily precipitation (mm)
    rainy_days_count: int     # days with precipitation_hours > 0
    hot_days_count: int       # days with temperature_2m_max >= HOT_DAY_THRESHOLD
    source: str               # "open-meteo-archive" | "open-meteo-forecast" | "fallback"


# ---------------------------------------------------------------------------
# Disk-backed cache with TTL
#
# Historical months (fully elapsed): cached forever — data never changes.
# Current month:                     cached for 24 h — data accumulates daily.
# Future months (fallback):          cached for 6 h  — re-checked periodically.
#
# Cache file: data/weather_cache.json  (next to wattif.db)
# Structure:  { "YYYY-MM": { ...MonthlyWeather fields..., "_cached_at": ISO } }
# ---------------------------------------------------------------------------

_CACHE_PATH = Path(__file__).parent.parent / "data" / "weather_cache.json"
_TTL_HISTORICAL = None          # never expires
_TTL_CURRENT    = timedelta(hours=24)
_TTL_FALLBACK   = timedelta(hours=6)

# In-memory mirror of the disk cache (loaded once at import time)
_mem_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()   # one lock covers both disk and memory ops


def _load_disk_cache() -> None:
    """Load the on-disk cache file into the in-memory mirror."""
    global _mem_cache
    if _CACHE_PATH.exists():
        try:
            _mem_cache = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            logger.debug("Weather disk cache loaded: %d entries.", len(_mem_cache))
        except Exception as exc:
            logger.warning("Could not load weather cache from %s: %s — starting fresh.", _CACHE_PATH, exc)
            _mem_cache = {}
    else:
        _mem_cache = {}


def _save_disk_cache() -> None:
    """Persist the in-memory cache to disk (best-effort)."""
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(
            json.dumps(_mem_cache, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Could not save weather cache to %s: %s", _CACHE_PATH, exc)


def _cache_get(year_month: str) -> Optional[MonthlyWeather]:
    """Return a cached MonthlyWeather if present and not expired, else None."""
    entry = _mem_cache.get(year_month)
    if entry is None:
        return None

    source = entry.get("source", "")
    cached_at_str = entry.get("_cached_at")

    # Determine TTL based on source and month position
    now = datetime.now(timezone.utc)
    current_ym = f"{now.year:04d}-{now.month:02d}"

    if year_month > current_ym:
        ttl = _TTL_FALLBACK
    elif year_month == current_ym:
        ttl = _TTL_CURRENT
    elif source == "fallback":
        # A historical month that got a fallback result — retry after 6 h
        # in case the API was temporarily down
        ttl = _TTL_FALLBACK
    else:
        ttl = _TTL_HISTORICAL  # real historical data: never expire

    if ttl is not None and cached_at_str:
        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            if now - cached_at > ttl:
                logger.debug("Cache entry for %s expired (source=%s).", year_month, source)
                return None
        except ValueError:
            return None  # malformed timestamp → treat as expired

    return MonthlyWeather(
        year_month=entry["year_month"],
        avg_temperature=entry["avg_temperature"],
        avg_humidity=entry["avg_humidity"],
        total_rainfall_mm=entry["total_rainfall_mm"],
        rainy_days_count=int(entry["rainy_days_count"]),
        hot_days_count=int(entry["hot_days_count"]),
        source=source,
    )


def _cache_put(result: MonthlyWeather) -> None:
    """Store a MonthlyWeather result in both memory and disk cache."""
    entry = asdict(result)
    entry["_cached_at"] = datetime.now(timezone.utc).isoformat()
    _mem_cache[result.year_month] = entry
    _save_disk_cache()


# Load cache from disk at module import time
_load_disk_cache()


# ---------------------------------------------------------------------------
# Philippine monthly climate priors (PAGASA Metro Manila normals)
# Last-resort fallback when Open-Meteo is unreachable
# ---------------------------------------------------------------------------

_PH_PRIORS: dict[str, dict[int, float]] = {
    "avg_temperature":   {1: 26.0, 2: 26.5, 3: 28.0, 4: 29.5, 5: 29.5,
                          6: 28.5, 7: 27.5, 8: 27.5, 9: 27.5, 10: 27.5,
                          11: 27.0, 12: 26.5},
    "avg_humidity":      {1: 78, 2: 76, 3: 74, 4: 74, 5: 78,
                          6: 82, 7: 85, 8: 85, 9: 84, 10: 82,
                          11: 80, 12: 79},
    "total_rainfall_mm": {1: 20,  2: 15,  3: 20,  4: 35,  5: 130,
                          6: 250, 7: 320, 8: 350, 9: 300, 10: 200,
                          11: 100, 12: 50},
    "hot_days_count":    {1: 4,  2: 5,  3: 12, 4: 18, 5: 17,
                          6: 10, 7: 6,  8: 6,  9: 7,  10: 8,
                          11: 7,  12: 5},
    "rainy_days_count":  {1: 5,  2: 4,  3: 5,  4: 7,  5: 14,
                          6: 20, 7: 24, 8: 23, 9: 22, 10: 18,
                          11: 13, 12: 9},
}


def _fallback(year_month: str) -> MonthlyWeather:
    """Return PAGASA climate priors for the given month."""
    try:
        m = int(year_month[5:7])
    except (ValueError, IndexError):
        m = 1
    return MonthlyWeather(
        year_month=year_month,
        avg_temperature=_PH_PRIORS["avg_temperature"][m],
        avg_humidity=_PH_PRIORS["avg_humidity"][m],
        total_rainfall_mm=_PH_PRIORS["total_rainfall_mm"][m],
        rainy_days_count=int(_PH_PRIORS["rainy_days_count"][m]),
        hot_days_count=int(_PH_PRIORS["hot_days_count"][m]),
        source="fallback",
    )


# ---------------------------------------------------------------------------
# Core fetch + aggregate
# ---------------------------------------------------------------------------


def _aggregate_daily(daily: dict, year_month: str, source: str) -> MonthlyWeather:
    """Aggregate a daily-keyed Open-Meteo response dict into MonthlyWeather."""
    temps_mean  = [v for v in daily.get("temperature_2m_mean", []) if v is not None]
    temps_max   = [v for v in daily.get("temperature_2m_max",  []) if v is not None]
    rh_max_list = [v for v in daily.get("relative_humidity_2m_max", []) if v is not None]
    rh_min_list = [v for v in daily.get("relative_humidity_2m_min", []) if v is not None]
    precip      = [v for v in daily.get("precipitation_sum",   []) if v is not None]
    prec_hours  = [v for v in daily.get("precipitation_hours", []) if v is not None]

    avg_temp = round(sum(temps_mean) / len(temps_mean), 2) if temps_mean else \
               _PH_PRIORS["avg_temperature"][int(year_month[5:7])]

    # Average of daily (max+min)/2 is a standard relative humidity estimate
    if rh_max_list and rh_min_list:
        avg_hum = round(
            sum((a + b) / 2 for a, b in zip(rh_max_list, rh_min_list)) / len(rh_max_list), 2
        )
    else:
        avg_hum = _PH_PRIORS["avg_humidity"][int(year_month[5:7])]

    total_rain  = round(sum(precip), 2) if precip else 0.0
    rainy_days  = sum(1 for h in prec_hours if h > 0)
    hot_days    = sum(1 for t in temps_max if t >= HOT_DAY_THRESHOLD)

    return MonthlyWeather(
        year_month=year_month,
        avg_temperature=avg_temp,
        avg_humidity=avg_hum,
        total_rainfall_mm=total_rain,
        rainy_days_count=rainy_days,
        hot_days_count=hot_days,
        source=source,
    )


def _first_and_last_day(year_month: str) -> tuple[str, str]:
    """Return ('YYYY-MM-01', 'YYYY-MM-DD') for a given year_month."""
    import calendar
    year, month = int(year_month[:4]), int(year_month[5:7])
    _, last_day = calendar.monthrange(year, month)
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


def _fetch_archive(year_month: str) -> Optional[MonthlyWeather]:
    """Fetch from the historical archive endpoint (data from 1940 onward)."""
    start, end = _first_and_last_day(year_month)
    params = {
        "latitude":  _LATITUDE,
        "longitude": _LONGITUDE,
        "start_date": start,
        "end_date":   end,
        "daily":      ",".join(_DAILY_VARIABLES),
        "timezone":   _TIMEZONE,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(_ARCHIVE_URL, params=params)
            resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        if not daily or not daily.get("temperature_2m_mean"):
            logger.warning("Open-Meteo archive returned no daily data for %s.", year_month)
            return None
        result = _aggregate_daily(daily, year_month, source="open-meteo-archive")
        logger.info(
            "Open-Meteo archive for %s: temp=%.1f°C hum=%.1f%% rain=%.1fmm "
            "rainy_days=%d hot_days=%d",
            year_month,
            result.avg_temperature, result.avg_humidity,
            result.total_rainfall_mm, result.rainy_days_count, result.hot_days_count,
        )
        return result
    except Exception as exc:
        logger.warning("Open-Meteo archive fetch failed for %s: %s", year_month, exc)
        return None


def _fetch_forecast_recent(year_month: str) -> Optional[MonthlyWeather]:
    """Fetch a recent month using the forecast API with start_date/end_date.

    The archive API has a ~5-day lag for the current month.  The forecast API
    carries 92 days of past data and can fill that gap.  We do NOT use past_days
    together with start_date/end_date — they are mutually exclusive parameters.
    """
    now = datetime.now(timezone.utc)
    try:
        ym_year, ym_month = int(year_month[:4]), int(year_month[5:7])
    except (ValueError, IndexError):
        return None

    months_ago = (now.year - ym_year) * 12 + (now.month - ym_month)
    if months_ago > 3:
        return None  # too far back for the forecast API's 92-day window

    start, end = _first_and_last_day(year_month)

    # Cap end_date at today — the forecast API rejects future end_dates
    today_str = now.strftime("%Y-%m-%d")
    if end > today_str:
        end = today_str
    if start > today_str:
        return None  # no data at all yet for a future month

    params = {
        "latitude":   _LATITUDE,
        "longitude":  _LONGITUDE,
        "start_date": start,
        "end_date":   end,
        "daily":      ",".join(_DAILY_VARIABLES),
        "timezone":   _TIMEZONE,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(_FORECAST_URL, params=params)
            resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        if not daily or not daily.get("temperature_2m_mean"):
            return None
        result = _aggregate_daily(daily, year_month, source="open-meteo-forecast")
        logger.info(
            "Open-Meteo forecast for %s: temp=%.1f°C hum=%.1f%% "
            "rain=%.1fmm rainy_days=%d hot_days=%d",
            year_month,
            result.avg_temperature, result.avg_humidity,
            result.total_rainfall_mm, result.rainy_days_count, result.hot_days_count,
        )
        return result
    except Exception as exc:
        logger.warning("Open-Meteo forecast fetch failed for %s: %s", year_month, exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Background fetch queue — one worker thread, prevents duplicate in-flight fetches
# ---------------------------------------------------------------------------

_fetch_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="weather-fetch")
_in_flight: set[str] = set()   # months currently being fetched in background


def _fetch_and_cache(year_month: str) -> None:
    """Fetch real weather data for *year_month* and store it in the cache.

    Intended to run in the background executor so callers never block.
    """
    now = datetime.now(timezone.utc)
    current_ym = f"{now.year:04d}-{now.month:02d}"

    if year_month > current_ym:
        result = _fallback(year_month)
    elif year_month == current_ym:
        result = (
            _fetch_forecast_recent(year_month)
            or _fetch_archive(year_month)
            or _fallback(year_month)
        )
    else:
        result = (
            _fetch_archive(year_month)
            or _fetch_forecast_recent(year_month)
            or _fallback(year_month)
        )

    with _cache_lock:
        _cache_put(result)
        _in_flight.discard(year_month)

    logger.info(
        "Weather background fetch complete for %s — source=%s.",
        year_month, result.source,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_monthly_weather(year_month: str) -> MonthlyWeather:
    """Return weather for *year_month*, never blocking the caller.

    Behaviour:
    - If the disk/memory cache has a fresh entry → return it immediately.
    - Otherwise → return the best available value right now (stale cache or
      PAGASA fallback) and schedule a background fetch to update the cache.

    This means the first call for an uncached month returns PAGASA priors
    instantly while the real data is fetched quietly in the background.
    Subsequent calls (e.g. next data entry) will find the real data cached.
    """
    with _cache_lock:
        cached = _cache_get(year_month)
        if cached is not None:
            logger.debug("Weather cache hit for %s (source=%s).", year_month, cached.source)
            return cached

        # Nothing fresh — return stale entry or PAGASA priors immediately
        stale_entry = _mem_cache.get(year_month)
        immediate = (
            MonthlyWeather(
                year_month=stale_entry["year_month"],
                avg_temperature=stale_entry["avg_temperature"],
                avg_humidity=stale_entry["avg_humidity"],
                total_rainfall_mm=stale_entry["total_rainfall_mm"],
                rainy_days_count=int(stale_entry["rainy_days_count"]),
                hot_days_count=int(stale_entry["hot_days_count"]),
                source=stale_entry["source"],
            )
            if stale_entry
            else _fallback(year_month)
        )

        # Schedule background fetch if not already in flight
        if year_month not in _in_flight:
            _in_flight.add(year_month)
            _fetch_executor.submit(_fetch_and_cache, year_month)
            logger.info(
                "Weather cache miss for %s — returning %s immediately, "
                "real fetch scheduled in background.",
                year_month, immediate.source,
            )

    return immediate


def clear_cache() -> None:
    """Clear both in-memory and on-disk weather cache."""
    with _cache_lock:
        _mem_cache.clear()
        if _CACHE_PATH.exists():
            try:
                _CACHE_PATH.unlink()
            except Exception as exc:
                logger.warning("Could not delete weather cache file: %s", exc)
    logger.info("Weather cache cleared.")
