# Week 13 Homework — ARIA v9.0: The Cloud Engine

**Course:** NTU Remote Sensing & Spatial Information Analysis (遙測與空間資訊之分析與應用)
**Author:** Huang YongZhi (黃詠智)
**Date:** 2026-05-19
**Study Area:** Xiulin / Taroko 山區 (秀林 / 太魯閣)
**Sensor:** Google Earth Engine (Sentinel-2 + Sentinel-1)
**Score Expected:** 100% + 20% bonus = **120%**

---

## 📌 作業概覽

將 ARIA 系統從 v8.0 升級到 **v9.0 — The Cloud Engine**。用 Google Earth Engine Python API 進行雲端時序分析，從「單張影像 snapshot」進化到「**數百張影像 → 時序敘事**」。

研究區為**秀林/太魯閣山區**（與 Exercise-12 課堂 demo 的「花蓮市平原區」不同），追蹤 2024/04/03 地震 + 馬太鞍堰塞湖事件的多階段災害時間線。

---

## 📂 檔案結構

```
Homework-12/
├── README.md                            ← 你正在看的這份
├── Homework-Week13.md                   (老師的作業說明，原始檔)
├── Week13_ARIA_v9_HuangYongZhi.ipynb    🎯 主要提交檔（4 Tasks + 2 Bonus）
└── outputs/
    └── taroko_ndvi_timelapse.gif        Bonus 2 動畫 GIF (13 frames, 2 sec/frame)
```

---

## 📊 主要分析結果（實際數據）

### Task 1 — NDVI 時序分析（25%）

| 指標 | 結果 |
|------|------|
| **Sentinel-2 影像張數** (2020-2026, cloud < 40%) | **291 張** |
| **平均雲量** | 21.3% (min 0.0%, max 39.9%) |
| **有資料的月份** | **72 / 75** 個月 (**96% 覆蓋率**) |
| **Pre-EQ 平均 NDVI** | +0.4851 (n=49) |
| **Post-EQ 平均 NDVI** | +0.4795 (n=23) |
| **平均變化** | **−0.0056**（極小，符合「AOI 太大稀釋訊號」假說） |
| **Pre-EQ 平均 Spread** | 1.5926 |
| **Post-EQ 平均 Spread** | 1.6528 |
| **Spread 放大率** | **+3.8%**（震後空間異質性升高） |

**關鍵發現：** Mean NDVI 看不到地震訊號（變化僅 −0.006），但 **spread（max−min）增加 3.8%** + **min NDVI 大幅下降至負值** 揭露了「兩極化地景」訊號。這是 Exercise S4 教學的「平均值掩蓋空間異質性」的實證。

---

### Task 2 — 三期 Composite + ΔNDVI（25%）

| Phase | 期間 | 損害面積 (ΔNDVI < −0.15) |
|-------|------|-------------------------|
| **Phase 2 − Phase 1** (EQ 直接損害) | 2024-04 ~ 09 vs 2023-01 ~ 2024-03 | **73.68 km² = 7,367.6 ha** |
| **Phase 3 − Phase 2** (堰塞湖階段變化) | 2025-10 ~ 2026-03 vs 2024-04 ~ 09 | 36.30 km² = 3,629.5 ha |
| **Phase 3 − Phase 1** (總累積變化) | 2025-10 ~ 2026-03 vs 2023-01 ~ 2024-03 | **61.55 km² = 6,154.9 ha** |

**🎯 重要發現：** Total (61.55 km²) **小於** EQ direct (73.68 km²)！

> 這代表**部分地震損害區已自然植被恢復**（先驅植物快速覆蓋裸地）。但新災害（堰塞湖潰堤下游沖刷）造成 36.30 km² 的新損害。**雙向變化讓淨損害數字下降**，這是時序分析最有價值的洞察 — **單看 EQ direct 會高估長期影響，單看 Total 會低估災害總體規模**。

---

### Task 3 — SAR 時序 + 跨感測器交叉比對（25%）

| 指標 | 結果 |
|------|------|
| **Sentinel-1 GRD 影像** (DESC, VV) | **146 張** |
| **有效觀測** | **146 張**（100% 可用，全天候優勢） |
| **高信心損害區** (ΔNDVI<−0.15 AND \|ΔVV\|>2dB) | **1.59 km² = 158.9 ha** |

**為何高信心損害區只有 1.59 km²？**
- NDVI 偵測到 73.68 km² 損害；SAR 篩選後僅 1.59 km² 通過雙重門檻
- 兩個感測器都偵測到變化 = 偽陽性機率極低 → 這 159 公頃**最值得實地確認**
- 大部分崩塌區只被 NDVI 偵測到（植被變化），但表面散射特性可能變化不到 2 dB

