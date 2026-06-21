"""
Generate a realistic synthetic monthly electricity bill dataset for WATT-IF.

Covers 5 years (Jan 2020 – Dec 2024) = 60 monthly rows.

New extended schema (Philippine household):
  year_month, kwh, price, meralco_rate, avg_temperature, avg_humidity,
  total_rainfall_mm, holiday_count, weekend_count, hot_days_count,
  rainy_days_count, is_el_nino, month, year

Realism factors:
  - Seasonality: hot dry season (Mar–May) has peak consumption
  - Wet season (Jun–Oct) has high rainfall, lower temp, lower consumption
  - Meralco rate drifts upward ~2%/year
  - Price derived as kwh × meralco_rate (no standing charge fiction)
  - El Niño active in 2023 (research-based)
  - Deliberate data quality issues in monthly_bills_dirty.csv

Usage:
    python data/generate_dataset.py
"""

import calendar
import csv
import math
import random
from pathlib import Path

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

START_YEAR = 2020
END_YEAR = 2024

# ── Philippine seasonal profile ───────────────────────────────────────────────
# Hot dry (Mar–May) → peak kWh; wet season (Jun–Oct) → lower kWh
# Index 0 = January
SEASONAL_KWH = [1.55, 1.45, 1.70, 1.80, 1.75, 1.35, 1.20, 1.25, 1.30, 1.40, 1.50, 1.60]

BASE_KWH = 220.0
ANNUAL_GROWTH_KWH = 0.01
KWH_NOISE_FRAC = 0.05

BASE_MERALCO_RATE = 10.50      # PHP/kWh start
ANNUAL_RATE_DRIFT = 0.02
RATE_NOISE_FRAC = 0.015

# Temperature profile (°C) — Philippine climate
AVG_TEMP = [26.5, 27.0, 28.5, 30.5, 31.2, 29.5, 28.5, 28.5, 28.8, 28.5, 27.5, 26.8]
TEMP_NOISE = 0.8

# Humidity profile (%)
AVG_HUMIDITY = [72, 70, 68, 66, 72, 80, 85, 85, 84, 82, 78, 74]
HUM_NOISE = 3.0

# Rainfall (mm/month) — wet season Jun–Oct
AVG_RAINFALL = [20, 15, 18, 25, 80, 180, 220, 200, 180, 150, 80, 35]
RAIN_NOISE_FRAC = 0.25

# Philippine public holidays per month (approximate)
HOLIDAY_COUNTS = [2, 1, 0, 1, 1, 1, 1, 2, 1, 1, 2, 3]

# Hot days (>35°C) per month
HOT_DAYS = [2, 2, 5, 10, 12, 6, 3, 3, 4, 4, 3, 2]
HOT_NOISE = 1

# Rainy days per month
RAINY_DAYS = [3, 2, 3, 4, 10, 18, 22, 20, 18, 16, 10, 5]
RAIN_DAY_NOISE = 2

# El Niño years (historically 2023 had a strong El Niño)
EL_NINO_MONTHS = {
    "2023-01", "2023-02", "2023-03", "2023-04", "2023-05",
    "2023-06", "2023-07", "2023-08", "2023-09", "2023-10",
    "2023-11", "2023-12",
}


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def generate_row(year: int, month: int) -> dict:
    ym = f"{year}-{month:02d}"
    year_idx = year - START_YEAR
    m = month - 1  # 0-based index

    # kWh
    base = BASE_KWH * ((1 + ANNUAL_GROWTH_KWH) ** year_idx)
    kwh = round(base * SEASONAL_KWH[m] * random.gauss(1.0, KWH_NOISE_FRAC), 2)
    kwh = max(80.0, kwh)

    # El Niño effect: +8% kWh during El Niño (hotter, more AC)
    is_el_nino = 1 if ym in EL_NINO_MONTHS else 0
    if is_el_nino:
        kwh = round(kwh * 1.08, 2)

    # Meralco rate
    meralco_rate = round(
        BASE_MERALCO_RATE * ((1 + ANNUAL_RATE_DRIFT) ** year_idx)
        * random.gauss(1.0, RATE_NOISE_FRAC), 4
    )
    meralco_rate = max(8.0, meralco_rate)

    # Price derived from consumption × rate
    price = round(kwh * meralco_rate, 2)

    # Weather
    avg_temp = round(clamp(random.gauss(AVG_TEMP[m], TEMP_NOISE), 22.0, 38.0), 1)
    avg_humidity = round(clamp(random.gauss(AVG_HUMIDITY[m], HUM_NOISE), 50.0, 98.0), 1)
    total_rainfall = round(
        max(0.0, AVG_RAINFALL[m] * random.gauss(1.0, RAIN_NOISE_FRAC)), 1
    )

    # Day counts
    _, days_in_month = calendar.monthrange(year, month)
    holiday_count = HOLIDAY_COUNTS[m]
    weekend_count = sum(
        1 for d in range(1, days_in_month + 1)
        if calendar.weekday(year, month, d) in (5, 6)  # Sat=5, Sun=6
    )
    hot_days = clamp(HOT_DAYS[m] + random.randint(-HOT_NOISE, HOT_NOISE), 0, days_in_month)
    rainy_days = clamp(RAINY_DAYS[m] + random.randint(-RAIN_DAY_NOISE, RAIN_DAY_NOISE), 0, days_in_month)

    return {
        "year_month": ym,
        "kwh": kwh,
        "price": price,
        "meralco_rate": meralco_rate,
        "avg_temperature": avg_temp,
        "avg_humidity": avg_humidity,
        "total_rainfall_mm": total_rainfall,
        "holiday_count": holiday_count,
        "weekend_count": int(weekend_count),
        "hot_days_count": int(hot_days),
        "rainy_days_count": int(rainy_days),
        "is_el_nino": is_el_nino,
        "month": month,
        "year": year,
    }


