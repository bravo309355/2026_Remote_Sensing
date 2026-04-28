# Week 10 Exercise — ARIA v7.0：SAR 淹水偵測與多源融合

**Course**: NTU 遙測與空間資訊之分析與應用  
**Instructor**: Prof. Su Wen-Ray (蘇文瑞教授)  
**Case Study**: 2025 馬太鞍溪堰塞湖（薇帕颱風後）  
**日期**: 2026-04-28

---

## 任務概述

延續 W8–W9 的 Sentinel-2 光學分析，本週將感測器切換到 **Sentinel-1 SAR**，建立 ARIA v7.0「全天候決策引擎」。

| Lab | 內容 | 時長 |
|-----|------|------|
| Lab 1 | SAR 淹水偵測（STAC + Sentinel-1 RTC + 形態學清理）| 35 min |
| Lab 2 | ARIA v7.0 Sensor Fusion（SAR + Optical NDWI + DEM）| 30 min |
| Challenge | SAR Threshold 比較（-14 dB vs -18 dB） | 15 min |

**核心學習點**：用同一個 `pystac_client → stackstac → xarray` pipeline 處理 SAR，差別只在 collection 與不需雲量過濾。

---

## 檔案結構

```
Exercise-10/
├── Week10-Student.ipynb           # 完整版（已填 TODO + 反思 + 執行結果）
├── Week10-Student-origin.ipynb    # 原始空白版備份
├── README.md                      # 本檔
└── output/
    ├── W10_sar_before_after.png   # 災前/災後 VV + 差異圖
    ├── W10_L1_sar_flood.png       # Lab 1: SAR 水體偵測 2×2
    ├── W10_optical_vs_sar.png     # 光學 vs SAR 對比 2×2
    ├── W10_L2_confidence_map.png  # Lab 2: 融合信心圖
    └── W10_threshold_compare.png  # 課堂挑戰閾值對比
```

---

## 方法論

### Lab 1：SAR 淹水偵測

```
Sentinel-1 RTC (VV)
  → 10 × log₁₀(linear) → dB
  → Median filter 5×5（去 speckle）
  → Threshold: VV < -14 dB（寬鬆）
  → Morphological opening（去零碎雜訊）
  → Connected component filter（≥ 0.5 ha = 50 px）
  → Final water mask
```

**關鍵設計選擇**：
- **bbox** `[121.270, 23.685, 121.310, 23.715]` 涵蓋堰塞湖 + 周邊地形
- **軌道方向** 自動偵測共同軌道（最終選 ascending），避免升降軌混用造成幾何偽影
- **閾值 -14 dB**（不採文獻 -18 dB）：因堰塞湖含泥沙懸浮，水面 backscatter 偏高
- **形態學後處理**：彌補寬鬆閾值的假陽性

### Lab 2：4-class Confidence Fusion

| Code | Label | 條件 |
|------|-------|------|
| 3 | High Confidence | SAR ✓ ∩ NDWI ✓（雙感測器確認） |
| 2 | SAR Only (Cloudy) | SAR ✓ ∩ Cloud ✓（雲遮蔽下 SAR 補充） |
| 1 | Optical Only | NDWI ✓ ∩ SAR ✗（需人工複核） |
| 0 | No Detection | — |

---

## 結果

### 數據總覽

| 階段 | 數值 | 與 NCDR 實測 80 ha 比較 |
|------|------|------------------------|
| SAR raw -14 dB（無清理） | 174.3 ha | 過估 2.2x |
| SAR + 形態學清理 | 153.9 ha | 過估 1.9x |
| SAR -18 dB（嚴格） | 62.0 ha | 低估 23% |
| **High Confidence (SAR ∩ NDWI)** | **78.3 ha** | **誤差 < 2%** ✅ |
| Optical Only | 280.4 ha | 含河道、水田（NDWI 寬門檻必然） |
| SAR Only (Cloudy) | 13.9 ha | 雲下少量補充 |

### 關鍵發現

1. **單感測器都不準**，但**雙感測器交集 (High Confidence) 與實測誤差 < 2%**
2. SAR 過估主因：升軌觀測下西向坡面 radar shadow + 河道與水田被誤判
3. NDWI 過估主因：閾值 0.0（為抓濁水）→ 連河道、灌溉水田都進來
4. **取交集自動消除彼此假陽性** — 這就是 ARIA v7.0 多源融合的核心價值

