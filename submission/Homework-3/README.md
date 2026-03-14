# Homework 3: ARIA

This branch implements the Week 3 ARIA workflow for flood-risk screening of shelters near rivers in Taiwan.

## Environment

Use the existing conda environment named `geopandas`.

```bash
conda run -n geopandas python aria_pipeline.py
```

The population workbook is an old `.xls` file, so this workflow requires `xlrd==2.0.1`.

## Inputs

- River polygons: `data/RIVERPOLY/riverpoly/riverpoly.shp`
- Shelter CSV: `data/避難收容處所點位檔案v9.csv`
- Township boundaries: `data/鄉(鎮、市、區)界線1140318/TOWN_MOI_1140318.shp`
- Township population workbook: `data/鄉鎮戶數及人口數-115年2月.xls`

## Workflow

1. Read the shelter CSV with encoding fallback.
2. Remove shelter rows with null or zero coordinates.
3. Validate shelter points against the township boundary land mask.
4. Parse township population from the local `.xls` workbook.
5. Reproject to `EPSG:3826`.
6. Build three non-overlapping river risk rings: `0-500m`, `500-1000m`, `1000-2000m`.
7. Assign shelter risk with spatial joins.
8. Aggregate counts and capacities by township.
9. Flag township capacity gaps using `required_safe_capacity = population * 0.2`.
10. Export outputs and copy deliverables into a single submission folder.

## Run

Create `.env` from `.env.example` if you want to override defaults.

```bash
copy .env.example .env
conda run -n geopandas python aria_pipeline.py
```

To run the Homework 3 tests:

```bash
conda run -n geopandas python -m pytest tests/test_aria_pipeline.py -q
```

## Outputs

The pipeline writes the main outputs into `outputs/aria/`:

- `cleaning_summary.json`
- `population_summary.csv`
- `population_join_audit.csv`
- `township_summary.csv`
- `top10_townships.csv`
- `shelter_risk_audit.json`
- `risk_map.html`
- `risk_map.png`

The final deliverables are copied into `submission/Homework-3/`:

- `ARIA.ipynb`
- `README.md`
- `shelter_risk_audit.json`
- `risk_map.png`

## AI Diagnostic Log

- The original repository was centered on AQI analysis, so the Homework 3 work was isolated in a new `aria_pipeline.py` module instead of being folded into `main.py`.
- The shelter CSV contains a small number of null/zero coordinate rows, and a larger set of points that fall outside the Taiwan township land mask. The pipeline records both counts in `outputs/aria/cleaning_summary.json`.
- The township population source is a legacy `.xls` workbook. The stable solution was to install `xlrd==2.0.1` in the `geopandas` conda environment and parse it with `pandas.read_excel(..., engine="xlrd")` instead of depending on Excel COM.
- Taiwan extent validation is based on the supplied township boundary shapefile, not hard-coded longitude/latitude ranges. This avoids silently keeping invalid offshore points that still fit a simple bounding box.
