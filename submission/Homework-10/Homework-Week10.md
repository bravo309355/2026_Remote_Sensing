# Week 10 Homework: ARIA v7.0 — The All-Weather Auditor

**Course:** NTU Remote Sensing & Spatial Information Analysis (遙測與空間資訊之分析與應用)  
**Instructor:** Prof. Su Wen-Ray  
**Assignment:** Week 10 Homework  
**Due Date:** See NTUCool (typically 1 week after class)  
**Case Study:** Hualien, Typhoon Fung-wong

---

## Overview

This week you build ARIA v7.0 — the **All-Weather Auditor** — by integrating SAR radar data with the optical change detection you developed in W8–W9. The key innovation is **cloud-piercing capability**: when optical satellites are blinded by clouds during a typhoon, SAR provides ground truth through the white wall.

**Scenario:** During Typhoon Fung-wong, cloud cover over Hualien was ~90%. Your ARIA system must demonstrate how it automatically detects cloudy areas and supplements optical gaps with SAR flood mapping.

**Key Deliverable:** A Jupyter notebook + markdown report that combines:
- SAR flood extraction with speckle filtering
- Multi-source sensor fusion (optical NDWI + SAR + DEM slope)
- Confidence-graded flood map
- AI-generated strategic briefing
- Comparison with W9's optical-only results

---

## Core Requirements (4 Tasks)

### Task 1: SAR All-Weather Flood Detection (25%)

**Procedure:**

1. **Load SAR data:** Read `S1_Hualien_dB.tif` using rasterio
   - This is a pre-processed Sentinel-1 GRD (VV polarization, calibrated, terrain-corrected, in dB)
   - Visualize the raw SAR image with an appropriate colormap (e.g., `gray`, range: -30 to 0 dB)

2. **Speckle filtering:** Apply a Median Filter (e.g., 5×5 kernel) to reduce speckle noise
   - Use `scipy.ndimage.median_filter` or equivalent
   - Visualize before/after comparison (side-by-side)

3. **Threshold segmentation:** Apply `sar_filtered < SAR_THRESHOLD` to extract water pixels
   - ARIA 文獻預設 -18 dB（全球通用），但最佳值因場景而異
   - 課堂案例（堰塞湖泥沙水）使用 -14 dB + morphological 後處理
   - 你的作業案例（花蓮一般淹水）可先用 -18 dB，觀察直方圖再調整
   - Create a binary flood mask
   - **進階（加分）：** 加入 morphological opening + connected component filtering 去除零碎假水體（參考 Demo notebook D6）
   - Visualize the mask overlaid on the SAR image

4. **Area calculation:** Compute flooded area in km² using pixel resolution from the GeoTIFF metadata

**Deliverable:**
- 2×2 subplot: (a) Raw SAR, (b) Filtered SAR, (c) Binary flood mask, (d) Overlay on base image
- Table: flooded area (km²), number of water pixels, mean backscatter in flood zone
- Statement: "SAR detected X km² of flooding that optical sensors could not see due to cloud cover"

---

### Task 2: Sensor Fusion — Multi-Source Confidence Map (30%)

**Fusion Logic:**

Combine your W9 optical NDWI result with the W10 SAR flood mask:

| Optical (NDWI > threshold) | SAR Water Mask | Cloud Masked? | Classification |
|---|---|---|---|
| ✅ Yes | ✅ Yes | No | **High Confidence** — dual evidence |
| ❌ No (cloudy) | ✅ Yes | Yes | **SAR Only (Cloudy)** — radar sees through clouds |
| ✅ Yes | ❌ No | No | **Optical Only** — needs manual review |
| ❌ No | ❌ No | — | **No Detection** |

**Note:** NDWI 閾值需依水質調整（清水 ~0.3，濁水 ~0.0）。課堂堰塞湖案例用 0.0。

**Procedure:**

1. **Load W9 outputs:** NDWI water mask and SCL cloud mask from your W9 notebook
   - Expected files: `../class9/output/ndwi_water_mask.npy` (or `.tif`) and `../class9/output/scl_cloud_mask.npy` (or `.tif`)
   - If you saved as numpy arrays: `np.load(path)`; if as GeoTIFF: `rasterio.open(path).read(1)`
   - If unavailable, you may re-compute from your W9 notebook, or use placeholder arrays for the fusion logic demo
2. **Align grids:** Ensure SAR and optical rasters are on the same grid (reproject/resample if needed)
   - Use `rioxarray`'s `reproject_match()` to align SAR to the optical grid (or vice versa)
   - Verify with: `assert sar_mask.shape == ndwi_mask.shape`
3. **Apply fusion logic:** Create a 4-class confidence map using the table above
4. **Compute area statistics:** For each class, calculate area in km²

