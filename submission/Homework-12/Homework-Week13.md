# Week 13 Homework: ARIA v9.0 — The Cloud Engine

**Course:** NTU Remote Sensing & Spatial Information Analysis (遙測與空間資訊之分析與應用)  
**Instructor:** Prof. Su Wen-Ray  
**Assignment:** Week 13 Homework  
**Due Date:** See NTUCool (typically 1 week after class)  
**Case Study:** Cloud-Scale Vegetation Trend Analysis — Xiulin / Taroko Study Area（秀林 / 太魯閣研究區）

---

## Overview

本週你要將 ARIA 系統從 v8.0 升級到 **v9.0 — The Cloud Engine**。v8.0 用的是 pixel-level 的分類（K-means、Random Forest），在本機上處理單張影像；v9.0 引入 Google Earth Engine 雲端運算，從「一張影像」升級到「數百張影像的時序分析」，並追蹤 2024 花蓮地震及後續堰塞湖事件的多階段災害時間線。

**升級邏輯：**
```
v5.0 (W8)  → 光譜分析引擎：一張影像、一個指標（NDVI）
v6.0 (W9)  → 變遷偵測引擎：兩張影像、一個差值（ΔNDVI）
v7.0 (W10) → SAR 穿雲引擎：一張光學 + 一張 SAR
v8.0 (W12) → 分類引擎：一張影像、所有波段 → 土地覆蓋圖
v9.0 (W13) → 雲端引擎：數百張影像 → 時序趨勢分析 ⬆
```

**Key Deliverable:** A Colab/Jupyter notebook (.ipynb) that demonstrates:
- GEE Python API 操作（ImageCollection 篩選、雲遮罩、Reducer）
- 花蓮秀林/太魯閣地區 NDVI 多年時序分析
- 震前震後 median composite 比較
- Sentinel-1 SAR GRD 時序分析（銜接 W10）
- GeoTIFF 匯出（可供 W12 分類流程使用）

**Total: 100 pts + 20 pts bonus**

---

## Scenario（任務情境）

指揮官需要掌握花蓮秀林/太魯閣山區的**長期植被變化趨勢**——不只是地震前後的短期差異，而是過去六年的變化脈絡，包含 2024/04/03 地震和後續馬太鞍堰塞湖事件。

W8–W12 的分析都是「快照」（snapshot）——一個時間點的影像。指揮官問的是時間軸上的問題：「這片山坡的植被是逐年退化，還是地震才突然崩塌的？」「堰塞湖潰堤後有造成新的損害嗎？」「震後兩年植被有恢復的跡象嗎？」這些問題需要**時序分析**——而時序分析需要處理數百張影像，這正是 GEE 的強項。

> **Important:** The homework study area is **Xiulin / Taroko**（秀林 / 太魯閣山區）, which differs from the in-class Demo area (**Hualien City**, 花蓮市平原區). Mountain areas have different cloud cover patterns, vegetation dynamics, and SAR backscatter characteristics. You will discover that time series analysis reveals patterns invisible in single-scene analysis.

---

## Study Area & Data

### GEE Setup

```python
import ee
import geemap
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

ee.Authenticate()  # First time only
ee.Initialize(project='your-project-id')

# Xiulin / Taroko study area BBOX
# West: Central Mountain Range; East: Pacific Ocean
TAROKO_BBOX = [121.34526379253053, 24.046021742135874, 121.85149217685861, 24.35767637905926]
aoi = ee.Geometry.Rectangle(TAROKO_BBOX)

print(f"Study area: Xiulin / Taroko")
print(f"BBOX: {TAROKO_BBOX}")
```

### Available Data in GEE

| Dataset | GEE Collection ID | Resolution | Use |
|---------|-------------------|------------|-----|
| Sentinel-2 L2A | `COPERNICUS/S2_SR_HARMONIZED` | 10m | NDVI time series |
| Sentinel-1 GRD | `COPERNICUS/S1_GRD` | 10m | SAR backscatter time series |
| SRTM DEM | `USGS/SRTMGL1_003` | 30m | Elevation context |

---

## Core Requirements (4 Tasks)

