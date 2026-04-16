# Week 8 Assignment: ARIA v5.0 — The Matai'an Three-Act Auditor

Submission deadline: Before next class

---

## 1. Scenario

After seven weeks of *modeling* disaster risk, the commander now demands **physical evidence**:

> "We have predictions. Now show me what actually happened on the ground — and tell me whether a lake that should not exist was visible before it killed 18 people."

Your task is to upgrade the ARIA system from **ARIA v4.0 (Network Accessibility, W7)** to **ARIA v5.0 (Matai'an Three-Act Auditor, W8)** by integrating **Sentinel-2 L2A** optical imagery via the **STAC API**. You will produce an optical forensic audit of the **2025 Matai'an Creek barrier lake event（馬太鞍溪堰塞湖事件）** — the most consequential disaster in Hualien County in 2025 — using three satellite scenes spanning the full life cycle of the barrier lake.

**The Matai'an timeline in one sentence**: On Jul 21, 2025 Typhoon Wipha's rainfall triggered a massive landslide in upper Wanrong that dammed the Matai'an Creek and formed a ~200 m deep barrier lake; the lake existed for 64 days and then breached on Sep 23, 2025 at 14:50, releasing 15.4 million m³ of water in 30 minutes and burying downstream Guangfu township (光復鄉). 18+ lives lost.

**Key differences from the in-class lab**:

- The lab used one fingerprint point per land cover type → **this assignment samples a full 20-point grid** along the Matai'an valley from upstream to downstream
- The lab picked one Mid and one Post scene with default thresholds → **this assignment tunes thresholds via confusion matrix + F1 score** against a ground-truth set
- The lab cross-referenced W3/W7/Guangfu visually → **this assignment produces a formal Eyewitness Impact Table** with quantitative audit metrics for all three acts

---

## 2. Data Sources

### A. Satellite Imagery (STAC)
- **Source**: Microsoft Planetary Computer
- **Collection**: `sentinel-2-l2a`
- **Area of interest**: Matai'an bounding box `121.28, 23.56, 121.52, 23.76` (covers upper Wanrong barrier lake site → downstream Guangfu township)
- **Three-act date windows**:
  - **Pre** (original forest): 2025-06-01 to 2025-07-15, cloud cover < 20%
  - **Mid** (lake present, pre-breach): 2025-08-01 to 2025-09-20, cloud cover < 40% (monsoon season — relax clouds)
  - **Post** (lake drained, debris in Guangfu): 2025-09-25 to 2025-11-15, cloud cover < 30%
- **Required bands**: B02, B03, B04, B08, B11, B12
- **Tool**: `pystac-client` + `stackstac` + `rioxarray` (see Pre-lab)
- **Recommended pattern**: Use the `robust_search()` helper from the Demo notebook (client-side cloud filtering with exponential backoff retry) for more reliable results than server-side `query={"eo:cloud_cover": {"lt": N}}`
- **COG token refresh**: Always call `pc.sign(item)` before reading band assets — SAS tokens expire after ~1 hour

### B. Outputs from Previous Weeks
- **Week 3 Shelters** GeoDataFrame — including `river_risk` (Hualien City range — geographically north of Matai'an; you will document this coverage gap)
- **Week 4 Terrain Risk** — `mean_elevation`, `max_slope`, `terrain_risk`
- **Week 5 Rainfall** — Wipha simulation (`wipha_202507.json`) *or* the teacher-provided historical rainfall record
- **Week 6 Kriging Output** — `kriging_rainfall.tif` (recommended for validation of the upstream landslide source)
- **Week 7 Top-5 Bottlenecks** — `top5_bottlenecks.gpkg`
- **Week 7 Road Network** — `hualien_network.graphml`

### C. New for Week 8 — Guangfu Overlay (built by you in Pre-lab)
- **`guangfu_overlay.gpkg`** — You built this yourself in **Pre-lab Step 7b**. Five required nodes (光復火車站、光復國小、光復鄉公所、台9線馬太鞍溪橋、佛祖街沉積區中心), schema `name / cn_name / node_type / priority / geometry`, saved as EPSG:3826. If your file is missing or malformed at submission time, the Demo notebook's Cell [17] has a synthetic fallback that will keep Part D runnable — but Part D full credit requires your own valid file with the 5 required nodes plus at least 2 optional nodes of your own choosing.

### D. Ground Truth & Verification
- **Esri Sentinel-2 Explorer**: Use [ArcGIS Sentinel-2 Explorer](https://sentinel2explorer.esri.com/) to visually verify your scene selection and compare spectral indices (NDWI, NDVI, NDMI) at the barrier lake location. This is an essential human-verification step.
- **NCDR reference data**: The barrier lake peaked at ~86 ha on Sep 11, and shrank to ~12 ha by Oct 16 after partial breach. Use these as calibration benchmarks for your lake mask area.
- Official post-event landslide reports from 農業部林業署花蓮分署 or 中央地質調查所 (if available)
- News photos of the Guangfu flood with geotags (you may georeference 5–10 of them for the ground-truth subset)
- The teacher will provide `reference_mataian_truth.gpkg` as a fallback

---

## 3. Core Requirements

Submit as a single **`.ipynb`** (Jupyter Notebook).

### A. Three-Act STAC Scene Selection + TCI Quick-QA

1. Connect to Planetary Computer via `pystac_client.Client.open()` + `planetary_computer.sign_inplace`
2. Query `sentinel-2-l2a` for each of the three date windows
3. **For each window**, preview the top-3 candidates using the `visual` (TCI) asset and **write a 2-sentence justification** in a markdown cell explaining why you picked each scene (pay attention to cloud cover over the Matai'an valley specifically, not just the tile-level percentage)
4. Save the chosen item IDs to your notebook metadata so results are reproducible — you should end up with exactly **three item IDs**: `PRE_ITEM_ID`, `MID_ITEM_ID`, `POST_ITEM_ID`

### B. Four Change Metrics (Three-Act aware)

Implement the following as reusable functions that take two `xarray.DataArray` cubes and return a single-band change raster:

1. **NIR Drop**: `nir_drop(pre, post) = pre_B08 - post_B08`
2. **SWIR Post Brightness**: `swir_post(post) = post_B12`
3. **Bare Soil Index change**: `bsi_change(pre, post) = bsi(post) - bsi(pre)` where `BSI = ((B11 + B04) - (B08 + B02)) / ((B11 + B04) + (B08 + B02))`
4. **NDVI Change**: `ndvi_change(pre, post) = ndvi(pre) - ndvi(post)` where `NDVI = (B08 - B04) / (B08 + B04)`

Apply these to two comparisons and save the resulting eight change maps as PNGs in `output/`:
- **Pre → Mid** (to capture the birth of the barrier lake)
- **Pre → Post** (to capture the landslide source + downstream debris flow)

### C. Three Detection Masks with Tuned Thresholds

You will produce **three** separate detection masks, each with its own physical justification:

#### C1. Barrier lake mask (Pre→Mid)
Baseline rule: `(nir_pre > 0.25) & (nir_mid < 0.18) & (blue_mid > 0.03) & (green_mid > nir_mid)`
- **Important**: The barrier lake water is **turbid** (loaded with suspended sediment), so its NIR is 0.10–0.18, NOT < 0.05 like clear water. Using 0.08 will return zero lake pixels.
- **Spatial gate**: Restrict detection to west of ~121.33°E to exclude downstream river flooding false positives
- Tune the `nir_mid` upper bound — pick 3 candidate values (e.g. 0.12, 0.15, 0.18) and report which best matches the NCDR reference ~0.86 km² peak lake area (Sep 11)
- **NCDR-verified lake center**: approximately (121.292, 23.696)
- Vectorize with `rasterio.features.shapes`

#### C2. Landslide source scar mask (Pre→Post)
Baseline rule: `(nir_drop > 0.15) & (swir_post > 0.25) & (nir_pre > 0.25)`
- Build a ground-truth set of at least **10 confirmed landslide pixels** + **10 stable-vegetation pixels** (from the reference gpkg, your own georeferencing of news photos, or hand-drawn in QGIS)
- Tune `nir_drop` and `swir_post` thresholds by computing the confusion matrix (TP, FP, TN, FN) at **5 candidate threshold pairs**
- Report the best F1-score and the pair you picked. Save as a markdown table in the notebook.
- Vectorize the final mask and drop polygons with area < 2000 m²

#### C3. Debris flow footprint mask (Pre→Post, downstream only)
Baseline rule: `(ndvi_change > 0.25) & (bsi_change > 0.10) & (nir_pre > 0.20)` — AND must be downstream of the Matai'an Creek mouth (lon > 121.35 as a simple gate)
- Drop polygons with area < 5000 m²
- **Explain in a markdown cell** why this rule is different from the C2 landslide rule (the physics of fresh mud sheet vs. exposed rock headwall)

### D. Multi-Layer Audit — The Eyewitness Impact Table

Produce an **Eyewitness Impact Table** as a DataFrame in the notebook:

| Asset | Type | Location | W4 Terrain Risk | W7 Centrality Rank | Barrier Lake Hit (Y/N) | Landslide Hit (Y/N) | Debris Flow Hit (Y/N) | Notes |
|-------|------|----------|-----------------|---------------------|-----------------------|---------------------|----------------------|-------|
| Shelter_H001 | W3 Shelter | Hualien City | 3 | — | N | N | N | outside event area |
| Node_H42 | W7 Bottleneck | Suhua Hwy | 2 | 1 | N | N | N | outside event area |
| Guangfu_Elementary | W8 Guangfu Overlay | 光復國小 | — | — | N | N | Y | buried in 20 cm debris |
| Matai'an_Bridge | W8 Guangfu Overlay | 台9線馬太鞍溪橋 | — | — | N | Y | Y | collapsed Sep 23 16:00 |

Rules:
- Include **all W3 shelters**, **all W7 Top-5 bottlenecks**, and **all nodes from the Guangfu overlay**
- "Hit" = inside (debris flow, lake) or within 200 m (landslide scar) of the detected polygon
- Sort by "Debris Flow Hit" first, then "Landslide Hit", then W4 terrain risk descending
- **Crucial teaching moment**: Include a markdown cell analyzing the **coverage gap** — how many W3/W7 Hualien City assets were hit (probably zero) vs. how many Guangfu overlay assets were hit. Discuss what this says about ARIA's pre-event coverage and what the county should do about it.

### E. AI Advisor Operational Brief (Bonus)

1. Feed the Impact Table + a text summary of the ARIA chain (W3→W4→W5→W6→W7→W8) + the **three-act timeline** into **any LLM you prefer** (ChatGPT / Gemini / Claude / local model — pick the tool you're most comfortable with)
2. Prompt specification: The AI should act as a *Hualien County Disaster Prevention Command Center — Chief of Operations* writing for the county magistrate
3. The AI brief must cover:
   - **Confirmed timeline**: What the imagery proves about each of the three acts
   - **The pre-breach window**: Between Jul 21 (lake formed) and Sep 23 (breach), what could ARIA v5.0 have warned about if it had been operational? Be specific — which satellite revisits had clean scenes?
   - **Coverage gap**: Why did the W3/W7 pre-event coverage miss Guangfu? What expansion does ARIA need?
   - **Next 24-hour orders** (as of the Post-event scene): priority clearance, shelter resupply, UAV tasking
   - **Model refinement**: One concrete suggestion to extend ARIA before the next barrier-lake event

```python
# Bonus Prompt Example (adapt to your AI of choice)
prompt = f"""You are the Chief of Operations at the Hualien County Disaster
Prevention Command Center, writing a brief for the county magistrate. ARIA v5.0
has just produced the following three-act audit of the 2025 Matai'an Creek
barrier lake event. Write a 250-word operational brief covering:

1. Three-act timeline — what the imagery proves
2. The pre-breach warning window (Jul 21 to Sep 23, 64 days) — what ARIA could
   have caught if it had been operational during that window
3. Coverage gap — why did W3/W7 miss Guangfu?
4. Next-24-hour orders: priority clearance, shelter resupply, UAV tasking
5. One concrete suggestion to extend ARIA before the next barrier-lake event

IMPACT TABLE:
{impact_table.to_markdown()}

THREE-ACT DETECTION SUMMARY:
- Act 1 (Pre, {PRE_ITEM_ID}): forested Matai'an valley, no lake
- Act 2 (Mid, {MID_ITEM_ID}): barrier lake {lake_area_km2:.3f} km² detected
- Act 3 (Post, {POST_ITEM_ID}): lake drained; landslide source {ls_area_km2:.3f} km²;
  debris flow footprint {db_area_km2:.3f} km² over Guangfu

ARIA CHAIN SUMMARY:
- W3: {len(shelters)} Hualien City shelters
- W4: {(shelters['terrain_risk'] > 2).sum()} shelters high terrain risk
- W7: Top 5 bottlenecks (all in Hualien City corridor)
- W8: 3 hazard masks produced, {n_guangfu_hits} Guangfu overlay nodes hit
"""
```

### F. Professional Standards (Infrastructure First)

1. **Environment Variables**: `.env` must contain `STAC_ENDPOINT`, `S2_COLLECTION`, `MATAIAN_BBOX`, `PRE_EVENT_START/END`, `MID_EVENT_START/END`, `POST_EVENT_START/END`, `TARGET_EPSG`
2. **Reproducible Scene IDs**: Save `PRE_ITEM_ID`, `MID_ITEM_ID`, `POST_ITEM_ID` as Python constants at the top of the notebook
3. **Captain's Log Markdown Cells**: Before each code block, write 1–2 sentences explaining *why* this step exists
4. **AI Diagnostic Log in README**: Describe how you solved at least one of:
   - "Mid-event STAC window returned only cloudy scenes — how did I find a usable one?"
   - "Barrier lake mask picked up river shadows as false positives — how did I filter them out?"
   - "Landslide mask had false positives on river sandbars — how did I use `pre_NIR > 0.3` or a slope gate?"
   - "Debris flow mask overlapped with the landslide mask — how did I decide which to keep?"
   - "Threshold tuning gave me F1 < 0.5 — what went wrong and how did I fix it?"

---

## 4. Recommended Coding Prompt

> "I need to build ARIA v5.0 — a satellite-based eyewitness auditor for the 2025 Matai'an Creek barrier lake event. I have:
> 1. `shelters_hualien.gpkg` from W3 (Hualien City range) with river_risk
> 2. `hualien_terrain.gpkg` from W4 with terrain_risk
> 3. `kriging_rainfall.tif` from W6
> 4. `top5_bottlenecks.gpkg` and `hualien_network.graphml` from W7
> 5. `guangfu_overlay.gpkg` from W8 (new Guangfu township critical nodes)
>
> Help me in separate Jupyter cells:
> 1. Connect to Planetary Computer STAC, query Sentinel-2 L2A for all three acts (Pre Jun / Mid Aug / Post Oct 2025)
> 2. TCI-preview the top-3 candidates in each window; let me pick and save item IDs
> 3. Stream B02/B03/B04/B08/B11/B12 via stackstac with Matai'an bbox (121.28, 23.56, 121.52, 23.76), EPSG:32651, 10 m
> 4. Compute nir_drop, swir_post, BSI change, and NDVI change as xarray DataArrays
> 5. Build three detection masks: (a) barrier lake Pre→Mid, (b) landslide source Pre→Post, (c) debris flow downstream Pre→Post
> 6. Ground-truth tune the landslide thresholds: 10+10 points, 5 threshold pairs, report F1
> 7. Vectorize each mask with rasterio.features.shapes (drop tiny polygons)
> 8. Spatial join with W3 shelters (100 m buffer), W7 top-5 bottlenecks (200 m buffer), and Guangfu overlay (within/100 m buffer)
> 9. Produce the Eyewitness Impact Table DataFrame with columns for all three hits + a coverage-gap discussion
> 10. Build the AI Advisor prompt (three-act timeline + impact table + coverage gap) and call my preferred LLM API
> 11. Save all figures to `output/` and write the README AI diagnostic log"

---

## 5. Deliverables

1. **GitHub Repo URL**
2. **`ARIA_v5_mataian.ipynb`** — Complete analysis notebook with all outputs executed
3. **`mataian_detections.gpkg`** — Multi-layer GeoPackage with three layers: `barrier_lake`, `landslide_source`, `debris_flow`
4. **`impact_table.csv`** — The Eyewitness Impact Table
5. **`output/` folder** — At minimum: three-act TCI panel, four change-metric maps, three detection masks, final impact map with all layers overlaid
6. **`README.md`** — Including AI diagnostic log, the three chosen STAC item IDs, and a coverage-gap discussion

---

## 6. Grading Rubric

| Item | Weight |
|------|--------|
| Three-act STAC scene selection + TCI quick-QA + reproducible item IDs | 15% |
| Four change metric functions (nir_drop, swir_post, BSI change, NDVI change) implemented correctly | 15% |
| Three detection masks (barrier lake + landslide source + debris flow) with threshold tuning and F1 reporting | 25% |
| Multi-layer audit (Impact Table with W3/W4/W7/Guangfu overlay join) + coverage-gap discussion | 20% |
| Professional standards (.env + README + Captain's logs + AI diagnostic log) | 15% |
| Visualization quality (three-act panel + detection overlays + final impact map) | 10% |
| Bonus: AI advisor three-act operational brief (any LLM) | +10% |

---

## 7. Tips and Notes

- **CRS consistency**: Sentinel-2 native = EPSG:32651 (UTM 51N). W3/W4/W7/Guangfu vectors = EPSG:3826 (TWD97). Always reproject *vectors to raster CRS* when sampling pixel values (faster than resampling the raster)
- **Memory safety**: `stackstac.stack()` with `bounds_latlon=MATAIAN_BBOX` keeps the cube under 200 MB. Without it you will get an OOM
- **Monsoon cloud traps**: August and September 2025 were peak monsoon. You may need `cloud_cover < 50%` and then hand-pick via TCI preview. This is normal and is exactly why Step A (TCI Quick-QA) exists
- **Turbid water NIR**: The Matai'an barrier lake is **turbid** (sediment-laden), so its NIR reflectance is 0.10–0.18, NOT < 0.05 like clear water. If you use a clear-water threshold, you will get zero lake pixels. Use `nir_mid < 0.18` as a starting point and add `green_mid > nir_mid` to confirm water-like spectral shape
- **Lake false-positive traps**: Deep shadows (especially on north-facing slopes in the afternoon) have low NIR *and* low blue. The `blue_mid > 0.03` gate handles most of them, but check near steep headwalls
- **Landslide false-positive traps**: Rivers, sandbars, bare harvested fields all trigger NIR-drop + SWIR-high. Use `pre_NIR > 0.3` (was actually vegetated) or a slope > 15° gate from W4 to clean it up
- **Debris flow false-positive traps**: Fresh wet rice paddies after harvest also have NDVI drop + moderate BSI. Use the `lon > 121.35` gate to restrict to downstream Guangfu, or cross-reference against a harvested-paddy mask
- **Cloud remnants**: Even cloud_cover < 20% scenes have scattered cloud shadows. Use the Sentinel-2 SCL (Scene Classification Layer, asset name `SCL`) and mask out classes 3 (cloud shadow), 8, 9, 10 (clouds of varying confidence)
- **TCI trick**: The TCI is served as 8-bit RGB JPEG — it loads in < 2 seconds even at full resolution. Use it for every visual check, not just the initial QA
- **Item ID format**: Sentinel-2 item IDs look like `S2A_MSIL2A_20250610T022601_R046_T51RTH_20250610T061802`. The 8-digit number in the middle is the acquisition date — use it to verify the scene falls inside your intended window
- **If you get zero lake pixels**: First check the `nir_mid` threshold — turbid water NIR is 0.10–0.18, not < 0.05 like clear water. If still zero, your Mid scene may be wrong (too early, lake hadn't formed, or too late, already breached). Check the item date is between 2025-08-01 and 2025-09-22. Also verify your spatial gate is not too aggressive — the lake center is at approximately (121.292, 23.696)
- **RAW vs GATED comparison**: The Demo notebook shows both unfiltered (`lake_mask_raw`) and spatially gated (`lake_mask`) results. This is good practice — always inspect raw results before applying spatial filters, to understand what the filter is doing

---

*"A risk model predicts the disaster. A network analysis tells you if you can still reach it. A satellite tells you whether your predictions were right — and whether there was a 200 m deep lake growing in the mountains for 64 days that nobody noticed."*