**Deliverable:**
- Color-coded confidence map (4 classes with legend)
- Area statistics table for each confidence class
- Interpretation: "High confidence zones cover X km², representing areas confirmed by both sensors. SAR-only zones add Y km² of flood detection in cloudy areas."

---

### Task 3: Topographic Analysis — DEM & Slope Assessment (20%)

**Motivation:** SAR images suffer from geometric distortions on steep terrain (foreshortening, layover). These can create false "water" signals on mountain slopes — which is physically impossible.

**Procedure:**

1. **Load W4 slope data:** Import the DEM-derived slope raster from Week 4
   - Expected file: `../class4/output/slope_degrees.tif`
   - If unavailable, compute from DEM: `slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))` using `np.gradient(dem, pixel_size)`
   - Remember to align the slope raster to the same grid as your fusion map (use `reproject_match()` if shapes differ)

2. **Apply topographic filter:**
   - Rule: If a pixel is classified as "flood" BUT slope > 25° → reclassify as **False Positive**
   - Water cannot accumulate on slopes steeper than 25°
   - ⚠ **重要考量：** DEM 是否反映「現在」的地形？
     - 如果是穩定地區（如花蓮平原），DEM slope 可直接使用
     - 如果是災後崩塌區（如堰塞湖），舊 DEM 的坡度不再正確 → 不適合嚴格過濾
     - 課堂案例示範了這個限制：Copernicus DEM (2011-2014) 是災前地形

3. **Before/after comparison:** Show the fusion map with and without topographic correction
   - Quantify: "Topographic filter removed X pixels (Y km²) of false positives"

4. **討論（必答）：** 在你的案例中，DEM 是否適合用於地形校正？為什麼？如果 DEM 不適用，你會用什麼替代方法清理假水體？（提示：morphological opening, connected component filtering）

**Deliverable:**
- Side-by-side maps: fusion result before and after topographic correction
- Table: false positives removed by slope class (25–35°, 35–45°, >45°)
- 討論段落：DEM 適用性分析（2-3 句）

---

### Task 4: AI Strategic Briefing + ARIA v7.0 Report (25%)

**Part A: AI Strategic Briefing (15%)**

Feed your fusion results to an LLM (Gemini, ChatGPT, Claude, etc.) and request a strategic operational briefing:

1. Prepare a summary of key metrics:
   ```
   - High confidence flood area: X km²
   - SAR-only (cloudy) flood area: Y km²
   - False positives removed by topographic filter: Z km²
   - Cloud cover percentage: W%
   - SAR threshold: [your value] dB (explain why you chose this value)
   - NDWI threshold: [your value] (explain: clear water ~0.3, turbid water ~0.0)
   ```

2. Prompt the LLM:
   > "You are an emergency management advisor for Hualien County during Typhoon Fung-wong.
   > Based on these ARIA v7.0 sensor fusion results, generate a strategic briefing that covers:
   > 1. Which areas require immediate evacuation?
   > 2. How should resources be allocated between high-confidence and SAR-only zones?
   > 3. What are the limitations of the current assessment?
   > 4. What additional data would improve confidence?"

3. **Document the exchange:** Copy exact prompt and response into your notebook
4. **Your reflection:** Add 3–4 sentences on what the LLM got right/wrong

**Part B: ARIA v7.0 Evolution Report (10%)**

Write a markdown section comparing W9 (optical-only) vs. W10 (fused) results:

| Metric | W9 (Optical Only) | W10 (Fused) | Improvement |
|---|---|---|---|
| Total detected flood area | X km² | Y km² | +Z km² |
| Cloud-covered area analyzed | 0 km² | W km² | — |
| False positives (pre-correction) | A | B | — |
| Confidence levels | 3-zone | 4-class | Finer granularity |

**Deliverable:**
- Markdown section "## AI Strategic Briefing" with prompt, response, and reflection
- Markdown section "## ARIA v7.0 vs. v6.0 Comparison" with comparison table

---

## Professional Standards

### 1. Environment Reproducibility

**`.env` file (do NOT commit to GitHub):**
```
SAR_FILE=S1_Hualien_dB.tif
NDWI_THRESHOLD=0.3    # 清水用 0.3；濁水用 0.0（依場景調整）
SAR_THRESHOLD=-18      # ARIA 預設；課堂堰塞湖案例用 -14 + morphological cleanup
SLOPE_THRESHOLD=25     # 保守值；若 DEM 不適用可改用 morphological 替代
BBOX_WEST=121.28
BBOX_SOUTH=23.56
BBOX_EAST=121.52
BBOX_NORTH=23.76
```

### 2. Captain's Log (Markdown Cells)

Between each major code section, insert a markdown cell describing:
- What you're doing and why
- Expected output
- Any insights or surprises

### 3. Code Documentation

- Each function has a docstring with 1-line summary, parameters, returns
- Comments explain *why*, not just *what*
- Variable names are self-documenting