### Task 1: NDVI Time Series Analysis (25%)

**目標：** 使用 GEE 計算秀林/太魯閣研究區 2020–2026 年的月均 NDVI 時序，觀察植被的季節變化和地震影響。

**Procedure：**

1. **篩選 Sentinel-2 ImageCollection：**
   ```python
   # Filter Sentinel-2 collection
   s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
       .filterBounds(aoi)
       .filterDate('2020-01-01', '2026-03-31')
       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40)))

   print(f"Total images: {s2.size().getInfo()}")
   ```

2. **定義雲遮罩 + NDVI 計算函數：**
   ```python
   def mask_and_ndvi(image):
       # SCL cloud mask (same concept as W12)
       scl = image.select('SCL')
       good = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
       masked = image.updateMask(good)
       # Calculate NDVI
       ndvi = masked.normalizedDifference(['B8', 'B4']).rename('NDVI')
       return ndvi.copyProperties(image, ['system:time_start'])

   ndvi_collection = s2.map(mask_and_ndvi)
   ```

3. **按月聚合並繪製時序圖：**
   - Compute monthly median NDVI over the AOI
   - Plot as a time series (x = month, y = mean NDVI)
   - Mark the 2024/04/03 earthquake with a vertical line
   - Annotate any visible NDVI drop after the earthquake

4. **觀察與分析：**
   - Is there a seasonal pattern?（是否有季節變化？）
   - Is the earthquake effect visible?（地震影響是否可見？）
   - Are there months with missing data? Why?（有缺值的月份嗎？為什麼？）

**Deliverables:**
- [ ] NDVI time series plot (2020–2026, monthly, with earthquake marker)
- [ ] Brief analysis (3–5 sentences): seasonal pattern, earthquake effect, data gaps
- [ ] Code with comments explaining each GEE operation

---

### Task 2: Pre/Post Earthquake Median Composite (25%)

**目標：** 使用 GEE Reducer 製作震前與震後的 median composite，計算 ΔNDVI，找出植被損失區域。

**Procedure：**

1. **製作震前 composite（2023/01–2024/03）：**
   ```python
   pre_eq = (ndvi_collection
       .filterDate('2023-01-01', '2024-03-31')
       .median())
   ```

2. **製作震後 composite（2024/04–2024/09）：**
   ```python
   post_eq = (ndvi_collection
       .filterDate('2024-04-01', '2024-09-30')
       .median())
   ```

3. **製作堰塞湖潰堤後 composite（2025/10–2026/03）：**
   ```python
   post_dam = (ndvi_collection
       .filterDate('2025-10-01', '2026-03-31')
       .median())
   ```

4. **計算三組 ΔNDVI：**
   ```python
   delta_eq = post_eq.subtract(pre_eq).rename('delta_NDVI')           # 地震損害
   delta_dam = post_dam.subtract(post_eq).rename('delta_NDVI_dam')    # 堰塞湖影響
   delta_total = post_dam.subtract(pre_eq).rename('delta_NDVI_total') # 總累積變化
   ```

5. **視覺化：**
   - Display three-phase composites and three ΔNDVI maps on a geemap interactive map
   - Use a diverging color palette (red = vegetation loss, blue = vegetation gain)
   - Compare: which areas show earthquake damage vs. landslide-dam damage vs. recovery?

6. **與 W9 方法比較：**
   - W9 used two single scenes → sensitive to clouds in either scene
   - W13 uses median composites from dozens of scenes → much more robust
   - Three-phase comparison disentangles different disaster events
   - Discuss: how does composite-based change detection improve reliability?

**Deliverables:**
- [ ] Interactive map or screenshot showing three-phase NDVI composites and three ΔNDVI maps
- [ ] Estimated area (in hectares) with ΔNDVI < −0.15 for each phase
- [ ] Analysis: earthquake damage vs. landslide-dam impact vs. vegetation recovery
- [ ] Comparison paragraph: W9 two-scene vs W13 composite-based change detection

---

### Task 3: Sentinel-1 SAR Time Series (25%)