---

### Task 4 — GeoTIFF 匯出 + Integration Summary（25%）

**匯出 2 個 GeoTIFF 到 Google Drive `GEE_Exports/`：**
- `taroko_post_eq_ndvi_2024.tif` — Phase 2 NDVI 中值合成
- `taroko_delta_ndvi_eq.tif` — ΔNDVI 變化圖（可餵 W12 RF）

規格：10 m 解析度, EPSG:32651 (UTM 51N)

**Integration Summary 480 字** — 涵蓋資料規模 / 主要發現 / 跨週整合 / GEE 局限四個面向，完整呈現於 notebook 內。

---

### Bonus 1 — InSAR 干涉圖判讀（+10%）

讀 **水保署電子報第 141 期** 2016 熊本地震 InSAR 干涉圖（圖 3），回答 5 題：

| Q | 答案 |
|---|------|
| 衛星 / 波段 / 波長 | **ALOS-2 PALSAR-2 / L-band / 23.6 cm** |
| 每環位移量 | **11.8 cm**（半波長） |
| 干涉環數量 | **15-17 個** |
| 色階方向 | **藍→紫→黃**，遠離衛星 |
| 總 LOS 位移量 | **180-204 cm**（~2 公尺，符合現場觀察） |

**心得（100 字）：** InSAR 用「相位」可達公分到毫米級精度的 3D 位移量測；W10 SAR 振幅只能告訴「變了」但不能「變多少」。InSAR 對地震斷層、火山膨脹、地盤下陷、緩慢山崩潛變等都是不可替代的工具。

---

### Bonus 2 — NDVI 時序動畫 GIF（+10%）

- **13 frames** 半年度合成 (2020 H1 → 2026 H1)
- **2 秒/frame** = 總長 26 秒
- 加時間標籤 + 事件標記 (★ 2024-04 地震、★ 2025 堰塞湖)
- 加色條 (NDVI 0=brown → 0.4=yellow → 0.8+=green)
- 大小：1.29 MB

**3 個最明顯變化時刻：**
1. **2024-04 地震直接衝擊** — 從整體綠色突然出現大量黃褐色斑塊
2. **季節循環** — 冬季偏黃褐、夏季濃綠，每年穩定重複
3. **2025-26 winter 堰塞湖潰堤後** — 下游河道帶狀新沖刷，同時 2024 崩塌區部分恢復

---

## 🛠️ 技術細節

### 環境
```bash
# Conda env: geopandas (Python 3.10)
pip install earthengine-api geemap ffmpeg-python imageio Pillow
```

### GEE Project
`rs-496806`（個人 academic-research project）

### 重要實作決策

1. **空間 mean/min/max** — Task 1 不只算 mean，加上 min/max + spread 子圖，這樣才能揭露「平均看不到、但 spread 加大」的災害訊號
2. **公頃面積統計** — Task 2 額外輸出 hectares（HW 明確要求）
3. **Cache check** — Task 1 / Task 3 都加了 cache check，重跑時不會重打 GEE API
4. **PIL 直接寫 GIF** — Bonus 2 用 PIL 而非 imageio.mimsave，duration 單位穩定為毫秒

---

## 📋 Submission Checklist

- [x] **Task 1**: NDVI 時序圖 + 4 點分析（季節 / 地震 / 缺值 / 防災意義） ✅
- [x] **Task 2**: 三期合成 + ΔNDVI 互動地圖 + 公頃面積 + W9 vs W13 比較表 ✅
- [x] **Task 3**: SAR VV 時序 + ΔVV 圖 + 跨感測器交叉比對 + 4 點分析 ✅
- [x] **Task 4**: 2 個 GeoTIFF 匯出 (Google Drive) + 480 字 Integration Summary ✅
- [x] **Bonus 1**: InSAR 5 題答案 + 100 字心得 ✅
- [x] **Bonus 2**: NDVI 13 frames 時序動畫 GIF + 3 點觀察 ✅
- [x] **Final Reflection**: 210 字心得（單景→雲端 + GEE 防災價值） ✅

**Expected: 100% + 20% bonus = 120%** 🎯

---

## 🎤 一句話總結

> **「秀林/太魯閣 6 年植被時序揭露：地震直接損害 7,368 公頃，部分自然恢復，但堰塞湖造成 3,630 公頃新損害；多感測器交叉驗證的最高信心損害區為 159 公頃。Mean 看不到、Spread 看得到，這就是時序分析的價值。」**
