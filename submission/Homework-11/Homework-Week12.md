# Week 12 Homework: ARIA v8.0 — The Classification Engine

**Course:** NTU Remote Sensing & Spatial Information Analysis (遙測與空間資訊之分析與應用)  
**Instructor:** Prof. Su Wen-Ray  
**Assignment:** Week 12 Homework  
**Due Date:** See NTUCool (typically 1 week after class)  
**Case Study:** Post-Earthquake Land Cover Classification — Xiulin / Taroko Study Area（秀林 / 太魯閣研究區）

---

## Overview

本週你要將 ARIA 系統從 v7.0 升級到 **v8.0 — The Classification Engine**。v7.0 用的是 pixel-level 的閾值（NDVI > T、VV < T_dB）；v8.0 引入分類器，從「一次一個指標分兩類」升級到「同時用所有波段分多類」。

**升級邏輯：**
```
v5.0 (W8)  → 光譜判讀：哪裡有異常？（目視 + 假彩色）
v6.0 (W9)  → 變遷偵測：變了多少？可信嗎？（ΔNDVI + confusion matrix）
v7.0 (W10) → SAR 融合：雲下面發生了什麼？（多源閾值 + 確信度）
v8.0 (W12) → 影像分類：每個像素是什麼地物？（K-means + Random Forest）⬆
```

**Key Deliverable:** A Colab/Jupyter notebook (.ipynb) that demonstrates:
- STAC API 串流 Sentinel-2 多光譜影像（延續 W8–W10 工作流）
- K-means 非監督式分類 → 地物分群
- Random Forest 監督式分類 → 地物類別圖
- Confusion matrix 分類精度評估（呼應 W9）
- AI-generated classification report

---

## Scenario（任務情境）

指揮官不再滿足於「哪裡有異常」。他需要一張完整的**災後土地覆蓋圖**——每個像素對應一個類別：水體、森林、農田、裸地/崩塌、建物/都市。這張圖是所有後續分析（避難所評估、路網可達性、崩塌面積計算）的基礎圖資。

Your task: using post-earthquake Sentinel-2 imagery, build a multi-class land cover classification for the **Xiulin / Taroko area**（秀林 / 太魯閣）— a study area different from the in-class Demo — and evaluate classification quality.

> **Important:** The homework study area is **Xiulin / Taroko**（山區 + 海岸）, which differs significantly from the in-class Demo area (**Hualien City**, 都市 + 平原). You must re-interpret land cover in Google Earth and re-draw your training samples from scratch. This mountainous region is dominated by forest and landslides, with very few built-up or cropland pixels — you will discover that the same classifier performs differently across different terrain types.

---

## Study Area & Data

### STAC API（延續 W8–W10 工作流）

```python
import pystac_client
import planetary_computer as pc
import stackstac

catalog = pystac_client.Client.open(
    'https://planetarycomputer.microsoft.com/api/stac/v1',
    modifier=pc.sign_inplace,
)

# Xiulin / Taroko study area BBOX
# West: Central Mountain Range foothills; East: Pacific Ocean (ensures water samples)
TAROKO_BBOX = [121.40, 24.10, 121.80, 24.25]

# Post-earthquake imagery — progressive search (strict → relaxed)
# Hualien April-May = plum rain season → high cloud cover, need flexible strategy
search_configs = [
    ('2024-04-15/2024-05-31', 20, 'Phase 1: 2 months post-quake, CC < 20%'),
    ('2024-04-03/2024-08-31', 30, 'Phase 2: 5 months post-quake, CC < 30%'),
    ('2024-04-03/2024-12-31', 50, 'Phase 3: full year post-quake, CC < 50%'),
]

for dt_range, max_cc, desc in search_configs:
    print(f"Trying {desc}...")
    search = catalog.search(
        collections=['sentinel-2-l2a'],
        bbox=TAROKO_BBOX,
        datetime=dt_range,
        query={'eo:cloud_cover': {'lt': max_cc}},
    )
    items = list(search.items())
    print(f"  → Found {len(items)} scenes")
    if len(items) > 0:
        break

# Sort by cloud cover, pick the best scene
items_sorted = sorted(items, key=lambda x: x.properties['eo:cloud_cover'])
best_item = items_sorted[0]
print(f"Selected: {best_item.id}, cloud cover: {best_item.properties['eo:cloud_cover']:.1f}%")
```

