# Homework 10: ARIA v7.0 — The All-Weather Auditor

**Student:** Huang YongZhi
**Course:** NTU 遙測與空間資訊之分析與應用
**Case:** 花蓮 / 馬太鞍流域 × 鳳凰颱風 (Typhoon Fung-wong, 2025-11)
**Notebook:** `Week10_ARIA_v70_HuangYongZhi.ipynb`

---

## 任務涵蓋（4 大 Task + 專業規範）

| Task | 內容 | 占比 | 主要 Output |
|------|------|------|------------|
| Task 1 | SAR 全天候淹水偵測 | 25% | `HW10_T1_*.png/csv` |
| Task 2 | 4-class Sensor Fusion | 30% | `HW10_T2_*.png/csv` |
| Task 3 | DEM 地形審計 + 適用性討論 | 20% | `HW10_T3_*.png/csv` |
| Task 4 | AI 戰略簡報 (Gemini) + W9 vs W10 比較 | 25% | `HW10_T4_*.md/csv` |

---

## 鳳凰颱風時序定位

透過 STAC 掃描 2025-08 至 12 的 Sentinel-2 雲覆蓋率，鳳凰颱風峰值期定位為 **2025-11-02**（雲量 100%）。

| 角色 | 日期 | 來源 | 雲量 |
|------|------|------|------|
| Pre SAR（基準） | 2025-10-30 | Sentinel-1 ascending | — |
| Post SAR（鳳凰過後） | 2025-11-05 | Sentinel-1 ascending | — |
| Pre Optical（清晰基準）| 2025-10-16 | Sentinel-2 L2A | 2.5% |
| **Peak Cloud (光學失明)** | **2025-11-02** | Sentinel-2 L2A | **100%** |
| Post Optical（融合用）| 2025-11-15 | Sentinel-2 L2A | 46% |

兩個 SAR 都是 ascending 軌道一致，符合 Exercise 教訓（避免幾何偽影）。

---

## 主要結果

### Task 1: SAR Flood Detection
- 處理流程：Median 5×5 → VV < -18 dB → Morphological opening → CC ≥ 0.5 ha
- 偵測淹水：**1.85 km²**
- 在 11/02 光學 100% 雲量下，這就是 SAR 提供的全天候訊號

### Task 2: Sensor Fusion（4-class）
| Class | Area (km²) | 解讀 |
|-------|-----------|------|
| High Confidence (SAR ∩ NDWI) | 0.46 | 雙感測器確認 |
| SAR Only (Cloudy) | 1.14 | 雲下 SAR 補充 |
| Optical Only | 3.15 | NDWI 單獨偵測 |
| No Detection | 550.2 | — |

### Task 3: 地形審計（slope > 25°）
- 套用 DEM (Hualien_dem_merge.tif, EPSG:3826) 計算坡度後重投影到 SAR 網格
- **移除假陽性 1.86 km²**（25-35°: 0.15 / 35-45°: 0.40 / 45-90°: 1.31 km²）
- 必答討論：bbox 主要為**花蓮縱谷流域**（光復、鳳林、馬太鞍上游 — **非沿海平原**），其中 52.9% 為陡坡，套用 slope filter 後 High Conf 從 0.46 → 0.11 km²（-75%）。實證結果暴露 DEM 不一定可信、NDWI 樣本不足、災害可能集中在窄帶水流走廊三種解釋；策略採 **precision-over-recall 保守版**（與 Exercise 的 recall-priority 取向相反）

### Task 4: AI Strategic Briefing (Gemini 2.5 Flash 系列)
- 透過 `google-genai` SDK 呼叫 Gemini API
- **模型 fallback chain**：`gemini-2.5-flash` → `2.5-flash-lite` → `flash-latest` → `flash-lite-latest`（任一成功即停；503 重試 3 次，429 立即跳下個模型）
- 本次執行主模型 503 過載 → 自動降級至 `gemini-2.5-flash-lite` 取得完整繁中策略簡報
- 完整 prompt + response 存於 `output/HW10_T4_ai_briefing.md`
- 反思 4 點（針對 LLM 行為模式而非特定字句，重跑 Gemini 仍適用）：
  1. evidence-based prompt 直接決定輸出品質
  2. LLM 在通用資料產品上具體、本地地名上籠統
  3. Gemini 2.5 在 calibration 上的進步（不誇大不確定結論）
  4. AI 角色為**翻譯器**（資料 → 敘事），非決策替代

---

## W9 vs W10 量化比較（重要修正）

