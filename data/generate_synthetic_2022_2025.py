"""
Generate a realistic synthetic monthly electricity dataset for WATT-IF.
Covers Jan 2022 – Dec 2025 (48 months).

Realism anchors (Philippine household, Meralco residential):
  - Meralco published residential rates by year:
      2022: ~₱9.74–10.20/kWh  (post-COVID recovery, fuel surcharges)
      2023: ~₱10.40–11.20/kWh (El Niño year, fuel hikes)
      2024: ~₱11.50–12.20/kWh (generation charge increases)
      2025: ~₱11.80–12.60/kWh (modest continued rise)
  - kWh baseline: ~280 kWh/month (lower-middle household, 3BR Metro Manila)
  - Seasonal pattern: peak Mar–May (hot dry), trough Jul–Sep (wet/cool)
  - El Niño 2023: +10% kWh, hotter temps, less rainfall
  - 2024–2025: neutral / La Niña tendencies
  - Slight annual consumption growth (~1.5%/yr, appliance creep)
  - Month-to-month noise: ±5%

Usage:
    python data/generate_synthetic_2022_2025.py
"""

import calendar
import csv
import random
from pathlib import Path

RANDOM_SEED = 2022
random.seed(RANDOM_SEED)

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUT_PATH = DATA_DIR / "synthetic_2022_2025.csv"

START_YEAR = 2022
END_YEAR   = 2025

# ── kWh baseline & seasonality ────────────────────────────────────────────────
BASE_KWH = 280.0           # monthly baseline (kWh)
ANNUAL_KWH_GROWTH = 0.015  # 1.5% per year

# Seasonal multiplier by month (Jan=0 … Dec=11)
# Peak: Mar–May (summer, AC blasting); trough: Jul–Sep (rainy, cooler)
SEASONAL_KWH = [
    1.30,  # Jan
    1.22,  # Feb
    1.45,  # Mar  ← hot dry season starts
    1.60,  # Apr  ← peak
    1.55,  # May  ← still hot
    1.15,  # Jun  ← rainy season starts
    1.00,  # Jul  ← coolest
    1.02,  # Aug
    1.05,  # Sep
    1.12,  # Oct  ← tail of wet season
    1.25,  # Nov
    1.38,  # Dec  ← holiday at home, some cold fronts
]

KWH_NOISE_FRAC = 0.05

# ── Meralco residential rate (₱/kWh) — monthly anchors ───────────────────────
# Based on published ERC-approved Meralco rate tables.
# Interpolated between actual known values.
MERALCO_RATE_BY_YM: dict[str, float] = {
    # 2022 — rates recovering from COVID-era suppression
    "2022-01": 9.74,  "2022-02": 9.80,  "2022-03": 9.88,
    "2022-04": 9.95,  "2022-05": 10.02, "2022-06": 10.08,
    "2022-07": 10.10, "2022-08": 10.15, "2022-09": 10.18,
    "2022-10": 10.20, "2022-11": 10.22, "2022-12": 10.25,
    # 2023 — fuel surcharges + El Niño demand spike
    "2023-01": 10.40, "2023-02": 10.48, "2023-03": 10.55,
    "2023-04": 10.62, "2023-05": 10.70, "2023-06": 10.75,
    "2023-07": 10.80, "2023-08": 10.90, "2023-09": 11.00,
    "2023-10": 11.10, "2023-11": 11.15, "2023-12": 11.20,
    # 2024 — generation charge increases
    "2024-01": 11.50, "2024-02": 11.55, "2024-03": 11.62,
    "2024-04": 11.68, "2024-05": 11.74, "2024-06": 11.80,
    "2024-07": 11.85, "2024-08": 11.90, "2024-09": 11.95,
    "2024-10": 12.00, "2024-11": 12.10, "2024-12": 12.20,
    # 2025 — modest continued rise
    "2025-01": 11.80, "2025-02": 11.85, "2025-03": 11.92,
    "2025-04": 12.00, "2025-05": 12.08, "2025-06": 12.15,
    "2025-07": 12.20, "2025-08": 12.25, "2025-09": 12.30,
    "2025-10": 12.38, "2025-11": 12.45, "2025-12": 12.55,
}
RATE_NOISE_FRAC = 0.008  # ±0.8% month-to-month variance