**目標：** 使用 GEE 分析 Sentinel-1 VV 時序，從 SAR 視角觀察地震前後的地表變化，銜接 W10 概念。

**Procedure：**

1. **篩選 Sentinel-1 GRD：**
   ```python
   s1 = (ee.ImageCollection('COPERNICUS/S1_GRD')
       .filterBounds(aoi)
       .filterDate('2022-01-01', '2026-03-31')
       .filter(ee.Filter.eq('instrumentMode', 'IW'))
       .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
       .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
       .select('VV'))

   print(f"S1 images: {s1.size().getInfo()}")
   ```

2. **繪製 VV 時序圖：**
   - Compute mean VV (dB) over the AOI for each image
   - Plot time series with earthquake marker
   - Look for backscatter changes (drops may indicate landslides, increases may indicate bare soil exposure)

3. **震前/震後 VV composite：**
   ```python
   pre_vv = s1.filterDate('2023-01-01', '2024-03-31').median()
   post_vv = s1.filterDate('2024-04-01', '2026-03-31').median()
   delta_vv = post_vv.subtract(pre_vv).rename('delta_VV')
   ```

4. **Cross-reference with NDVI：**
   - Areas with both ΔNDVI < −0.15 AND |ΔVV| > 2 dB → high-confidence change areas
   - This is the multi-source validation concept from W10, now at cloud scale

**Deliverables:**
- [ ] SAR VV time series plot (2022–2026, with earthquake marker)
- [ ] ΔVV map (pre vs post earthquake)
- [ ] Brief analysis: how does SAR change correlate with NDVI change?

---

### Task 4: Export GeoTIFF + Integration Summary (25%)

**目標：** 將 GEE 分析結果匯出為 GeoTIFF，並撰寫 ARIA v9.0 升級摘要報告。

**Procedure：**

1. **匯出 GeoTIFF：**
   ```python
   # Export post-earthquake NDVI composite as GeoTIFF
   task = ee.batch.Export.image.toDrive(
       image=post_eq,
       description='taroko_ndvi_post_eq_2024',
       folder='GEE_Exports',
       region=aoi,
       scale=10,
       crs='EPSG:32651',
       maxPixels=1e9,
   )
   task.start()
   print("Export started — check Google Drive when complete")
   ```

   Export at least 2 products:
   - Post-earthquake NDVI composite
   - ΔNDVI map

2. **Integration summary report：**

   Write a structured summary (300–500 words) covering:

   **a. Data scale comparison:**
   - How many Sentinel-2 images were processed? How many Sentinel-1?
   - How long would it take to download and process these locally (estimate)?

   **b. Key findings:**
   - Seasonal NDVI pattern observed
   - Earthquake impact on vegetation (ΔNDVI)
   - SAR backscatter changes and correlation with NDVI

   **c. Cross-week integration:**
   - How does GEE time series improve upon W8 single-scene NDVI?
   - How does median composite improve upon W9 two-scene change detection?
   - How does GEE SAR time series extend W10 single-scene SAR analysis?
   - If you fed the exported GeoTIFF into W12's Random Forest classifier, what would you expect?

   **d. Limitations:**
   - What can GEE NOT do that STAC API + local processing can?
   - When would you still choose the W8–W12 approach?

**Deliverables:**
- [ ] At least 2 exported GeoTIFF files (on Google Drive, include screenshots of Drive files)
- [ ] Integration summary report (300–500 words)

---

## Bonus: InSAR Interferogram Reading Exercise (+10%)

**目標：** 練習閱讀 InSAR 干涉圖——不需要任何軟體操作，純粹練習「讀圖」能力。

**Background：** InSAR 干涉圖（interferogram）用彩虹色環表示地表位移。每一個完整的色環（fringe）代表半個雷達波長的位移量。色環越密集，位移越劇烈。

