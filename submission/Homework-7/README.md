# Week 7 Assignment: ARIA v4.0 — Accessible Auditor (花蓮市防災路網可及性評估)

## 分析概要

本專案整合 OpenStreetMap 路網、模擬降雨量與 Betweenness Centrality，
對花蓮市進行颱風情境下的道路可及性評估。

---

## 資料來源

| 資料 | 來源 |
|------|------|
| 路網 | OpenStreetMap (via OSMnx) |
| 降雨模擬 | NumPy 隨機模擬（模擬鳳凰颱風分布） |
| 地形風險 | Week 4（可選疊加，未使用） |
| AI 建議 | Gemini 2.5 Flash (google-generativeai SDK) |

---

## 核心分析結果

### Top 5 瓶頸節點 (Betweenness Centrality)

| 排名 | Node ID | Centrality |
|------|---------|-----------|
| 1 | 649286213 | 0.1402 |
| 2 | 649286214 | 0.1394 |
| 3 | 1061487893 | 0.1253 |
| 4 | 929963021 | 0.1235 |
| 5 | 1074772659 | 0.1157 |

### 可及性縮減比較 (5 min / 10 min 等時圈)

| Facility Node | 短距離縮減 (5min) | 長距離縮減 (10min) |
|--------------|-----------------|-----------------|
| 649286213 | 80.6% | 29.8% |
| 649286214 | 77.2% | 24.5% |
| 1061487893 | 79.3% | 29.1% |

---

## AI 診斷日誌

### 1. OSMnx 擷取路網
**問題**：首次執行提示 kernel 找不到 osmnx，因為 nbconvert 預設使用 base env。
**解法**：手動安裝 geopandas conda env 的 ipykernel，並在 nbconvert 加上 `--ExecutePreprocessor.kernel_name=geopandas`。

### 2. Point is not defined 錯誤
**問題**：S6 cell 使用了 Point 但沒有 import shapely.geometry。
**解法**：在 build_notebook.py 修補 S6 cell，加入 `from shapely.geometry import Point`。

### 3. 可及性縮減率接近 100%（第一版）
**問題**：`get_adaptive_thresholds` 計算出的閾值只有 0.3/0.5 分鐘（18-30 秒），導致幾乎所有面積都縮到 0。
**解法**：在修補版中加入最低閾值保護（`MIN_SHORT = 5 分鐘`，`MIN_LONG = 10 分鐘`），縮減率降至合理的 77-80%。

### 4. Gemini API 呼叫限速
**問題**：免費版 Gemini API 有 RPM 限制，重複跑 notebook 可能觸發 429 Rate Limit。
**解法**：AI 報告僅在第一次執行時取得，結果已保存在 ARIA_v4.ipynb 的 cell output 中，不需重複呼叫。

---

## 提交清單 (Deliverables)

- [x] ARIA_v4.ipynb — 完整執行 Notebook（含圖表和 AI 策略報告）
- [x] data/hualien_network.graphml — 路網資料（5.1 MB）
- [x] accessibility_table.csv — 可及性效益評估表
- [x] .env — 環境變數設定檔
- [x] README.md — 本文件（含 AI 診斷日誌）

---

*「路網是防災的命脈；哪條路最重要，Betweenness Centrality 會告訴你。」*