### Classification Bands + SCL Cloud Mask

```python
# 6 reflectance bands + SCL (Scene Classification Layer) for cloud masking
BANDS = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
BANDS_ALL = BANDS + ['SCL']
# B02=Blue, B03=Green, B04=Red, B08=NIR, B11=SWIR1, B12=SWIR2
# SCL: Sentinel-2 L2A built-in scene classification — identifies cloud, shadow, snow
```

> **Important:** Post-earthquake imagery may have high cloud cover. You **must** apply SCL cloud masking to filter cloud, cloud shadow, and snow pixels before classification. Refer to the in-class Demo cell D3 for implementation details.

### Target Land Cover Classes

| 類別 ID | 名稱 | 英文 | 光譜特徵 |
|---------|------|------|---------|
| 1 | 水體 | Water | NIR 低、SWIR 低 |
| 2 | 森林 | Forest | NIR 高、Red 低 |
| 3 | 農田 | Cropland | NIR 中高、季節變化大 |
| 4 | 裸地/崩塌 | Bare/Landslide | 各波段中等、SWIR 高 |
| 5 | 建物/都市 | Built-up | 反射率高、各波段混合 |

---

## Core Requirements (4 Tasks)

### Task 1: K-means Unsupervised Classification (15%)

**Goal:** Apply K-means to the post-earthquake multispectral image to explore spectral clustering without training data.

**Procedure：**

1. **STAC API image loading + preprocessing：**
   ```python
   import numpy as np
   
   # Stream loading (same as W8 stream_cube pattern)
   cube = stackstac.stack([best_item], assets=BANDS_ALL, bounds_latlon=TAROKO_BBOX, resolution=20)
   img = cube.isel(time=0).compute()
   
   # Convert to surface reflectance
   img_sr = img / 10000.0
   
   # Build feature matrix: (n_pixels, n_bands)
   n_bands, h, w = img_sr.shape
   X = img_sr.values.reshape(n_bands, -1).T  # shape: (h*w, 6)
   
   # Remove NaN pixels
   valid = ~np.isnan(X).any(axis=1)
   X_valid = X[valid]
   print(f"Feature matrix: {X_valid.shape}")  # (n_valid_pixels, 6)
   ```

2. **K-means clustering (K=5)：**
   ```python
   from sklearn.cluster import KMeans
   
   kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
   labels = kmeans.fit_predict(X_valid)
   
   # Rebuild as 2D map
   label_map = np.full(h * w, np.nan)
   label_map[valid] = labels
   label_map = label_map.reshape(h, w)
   
   plt.figure(figsize=(10, 8))
   plt.imshow(label_map, cmap='tab10')
   plt.title('K-means Classification (K=5)')
   plt.colorbar(label='Cluster ID')
   plt.show()
   ```

3. **Cluster spectral analysis — label each cluster：**
   ```python
   # Compute mean spectrum per cluster
   for k in range(5):
       cluster_mean = X_valid[labels == k].mean(axis=0)
       print(f"Cluster {k}: B02={cluster_mean[0]:.3f}, B03={cluster_mean[1]:.3f}, "
             f"B04={cluster_mean[2]:.3f}, B08={cluster_mean[3]:.3f}, "
             f"B11={cluster_mean[4]:.3f}, B12={cluster_mean[5]:.3f}")
   # Based on spectral signatures, manually label each cluster to a land cover class
   ```

