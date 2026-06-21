"""
Exploratory Data Analysis for WATT-IF monthly electricity bill dataset.

Reads data/monthly_bills.csv (new extended schema), computes statistics, and
writes human-readable narrative summaries to data/eda_summaries.json for
ChromaDB RAG ingestion.

New columns supported:
  meralco_rate, avg_temperature, avg_humidity, total_rainfall_mm,
  holiday_count, weekend_count, hot_days_count, rainy_days_count, is_el_nino

Usage:
    python data/eda.py
"""

from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CSV_PATH = DATA_DIR / "monthly_bills.csv"
OUTPUT_PATH = DATA_DIR / "eda_summaries.json"

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _i(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def month_name(ym: str) -> str:
    year, month = ym.split("-")
    return f"{MONTH_NAMES[int(month) - 1]} {year}"


def pct_change(old: float, new: float) -> float:
    return ((new - old) / old * 100) if old else 0.0


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    sx, sy = stdev(xs), stdev(ys)
    if sx == 0 or sy == 0:
        return 0.0
    return mean([(x - mx) * (y - my) for x, y in zip(xs, ys)]) / (sx * sy)


# ── EDA ───────────────────────────────────────────────────────────────────────

def run_eda(rows: list[dict]) -> list[dict[str, str]]:
    """Run EDA and return list of {id, text} summaries."""
    records = []
    for r in rows:
        records.append({
            "ym": r["year_month"],
            "year": int(r["year_month"][:4]),
            "month": int(r["year_month"][5:7]),
            "kwh": _f(r.get("kwh", 0)),
            "price": _f(r.get("price", 0)),
            "meralco_rate": _f(r.get("meralco_rate", 0)),
            "avg_temperature": _f(r.get("avg_temperature", 0)),
            "avg_humidity": _f(r.get("avg_humidity", 0)),
            "total_rainfall_mm": _f(r.get("total_rainfall_mm", 0)),
            "holiday_count": _i(r.get("holiday_count", 0)),
            "weekend_count": _i(r.get("weekend_count", 0)),
            "hot_days_count": _i(r.get("hot_days_count", 0)),
            "rainy_days_count": _i(r.get("rainy_days_count", 0)),
            "is_el_nino": _i(r.get("is_el_nino", 0)),
        })

    kwh_all   = [r["kwh"]   for r in records]
    price_all = [r["price"] for r in records]
    rate_all  = [r["meralco_rate"] for r in records]
    temp_all  = [r["avg_temperature"] for r in records]
    hum_all   = [r["avg_humidity"] for r in records]
    rain_all  = [r["total_rainfall_mm"] for r in records]

    summaries: list[dict[str, str]] = []

    by_year: dict[int, list[dict]] = defaultdict(list)
    by_month_idx: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        by_year[r["year"]].append(r)
        by_month_idx[r["month"]].append(r)

    # ── 1. Dataset overview ───────────────────────────────────────────────────
    summaries.append({
        "id": "eda_overview",
        "text": (
            f"Dataset overview: {len(records)} monthly electricity bill records "
            f"from {month_name(records[0]['ym'])} to {month_name(records[-1]['ym'])}. "
            f"Average monthly consumption is {mean(kwh_all):.1f} kWh (range: {min(kwh_all):.1f}–{max(kwh_all):.1f} kWh). "
            f"Average monthly electricity bill is ₱{mean(price_all):.2f} (range: ₱{min(price_all):.2f}–₱{max(price_all):.2f}). "
            f"Average Meralco rate is ₱{mean(rate_all):.4f}/kWh (range: ₱{min(rate_all):.4f}–₱{max(rate_all):.4f}/kWh). "
            f"Average temperature is {mean(temp_all):.1f}°C. "
            f"Average humidity is {mean(hum_all):.1f}%. "
            f"These averages serve as the baseline for comparing any individual month's forecast."
        ),
    })

    # ── 2. Annual summaries ───────────────────────────────────────────────────
    for year, yr in sorted(by_year.items()):
        kwh_v  = [r["kwh"] for r in yr]
        price_v = [r["price"] for r in yr]
        peak = max(yr, key=lambda r: r["kwh"])
        low  = min(yr, key=lambda r: r["kwh"])
        avg_rate = mean([r["meralco_rate"] for r in yr])
        avg_temp = mean([r["avg_temperature"] for r in yr])
        el_nino_months = sum(r["is_el_nino"] for r in yr)
        el_nino_note = (
            f"El Niño was active for {el_nino_months} month(s) in {year}, "
            f"contributing to higher temperatures and potentially higher consumption."
            if el_nino_months > 0
            else f"El Niño was not active in {year}, so weather conditions were relatively normal."
        )
        summaries.append({
            "id": f"eda_annual_{year}",
            "text": (
                f"Annual summary for {year}: "
                f"Average monthly consumption was {mean(kwh_v):.1f} kWh (total {sum(kwh_v):.1f} kWh). "
                f"Average monthly bill was ₱{mean(price_v):.2f} (total ₱{sum(price_v):.2f}). "
                f"Average Meralco rate was ₱{avg_rate:.4f}/kWh. "
                f"Average temperature was {avg_temp:.1f}°C. "
                f"Peak consumption month: {month_name(peak['ym'])} at {peak['kwh']:.1f} kWh (₱{peak['price']:.2f}). "
                f"Lowest consumption month: {month_name(low['ym'])} at {low['kwh']:.1f} kWh (₱{low['price']:.2f}). "
                f"{el_nino_note}"
            ),
        })

    # ── 3. Year-over-year changes ─────────────────────────────────────────────
    sorted_years = sorted(by_year.keys())
    for i in range(1, len(sorted_years)):
        py, cy = sorted_years[i - 1], sorted_years[i]
        pk = sum(r["kwh"] for r in by_year[py])
        ck = sum(r["kwh"] for r in by_year[cy])
        pp = sum(r["price"] for r in by_year[py])
        cp = sum(r["price"] for r in by_year[cy])
        summaries.append({
            "id": f"eda_yoy_{py}_{cy}",
            "text": (
                f"Year-over-year {py}→{cy}: "
                f"kWh {pct_change(pk, ck):+.1f}% ({pk:.1f}→{ck:.1f} kWh). "
                f"Bill {pct_change(pp, cp):+.1f}% (₱{pp:.2f}→₱{cp:.2f})."
            ),
        })

    # ── 4. Monthly seasonality ────────────────────────────────────────────────
    season_lines = []
    for m in range(1, 13):
        mr = by_month_idx[m]
        season_lines.append(
            f"{MONTH_NAMES[m-1]}: avg {mean([r['kwh'] for r in mr]):.1f} kWh, "
            f"₱{mean([r['price'] for r in mr]):.2f}, "
            f"{mean([r['avg_temperature'] for r in mr]):.1f}°C"
        )
    peak_m = max(range(1, 13), key=lambda m: mean([r["kwh"] for r in by_month_idx[m]]))
    trough_m = min(range(1, 13), key=lambda m: mean([r["kwh"] for r in by_month_idx[m]]))
    peak_kwh = mean([r["kwh"] for r in by_month_idx[peak_m]])
    trough_kwh = mean([r["kwh"] for r in by_month_idx[trough_m]])
    diff_pct = ((peak_kwh - trough_kwh) / trough_kwh * 100) if trough_kwh > 0 else 0.0
    summaries.append({
        "id": "eda_seasonality",
        "text": (
            f"Monthly seasonality patterns (averaged across all years): " + "; ".join(season_lines) + ". "
            f"{MONTH_NAMES[peak_m-1]} is historically the highest consumption month "
            f"(avg {peak_kwh:.1f} kWh), while {MONTH_NAMES[trough_m-1]} is the lowest "
            f"(avg {trough_kwh:.1f} kWh) — a difference of {diff_pct:.1f}%. "
            f"This seasonal pattern is driven primarily by temperature and weather variation across the year. "
            f"Summer months (March–May) tend to be hotter and drier, increasing cooling load. "
            f"Rainy season months (June–October) tend to be cooler, reducing cooling demand."
        ),
    })

    # ── 5. Long-term trends ───────────────────────────────────────────────────
    n = len(records)
    x = list(range(n))
    x_mean = mean(x)
    denom = sum((xi - x_mean) ** 2 for xi in x)

    def slope(ys):
        return sum((xi - x_mean) * (yi - mean(ys)) for xi, yi in zip(x, ys)) / denom if denom else 0.0

    kwh_slope   = slope(kwh_all)
    price_slope = slope(price_all)
    rate_slope  = slope(rate_all)
    summaries.append({
        "id": "eda_trend",
        "text": (
            f"Long-term trends over {n} months: "
            f"kWh {'increasing' if kwh_slope > 0 else 'decreasing'} "
            f"~{abs(kwh_slope):.2f} kWh/month. "
            f"Bill price {'increasing' if price_slope > 0 else 'decreasing'} "
            f"~₱{abs(price_slope):.2f}/month. "
            f"Meralco rate {'increasing' if rate_slope > 0 else 'decreasing'} "
            f"~₱{abs(rate_slope):.5f}/kWh per month."
        ),
    })

    # ── 6. Meralco rate trend ─────────────────────────────────────────────────
    yr_rate_lines = [
        f"{year}: ₱{mean([r['meralco_rate'] for r in yr]):.4f}/kWh"
        for year, yr in sorted(by_year.items())
    ]
    rate_direction = "increased" if rate_slope > 0 else "decreased"
    summaries.append({
        "id": "eda_meralco_rate",
        "text": (
            f"Meralco rate trend: The average electricity rate has {rate_direction} over time. "
            f"Overall average: ₱{mean(rate_all):.4f}/kWh (min ₱{min(rate_all):.4f}, max ₱{max(rate_all):.4f}). "
            f"Annual averages: {'; '.join(yr_rate_lines)}. "
            f"The Meralco rate directly determines how much the bill costs per kWh consumed. "
            f"Even if consumption stays the same, a higher rate will increase the estimated bill."
        ),
    })

    # ── 7. Top/bottom consumption months ─────────────────────────────────────
    by_kwh = sorted(records, key=lambda r: r["kwh"], reverse=True)
    top5 = ", ".join(f"{month_name(r['ym'])} ({r['kwh']:.1f} kWh, {r['avg_temperature']:.1f}°C)" for r in by_kwh[:5])
    bot5 = ", ".join(f"{month_name(r['ym'])} ({r['kwh']:.1f} kWh, {r['avg_temperature']:.1f}°C)" for r in reversed(by_kwh[-5:]))
    summaries.append({
        "id": "eda_extremes_kwh",
        "text": (
            f"Highest consumption months: {top5}. "
            f"Lowest consumption months: {bot5}. "
            f"Notice that the highest consumption months tend to coincide with higher average temperatures, "
            f"reflecting increased use of cooling appliances like fans and air conditioners."
        ),
    })

    # ── 8. Top/bottom bill months ─────────────────────────────────────────────
    by_price = sorted(records, key=lambda r: r["price"], reverse=True)
    top5p = ", ".join(f"{month_name(r['ym'])} (₱{r['price']:.2f}, rate ₱{r['meralco_rate']:.4f}/kWh)" for r in by_price[:5])
    bot5p = ", ".join(f"{month_name(r['ym'])} (₱{r['price']:.2f}, rate ₱{r['meralco_rate']:.4f}/kWh)" for r in reversed(by_price[-5:]))
    summaries.append({
        "id": "eda_extremes_price",
        "text": (
            f"Highest bill months: {top5p}. "
            f"Lowest bill months: {bot5p}. "
            f"A high bill can be caused by high consumption, a high Meralco rate, or both. "
            f"The Meralco rate shown alongside each month helps identify whether the bill is driven by "
            f"consumption or by rate increases."
        ),
    })

    # ── 9. Temperature vs kWh ─────────────────────────────────────────────────
    corr_temp = pearson(temp_all, kwh_all)
    hot_records = [r for r in records if r["avg_temperature"] >= 30]
    cool_records = [r for r in records if r["avg_temperature"] < 28]
    hot_avg = mean([r["kwh"] for r in hot_records]) if hot_records else 0.0
    cool_avg = mean([r["kwh"] for r in cool_records]) if cool_records else 0.0
    temp_effect = "increases" if corr_temp > 0 else "decreases"
    corr_strength = "strong" if abs(corr_temp) >= 0.5 else ("moderate" if abs(corr_temp) >= 0.3 else "weak")
    summaries.append({
        "id": "eda_temperature_vs_kwh",
        "text": (
            f"Temperature and electricity consumption relationship: "
            f"There is a {corr_strength} {'positive' if corr_temp > 0 else 'negative'} correlation "
            f"(Pearson r = {corr_temp:.3f}) between average monthly temperature and kWh consumption. "
            f"Months with average temperature ≥30°C consumed an average of {hot_avg:.1f} kWh, "
            f"compared to {cool_avg:.1f} kWh for months with temperature <28°C. "
            f"This means higher temperatures tend to {temp_effect} electricity consumption, "
            f"likely because of greater use of fans and air conditioners during hot months. "
            f"When a forecast month has a high average temperature, expect higher than normal consumption."
        ),
    })

    # ── 10. Rainfall vs kWh ───────────────────────────────────────────────────
    corr_rain = pearson(rain_all, kwh_all)
    avg_rain = mean(rain_all)
    rainy_records = [r for r in records if r["total_rainfall_mm"] > avg_rain]
    dry_records   = [r for r in records if r["total_rainfall_mm"] <= avg_rain]
    rainy_avg = mean([r["kwh"] for r in rainy_records]) if rainy_records else 0.0
    dry_avg   = mean([r["kwh"] for r in dry_records]) if dry_records else 0.0
    rain_effect = "decreases" if corr_rain < 0 else "increases"
    summaries.append({
        "id": "eda_rainfall_vs_kwh",
        "text": (
            f"Rainfall and electricity consumption relationship: "
            f"Pearson r = {corr_rain:.3f} between total monthly rainfall and kWh consumption. "
            f"Wetter months (above the average rainfall of {avg_rain:.1f} mm) consumed an average of "
            f"{rainy_avg:.1f} kWh, compared to {dry_avg:.1f} kWh for drier months. "
            f"Higher rainfall generally brings cooler temperatures, which tends to {rain_effect} "
            f"electricity consumption by reducing the need for cooling appliances. "
            f"A forecast month with high rainfall and more rainy days is likely to have lower consumption."
        ),
    })

    # ── 11. Holiday effects ───────────────────────────────────────────────────
    holiday_all = [r["holiday_count"] for r in records]
    corr_hol = pearson([float(h) for h in holiday_all], kwh_all)
    avg_holidays = mean([float(h) for h in holiday_all])
    many_hol = [r for r in records if r["holiday_count"] >= 3]
    few_hol  = [r for r in records if r["holiday_count"] < 3]
    many_avg = mean([r["kwh"] for r in many_hol]) if many_hol else 0.0
    few_avg  = mean([r["kwh"] for r in few_hol]) if few_hol else 0.0
    summaries.append({
        "id": "eda_holiday_effects",
        "text": (
            f"Holiday and weekend effects on electricity consumption: "
            f"Pearson r between holiday count and kWh = {corr_hol:.3f}. "
            f"Months with 3 or more holidays averaged {many_avg:.1f} kWh, "
            f"compared to {few_avg:.1f} kWh for months with fewer holidays. "
            f"The average month has {avg_holidays:.1f} holiday(s). "
            f"More holidays and weekends mean more time spent at home, which can "
            f"increase household electricity consumption through prolonged appliance use."
        ),
    })

    # ── 12. El Niño effects ───────────────────────────────────────────────────
    el_nino_records = [r for r in records if r["is_el_nino"] == 1]
    normal_records  = [r for r in records if r["is_el_nino"] == 0]
    el_nino_pct = len(el_nino_records) / len(records) * 100 if records else 0
    en_kwh_avg  = mean([r["kwh"] for r in el_nino_records]) if el_nino_records else 0.0
    nm_kwh_avg  = mean([r["kwh"] for r in normal_records]) if normal_records else 0.0
    en_price_avg = mean([r["price"] for r in el_nino_records]) if el_nino_records else 0.0
    nm_price_avg = mean([r["price"] for r in normal_records]) if normal_records else 0.0
    en_temp_avg  = mean([r["avg_temperature"] for r in el_nino_records]) if el_nino_records else 0.0
    nm_temp_avg  = mean([r["avg_temperature"] for r in normal_records]) if normal_records else 0.0
    kwh_diff_pct = ((en_kwh_avg - nm_kwh_avg) / nm_kwh_avg * 100) if nm_kwh_avg > 0 else 0.0
    summaries.append({
        "id": "eda_el_nino_effects",
        "text": (
            f"El Niño effects on electricity consumption: "
            f"{len(el_nino_records)} of {len(records)} months ({el_nino_pct:.1f}%) had El Niño active. "
            f"During El Niño months, average consumption was {en_kwh_avg:.1f} kWh "
            f"(₱{en_price_avg:.2f}/month), compared to {nm_kwh_avg:.1f} kWh "
            f"(₱{nm_price_avg:.2f}/month) during non–El Niño months — "
            f"a difference of {kwh_diff_pct:+.1f}%. "
            f"El Niño months were also hotter on average: {en_temp_avg:.1f}°C vs "
            f"{nm_temp_avg:.1f}°C in normal months. "
            f"When a forecast month is marked as El Niño active, expect higher than normal "
            f"temperatures and electricity consumption due to the drier, hotter conditions El Niño brings."
        ),
    })

    # ── 13. Quarterly averages ────────────────────────────────────────────────
    def quarter(m): return ["Q1","Q1","Q1","Q2","Q2","Q2","Q3","Q3","Q3","Q4","Q4","Q4"][m-1]
    by_q: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_q[quarter(r["month"])].append(r)
    q_lines = [
        f"{q}: avg {mean([r['kwh'] for r in by_q[q]]):.1f} kWh, "
        f"₱{mean([r['price'] for r in by_q[q]]):.2f}, "
        f"{mean([r['avg_temperature'] for r in by_q[q]]):.1f}°C"
        for q in ["Q1", "Q2", "Q3", "Q4"]
    ]
    q_peak = max(["Q1","Q2","Q3","Q4"], key=lambda q: mean([r["kwh"] for r in by_q[q]]))
    q_trough = min(["Q1","Q2","Q3","Q4"], key=lambda q: mean([r["kwh"] for r in by_q[q]]))
    quarter_names = {"Q1": "January–March", "Q2": "April–June", "Q3": "July–September", "Q4": "October–December"}
    summaries.append({
        "id": "eda_quarterly",
        "text": (
            f"Quarterly electricity consumption patterns: " + "; ".join(q_lines) + ". "
            f"{q_peak} ({quarter_names[q_peak]}) is the highest consumption quarter, "
            f"typically coinciding with the hottest months of the year in the Philippines. "
            f"{q_trough} ({quarter_names[q_trough]}) is the lowest consumption quarter."
        ),
    })

    # ── 14. Humidity vs kWh ───────────────────────────────────────────────────
    corr_hum = pearson(hum_all, kwh_all)
    summaries.append({
        "id": "eda_humidity_vs_kwh",
        "text": (
            f"Humidity and electricity consumption relationship: "
            f"Pearson r = {corr_hum:.3f} between average monthly humidity and kWh consumption. "
            f"Average humidity across all months is {mean(hum_all):.1f}% "
            f"(range {min(hum_all):.1f}–{max(hum_all):.1f}%). "
            f"Higher humidity is typically associated with wetter, cooler months (rainy season), "
            f"which may moderately reduce electricity demand from cooling."
        ),
    })

    # ── 15. Per-month all-time records ────────────────────────────────────────
    record_lines = []
    for m in range(1, 13):
        mr = by_month_idx[m]
        if not mr:
            continue
        best  = max(mr, key=lambda r: r["kwh"])
        worst = min(mr, key=lambda r: r["kwh"])
        record_lines.append(
            f"{MONTH_NAMES[m-1]}: highest {best['kwh']:.1f} kWh ({best['year']}), "
            f"lowest {worst['kwh']:.1f} kWh ({worst['year']})"
        )
    summaries.append({
        "id": "eda_monthly_records",
        "text": (
            f"All-time consumption records per calendar month: " + "; ".join(record_lines) + ". "
            f"These records can help identify whether a forecast for a given month is unusually high "
            f"or low compared to historical observations for the same month."
        ),
    })

    # ── 16. What affects the electricity bill most ────────────────────────────
    factors = [
        ("Meralco rate", abs(pearson(rate_all, price_all))),
        ("Average temperature", abs(pearson(temp_all, price_all))),
        ("Total rainfall", abs(pearson(rain_all, price_all))),
        ("Humidity", abs(pearson(hum_all, price_all))),
        ("Holiday count", abs(pearson([float(r["holiday_count"]) for r in records], price_all))),
        ("El Niño", abs(pearson([float(r["is_el_nino"]) for r in records], price_all))),
        ("Hot days", abs(pearson([float(r["hot_days_count"]) for r in records], price_all))),
        ("Rainy days", abs(pearson([float(r["rainy_days_count"]) for r in records], price_all))),
    ]
    factors_sorted = sorted(factors, key=lambda x: x[1], reverse=True)
    factor_lines = [f"{name} (r={corr:.3f})" for name, corr in factors_sorted]
    summaries.append({
        "id": "eda_bill_drivers",
        "text": (
            f"What affects the electricity bill the most (correlation with monthly bill amount): "
            + "; ".join(factor_lines) + ". "
            f"The strongest driver is {factors_sorted[0][0]}, followed by {factors_sorted[1][0]}. "
            f"This ranking reflects which variables are most predictive of bill changes over time."
        ),
    })

    # ── 17. Hot days vs kWh ───────────────────────────────────────────────────
    hot_days_all = [float(r["hot_days_count"]) for r in records]
    corr_hot = pearson(hot_days_all, kwh_all)
    avg_hot_days = mean(hot_days_all)
    many_hot = [r for r in records if r["hot_days_count"] >= avg_hot_days]
    few_hot  = [r for r in records if r["hot_days_count"] < avg_hot_days]
    many_hot_avg = mean([r["kwh"] for r in many_hot]) if many_hot else 0.0
    few_hot_avg  = mean([r["kwh"] for r in few_hot]) if few_hot else 0.0
    summaries.append({
        "id": "eda_hot_days_vs_kwh",
        "text": (
            f"Hot days and electricity consumption relationship: "
            f"Pearson r = {corr_hot:.3f} between hot day count and monthly kWh. "
            f"Average hot days per month: {avg_hot_days:.1f}. "
            f"Months with above-average hot days consumed {many_hot_avg:.1f} kWh on average, "
            f"vs {few_hot_avg:.1f} kWh for months with fewer hot days. "
            f"Hot days directly increase the number of hours that cooling appliances run, "
            f"which is why forecasts for months with many hot days tend to be higher."
        ),
    })

    return summaries


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Loading data from: {CSV_PATH}")
    rows = load_csv(CSV_PATH)
    print(f"  Loaded {len(rows)} rows.\n")
    summaries = run_eda(rows)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(summaries)} EDA summaries → {OUTPUT_PATH}\n")
    for s in summaries:
        print(f"  [{s['id']}]  {s['text'][:100]}…")


if __name__ == "__main__":
    main()
