"""
Meralco rate scraper for WATT-IF.

Downloads the official Summary Schedule of Rates PDF from Meralco's S3 bucket
and parses all customer types and their consumption brackets.

URL pattern:
  https://meralcomain.s3.ap-southeast-1.amazonaws.com/YYYY-MM/MM-YYYY_rate_schedule.pdf

Results are cached in memory for 24 hours.

Public API
----------
get_rate()     -> MeralcoRateResult   (uses cache)
refresh_rate() -> MeralcoRateResult   (bypasses cache)
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import pdfplumber

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_TTL = timedelta(hours=24)

_VAT = {
    "generation":   0.0922,
    "transmission": 0.1114,
    "system_loss":  0.0946,
    "other":        0.12,
}

# Customer types and the PDF row labels that belong to each.
# Each entry: (customer_type_key, customer_type_label, [(pdf_row_label, friendly_label), ...])
_CUSTOMER_TYPES = [
    (
        "Residential",
        "Residential",
        [
            ("0 TO 50 KWH",    "0–50 kWh"),
            ("51 TO 70 KWH",   "51–70 kWh"),
            ("71 TO 100 KWH",  "71–100 kWh"),
            ("101 TO 200 KWH", "101–200 kWh"),
            ("201 TO 300 KWH", "201–300 kWh"),
            ("301 TO 400 KWH", "301–400 kWh"),
            ("OVER 400 KWH",   "Over 400 kWh"),
        ],
    ),
    (
        "General Service A",
        "General Service A",
        [
            ("0 TO 200 KWH",   "0–200 kWh"),
            ("201 TO 300 KWH", "201–300 kWh"),
            ("301 TO 400 KWH", "301–400 kWh"),
            ("OVER 400 KWH",   "Over 400 kWh"),
        ],
    ),
    (
        "General Service B",
        "General Service B",
        [
            ("GENERAL SERVICE B", "Flat rate"),
        ],
    ),
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RateBracket:
    """Rates for one consumption bracket within a customer type.

    Base charges are VAT-exclusive (matching the PDF / Meralco website).
    VAT amounts are provided separately for transparency.
    """
    bracket_key: str
    bracket_label: str
    generation_charge_per_kwh: float       # VAT-exclusive
    transmission_charge_per_kwh: float     # VAT-exclusive
    system_loss_per_kwh: float             # VAT-exclusive
    distribution_charge_per_kwh: float     # VAT-exclusive
    supply_per_kwh: float                  # VAT-exclusive
    supply_fixed_monthly: float            # VAT-exclusive
    metering_per_kwh: float                # VAT-exclusive
    metering_fixed_monthly: float          # VAT-exclusive
    other_charges_per_kwh: float           # VAT-exempt (no VAT applied)
    residential_rate_per_kwh: float        # per-kWh sum excl. fixed monthly (VAT-exclusive)
    # Separate VAT amounts
    vat_generation: float                  # VAT amount on generation
    vat_transmission: float                # VAT amount on transmission
    vat_system_loss: float                 # VAT amount on system loss
    vat_distribution: float                # VAT amount on distribution
    vat_supply_per_kwh: float              # VAT amount on supply (per kWh)
    vat_supply_fixed: float                # VAT amount on supply (fixed monthly)
    vat_metering_per_kwh: float            # VAT amount on metering (per kWh)
    vat_metering_fixed: float              # VAT amount on metering (fixed monthly)


@dataclass
class CustomerType:
    """One customer type (e.g. Residential) with its brackets."""
    type_key: str
    type_label: str
    brackets: list  # list[RateBracket]

    def get_bracket_for_kwh(self, kwh: float) -> RateBracket:
        """Auto-select the correct bracket for a given kWh consumption."""
        if self.type_key == "Residential":
            if kwh <= 50:   return self._find("0 TO 50 KWH")
            if kwh <= 70:   return self._find("51 TO 70 KWH")
            if kwh <= 100:  return self._find("71 TO 100 KWH")
            if kwh <= 200:  return self._find("101 TO 200 KWH")
            if kwh <= 300:  return self._find("201 TO 300 KWH")
            if kwh <= 400:  return self._find("301 TO 400 KWH")
            return self._find("OVER 400 KWH")
        if self.type_key == "General Service A":
            if kwh <= 200:  return self._find("0 TO 200 KWH")
            if kwh <= 300:  return self._find("201 TO 300 KWH")
            if kwh <= 400:  return self._find("301 TO 400 KWH")
            return self._find("OVER 400 KWH")
        # For flat-rate types just return the first bracket
        return self.brackets[0]

    def _find(self, key: str) -> RateBracket:
        for b in self.brackets:
            if b.bracket_key == key:
                return b
        return self.brackets[-1]


@dataclass
class MeralcoRateResult:
    customer_types: list  # list[CustomerType]
    fetched_at: str
    is_fallback: bool
    effective_month: str

    def get_type(self, key: str) -> CustomerType:
        for ct in self.customer_types:
            if ct.type_key == key:
                return ct
        return self.customer_types[0]  # default to Residential


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_cached: Optional[MeralcoRateResult] = None
_cached_at: Optional[datetime] = None


def _is_cache_fresh() -> bool:
    return (
        _cached is not None
        and _cached_at is not None
        and datetime.now(timezone.utc) - _cached_at < CACHE_TTL
    )


# ---------------------------------------------------------------------------
# PDF parsing
# ---------------------------------------------------------------------------


def _pdf_url(year: int, month: int) -> str:
    return (
        f"https://meralcomain.s3.ap-southeast-1.amazonaws.com/"
        f"{year:04d}-{month:02d}/{month:02d}-{year:04d}_rate_schedule.pdf"
    )


def _parse_amount(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    v = value.strip()
    if not v:
        return None
    negative = v.startswith("(") and v.endswith(")")
    v = v.strip("()").replace(",", "")
    try:
        result = float(v)
        return -result if negative else result
    except ValueError:
        return None


def _row_to_bracket(row: list, bracket_key: str, bracket_label: str) -> RateBracket:
    """Parse one PDF table row into a RateBracket with base (VAT-exclusive) charges and separate VAT."""

    def get(col: int) -> float:
        v = _parse_amount(row[col] if col < len(row) else None)
        return v if v is not None else 0.0

    gen     = get(1)
    trans   = get(2)
    sl      = get(4)
    dist    = get(5)
    sup_kwh = get(7)
    sup_fix = get(8)   # per cust/mo
    met_kwh = get(9)
    met_fix = get(10)  # per cust/mo

    vat_exempt_cols = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23]
    other = sum(
        (v or 0.0)
        for col in vat_exempt_cols
        if (v := _parse_amount(row[col] if col < len(row) else None)) is not None
    )

    # Compute VAT amounts separately
    vat_gen     = round(gen     * _VAT["generation"],   4)
    vat_trans   = round(trans   * _VAT["transmission"], 4)
    vat_sl      = round(sl      * _VAT["system_loss"],  4)
    vat_dist    = round(dist    * _VAT["other"],        4)
    vat_sup_kwh = round(sup_kwh * _VAT["other"],        4)
    vat_sup_fix = round(sup_fix * _VAT["other"],        4)
    vat_met_kwh = round(met_kwh * _VAT["other"],        4)
    vat_met_fix = round(met_fix * _VAT["other"],        4)

    other_r     = round(other, 4)

    # Base rate sum (VAT-exclusive, per-kWh only, excl. fixed monthly)
    approx = round(gen + trans + sl + dist + sup_kwh + met_kwh + other_r, 4)

    return RateBracket(
        bracket_key=bracket_key,
        bracket_label=bracket_label,
        generation_charge_per_kwh=round(gen, 4),
        transmission_charge_per_kwh=round(trans, 4),
        system_loss_per_kwh=round(sl, 4),
        distribution_charge_per_kwh=round(dist, 4),
        supply_per_kwh=round(sup_kwh, 4),
        supply_fixed_monthly=round(sup_fix, 4),
        metering_per_kwh=round(met_kwh, 4),
        metering_fixed_monthly=round(met_fix, 4),
        other_charges_per_kwh=other_r,
        residential_rate_per_kwh=approx,
        vat_generation=vat_gen,
        vat_transmission=vat_trans,
        vat_system_loss=vat_sl,
        vat_distribution=vat_dist,
        vat_supply_per_kwh=vat_sup_kwh,
        vat_supply_fixed=vat_sup_fix,
        vat_metering_per_kwh=vat_met_kwh,
        vat_metering_fixed=vat_met_fix,
    )


def _fetch_and_parse(year: int, month: int) -> Optional[MeralcoRateResult]:
    url = _pdf_url(year, month)
    ym = f"{year:04d}-{month:02d}"
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        pdf_bytes = resp.content
        logger.info("Downloaded %s PDF (%d bytes)", ym, len(pdf_bytes))
    except Exception as exc:
        logger.warning("Could not download PDF for %s: %s", ym, exc)
        return None

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if not pdf.pages:
                return None
            table = pdf.pages[0].extract_table()
            if not table:
                return None

        # Build a lookup: normalised row label → row data
        # GSB label in PDF is just "General Service B" (not a kWh bracket)
        row_map: dict[str, list] = {}
        for row in table:
            if row and row[0]:
                key = str(row[0]).strip().upper()
                row_map[key] = row

        customer_types: list[CustomerType] = []
        for type_key, type_label, brackets_spec in _CUSTOMER_TYPES:
            brackets: list[RateBracket] = []
            for pdf_key, friendly_label in brackets_spec:
                row = row_map.get(pdf_key.upper())
                if row is None:
                    logger.debug("Row '%s' not found in %s PDF", pdf_key, ym)
                    continue
                brackets.append(_row_to_bracket(row, pdf_key, friendly_label))
            if brackets:
                customer_types.append(CustomerType(
                    type_key=type_key,
                    type_label=type_label,
                    brackets=brackets,
                ))

        if not customer_types:
            logger.warning("No customer types parsed from %s PDF", ym)
            return None

        logger.info("Parsed %d customer types from %s PDF", len(customer_types), ym)
        return MeralcoRateResult(
            customer_types=customer_types,
            fetched_at=now_iso,
            is_fallback=False,
            effective_month=ym,
        )

    except Exception as exc:
        logger.warning("Failed to parse PDF for %s: %s", ym, exc, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Fallback (June 2026, VAT-inclusive)
# ---------------------------------------------------------------------------

def _make_bracket(key: str, label: str, dist: float, sup_fix: float = 18.3456, met_fix: float = 5.6) -> RateBracket:
    # Base rates (VAT-exclusive, matching PDF/website values)
    gen   = 9.0704
    trans = 1.2537
    sl    = 0.8320
    sup   = 0.4979
    met   = 0.3350
    other_r = 0.109

    # Compute VAT amounts
    vat_gen   = round(gen   * _VAT["generation"],   4)
    vat_trans = round(trans * _VAT["transmission"], 4)
    vat_sl    = round(sl    * _VAT["system_loss"],  4)
    vat_dist  = round(dist  * _VAT["other"],        4)
    vat_sup   = round(sup   * _VAT["other"],        4)
    vat_sup_f = round(sup_fix * _VAT["other"],      4)
    vat_met   = round(met   * _VAT["other"],        4)
    vat_met_f = round(met_fix * _VAT["other"],      4)

    approx = round(gen + trans + sl + dist + sup + met + other_r, 4)

    return RateBracket(
        bracket_key=key, bracket_label=label,
        generation_charge_per_kwh=gen,
        transmission_charge_per_kwh=trans,
        system_loss_per_kwh=sl,
        distribution_charge_per_kwh=dist,
        supply_per_kwh=sup,
        supply_fixed_monthly=sup_fix,
        metering_per_kwh=met,
        metering_fixed_monthly=met_fix,
        other_charges_per_kwh=other_r,
        residential_rate_per_kwh=approx,
        vat_generation=vat_gen,
        vat_transmission=vat_trans,
        vat_system_loss=vat_sl,
        vat_distribution=vat_dist,
        vat_supply_per_kwh=vat_sup,
        vat_supply_fixed=vat_sup_f,
        vat_metering_per_kwh=vat_met,
        vat_metering_fixed=vat_met_f,
    )


def _fallback() -> MeralcoRateResult:
    residential = CustomerType(
        type_key="Residential", type_label="Residential",
        brackets=[
            _make_bracket("0 TO 50 KWH",    "0–50 kWh",    0.9803),
            _make_bracket("51 TO 70 KWH",   "51–70 kWh",   0.9803),
            _make_bracket("71 TO 100 KWH",  "71–100 kWh",  0.9803),
            _make_bracket("101 TO 200 KWH", "101–200 kWh", 0.9803),
            _make_bracket("201 TO 300 KWH", "201–300 kWh", 1.2908),
            _make_bracket("301 TO 400 KWH", "301–400 kWh", 1.5837),
            _make_bracket("OVER 400 KWH",   "Over 400 kWh", 2.0941),
        ],
    )
    gsa = CustomerType(
        type_key="General Service A", type_label="General Service A",
        brackets=[
            _make_bracket("0 TO 200 KWH",   "0–200 kWh",   0.9803),
            _make_bracket("201 TO 300 KWH", "201–300 kWh", 1.2908),
            _make_bracket("301 TO 400 KWH", "301–400 kWh", 1.5837),
            _make_bracket("OVER 400 KWH",   "Over 400 kWh", 2.0941),
        ],
    )
    return MeralcoRateResult(
        customer_types=[residential, gsa],
        fetched_at=datetime.now(timezone.utc).isoformat(),
        is_fallback=True,
        effective_month="",
    )


# ---------------------------------------------------------------------------
# Scrape with month fallback
# ---------------------------------------------------------------------------

def _scrape() -> MeralcoRateResult:
    now = datetime.now(timezone.utc)
    for delta in range(3):
        month = now.month - delta
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        result = _fetch_and_parse(year, month)
        if result is not None:
            return result
    logger.error("All PDF attempts failed — using hardcoded fallback.")
    return _fallback()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_rate() -> MeralcoRateResult:
    global _cached, _cached_at
    if _is_cache_fresh():
        assert _cached is not None
        return _cached
    result = _scrape()
    _cached = result
    _cached_at = datetime.now(timezone.utc)
    return result


def refresh_rate() -> MeralcoRateResult:
    global _cached, _cached_at
    result = _scrape()
    _cached = result
    _cached_at = datetime.now(timezone.utc)
    return result