**Deliverables:**
- [ ] K-means classification map (K=5)
- [ ] Mean spectrum table per cluster + your land cover labels
- [ ] Brief discussion: which clusters are easy/hard to interpret? Why?

---

### Task 2: Random Forest Supervised Classification (25%)

**Goal:** Apply Random Forest supervised classification to produce a land cover map with labeled classes.

**Procedure：**

1. **Define training samples：**
   
   Manually select training pixels for each land cover class (ROI = Region of Interest)：
   
   ```python
   # === Method A: Pixel coordinates (simple) ===
   training_data = {
       'Water':     {'rows': [100, 101, 102, ...], 'cols': [200, 201, 202, ...]},
       'Forest':    {'rows': [300, 301, 302, ...], 'cols': [150, 151, 152, ...]},
       'Cropland':  {'rows': [400, 401, 402, ...], 'cols': [250, 251, 252, ...]},
       'Bare':      {'rows': [500, 501, 502, ...], 'cols': [300, 301, 302, ...]},
       'Built-up':  {'rows': [200, 201, 202, ...], 'cols': [400, 401, 402, ...]},
   }
   
   # === Method B (recommended): KMZ polygons — same as in-class Demo ===
   # Draw polygon ROIs for 5 land cover classes in Google Earth, export as KMZ
   # Upload to Colab and parse using the KMZ workflow from Demo cell D11
   ```
   
   > **Method B (KMZ) is recommended** — consistent with the in-class Demo, and polygon-based ROIs generally yield better training sample quality than manual pixel selection.
   
   > **Training sample 原則：**
   > - 每個類別至少 50-100 個像素
   > - 樣本分散在研究區各處（不要只集中在一個地方）
   > - 選擇「純淨」的像素（避免混合像素邊界）

2. **Assemble training data + train Random Forest：**
   ```python
   from sklearn.ensemble import RandomForestClassifier
   from sklearn.model_selection import train_test_split
   
   # 組合所有訓練樣本
   X_train_list, y_train_list = [], []
   class_names = list(training_data.keys())
   
   for class_id, class_name in enumerate(class_names):
       roi = training_data[class_name]
       for r, c in zip(roi['rows'], roi['cols']):
           pixel = img_sr[:, r, c].values
           if not np.isnan(pixel).any():
               X_train_list.append(pixel)
               y_train_list.append(class_id)
   
   X_train = np.array(X_train_list)
   y_train = np.array(y_train_list)
   
   # 80/20 split
   X_tr, X_te, y_tr, y_te = train_test_split(
       X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
   )
   
   # Train Random Forest (oob_score=True enables OOB validation for Task 3)
   rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, oob_score=True)
   rf.fit(X_tr, y_tr)
   
   print(f"Training accuracy: {rf.score(X_tr, y_tr):.3f}")
   print(f"Test accuracy: {rf.score(X_te, y_te):.3f}")
   ```

3. **Classify entire image：**
   ```python
   # 對整張影像進行預測
   y_pred_all = rf.predict(X_valid)
   
   # 重建為 2D 地圖
   class_map = np.full(h * w, np.nan)
   class_map[valid] = y_pred_all
   class_map = class_map.reshape(h, w)
   
   # 視覺化
   from matplotlib.colors import ListedColormap
   colors = ['#0077BE', '#228B22', '#DAA520', '#CD853F', '#808080']
   cmap = ListedColormap(colors)
   
   plt.figure(figsize=(12, 10))
   plt.imshow(class_map, cmap=cmap)
   plt.colorbar(ticks=range(5), label='Class')
   plt.title('Random Forest Land Cover Classification')
   plt.show()
   ```

4. **Feature Importance — which bands matter most?**
   ```python
   importance = rf.feature_importances_
   band_names = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
   
   plt.barh(band_names, importance)
   plt.xlabel('Feature Importance')
   plt.title('Random Forest — Band Importance')
   plt.show()
   ```

