"""
ENSO phase lookup for WATT-IF.

Uses the NOAA Oceanic Niño Index (ONI) — the 3-month running mean of sea
surface temperature anomalies in the Niño 3.4 region — to determine whether
a given calendar month falls during El Niño, La Niña, or a Neutral period.

ONI thresholds (NOAA/CPC official):
  ≥ +0.5°C for ≥ 5 consecutive seasons → El Niño   (is_el_nino = 1)
  ≤ -0.5°C for ≥ 5 consecutive seasons → La Niña   (is_el_nino = -1)
  Otherwise                             → Neutral   (is_el_nino = 0)

The ONI table is sourced from:
  https://cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php
  (retrieved July 2026)

The table uses 3-month season labels. We map each season to the middle month:
  DJF → Feb, JFM → Mar, FMA → Apr, MAM → May, AMJ → Jun, MJJ → Jul,
  JJA → Aug, JAS → Sep, ASO → Oct, SON → Nov, OND → Dec, NDJ → Jan(+1)

For months where the ONI is not yet available (recent or future), this module
returns 0 (Neutral / unknown) so the model always receives a valid value.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ONI table: year → {month (1-12): oni_value}
# Derived from the NOAA ONI_v5 seasonal table.
# Season → centre-month mapping:
#   DJF=2, JFM=3, FMA=4, MAM=5, AMJ=6, MJJ=7, JJA=8, JAS=9,
#   ASO=10, SON=11, OND=12, NDJ=1 (of the following year)
# ---------------------------------------------------------------------------

# Raw data: year → [DJF, JFM, FMA, MAM, AMJ, MJJ, JJA, JAS, ASO, SON, OND, NDJ]
_RAW: dict[int, list[float | None]] = {
    2016: [ 2.6,  2.3,  1.7,  1.0,  0.5,  0.0, -0.3, -0.5, -0.6, -0.6, -0.6, -0.5],
    2017: [-0.2,  0.0,  0.2,  0.3,  0.4,  0.4,  0.2, -0.1, -0.3, -0.6, -0.8, -0.9],
    2018: [-0.8, -0.7, -0.6, -0.4, -0.1,  0.1,  0.1,  0.3,  0.5,  0.8,  1.0,  0.9],
    2019: [ 0.9,  0.9,  0.8,  0.8,  0.6,  0.5,  0.3,  0.2,  0.2,  0.4,  0.6,  0.7],
    2020: [ 0.6,  0.6,  0.5,  0.3,  0.0, -0.2, -0.4, -0.5, -0.8, -1.1, -1.2, -1.1],
    2021: [-0.9, -0.8, -0.7, -0.5, -0.4, -0.3, -0.3, -0.4, -0.6, -0.8, -0.9, -0.9],
    2022: [-0.8, -0.8, -0.9, -1.0, -0.9, -0.8, -0.8, -0.9, -1.0, -0.9, -0.8, -0.7],
    2023: [-0.5, -0.3,  0.0,  0.3,  0.6,  0.8,  1.1,  1.4,  1.6,  1.8,  2.0,  2.1],
    2024: [ 1.9,  1.6,  1.3,  0.8,  0.5,  0.2,  0.1, -0.1, -0.2, -0.2, -0.3, -0.4],
    2025: [-0.4, -0.2, -0.1,  0.0,  0.0,  0.0, -0.1, -0.3, -0.4, -0.5, -0.6, -0.5],
    2026: [-0.4, -0.1,  0.1,  0.5,  1.0,  None, None, None, None, None, None, None],
}

# Season index → centre month (1-based)
# DJF(0)→Feb=2, JFM(1)→Mar=3, FMA(2)→Apr=4, MAM(3)→May=5,
# AMJ(4)→Jun=6, MJJ(5)→Jul=7, JJA(6)→Aug=8, JAS(7)→Sep=9,
# ASO(8)→Oct=10, SON(9)→Nov=11, OND(10)→Dec=12, NDJ(11)→Jan=1
_SEASON_TO_MONTH: list[int] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1]


def _build_oni_lookup() -> dict[str, float]:
    """Convert the raw season table into a {YYYY-MM: oni} dict."""
    oni: dict[str, float] = {}
    for year, seasons in _RAW.items():
        for season_idx, val in enumerate(seasons):
            if val is None:
                continue
            centre_month = _SEASON_TO_MONTH[season_idx]
            # NDJ season belongs to January of the *next* year
            record_year = year + 1 if season_idx == 11 else year
            ym = f"{record_year:04d}-{centre_month:02d}"
            oni[ym] = val
    return oni


_ONI: dict[str, float] = _build_oni_lookup()

# Official ENSO episode thresholds (NOAA/CPC)
_EL_NINO_THRESHOLD = 0.5
_LA_NINA_THRESHOLD = -0.5


def get_oni(year_month: str) -> float | None:
    """Return the ONI value for a given YYYY-MM, or None if not available."""
    return _ONI.get(year_month)


def get_enso_phase(year_month: str) -> int:
    """Return the ENSO phase for a calendar month as an integer flag.

    Returns
    -------
    1   El Niño  (ONI ≥ +0.5)
    -1  La Niña  (ONI ≤ -0.5)
    0   Neutral or unknown
    """
    oni = _ONI.get(year_month)
    if oni is None:
        return 0
    if oni >= _EL_NINO_THRESHOLD:
        return 1
    if oni <= _LA_NINA_THRESHOLD:
        return -1
    return 0


def get_is_el_nino(year_month: str) -> int:
    """Return 1 if El Niño, 0 otherwise (for backwards-compatible binary flag)."""
    return 1 if get_enso_phase(year_month) == 1 else 0
