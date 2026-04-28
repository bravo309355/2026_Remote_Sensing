# Homework 9: ARIA v6.0 - The Validated Auditor

Student: Huang YongZhi  
Case study: Matai'an Barrier Lake, Taiwan  
Notebook: `Week9_ARIA_v6_HuangYongZhi.ipynb`

## Filename Note

The homework checklist says `Week9_ARIA_v60_[Your_Name].ipynb`, while the assignment title and framework name are **ARIA v6.0**. I interpret `v60` as a checklist typo for `v6.0`. The submitted notebook therefore uses `Week9_ARIA_v6_HuangYongZhi.ipynb` and keeps the ARIA v6.0 naming consistent with the assignment title.

## What Is Included

- Task 1: NDVI, NDWI, and BSI change detection with mandatory SCL cloud masking via `stream_scl()`.
- Task 2: 9-threshold sweep for regional teacher validation points, plus LAKE_BBOX local accuracy sweep.
- Task 3: Confusion matrix, OA, PA, UA, Kappa, F1, LAKE_BBOX local metrics, and student GEP bonus comparison.
- Task 4: Phantom-water comparison and three-zone confidence map.
- Task 5: ARIA v6.0 validated disaster report.
- Task 6: AI Advisor prompt, response, and student reflection using the actual Task 3/4 metrics.
- Task 7: Week 8 vs Week 9 comparison using actual validation results.

## Key Metrics

Regional teacher validation, threshold `Delta NDVI < -0.05`:

| Metric | Value |
|---|---:|
| Overall Accuracy (OA) | 0.733 |
| Producer's Accuracy (PA) | 0.500 |
| User's Accuracy (UA) | 0.938 |
| Cohen's Kappa | 0.467 |
| F1-score | 0.652 |

Task 4 confidence zones:

| Zone | Condition | Area (km2) |
|---|---|---:|
| Zone 1 High | `|Delta NDVI| > 0.075` | 83.196 |
| Zone 2 Low | `0.050 < |Delta NDVI| <= 0.075` | 38.230 |
| Zone 3 None | `|Delta NDVI| <= 0.050` | 298.290 |

Phantom-water result:

| Case | Pixels flagged as water (`Delta NDWI > 0.10`) |
|---|---:|
| Without SCL mask | 1,484,359 |
| With SCL mask | 422,011 |
| Removed as phantom water | 1,062,348 (71.6%) |

## Output Files

All outputs are in `output/`:

```text
HW9_T1_difference_panel.png
HW9_T1_stats.csv
HW9_T2_threshold_sweep.png
HW9_T2_sweep.csv
HW9_T2_lake_sweep.csv
HW9_T3_confusion_matrix.png
HW9_T3_metrics.csv
HW9_T3_lake_metrics.csv
HW9_T3_bonus_comparison.csv
HW9_T4_phantom_water.png
HW9_T4_confidence_map.png
HW9_T4_zones.csv
```

## Reproducibility

The notebook reads Sentinel-2 item IDs, bounding boxes, and the final threshold from `.env`. The `.env` file is intentionally ignored by Git.

Run from `submission/Homework-9` with the course conda environment:

```powershell
& 'C:\Users\user\anaconda3\envs\geopandas\python.exe' -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1500 Week9_ARIA_v6_HuangYongZhi.ipynb
```
