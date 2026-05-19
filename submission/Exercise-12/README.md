# Exercise 12 — Week 13: Google Earth Engine & Cloud-Scale Time Series

**Course:** Remote Sensing and Spatial Information Analysis and Applications
**Theme:** Cloud-based satellite time-series analysis with Google Earth Engine
**Date:** 2026-05-19

---

## 練習概述 (Exercise Overview)

本次練習使用 **Google Earth Engine (GEE) Python API** 進行雲端時間序列分析，主要學習目標：

1. 透過 GEE 篩選並處理大型衛星資料集（Sentinel-2 / Sentinel-1 / Landsat）
2. 計算 NDVI / NDWI 時間序列、偵測地表變化
3. 整合光學 (Sentinel-2) 與 SAR (Sentinel-1) 觀測
4. 建立前/後 (pre/post) 中值合成、計算 ΔNDVI 變化圖
5. 跨感測器交叉驗證高信心災害損害區
6. 匯出雲端產品供本地分析使用
7. **自選研究區與光譜指標，做個人化時序分析（S10）**

主要 case study 是 **2024-04-03 花蓮地震 + 馬太鞍堰塞湖** 災害監測（Sentinel-2 + Sentinel-1）。S10 自由探索區段由學生自選地點 + 指標。

---

## 📂 檔案結構 (Files in This Folder)

```
Exercise-12/
├── README.md                                  ← 你正在看的這份
├── Week13-Slides.pptx                         (上課投影片，不上傳 git)
├── Week13-Student-original.ipynb              (老師發佈的原始空白檔備份)
├── Week13-Student-SunMoonLake.ipynb           🎯 主要提交版本（S10 = 日月潭 + 2021 大旱）
├── Week13-Student-2001Taipei-Failed.ipynb     📚 失敗探索紀錄（S10 = 台北 + 2001 納莉）
└── outputs/
    ├── sunmoonlake_drought_timelapse.gif       Sentinel-2 (2019-2023) 春季 RGB 動畫
    └── taipei_nari_timelapse.gif               Landsat 5 (1998-2012) 濕季 RGB 動畫
```

S1–S8 在兩份檔案內容**完全一致**（花蓮 + SAR 主題），**差異只在 S10**。

---

## 🎯 S10 自由探索 — 平行雙案例

老師規則允許學生自選地點 + 指標，做至少 2 年的時序 + 標記事件 + 寫 100 字說明。我做了**兩個案例平行測試**，最後選成功的一份當主要提交：

### 案例 A：台北盆地 + 2001 納莉颱風（**失敗** ❌）

> 📁 `Week13-Student-2001Taipei-Failed.ipynb`

| 項目 | 設定 |
|------|------|
| **地點** | 台北盆地 (BBOX: `[121.45, 25.00, 121.60, 25.13]`, ~150 km²) |
| **指標** | NDWI = (SR_B2 − SR_B4) / (SR_B2 + SR_B4) — Landsat 5 |
| **感測器** | Landsat 5 TM (30 m, 16 天重訪, 1984-2013) |
| **時間** | 1998-01 至 2013-05 (Landsat 5 整個運作期) |
| **事件** | 2001-09-17 納莉颱風 — 台灣鐵道史唯一 MRT 大規模淹水 |
| **對照** | 同期 8 個其他大颱風 (瑞伯、艾利、海棠、辛樂克、莫拉克、凡那比、蘇拉、蘇力) |

#### 假說
**Landsat 5 NDWI 能否在 8 個颱風背景中顯示出納莉的特殊性？**

#### 實際結果
```
⚠️ 2001-09 沒有可用影像 — Landsat 5 在颱風期間無法成像
Total months with data: 98 / 186 possible (53% 覆蓋率)
```

**完全失敗** — 因為：
1. **Landsat 5 重訪期 16 天** — 颱風期間 (9/16-19) 衛星沒過境
2. **颱風期間 100% 雲遮蔽** — 即使有過境也無法穿透
3. **都市淹水退水快** (24-72h) — 等到下次過境水已退
4. 整個 9 月 2001 **找不到 CLOUD_COVER < 60% 的影像**

#### 「失敗」的科學價值
這次的負面結果 (negative result) 反而是最重要的教學發現：

> **單一光學感測器的物理限制決定了你能或不能看到什麼歷史事件。**

如果歷史重演納莉等級颱風，光靠 Sentinel-2 仍然看不到淹水那一刻 — 必須等到 24h 後雲散，水都退了。**這證明現代災害監測必須結合 SAR 穿雲 + 多衛星 constellation + 地面感測網。**

> 詳細紀錄完整保留於 [`Week13-Student-2001Taipei-Failed.ipynb`](./Week13-Student-2001Taipei-Failed.ipynb)，作為「衛星遙測時間解析度限制」的具體教材。

---

### 案例 B：日月潭 + 2021 百年大旱（**成功** ✅，且有彩蛋）

> 📁 `Week13-Student-SunMoonLake.ipynb` ← **這是主要提交版本**