# ── ENSO classification ───────────────────────────────────────────────────────
# 2022: La Niña (continuing from late 2021)
# 2023: El Niño (onset ~Jun 2023, peak Oct–Dec)
# 2024: Neutral → transitioning La Niña (late 2024)
# 2025: La Niña conditions
ENSO_BY_YM: dict[str, int] = {
    # 2022 — La Niña (is_el_nino = 0, cooler/wetter than normal)
    **{f"2022-{m:02d}": 0 for m in range(1, 13)},
    # 2023 — El Niño developing then strong
    "2023-01": 0, "2023-02": 0, "2023-03": 0,
    "2023-04": 0, "2023-05": 0, "2023-06": 1,
    "2023-07": 1, "2023-08": 1, "2023-09": 1,
    "2023-10": 1, "2023-11": 1, "2023-12": 1,
    # 2024 — El Niño weakening → neutral → La Niña
    "2024-01": 1, "2024-02": 1, "2024-03": 1,
    "2024-04": 0, "2024-05": 0, "2024-06": 0,
    "2024-07": 0, "2024-08": 0, "2024-09": 0,
    "2024-10": 0, "2024-11": 0, "2024-12": 0,
    # 2025 — La Niña (cooler/wetter)
    **{f"2025-{m:02d}": 0 for m in range(1, 13)},
}

# ── El Niño adjustments ───────────────────────────────────────────────────────
EL_NINO_KWH_BOOST   = 0.10   # +10% consumption (more AC)
EL_NINO_TEMP_BOOST  = 1.2    # +1.2°C average
EL_NINO_RAIN_FACTOR = 0.65   # 35% less rainfall
LA_NINA_KWH_PENALTY = -0.04  # −4% consumption (cooler)
LA_NINA_TEMP_PENALTY = -0.8  # −0.8°C
LA_NINA_RAIN_FACTOR  = 1.30  # 30% more rainfall

# ── Temperature profile (°C) — Metro Manila monthly normals ──────────────────
AVG_TEMP_BASE = [
    26.2, 26.6, 27.8, 29.8, 30.5,  # Jan–May
    29.2, 28.2, 28.1, 28.3, 28.2,  # Jun–Oct
    27.4, 26.6,                      # Nov–Dec
]
TEMP_NOISE_SD = 0.7

# ── Humidity profile (%) ──────────────────────────────────────────────────────
AVG_HUMIDITY_BASE = [
    74, 72, 70, 68, 74,   # Jan–May (dry → getting humid)
    82, 86, 86, 85, 83,   # Jun–Oct (wet season)
    80, 76,               # Nov–Dec
]
HUM_NOISE_SD = 2.5

# ── Rainfall (mm/month) ───────────────────────────────────────────────────────
AVG_RAINFALL_BASE = [
    18, 12, 16, 28, 95,   # Jan–May
    200, 260, 240, 210, 165,  # Jun–Oct
    75, 30,               # Nov–Dec
]
RAIN_NOISE_FRAC = 0.22

# ── Hot days (max temp ≥ 33°C) ────────────────────────────────────────────────
HOT_DAYS_BASE = [3, 3, 7, 14, 15, 8, 4, 4, 5, 5, 4, 2]
HOT_DAYS_NOISE = 2

# ── Rainy days per month ──────────────────────────────────────────────────────
RAINY_DAYS_BASE = [4, 3, 4, 5, 12, 20, 24, 23, 21, 17, 11, 6]
RAINY_DAYS_NOISE = 2

