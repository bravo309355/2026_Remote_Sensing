# Homework 5: ARIA v3.0

This submission builds a formal Homework 5 workflow for **花蓮縣 + 宜蘭縣**.
It does **not** use `Week5-Student.ipynb` as the source of truth because the classroom notebook simplifies the static-risk side of the assignment and reuses Week 3 `risk_level` directly.

## Deliverables

- `ARIA_v3.ipynb`
- `ARIA_v3_Fungwong.html`
- `README.md`

Internal debug outputs are also written to `outputs/aria_v3/`:

- `static_baseline.geojson`
- `rainfall_stations.geojson`
- `dynamic_risk_audit.csv`

## Execution

Use the `geopandas` conda environment:

```powershell
C:\Users\user\anaconda3\envs\geopandas\python.exe scripts\build_aria_v3_notebook.py
```

Open and run:

```text
scripts/ARIA_v3.ipynb
```

The notebook writes the final map to:

```text
submission/Homework-5/ARIA_v3_Fungwong.html
```

## Environment Variables

The notebook reads the repo-root `.env`. The Week 5 fields are:

```env
APP_MODE=SIMULATION
SIMULATION_DATA=data/scenarios/fungwong_202511.json
TARGET_COUNTIES=花蓮縣,宜蘭縣
CWA_API_KEY=your-cwa-key
RAIN_BUFFER_M=5000
WARNING_RAIN_MM=40
CRITICAL_RAIN_MM=80
SLOPE_THRESHOLD=30
ELEVATION_LOW=50
BUFFER_HIGH=500
COUNTY_BUFFER=1000
OUTPUT_DIR=outputs/aria_v3
SUBMISSION_DIR=submission/Homework-5
REBUILD_STATIC_BASELINE=0
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_REQUEST_DELAY_S=1.5
```

Compatibility note:

- The code accepts `API_KEY_CWA` as a fallback if `CWA_API_KEY` is not present.
- `.env` stays at the repo root and must not be copied into `submission/`.

## Why Not Use `Week5-Student.ipynb`

The classroom notebook is useful for demonstrating Folium layers and a simple rainfall overlay, but it does not meet the formal Homework 5 contract:

- It uses Week 3 `risk_level` directly instead of a fresh Homework 5 `terrain_risk`.
- It does not rebuild the Week 4 terrain baseline for both Hualien and Yilan.
- Its dynamic classification is closer to the lab exercise than the assignment spec.

This submission instead rebuilds:

1. Week 3 river-distance context
2. Week 4 DEM / slope / zonal-stats terrain baseline
3. Homework 5 rainfall normalization, fallback, dynamic risk, and Gemini bonus

## AI Diagnostic Log

- **`-998` rainfall values**: the rainfall normalizer drops them before building the rain-station GeoDataFrame, so missing sensors do not distort the map or color scale.
- **CRS mismatch before `sjoin`**: all dynamic overlay work is done in `EPSG:3826`; the map is only converted back to `EPSG:4326` at Folium rendering time.
- **Folium lat/lon order**: Folium expects `[latitude, longitude]`, so all marker placement uses `geometry.y, geometry.x` after converting to `EPSG:4326`.
- **Dual-coordinate JSON normalization**: LIVE CWA payloads can include multiple coordinate entries; the parser explicitly picks the WGS84 lat/lon pair instead of assuming the first record is safe to use.
- **Week 4 output gap**: the existing Homework 4 audit JSON does not expose a standalone `terrain_risk` field, so Homework 5 now derives an explicit `terrain_risk` from `max_slope > SLOPE_THRESHOLD`.

## Bonus: Gemini Advice

Bonus mode is built in but safe to skip:

- If `GEMINI_API_KEY` is configured, the notebook asks Gemini for short commander guidance on the top 3 most impacted shelters.
- Gemini calls are spaced by `GEMINI_REQUEST_DELAY_S` seconds to reduce short-burst rate limiting.
- If Gemini hits quota or auth errors, the popup shows a short status message instead of the raw API payload.
- If the key is missing, the bonus step is skipped cleanly and the rest of the notebook still succeeds.
