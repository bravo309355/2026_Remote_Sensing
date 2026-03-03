# Exercise 2 Reflection

## What was validated
- The CWA station API provides two coordinate systems per station (`TWD67` and `WGS84`) in the same payload.
- When both are interpreted directly as WGS84 decimal degrees, most stations show a consistent spatial offset.

## Observed pattern
- Central tendency is close to the expected shift:
  - Mean: `855.042 m`
  - Median: `850.764 m`
- This aligns with the expected Taiwan datum shift scale (around 800-900 meters), including the "Jiji ~800m" intuition.

## Outliers and caveats
- A small number of stations have much larger offsets (max `3682.692 m`), likely caused by station-specific metadata quality issues or special station contexts.
- For practical mapping, CRS-aware transformation should be applied before overlaying data from different datums.

## Reproducibility
- Re-run with:
  - `venv\Scripts\python.exe cwa_crs_compare.py`
