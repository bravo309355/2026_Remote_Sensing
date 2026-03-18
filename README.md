# Homework 4: ARIA v2

This branch upgrades the Week 3 ARIA workflow with terrain intelligence for `花蓮縣`, then extends it into a reusable county-level workflow when a full Taiwan DEM is available.

## Deliverables

Official required deliverables:

- `ARIA_v2.ipynb`
- `terrain_risk_audit.json`
- `terrain_risk_map.png`
- `README.md`

Supporting outputs included in this submission:

- `terrain_risk_top10_scatter.png` and `terrain_risk_top10_ranked.png` for the default `花蓮縣` run
- `terrain_risk_audit_新北市.json`, `terrain_risk_map_新北市.png`, `terrain_risk_top10_scatter_新北市.png`, and `terrain_risk_top10_ranked_新北市.png` as a county-switching demonstration using the same notebook after changing only `TARGET_COUNTY`

The final submission bundle is copied into `submission/Homework-4/`.

## Colab Workflow

The notebook is designed for Google Colab with these fixed locations:

- Notebook folder: `/content/drive/MyDrive/Colab Notebooks/`
- Input data folder: `/content/drive/MyDrive/Colab Notebooks/data/`

Place these files in `Colab Notebooks/data/`:

- Recommended for the stretch goal: `DEM_tawiwan_V2025.tif`
- Optional county-specific fallback: `dem_20m_hualien.tif`
- `riverpoly/` shapefile folder
- `鄉(鎮、市、區)界線1140318/` shapefile folder
- `避難收容處所點位檔案v9.csv`

Place these files in `Colab Notebooks/`:

- `ARIA_v2.ipynb`
- `.env`

Current `.env` format used by the notebook:

```env
SLOPE_THRESHOLD=30
ELEVATION_LOW=50
BUFFER_HIGH=500
TARGET_COUNTY=花蓮縣
```

Do not push these large raster inputs to GitHub:

- `DEM_tawiwan_V2025.tif`
- `dem_20m_hualien.tif`
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

!apt-get update -qq
!apt-get install -y fonts-noto-cjk

%pip install -q geopandas rioxarray rasterstats python-dotenv matplotlib pyogrio rasterio shapely xarray
```

The notebook also includes a dedicated CJK font test cell immediately after setup, and the README follows that Colab-tested version as the source of truth.

## Notebook Outputs

The notebook writes outputs to:

- `/content/drive/MyDrive/Colab Notebooks/outputs/homework4/terrain_risk_audit.json`
- `/content/drive/MyDrive/Colab Notebooks/outputs/homework4/terrain_risk_map.png`
- `/content/drive/MyDrive/Colab Notebooks/outputs/homework4/terrain_risk_top10_scatter.png` (assignment-required scatter plot)
- `/content/drive/MyDrive/Colab Notebooks/outputs/homework4/terrain_risk_top10_ranked.png` (supplementary readability chart)

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
- `outputs/aria_v2/terrain_risk_top10_scatter.png` (assignment-required scatter plot)
- `outputs/aria_v2/terrain_risk_top10_ranked.png` (supplementary readability chart)
- `outputs/aria_v2/terrain_run_summary.json`

## AI Diagnostic Log

- The notebook now supports either a county-specific DEM or a full Taiwan DEM. With a full Taiwan DEM, it first clips by county buffer bounds and only then performs the exact polygon clip.
- `dem_20m_hualien.tif` may not carry CRS metadata, so both the notebook and the local workflow explicitly repair it to `EPSG:3826` before clipping.
- The county `+1000m` clip can slightly exceed a county-specific DEM bounds, so the notebook clamps the window clip to the overlap before doing the exact polygon clip.
- The final terrain map overlays river polygons. The assignment-required scatter plot is still exported, but the notebook also writes a ranked companion chart because dense counties such as New Taipei compress too many labels into the same static scatter view.
- If zonal statistics return `NaN`, the first checks are CRS alignment and whether a shelter buffer falls outside raster coverage.
- The slope calculation uses `np.gradient(..., 20)` so the pixel spacing matches the 20m DEM resolution.

## GitHub Submission

Use the `Homework-4` branch URL as the submission link unless the branch is later merged.