**Deliverables:**
- [ ] Random Forest land cover classification map
- [ ] Training / Test accuracy
- [ ] Feature importance bar chart + interpretation (which band ranks highest? why?)
- [ ] K-means vs Random Forest side-by-side comparison

---

### Task 3: Accuracy Assessment & Independent Validation (35%)

**Goal:** Evaluate classification quality using both internal metrics (confusion matrix) and **independent reference data** from SWCB（農業部水土保持署）post-earthquake landslide inventory.

This task has two parts: **Part A** uses your own train/test split (internal validation); **Part B** compares your "Bare/Landslide" class against an official government dataset (external validation).

#### Part A: Internal Accuracy Metrics

1. **Confusion Matrix + Classification Report：**
   ```python
   from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay
   
   y_pred_test = rf.predict(X_te)
   cm = confusion_matrix(y_te, y_pred_test)
   
   disp = ConfusionMatrixDisplay(cm, display_labels=class_names)
   disp.plot(cmap='Blues', values_format='d')
   plt.title('Classification Confusion Matrix')
   plt.show()
   
   print(classification_report(y_te, y_pred_test, target_names=class_names))
   ```

2. **OOB Score & Macro/Weighted Avg Analysis：**
   ```python
   # Enable OOB score during training (add oob_score=True in Task 2)
   print(f"OOB Accuracy:  {rf.oob_score_:.4f}")
   print(f"Test Accuracy: {rf.score(X_te, y_te):.4f}")
   ```
   - Compare **Macro avg** vs **Weighted avg** F1 in `classification_report` — gap > 0.03 suggests minority classes are being diluted
   - Check **Support** per class: metrics with < 30 test pixels may be unreliable

#### Part B: Independent Validation with SWCB Landslide Inventory

The file `20240802新生崩塌地.kml` contains **official post-earthquake landslide polygons** mapped by SWCB（農業部水土保持署）using high-resolution imagery. This is your **independent reference data** — it was NOT used in training.