**參考資料：**
- [InSAR 彩虹干涉環判讀](https://tech.ardswc.gov.tw/EPaper/Home/EPaper?PaperID=97f62ecf-44eb-4f41-a5a7-5a1d4048ef67)（水保署電子報第 141 期，中文，必讀）
- [大型山崩判釋新利器：結合 InSAR 與光達數值地形](https://www.ceci.org.tw/Upload/Download/F45F3A64-D098-465A-9CDB-F2A4B7A9DD10.pdf)（陳柔妃、林慶偉，2018，台灣案例）

**Exercise：**

閱讀水保署電子報第 141 期中的 2016 熊本地震干涉圖（圖 3），回答以下問題：

1. **衛星資訊：** 該干涉圖使用哪個衛星？什麼波段？波長多少？
2. **每環位移量：** 每一個完整干涉環代表多少公分的位移？（提示：半波長）
3. **干涉環數量：** 斷層上方區域大約有幾個完整的干涉環？
4. **位移方向：** 色階變化是「藍→黃→紫」還是「藍→紫→黃」？代表接近還是遠離衛星？
5. **總位移量估算：** 根據以上資訊，估算 LOS（視線方向）位移量是多少公分？

**Deliverables:**
- [ ] 五個問題的答案（簡答即可，每題 1–2 句）
- [ ] 簡短心得（50–100 字）：InSAR 干涉圖能提供什麼是 SAR 振幅分析（W10）做不到的？

---

## Bonus 2: NDVI Time-Lapse Animation (+10%)

**目標：** 製作太魯閣/秀林研究區的 NDVI 時序動畫 GIF，用視覺化方式呈現 2020–2026 的植被變化歷程。

**背景：** 靜態圖只能看到「某個時間點的狀態」或「兩期之間的差異」。動畫則讓你一眼看出**變化的連續過程**——季節循環、地震衝擊、堰塞湖事件、植被恢復，全都在幾秒鐘內展現。這是災害監測簡報中最有說服力的素材之一。

**Procedure：**

1. **用 GEE 產生半年度 NDVI 合成影像序列：**
   ```python
   import io, requests
   from PIL import Image
   import imageio

   periods = [
       ('2020-01', '2020-06'), ('2020-07', '2020-12'),
       ('2021-01', '2021-06'), ('2021-07', '2021-12'),
       ('2022-01', '2022-06'), ('2022-07', '2022-12'),
       ('2023-01', '2023-06'), ('2023-07', '2023-12'),
       ('2024-01', '2024-03'),                          # pre-EQ
       ('2024-04', '2024-09'),                          # post-EQ
       ('2024-10', '2025-03'), ('2025-04', '2025-09'),
       ('2025-10', '2026-03'),                          # post-dam
   ]
   ```

2. **對每個時段產生 NDVI 中值合成並匯出為縮圖：**
   ```python
   frames = []
   ndvi_palette = ['brown', 'yellow', 'green', 'darkgreen']

   for start, end in periods:
       composite = (ndvi_collection
           .filterDate(f'{start}-01', f'{end}-28')
           .median())

       # 用 getThumbURL 取得縮圖
       thumb_url = composite.getThumbURL({
           'region': aoi,
           'dimensions': 512,
           'min': 0, 'max': 0.8,
           'palette': ndvi_palette,
       })
       response = requests.get(thumb_url)
       img = Image.open(io.BytesIO(response.content)).convert('RGB')

       # 加上時間標籤
       # (提示：用 PIL.ImageDraw 在角落加文字)
       frames.append(img)
       print(f"  {start} ~ {end}: OK")
   ```

3. **組合為動畫 GIF：**
   ```python
   imageio.mimsave('taroko_ndvi_timelapse.gif',
                    [np.array(f) for f in frames],
                    duration=0.8,  # 每幀 0.8 秒
                    loop=0)        # 無限循環
   print("Saved: taroko_ndvi_timelapse.gif")
   ```

4. **進階挑戰（加分中的加分）：**
   - 在每幀上疊加時間標籤（例如 `2024-04 ★ 地震`、`2025-10 ★ 堰塞湖`）
   - 加入色條（colorbar）讓觀眾知道顏色對應的 NDVI 值
   - 用 matplotlib.animation 製作更精緻的版本（含標題、座標軸、事件標記）
   - 同時做一個 RGB 真色版本的動畫，和 NDVI 版本並排比較

**技術提示：**
- `getThumbURL()` 是 GEE 的輕量化縮圖 API，不需要完整匯出
- `PIL`（Pillow）處理影像、`imageio` 組合 GIF — 這兩個套件 Colab 已預裝
- 如果某個時段影像太少（全被雲遮掉），該幀會出現黑色或空白 → 可以跳過或標記 "no data"
- GIF 檔案大小建議控制在 5 MB 以內（降低 `dimensions` 或減少幀數）

**Deliverables:**
- [ ] 動畫 GIF 檔案（`taroko_ndvi_timelapse.gif`）
- [ ] 程式碼（含註解）
- [ ] 簡短說明（50–100 字）：動畫中最明顯的三個變化時刻是什麼？

---

## Technical Notes

### 常見問題

**Q: `ee.Initialize()` 報錯？**
- 確認已執行 `ee.Authenticate()`
- 確認已設定 project ID：`ee.Initialize(project='your-project-id')`
- 如果帳號剛註冊，可能需要等待最多 24 小時核准

**Q: 時序圖全部是零或 NaN？**
- 確認 BBOX 座標順序：GEE 用 `[west, south, east, north]`
- 確認雲量過濾條件不要太嚴格（山區可能需要放寬到 50–60%）
- 確認日期範圍內有 Sentinel-2 影像覆蓋

**Q: 月均值某些月份缺值？**
- 花蓮山區多雨，某些月份（特別是梅雨季和颱風季）可能所有影像都被雲量過濾掉
- 這是正常現象，在時序圖上標記為「no data」即可
- 可嘗試放寬雲量條件，或改用 SCL 雲遮罩而非整景雲量百分比

**Q: 匯出很慢？**
- GEE 匯出是非同步的（asynchronous）——`task.start()` 只是送出任務
- 用 `task.status()` 檢查進度
- 小區域通常 1–5 分鐘；大區域可能 10–30 分鐘
- 匯出期間可以繼續做其他分析

**Q: geemap 地圖在 Colab 上不顯示？**
- 試用 `geemap.Map()` 而非 `geemap.Map(basemap='HYBRID')`
- 確認 Colab 允許互動式 widget：`from google.colab import output; output.enable_custom_widget_manager()`

---

## Submission Format

1. **Notebook** (.ipynb) — 包含所有 4 個 Task 的程式碼和執行結果
2. **Exported GeoTIFF screenshots** — Google Drive 中的匯出檔案截圖
3. **Integration summary report** — Task 4 的 300–500 字摘要（可在 notebook 的 Markdown cell 中撰寫）
4. **簡短心得**（100–200 字）：
   - 從單景分析到雲端時序分析，思維上有什麼改變？
   - GEE 在防災應用中的價值是什麼？

上傳至 NTUCool 作業區。

---

## Grading Rubric

| 項目 | 配分 | 評分重點 |
|------|------|---------|
| Task 1: NDVI 時序 | 25% | 時序圖品質、季節/地震分析、程式碼註解 |
| Task 2: Composite 比較 | 25% | 震前/震後合成影像、ΔNDVI 分析、與 W9 比較 |
| Task 3: SAR 時序 | 25% | VV 時序圖、ΔVV map、光學/SAR 交叉比對 |
| Task 4: 匯出 + 摘要 | 25% | GeoTIFF 匯出成功、Integration summary 深度 |
| **Bonus 1** | +10% | InSAR 干涉圖判讀練習（5 題 + 心得） |
| **Bonus 2** | +10% | NDVI 時序動畫 GIF（動畫品質、程式碼、變化說明） |

---

## The Captain's Tip

> 「以前你拿一張照片給我看——『長官，這裡有崩塌。』現在你給我看一條時間線——『長官，這片山坡在地震後崩塌，堰塞湖潰堤又造成下游新損害，但東側已經開始恢復。』三期比較讓你拆解每個事件的貢獻。這就是時序分析的價值：它把『快照』變成『故事』。而且你不需要下載一張影像，全部在雲端完成。」

---

*Note: This homework does NOT require GPU. All GEE computation runs on Google's cloud servers. A regular laptop with internet access is sufficient. If you encounter any issues, post on NTUCool or email Prof. Su.*