---

## 反思摘要（完整答案見 notebook）

### Q1: 為什麼 -18 dB 是合理閾值？

介於平靜水面（< -20 dB 鏡面反射）與粗糙地表（> -10 dB 表面散射）之間的近似分界。-12 dB 過寬會抓到裸土，-25 dB 過嚴會漏掉風吹水面與濁水。

### Q2: 只用 SAR 能否偵測堰塞湖？

**能偵測但會嚴重過估** — 本實驗 153.9 ha vs 實測 80 ha，誤差來自 radar shadow + 平滑非水體。颱風期是唯一可用訊號（光學被雲遮蔽），但需要光學在雲開時做事後校正。

### Q3: 為什麼不能用 Copernicus DEM 過濾假水體？

Copernicus DEM 是 2011-2014 年地形（**災前**），但堰塞湖正是 2025/7 崩塌後形成的新地物 — 在舊 DEM 上仍是 30°+ 陡溪谷。用舊 DEM 的坡度做 `slope > 30° → 排除`，會把真正的堰塞湖也濾掉，造成漏報。

### Q4: 災後新 DEM 取得方式？

| 方法 | 時效 | 精度 |
|------|------|------|
| Sentinel-1 InSAR | 24-48 hr | 5-10 m |
| 空載 LiDAR | 1-7 天 | 0.1-0.5 m |
| UAV SfM | 1-3 天 | 0.05-0.2 m |
| 全國性 LiDAR 更新 | 數年 | 0.1 m |

本週的 SAR 偵測在「災後 0-7 天黃金救援期」進行 — 還沒有災後 DEM。**正確做法是承認過估，改用光學雙重確認來收斂結果**。

### Q5: 課堂挑戰判斷 — 寬鬆 + 後處理 vs 嚴格門檻？

**防災早期預警應採寬鬆 -14 dB + 形態學後處理**：
- **Recall 優先**：嚴格 -18 dB 漏報率 23%，早期預警漏報代價遠大於誤報
- **精度可由後處理補回**：median filter + opening + connected component 三道清理 + 光學交集，最終 78.3 ha 與 NCDR 80 ha 誤差 < 2%
- 結論：**訊號階段別自我設限，雜訊用幾何方法收斂**

---

## 環境與執行

```bash
# 環境
c:\Users\user\anaconda3\envs\geopandas

# 主要套件
- pystac_client, planetary_computer, stackstac
- xarray, rioxarray, rasterio
- numpy, scipy.ndimage (median_filter, binary_opening, label)
- matplotlib

# 執行
jupyter nbconvert --to notebook --execute --inplace Week10-Student.ipynb
```

**雲端串流**：全程透過 Microsoft Planetary Computer STAC API，**不需下載任何檔案**。

---

## W8–W10 完整鏈結

| Week | Sensor | Collection | 重點差異 |
|------|--------|------------|----------|
| W8 | Sentinel-2 | `sentinel-2-l2a` | 光復重災區光學分析 |
| W9 | Sentinel-2 | `sentinel-2-l2a` | 變遷偵測 + 雲遮罩驗證 |
| **W10** | **Sentinel-1** | **`sentinel-1-rtc`** | **SAR 全天候 + 雙感測器融合** |

同一個工作流，不同感測器，互補長短 — 這就是 ARIA v7.0 的設計哲學。

---

## Sanity Check 結果

| Check | 結果 | 判讀 |
|-------|------|------|
| Flood area 比例 | 78.3 / 1396 ha ≈ 5.6% | ✅ 合理（< 10%） |
| Speckle 處理 | Median 5×5 → threshold → opening → CC | ✅ 完整三階段 |
| Topo filter | 已說明本案例不適用 DEM 校正 | ⚠ 文件化限制 |
| Fusion 邏輯 | High Conf = SAR ∩ NDWI；SAR Only = SAR ∩ Cloud | ✅ 邏輯清楚 |

**結論：High Confidence 78.3 ha vs NCDR 實測 80 ha，誤差 < 2% — 方法論完整、結果可信。**
