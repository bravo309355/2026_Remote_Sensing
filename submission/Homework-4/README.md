# Homework 4: ARIA v2

This branch upgrades the Week 3 ARIA workflow with terrain intelligence for `花蓮縣`.

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

- `Hualien_dem_merge.tif`
- `RIVERPOLY/riverpoly/` shapefile folder
- `鄉(鎮、市、區)界線1140318/` shapefile folder
- `避難收容處所點位檔案v9.csv`

Place these files in `Colab Notebooks/`:

- `ARIA_v2.ipynb`
- Optional `.env`

Do not push these large raster inputs to GitHub:

- `DEM_tawiwan_V2025.tif`
- `Hualien_dem_merge.tif`
- `Hualien_dem_merge.vrt`
- `fixed_tif/`

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

- `Hualien_dem_merge.tif` does not carry CRS metadata, so both the notebook and the local workflow explicitly repair it to `EPSG:3826` before clipping.
- `Hualien_dem_merge.vrt` points to raster tiles with a broken relative path in this repo layout, so it is treated as a fallback reference only, not the primary analysis input.
- The county `+1000m` clip slightly exceeds the pre-merged Hualien DEM bounds, but the Homework 4 workflow still completes successfully because the clipped raster covers the actual shelter buffers used for zonal statistics.
- If zonal statistics return `NaN`, the first checks are CRS alignment and whether a shelter buffer falls outside raster coverage.
- The slope calculation uses `np.gradient(..., 20)` so the pixel spacing matches the 20m DEM resolution.

## GitHub Submission

Use the `Homework-4` branch URL as the submission link unless the branch is later merged.