# ── Philippine public holidays per month ─────────────────────────────────────
HOLIDAY_COUNTS = [2, 1, 0, 2, 2, 1, 1, 2, 1, 1, 2, 4]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def generate_row(year: int, month: int) -> dict:
    ym = f"{year}-{month:02d}"
    m  = month - 1  # 0-based
    year_idx = year - START_YEAR  # 0-based from 2022

    is_el_nino = ENSO_BY_YM.get(ym, 0)
    # La Niña: 2022 + 2025
    is_la_nina = 1 if year in (2022, 2025) else 0

    # ── kWh ──────────────────────────────────────────────────────────────────
    base_kwh = BASE_KWH * ((1 + ANNUAL_KWH_GROWTH) ** year_idx)
    kwh = base_kwh * SEASONAL_KWH[m] * random.gauss(1.0, KWH_NOISE_FRAC)
    if is_el_nino:
        kwh *= (1 + EL_NINO_KWH_BOOST)
    elif is_la_nina:
        kwh *= (1 + LA_NINA_KWH_PENALTY)
    kwh = round(max(100.0, kwh), 2)

    # ── Meralco rate ──────────────────────────────────────────────────────────
    base_rate = MERALCO_RATE_BY_YM[ym]
    meralco_rate = round(base_rate * random.gauss(1.0, RATE_NOISE_FRAC), 4)
    meralco_rate = max(8.0, meralco_rate)

    # ── Price ─────────────────────────────────────────────────────────────────
    price = round(kwh * meralco_rate, 2)

    # ── Temperature ───────────────────────────────────────────────────────────
    temp = random.gauss(AVG_TEMP_BASE[m], TEMP_NOISE_SD)
    if is_el_nino:
        temp += EL_NINO_TEMP_BOOST
    elif is_la_nina:
        temp += LA_NINA_TEMP_PENALTY
    avg_temperature = round(clamp(temp, 22.0, 38.0), 1)

    # ── Humidity ──────────────────────────────────────────────────────────────
    avg_humidity = round(clamp(random.gauss(AVG_HUMIDITY_BASE[m], HUM_NOISE_SD), 50.0, 98.0), 1)

    # ── Rainfall ──────────────────────────────────────────────────────────────
    rain_base = AVG_RAINFALL_BASE[m]
    if is_el_nino:
        rain_base *= EL_NINO_RAIN_FACTOR
    elif is_la_nina:
        rain_base *= LA_NINA_RAIN_FACTOR
    total_rainfall_mm = round(max(0.0, rain_base * random.gauss(1.0, RAIN_NOISE_FRAC)), 1)

    # ── Day counts ────────────────────────────────────────────────────────────
    _, days_in_month = calendar.monthrange(year, month)
    weekend_count = sum(
        1 for d in range(1, days_in_month + 1)
        if calendar.weekday(year, month, d) in (5, 6)
    )
    holiday_count = HOLIDAY_COUNTS[m]

    hot_days_raw = HOT_DAYS_BASE[m]
    if is_el_nino:
        hot_days_raw = int(hot_days_raw * 1.4)
    hot_days = int(clamp(hot_days_raw + random.randint(-HOT_DAYS_NOISE, HOT_DAYS_NOISE), 0, days_in_month))

    rainy_days_raw = RAINY_DAYS_BASE[m]
    if is_el_nino:
        rainy_days_raw = int(rainy_days_raw * 0.7)
    elif is_la_nina:
        rainy_days_raw = int(rainy_days_raw * 1.2)
    rainy_days = int(clamp(rainy_days_raw + random.randint(-RAINY_DAYS_NOISE, RAINY_DAYS_NOISE), 0, days_in_month))

    return {
        "year_month":        ym,
        "kwh":               kwh,
        "price":             price,
        "meralco_rate":      meralco_rate,
        "avg_temperature":   avg_temperature,
        "avg_humidity":      avg_humidity,
        "total_rainfall_mm": total_rainfall_mm,
        "holiday_count":     holiday_count,
        "weekend_count":     int(weekend_count),
        "hot_days_count":    hot_days,
        "rainy_days_count":  rainy_days,
        "is_el_nino":        is_el_nino,
    }


FIELDNAMES = [
    "year_month", "kwh", "price", "meralco_rate",
    "avg_temperature", "avg_humidity", "total_rainfall_mm",
    "holiday_count", "weekend_count", "hot_days_count",
    "rainy_days_count", "is_el_nino",
]


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    rows = []
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            rows.append(generate_row(year, month))

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    # ── Summary ───────────────────────────────────────────────────────────────
    kwh_vals   = [r["kwh"] for r in rows]
    price_vals = [r["price"] for r in rows]
    rate_vals  = [r["meralco_rate"] for r in rows]
    el_nino_n  = sum(r["is_el_nino"] for r in rows)

    print(f"\n✓ Synthetic dataset written → {OUT_PATH}")
    print(f"  Rows        : {len(rows)}  ({START_YEAR}-01 → {END_YEAR}-12)")
    print(f"  kWh range   : {min(kwh_vals):.1f} – {max(kwh_vals):.1f} kWh/month")
    print(f"  Price range : ₱{min(price_vals):.2f} – ₱{max(price_vals):.2f}/month")
    print(f"  Rate range  : ₱{min(rate_vals):.4f} – ₱{max(rate_vals):.4f}/kWh")
    print(f"  El Niño     : {el_nino_n} months  (2023-Jun – 2024-Mar)")
    print(f"\n  Sample rows:")
    for r in rows[:3] + rows[23:26] + rows[-3:]:
        print(f"    {r['year_month']}  {r['kwh']:6.1f} kWh  "
              f"₱{r['price']:7.2f}  rate=₱{r['meralco_rate']:.4f}  "
              f"temp={r['avg_temperature']}°C  "
              f"el_nino={r['is_el_nino']}")
    print()


if __name__ == "__main__":
    main()