FIELDNAMES = [
    "year_month", "kwh", "price", "meralco_rate",
    "avg_temperature", "avg_humidity", "total_rainfall_mm",
    "holiday_count", "weekend_count", "hot_days_count", "rainy_days_count",
    "is_el_nino", "month", "year",
]


def generate_rows() -> list[dict]:
    rows = []
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            rows.append(generate_row(year, month))
    return rows


def write_clean(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Clean dataset written → {path}  ({len(rows)} rows)")


def write_dirty(rows: list[dict], path: Path) -> None:
    """Introduce deliberate data quality issues for pipeline testing."""
    import copy
    dirty = copy.deepcopy(rows)

    # Issue 1: 2021-03 kwh = blank
    for row in dirty:
        if row["year_month"] == "2021-03":
            row["kwh"] = ""
            break

    # Issue 2: 2022-08 price = "N/A"
    for row in dirty:
        if row["year_month"] == "2022-08":
            row["price"] = "N/A"
            break

    # Issue 3: duplicate 2023-01
    insert_idx = next(i for i, r in enumerate(dirty) if r["year_month"] == "2023-01")
    dup = copy.deepcopy(dirty[insert_idx])
    dup["kwh"] = round(float(dup["kwh"]) + 20.0, 2)
    dup["price"] = round(float(dup["price"]) + 250.0, 2)
    dirty.insert(insert_idx + 1, dup)

    # Issue 4: 2024-06 bad format
    for row in dirty:
        if row["year_month"] == "2024-06":
            row["year_month"] = "2024/06"
            break

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(dirty)

    print(f"Dirty dataset written  → {path}  ({len(dirty)} rows)")
    print("Issues introduced:")
    print("  • 2021-03 : kwh = '' (blank → imputed)")
    print("  • 2022-08 : price = 'N/A' (non-numeric → imputed)")
    print("  • 2023-01 : duplicate row (last wins)")
    print("  • 2024-06 : year_month = '2024/06' (bad format → rejected)")


def print_summary(rows: list[dict]) -> None:
    print("\n── Dataset summary ─────────────────────────────────────────")
    print(f"  Rows        : {len(rows)}")
    print(f"  Date range  : {rows[0]['year_month']} → {rows[-1]['year_month']}")
    kwh_vals = [float(r["kwh"]) for r in rows]
    price_vals = [float(r["price"]) for r in rows]
    rate_vals = [float(r["meralco_rate"]) for r in rows]
    print(f"  kWh range   : {min(kwh_vals):.1f} – {max(kwh_vals):.1f} kWh/month")
    print(f"  Price range : ₱{min(price_vals):.2f} – ₱{max(price_vals):.2f}/month")
    print(f"  Rate range  : ₱{min(rate_vals):.4f} – ₱{max(rate_vals):.4f}/kWh")
    el_nino = sum(1 for r in rows if int(r["is_el_nino"]) == 1)
    print(f"  El Niño     : {el_nino} months active")
    print("────────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    rows = generate_rows()
    write_clean(rows, DATA_DIR / "monthly_bills.csv")
    write_dirty(rows, DATA_DIR / "monthly_bills_dirty.csv")
    print_summary(rows)