| 項目 | 設定 |
|------|------|
| **地點** | 日月潭 (BBOX: `[120.86, 23.81, 120.96, 23.89]`, ~88 km²) |
| **指標** | NDWI = (B3 − B8) / (B3 + B8) — Sentinel-2 |
| **感測器** | Sentinel-2 SR Harmonized (10 m, 5 天重訪, 2017-) |
| **時間** | 2020-01 至 2022-12 (涵蓋乾旱前/中/後) |
| **事件** | 2021-04-06 台灣百年大旱顛峰 — 中部水庫蓄水率 < 5%，分區供水 |

#### 實際結果

##### ① 時間序列訊號（S10 step 2）
```
=== Drought Signal Check ===
2021 H1 drought NDWI:   -0.5303
Normal periods NDWI:    -0.5846
Anomaly:                +0.0542  (+1.68 σ)     ← 統計顯著（> 1.5σ 門檻）
```

##### ② 空間合成分析（S10b）
```
Pre-drought water area:    8.010 km²
Drought-peak water area:   6.704 km²  (-16.3%)  ← 湖面真的縮小 16%
Recovery water area:       8.172 km²  (+2.0% vs pre-drought)

Lost during drought:       1.306 km²
Regained after recovery:   1.468 km²
```

##### ③ 5 年 GIF 動畫（S10c）
`outputs/sunmoonlake_drought_timelapse.gif` — 2019/2020/**2021 (湖面最小)**/2022/2023 春季 RGB 對比，**視覺上可以直接看到湖面縮小再恢復**。

#### 彩蛋：發現「NDWI 上升」的反直覺現象

我原本預期乾旱會讓 AOI 平均 NDWI **下降**（水體 → 裸地，NDWI 由正變負），但實際**上升** +0.054。深入分析發現：

| 訊號來源 | 證據 |
|---------|------|
| **湖面縮小** | S10b 空間合成 — 水體面積由 8.010 → 6.704 km² (−16.3%) |
| **植被乾化** | AOI 大部分是周圍森林，乾旱讓 NIR 反射率下降、Green 變化少 → 植被 NDWI 微升 |
| **AOI 平均 +0.054** | 上述兩個過程的混合，植被效應主導 (因為植被像素遠多於湖面像素) |

#### 科學啟示

> **單一指標可能反映多重物理過程。**

只看時間序列圖會得到「乾旱期 NDWI 上升」的反直覺結論。但**配合空間合成圖**才能釐清：水面確實縮小了 (16.3%)，同時周圍植被也乾化了。**兩者交叉驗證才是完整的科學分析。**

---

## 🔁 為什麼保留兩份檔案？

1. **科學誠信**：完整紀錄探索過程，包括失敗的嘗試
2. **教學價值**：Plan A 的失敗本身就是「遙測時間解析度天花板」的最佳示例
3. **發表素材**：上台 2 分鐘可以講「我先試 Landsat 5 + 納莉但失敗，於是改做日月潭 + 大旱 — 而後者意外揭露 NDWI 同時反映水面與植被」的雙層故事，比單一案例更有深度

---

## 🛠️ 環境與套件 (Setup)

```bash
# Conda env: geopandas
pip install earthengine-api geemap ffmpeg-python

# Authenticate (one-time, from PowerShell):
earthengine authenticate --auth_mode=notebook

# Then in notebook:
ee.Initialize(project='your-gcp-project-id')
```

**GCP project ID:** `rs-496806` (個人 academic-research project)

---

## 📊 主要產出 (Key Deliverables)

| 產出 | 檔案 | 描述 |
|------|------|------|
| Plan A notebook | `Week13-Student-2001Taipei-Failed.ipynb` | 完整失敗紀錄 + 教學反思 |
| Plan B notebook | `Week13-Student-SunMoonLake.ipynb` | 完整成功分析 + 彩蛋反思 |
| Plan A GIF | `outputs/taipei_nari_timelapse.gif` | 1998-2012 濕季動畫 (15 frames) |
| Plan B GIF | `outputs/sunmoonlake_drought_timelapse.gif` | 2019-2023 春季動畫 (5 frames) |

---

## 🎤 課堂發表大綱（2 分鐘）

1. **開場故事 (20s)**：「我本來想做台北捷運唯一一次淹水 — 2001 納莉颱風 — 但是衛星根本看不到。」
2. **科學發現 1：失敗的價值 (30s)**：Landsat 5 在 2001-09 完全無影像，證明遙測有時間解析度天花板。
3. **轉折 (20s)**：「於是我改做 2021 日月潭大旱 — 結果是雙重訊號的驚喜。」
4. **科學發現 2：成功 + 彩蛋 (40s)**：z = +1.68σ 顯著但方向反直覺；空間合成顯示湖面 −16.3%；最終結論是 NDWI 同時編碼水面與植被乾旱。
5. **總結 (10s)**：科學分析的關鍵是 **不能單看一張圖下結論**，要追問訊號來源。

---

## 📝 提交說明

- 兩份 notebook 都已執行完畢，outputs 完整保留於 cells
- 若助教要重跑：S4/S4b/S10 step 2 都有 **cache check**，已執行過的不會重新打 GEE API
- GIF 已生成於 `outputs/` 資料夾
- **主要評分以 `Week13-Student-SunMoonLake.ipynb` 為準**