> **Download link:** [20240802新生崩塌地.kml（Google Drive）](https://drive.google.com/file/d/17ka8y4N3IADSnJ1ymCJuzOfkutRzG-p8/view?usp=sharing) — download this file and upload it to your Colab working directory.

3. **Load and clip SWCB landslide polygons to study area：**
   ```python
   import geopandas as gpd
   import xml.etree.ElementTree as ET
   from shapely.geometry import Polygon, box
   
   # Parse KML — extract polygon coordinates
   # (adjust path if you placed the file in a subfolder)
   tree = ET.parse('20240802新生崩塌地.kml')
   ns = {'kml': 'http://www.opengis.net/kml/2.2'}
   
   polygons = []
   for pm in tree.getroot().findall('.//kml:Placemark', ns):
       coords_el = pm.find('.//kml:coordinates', ns)
       if coords_el is not None:
           coords = []
           for pt in coords_el.text.strip().split():
               lon, lat, *_ = pt.split(',')
               coords.append((float(lon), float(lat)))
           if len(coords) >= 3:
               polygons.append(Polygon(coords))
   
   gdf_swcb = gpd.GeoDataFrame(geometry=polygons, crs='EPSG:4326')
   
   # Clip to study area BBOX
   study_box = box(*TAROKO_BBOX)
   gdf_clipped = gdf_swcb[gdf_swcb.intersects(study_box)].copy()
   print(f"SWCB landslide polygons in study area: {len(gdf_clipped)}")
   ```

4. **Rasterize SWCB polygons to match classification grid：**
   ```python
   from rasterio.features import rasterize
   from rasterio.transform import from_bounds
   
   # Build transform matching your classification map
   transform = from_bounds(*TAROKO_BBOX, w, h)
   
   # Rasterize: 1 = SWCB landslide, 0 = not landslide
   swcb_mask = rasterize(
       [(geom, 1) for geom in gdf_clipped.geometry],
       out_shape=(h, w),
       transform=transform,
       fill=0,
       dtype='uint8',
   )
   print(f"SWCB landslide pixels: {swcb_mask.sum()}")
   ```

5. **Compute spatial overlap metrics：**
   ```python
   # Your classification: "Bare/Landslide" class (class_id = 3)
   rf_landslide = (class_map == 3).astype(int)  # adjust class_id as needed
   
   # Pixel-level comparison
   intersection = np.sum((rf_landslide == 1) & (swcb_mask == 1))
   union = np.sum((rf_landslide == 1) | (swcb_mask == 1))
   
   # Recall: how much of SWCB landslide did you detect?
   recall = intersection / swcb_mask.sum() if swcb_mask.sum() > 0 else 0
   # Precision: how much of your "landslide" is confirmed by SWCB?
   precision = intersection / rf_landslide.sum() if rf_landslide.sum() > 0 else 0
   # IoU (Intersection over Union)
   iou = intersection / union if union > 0 else 0
   
   print(f"Recall (detection rate):  {recall:.3f}")
   print(f"Precision (commission):   {precision:.3f}")
   print(f"IoU (Jaccard index):      {iou:.3f}")
   ```

6. **Overlay visualization + discussion：**
   ```python
   # Create overlay map: TP (green), FN (red), FP (yellow)
   overlay = np.zeros((h, w, 3), dtype=np.uint8)
   overlay[(rf_landslide == 1) & (swcb_mask == 1)] = [0, 200, 0]    # TP: green
   overlay[(rf_landslide == 0) & (swcb_mask == 1)] = [200, 0, 0]    # FN: red (missed)
   overlay[(rf_landslide == 1) & (swcb_mask == 0)] = [200, 200, 0]  # FP: yellow
   
   plt.figure(figsize=(12, 10))
   plt.imshow(overlay)
   plt.title('RF vs SWCB Landslide Overlay (Green=TP, Red=FN, Yellow=FP)')
   plt.show()
   ```
   
   **Discussion questions（必答）：**
   - Why is perfect overlap (IoU = 1.0) unlikely? Consider: temporal gap（影像日期 vs SWCB 判釋日期）, spatial resolution (Sentinel-2 20m vs high-res imagery), class definition differences
   - Where are the FN (missed) landslides concentrated? What might explain this?
   - How does this external validation compare to your internal test accuracy?

**Deliverables:**
- [ ] Confusion matrix heatmap + classification report
- [ ] OOB vs Test accuracy + Macro/Weighted avg gap analysis
- [ ] SWCB overlay map (TP/FN/FP visualization)
- [ ] Spatial overlap metrics table (Recall, Precision, IoU)
- [ ] Discussion: why overlap is imperfect + where FN concentrate (1-2 paragraphs)

---

### Task 4: AI Classification Report (25%)

**Goal:** Compute area statistics and use an LLM to generate a commander's briefing, then critically evaluate the AI output.

**Procedure：**

1. **Area statistics per class:**
   ```python
   pixel_area_m2 = 20 * 20  # 20m resolution
   
   class_stats = {}
   for i, name in enumerate(class_names):
       n_pixels = np.sum(class_map == i)
       area_ha = n_pixels * pixel_area_m2 / 10000
       class_stats[name] = {
           'pixels': int(n_pixels),
           'area_ha': round(area_ha, 1),
           'percentage': round(n_pixels / np.sum(~np.isnan(class_map)) * 100, 1),
       }
   
   import pandas as pd
   stats_df = pd.DataFrame(class_stats).T
   print(stats_df)
   ```

2. **LLM Report Generation：**
   ```python
   import google.generativeai as genai
   
   genai.configure(api_key="YOUR_GEMINI_API_KEY")
   model = genai.GenerativeModel("gemini-2.0-flash")
   
   prompt = f"""
   你是花蓮縣災害應變中心的 GIS 分析師。根據以下災後土地覆蓋分類結果，
   撰寫一份「災後土地覆蓋分析報告」（中文，300-500 字）。
   
   研究區：秀林鄉 / 太魯閣周邊（含蘇花公路沿線及近海區域）
   災害事件：2024 年 4 月 3 日花蓮地震（M7.4）
   分類方法：Random Forest（6 波段 Sentinel-2，5 類別）
   Overall accuracy: {rf.score(X_te, y_te):.1%}
   SWCB landslide IoU: [填入 Task 3 計算的 IoU]
   
   各類別面積：
   {stats_df.to_string()}
   
   報告需包含：
   1. 災後土地覆蓋概況
   2. 崩塌/裸地面積估計及其空間分布
   3. 與 SWCB 官方判釋的比對結果 + 不確定性說明
   4. 建議：這張分類圖可以如何支援後續的避難所評估或路網分析？
   """
   
   response = model.generate_content(prompt)
   print(response.text)
   ```

3. **LLM output evaluation：**
   - Are the area numbers in the LLM report correct? (Check for AI hallucination)
   - Is the uncertainty description reasonable?
   - What would you add or change?

**Deliverables:**
- [ ] Area statistics table per class
- [ ] LLM-generated report（中文，300-500 字）
- [ ] Your critical evaluation of the LLM report (1 paragraph)

---

## Submission Format

1. **Colab Notebook** (.ipynb) — all 4 Tasks with code and outputs
2. **Markdown Report** (.md) — extending the W8–W10 report format:
   - Abstract（200 words or less）
   - Results and discussion per Task
   - ARIA v8.0 upgrade reflection: from thresholds to classifiers
3. **Output files：**
   - `kmeans_classification.png` — K-means classification map
   - `rf_classification.png` — Random Forest classification map
   - `confusion_matrix.png` — classification confusion matrix
   - `swcb_overlay.png` — RF vs SWCB landslide overlay (TP/FN/FP)
   - `class_area_stats.csv` — area statistics per class

Upload to NTUCool assignment area.

---

## Grading Rubric

| Task | Weight | Key Criteria |
|------|--------|-------------|
| Task 1: K-means | 15% | Cluster spectral analysis, land cover labeling rationale |
| Task 2: Random Forest | 25% | Training sample quality, classification map, feature importance |
| Task 3: Accuracy + SWCB Validation | 35% | Confusion matrix, OOB/Macro-Weighted analysis, SWCB overlap metrics, FN discussion |
| Task 4: AI Report | 25% | Area statistics, LLM report quality, critical evaluation |

---

## The Captain's Tip

> 「閾值法是你的第一把尺——簡單但只能量一個維度。分類器是你的 CT 掃描——同時看所有波段，告訴你每個像素是什麼。但再好的工具也需要好的訓練資料，garbage in = garbage out。」

---

## Technical Notes

### FAQ

**Q: How do I choose training sample locations?**
- Use W8 true-color / false-color imagery for visual interpretation
- Cross-reference with Google Earth historical imagery
- At least 50 pixels per class, distributed across the study area

**Q: K-means is running too slowly?**
- Reduce resolution: `resolution=60` (from 20m to 60m)
- Or random subsample: `X_sample = X_valid[np.random.choice(len(X_valid), 50000)]`

**Q: How many trees for Random Forest (n_estimators)?**
- 100–500 trees is usually sufficient; more trees = more stable but slower
- Default `n_estimators=200` is a reasonable starting point

**Q: Salt-and-pepper noise in classification result?**
- Apply `scipy.ndimage.median_filter(class_map, size=3)` as post-processing
- Same concept as W10 SAR morphological cleanup

**Q: How do I upload the SWCB KML file to Colab?**
- Download from [Google Drive](https://drive.google.com/file/d/17ka8y4N3IADSnJ1ymCJuzOfkutRzG-p8/view?usp=sharing), then upload to your Colab working directory
- Or use the file from the course `class12/data/` folder on NTUCool

---

*Note: If you encounter any issues, post on NTUCool or email Prof. Su.*