W9 量「NDVI 變化區」（含植被擾動 + 崩塌 + 淹水），W10 量「水體」(NDWI + SAR backscatter)。**直接比較 km² 是 apples-to-oranges**，因此比較表聚焦在「能力差異」而非「面積差異」：

| Metric | W9 Optical Only | W10 Fused |
|--------|-----------------|-----------|
| 颱風日可分析性 | 0（100% 雲下失明） | ✅ SAR 穿雲可分析 |
| Cloud-recovered area | 0 km² | 1.14 km² (SAR Only class) |
| 假陽性處理 | 事後 SCL 遮罩（71.6% 移除） | SAR ∩ NDWI 自動交集 |
| 地形校正 | 不需要（無 SAR） | slope > 25° 移除 1.86 km² |
| 信心分級 | 3 zones（強度）| 4 classes（**含感測器來源**） |

**關鍵差異**：W10 的 4-class 不只給「信心強弱」，還給「為什麼信心」— 這是真正的 ARIA v7.0 進化點。

---

## 檔案結構

```
Homework-10/
├── Week10_ARIA_v70_HuangYongZhi.ipynb   # 主 notebook（4 MB，含所有圖表）
├── build_homework10.py                  # Notebook 構建腳本（重複執行用）
├── .env                                 # 本地參數（git-ignored）
├── .env.example                         # 參數範本
├── .gitignore
├── README.md                            # 本檔
├── Homework-Week10.md                   # 老師的作業說明
└── output/
    ├── HW10_T1_sar_panel.png            # Task 1: 2×2 SAR 面板
    ├── HW10_T1_change_detection.png     # Task 1: pre/post diff
    ├── HW10_T1_stats.csv                # Task 1: 階段統計
    ├── HW10_T2_fusion_map.png           # Task 2: 4-class 融合圖
    ├── HW10_T2_fusion_stats.csv         # Task 2: 各 class 面積
    ├── HW10_T3_topographic.png          # Task 3: before/after 地形校正
    ├── HW10_T3_slope_breakdown.csv      # Task 3: 各坡度級距
    ├── HW10_T4_ai_briefing.md           # Task 4A: Gemini prompt + response
    └── HW10_T4_w9_vs_w10.csv            # Task 4B: W9 vs W10 比較
```

---

## 環境與重現

```bash
# 環境
c:\Users\user\anaconda3\envs\geopandas

# 主要套件
- pystac_client, planetary_computer, stackstac
- xarray, rioxarray, rasterio
- numpy, pandas, scipy.ndimage
- matplotlib
- python-dotenv
- google-genai (Gemini SDK)

# 執行
"c:/Users/user/anaconda3/envs/geopandas/python.exe" -m jupyter nbconvert \
  --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 \
  Week10_ARIA_v70_HuangYongZhi.ipynb
```

**所有閾值與日期均存於 `.env`**（git-ignored），code 從 environment 讀取，符合 reproducibility 要求。Captain's Log 共 5 個 markdown cell 記錄推理。

---

## 提交清單

- [x] 4 大 Task 完整交付
- [x] `.env` 機制 + `.env.example` 範本
- [x] 5 個 Captain's Log（Setup → Task 1 → Task 2 → Task 3 → Task 4）
- [x] DEM 適用性討論（Task 3 必答）
- [x] AI Briefing 包含 prompt + response + 反思（Task 4A）
- [x] W9 vs W10 比較（Task 4B，含 metric 不對等的修正說明）
- [x] Sanity check：無 90% 以上水體、speckle 已濾、地形校正已套用、融合邏輯可解釋
- [x] STAC 純串流，不下載原始檔（DEM 為先前作業已有的本地檔）

---

## 與作業預設路徑的偏離說明

兩處刻意偏離原始 rubric 預設步驟，效果等價或更佳，但需向 TA 說明：

| 偏離項 | rubric 預設 | 本作業實際 | 理由 |
|--------|-------------|-----------|------|
| **SAR 來源** | `rasterio.open('S1_Hualien_dB.tif')` 讀本地檔 | 用 STAC 串流 `sentinel-1-rtc` collection | (1) Exercise 已示範雲端串流工作流；(2) 不依賴本地檔，TA 重現環境零障礙；(3) 同一 pipeline 可套用任何 AOI |
| **W9 vs W10 比較表結構** | rubric 4 列固定格式 | 6 列含 `Note` 欄位 | W9（NDVI 變化區）vs W10（水體）非同物件，直接比 km² 是 apples-to-oranges；表格更精確 |

兩項都不影響 deliverables 完整度（圖、表、CSV 都有），且符合「先量化再敘事」的學術誠實。

---

> *"A commander doesn't care if it's cloudy. He needs the truth. ARIA v7.0 delivers it."*
