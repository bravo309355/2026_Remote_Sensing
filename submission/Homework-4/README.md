# Homework 4: ARIA v2

This branch upgrades the Week 3 ARIA workflow with terrain intelligence for `花蓮縣`, then extends it into a reusable county-level workflow when a full Taiwan DEM is available.

## Deliverables

- `ARIA_v2.ipynb`
- `terrain_risk_audit.json`
- `terrain_risk_map.png`
- `README.md`

The final submission bundle is copied into `submission/Homework-4/`.

## Colab Workflow

The notebook is designed for Google Colab with these fixed locations:

- Notebook folder: `/content/drive/MyDrive/Colab Notebooks/`
- Input data folder: `/content/drive/MyDrive/Colab Notebooks/data/`

Place these files in `Colab Notebooks/data/`:

- Recommended for the stretch goal: `DEM_tawiwan_V2025.tif`
- Optional county-specific fallback: `Hualien_dem_merge.tif`
- `RIVERPOLY/riverpoly/` shapefile folder
- `鄉(鎮、市、區)界線1140318/` shapefile folder
- `避難收容處所點位檔案v9.csv`

Place these files in `Colab Notebooks/`:

- `ARIA_v2.ipynb`
- Optional `.env` copied from `submission/Homework-4/.env.example`

Recommended `.env` values for the stretch-goal workflow:

```env
TARGET_COUNTY=花蓮縣
DEM_PATH=/content/drive/MyDrive/Colab Notebooks/data/DEM_tawiwan_V2025.tif
SLOPE_THRESHOLD=30
ELEVATION_LOW=50
BUFFER_HIGH=500
COUNTY_BUFFER=1000
```

Do not push these large raster inputs to GitHub:

- `DEM_tawiwan_V2025.tif`
- `Hualien_dem_merge.tif`
- `Hualien_dem_merge.vrt`
- `fixed_tif/`

When a full Taiwan DEM is available, the notebook clips it twice:

1. Bounding-box clip using the target county `+1000m` buffer
2. Precise polygon clip using the dissolved county boundary

This keeps the workflow reusable across counties without running terrain analysis on the full raster extent.

## Colab Setup Cell

`ARIA_v2.ipynb` starts with:

```python
from google.colab import drive
drive.mount('/content/drive')

%pip install -q geopandas rioxarray rasterstats python-dotenv matplotlib pyogrio rasterio shapely xarray
```

## Notebook Outputs

The notebook writes outputs to:

- `/content/drive/MyDrive/Colab Notebooks/outputs/homework4/terrain_risk_audit.json`
- `/content/drive/MyDrive/Colab Notebooks/outputs/homework4/terrain_risk_map.png`
- `/content/drive/MyDrive/Colab Notebooks/outputs/homework4/terrain_risk_top10_scatter.png`

## Local Helper Pipeline

This branch also includes a local helper script:

```bash
"C:\Program Files\QGISQT6 3.40.14\apps\Python312\python.exe" scripts/build_aria_v2_notebook.py
"C:\Program Files\QGISQT6 3.40.14\apps\Python312\python.exe" scripts/aria_v2_pipeline.py
```

The local helper uses `GDAL + geopandas` so the repo can still generate the required JSON and PNG even though the bundled project venv is broken on this machine.

Local outputs are written to:

- `outputs/aria_v2/terrain_risk_audit.json`
- `outputs/aria_v2/terrain_risk_map.png`
- `outputs/aria_v2/terrain_risk_top10_scatter.png`
- `outputs/aria_v2/terrain_run_summary.json`

## AI Diagnostic Log

- The notebook now supports either a county-specific DEM or a full Taiwan DEM. With a full Taiwan DEM, it first clips by county buffer bounds and only then performs the exact polygon clip.
- `Hualien_dem_merge.tif` does not carry CRS metadata, so both the notebook and the local workflow explicitly repair it to `EPSG:3826` before clipping.
- `Hualien_dem_merge.vrt` points to raster tiles with a broken relative path in this repo layout, so it is treated as a fallback reference only, not the primary analysis input.
- The county `+1000m` clip can slightly exceed a county-specific DEM bounds, so the notebook clamps the window clip to the overlap before doing the exact polygon clip.
- If zonal statistics return `NaN`, the first checks are CRS alignment and whether a shelter buffer falls outside raster coverage.
- The slope calculation uses `np.gradient(..., 20)` so the pixel spacing matches the 20m DEM resolution.

## GitHub Submission

Use the `Homework-4` branch URL as the submission link unless the branch is later merged.