---

## Important: Academic Responsibility & Output Verification

> **⚠️ 警告：你必須對作業內容負責。**

SAR outputs are especially prone to false positives due to speckle noise and terrain distortion. Before you submit:

1. **Does your flood map make physical sense?** Water on mountaintops is wrong. If your flood area covers the entire study region, something is broken.
2. **Did you apply the Median Filter BEFORE thresholding?** Thresholding raw SAR produces garbage.
3. **Did you consider topographic effects?** 如果有合適的 DEM，用 slope 過濾；如果 DEM 不適用（如災後地形改變），改用 morphological cleaning。
4. **Can you explain the fusion logic?** If someone asks "Why is this zone High Confidence?", can you answer?

**不懂可以提問（NTUCool、office hours、課堂上都可以），但不要敷衍交差。**  
**Submitting unverified outputs will result in point deductions.**

---

## Grading Rubric (100%)

| Task | Component | Points | Criteria |
|------|-----------|--------|----------|
| **1. SAR Detection** | Load & visualize SAR | 8% | GeoTIFF loaded; appropriate colormap |
| | Speckle filtering | 7% | Median filter applied; before/after comparison |
| | Threshold & mask | 5% | Binary mask correct; area computed |
| | Visualization | 5% | 2×2 subplot; labeled; professional |
| **2. Sensor Fusion** | Fusion logic | 12% | 4-class confidence map correctly implemented |
| | Grid alignment | 8% | SAR and optical on same grid |
| | Area statistics | 5% | All classes quantified in km² |
| | Visualization | 5% | Color-coded map with legend |
| **3. Topographic Audit** | Slope loading | 5% | DEM slope raster loaded correctly |
| | Filter application | 8% | Slope > 25° pixels removed; before/after shown |
| | Quantification | 7% | False positives counted by slope class |
| **4. AI Briefing + Report** | LLM prompt & response | 8% | Thoughtful prompt; documented response |
| | Reflection | 7% | Your analysis of LLM's answer |
| | W9 vs W10 comparison | 10% | Table with quantitative comparison |
| **Professional Standards** | .env reproducibility | 3% | Parameters in .env; code reads from environment |
| | Captain's Log | 3% | ≥3 markdown cells explain reasoning |
| | Code quality | 2% | Well-commented; documented functions |
| | **Output verification** | 2% | Evidence of sanity checks in Captain's Log |

**Total: 100%**

---

## Bilingual Resources

### English Terms
- Synthetic Aperture Radar = 合成孔徑雷達
- Backscatter = 後向散射
- Specular Reflection = 鏡面反射
- Speckle = 斑點雜訊
- Sensor Fusion = 資料融合 / 感測器融合
- Confidence Map = 確信度圖
- Topographic Filter = 地形過濾
- Foreshortening = 前縮效應
- Layover = 疊置效應

### Chinese Concepts
- **鏡面反射** = 平滑水面將雷達能量反射走 → 低回波 → 暗色
- **體散射** = 植被冠層內多重散射 → 高回波 → 亮色
- **確信度分級** = 高（雙證據）/ 中（單SAR）/ 低（單光學）/ 無
- **地形審計** = 用坡度圖排除陡坡上的誤報

---

## Submission Checklist

- [ ] **All outputs verified**: Every metric, figure, and table checked for reasonableness
- [ ] Jupyter notebook named `Week10_ARIA_v70_[Your_Name].ipynb`
- [ ] `.env` file (with thresholds and parameters)
- [ ] All 4 tasks completed with deliverables
- [ ] Professional presentation: clear markdown, figures, tables
- [ ] Captain's Log cells throughout notebook
- [ ] Topographic analysis completed (DEM 適用性討論 included)
- [ ] AI briefing includes your own reflection
- [ ] W9 vs. W10 comparison table filled with real numbers
- [ ] Code is reproducible (runs without errors for TAs)
- [ ] Uploaded to NTUCool by due date (before 23:59)

---

## Additional Resources

- **SAR fundamentals:** https://www.asf.alaska.edu/information/sar-information/
- **Sentinel-1 user guide:** https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-1-sar
- **ASF HyP3:** https://hyp3-docs.asf.alaska.edu/ (cloud-based SAR pre-processing)
- **Prof. Su's Week 9 notebook:** Available on NTUCool

---

## Contact & Support

- **Questions?** Post on NTUCool Discussion or attend office hours
- **SAR data issues?** Check that `S1_Hualien_dB.tif` is in your `data/` folder
- **Environment errors?** Verify rasterio/rioxarray in Week 10 Pre-Lab

**The Captain's Final Thought:**
"A commander doesn't care if it's cloudy. He needs the truth. ARIA v7.0 delivers it."

---

*End of Homework Assignment — Week 10*
