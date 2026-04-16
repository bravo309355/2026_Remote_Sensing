# Homework Week 8 - ARIA v5.0

## Assignment Completion

- Three-act STAC scene selection and TCI quick-QA: completed
- Sentinel-2 cube streaming and change metrics: completed
- Barrier lake, landslide source, and debris-flow masks: completed
- Threshold tuning with confusion matrix + F1 report: completed
- Eyewitness Impact Table using W3 + W7 + W8 layers: completed
- Coverage-gap discussion and final map: completed
- Optional AI advisor prompt + Gemini call: included

## Chosen Scene IDs

- Pre: `S2A_MSIL2A_20250615T023141_R046_T51QUG_20250615T070417`
- Mid: `S2C_MSIL2A_20250911T022551_R046_T51QUG_20250911T055914`
- Post: `S2B_MSIL2A_20251016T022559_R046_T51QUG_20251016T042804`

## Detection Summary

- Barrier lake area (Act 2): `1.033 km²`
- Landslide source area (Act 3): `0.604 km²`
- Debris-flow footprint (Act 3): `2.045 km²`
- Landslide threshold tuning: best pair `(nir_drop > 0.15, swir_post > 0.25)` with `F1 = 1.00`
- Guangfu overlay nodes: `7` (`5` required + `2` optional)

## Coverage Gap Summary

Homework-8 keeps the detection work in the Matai'an / Guangfu corridor, but the inherited W3 shelter layer and W7 bottleneck layer still represent Hualien City assets farther north. That mismatch is the main teaching point of Week 8: ARIA v4.0 could model preparedness for Hualien City, but it did not yet maintain valley-scale reference layers for Matai'an, Wanrong, and Guangfu.

In the current audit run, the hit counts are:

- W3 shelter hits: `0 / 5`
- W7 bottleneck hits: `0 / 5`
- W8 Guangfu overlay hits: `1 / 7` (`Foxu_Debris_Zone`)

The W8 Guangfu overlay is therefore the only layer that directly tests on-the-ground exposure inside the actual impact corridor. The notebook's two-panel final map shows this explicitly by placing the inherited Hualien assets beside the Matai'an AOI box.

## AI Diagnostic Log

- Mid-event cloud filtering used client-side sorting plus TCI inspection rather than trusting tile-level cloud cover alone.
- The barrier-lake rule kept `green_mid > nir_mid` and an upstream gate to suppress dark river-shadow false positives.
- The Homework notebook intentionally separates inherited W3/W7 assets from the W8 Guangfu overlay so the coverage gap is visible instead of being hidden by a Guangfu-only local rebuild.

## Deliverables

- `ARIA_v5_mataian.ipynb`
- `impact_table.csv`
- `mataian_detections.gpkg`
- `output/`
- `README.md`
- `.env.example`
