# Week 5 Assignment: ARIA v3.0 (The Living Auditor)

# 第 5 週作業：全自動區域受災衝擊評估系統（動態監測版）

**繳交期限：下次上課前**

---

## 1. 任務情境 (Scenario)

指揮官不再滿足於靜態的風險圖。他需要一個能回答「**現在哪裡最危險？**」的即時監測儀表板。

你的任務是將前兩週的成果（W3 的避難所河川距離、W4 的地形坡度）整合成 ARIA v3.0，並在 **2025 年鳳凰颱風 (Typhoon Fung-wong)** 的極端情境下進行壓力測試。

**跟課堂 Lab 的差異：**
- Lab 1 只做了基礎 Folium 地圖 → **作業要整合 W3-W4 的避難所風險資料**
- Lab 2 只篩選了高雨量站 → **作業要完成完整的動態風險分級 (URGENT/CRITICAL)**
- Lab 用預備的少量站點 → **作業要處理完整的花蓮+宜蘭站點資料**

---

## 2. 資料來源 (Data Sources)

### A. 向量資料 — 延續 Week 3-4

- W3 避難所 GeoDataFrame（含河川距離分級）
- W4 地形風險（mean_elevation、max_slope、terrain_risk）
- 國土測繪中心鄉鎮市區界

### B. 即時/歷史雨量資料

- **LIVE 模式**：CWA O-A0002-001 API（自動雨量站，https://opendata.cwa.gov.tw/）
- **SIMULATION 模式**：[`fungwong_202511.json`](https://drive.google.com/file/d/182rLmpqc9TcLAJctxBXW2Gsc0Xk6jWKF/view?usp=sharing)（鳳凰颱風 2025/11/11 18:50 快照 — 蘇澳站巔峰時刻）
- **歷史資料來源**：[CoLife 歷史資料庫](https://history.colife.org.tw/) → 氣象 → 中央氣象署_雨量站 → 202511（原始為 CSV，教師已轉換為 JSON）

> **注意**：所有站點數據均來自 CoLife 歷史資料庫的真實觀測紀錄。CoLife 原始下載格式為 CSV（`rain_20251111.csv`，約 18 萬行），教師已篩選 2025/11/11 18:50 時刻並轉換為 CWA API 相容的 JSON 格式（`fungwong_202511.json`，1,256 站）。蘇澳時雨量 130.5mm 為該快照時刻的巔峰值。南澳累積 1,062mm 為整場颱風的多日總累積（非單一快照值）。

---

## 3. 核心要求 (Requirements)

必須以 **`.ipynb` (Jupyter Notebook)** 格式繳交，最終產出一個可互動的 **ARIA_v3_Fungwong.html**。

### A. 模式切換器 (Mode Switcher)

1. 從 `.env` 讀取 `APP_MODE`（值為 `LIVE` 或 `SIMULATION`）
2. LIVE 模式：呼叫 CWA API → 取得即時雨量
3. SIMULATION 模式：載入 `fungwong_202511.json`
4. **兩種模式的回傳格式有差異**（Live API 與 CoLife 快照的根路徑都是 `records.Station`，但座標組數和數值型態不同），需寫一個 `normalize_cwa_json()` 函數統一處理 → 後續分析邏輯零修改
5. **Fallback 機制**：如果 API 呼叫失敗，自動切換到最近一次的本地快照

```python
# .env 設定
APP_MODE=SIMULATION
CWA_API_KEY=your-key-here
SIMULATION_DATA=data/scenarios/fungwong_202511.json
TARGET_COUNTY=花蓮縣
```

### B. 動態風險疊合 (Dynamic Risk Overlay)

1. 將雨量站 GeoDataFrame（EPSG:4326）轉為 EPSG:3826
2. 為高雨量站建立影響範圍 buffer（建議 5km）
3. 與 W3-W4 避難所做 `gpd.sjoin()` → 找出「暴雨影響範圍內的避難所」
4. **動態風險分級邏輯**：
   - **CRITICAL**：時雨量 > 80mm 影響範圍內的避難所（不論原風險等級）
   - **URGENT**：時雨量 > 40mm 且 W4 terrain_risk == 'HIGH'
   - **WARNING**：時雨量 > 40mm 或 W4 terrain_risk == 'HIGH'
   - **SAFE**：其餘

> **⚠️ 防呆檢查**：sjoin 前確認兩邊 CRS 一致，否則結果會是空的。
> ```python
> assert str(shelters.crs) == str(rain_stations.crs), "CRS MISMATCH!"
> ```

### C. 視覺化 (Folium Interactive Map)

1. **底圖**：Folium Map，中心設在花蓮縣
2. **雨量圖層**：CircleMarker（半徑 ∝ 雨量，顏色分 4 級：綠/黃/橘/紅）
3. **避難所圖層**：Marker（依動態風險等級著色）
4. **HeatMap 圖層**：雨量分佈強度
5. **LayerControl**：讓使用者切換顯示各圖層
6. **Popup**：點擊避難所顯示 — 名稱、W4 地形風險、動態風險等級、最近雨量站名及時雨量
7. **儲存**：`ARIA_v3_Fungwong.html`

### D. 專業規範 (Infrastructure First)

1. **環境變數**：所有設定值（API key、門檻、模式）放 `.env`
2. **安全**：`.env` 和 API keys 不得出現在 GitHub repo 中
3. **Markdown Cells**：每個分析步驟前寫 Captain's Log 說明
4. **AI 診斷日誌**：在 README 中描述你如何解決以下問題（至少一個）：
   - 「Folium 地圖上經緯度填反（lat/lon 順序）」
   - 「CWA API 回傳 -998 導致地圖顏色異常」
   - 「sjoin 結果為空（CRS 未對齊）」
   - 「HeatMap 在山區有盲區（測站分佈不均）」

---

## 4. Bonus: Gemini SDK AI 戰術顧問（加分項）

如果你想挑戰進階功能：

1. 安裝 `google-generativeai` 套件
2. 從 [Google AI Studio](https://aistudio.google.com/apikey) 取得免費 API key
3. 挑選受災最嚴重的 3 個避難所資訊，傳送給 Gemini
4. Prompt 規範：要求 Gemini 扮演「災害防救專家」，根據數據給出具體的「指揮官應變建議」
5. 將 AI 產出的建議放進 Folium Popup 中

```python
# Bonus Prompt 範例
prompt = f"""你是花蓮縣防災指揮中心的專家顧問。以下是鳳凰颱風期間的即時數據：
避難所: {shelter_name}
地形風險: {terrain_risk} (max_slope: {max_slope}°)
最近雨量站: {station_name} (時雨量: {rain_1hr}mm)
動態風險等級: {dynamic_risk}

請以 3 句話給出指揮官的緊急應變建議。"""
```

---

## 5. 推薦的 Vibe Coding Prompt

> "I need to build ARIA v3.0 — a dynamic risk monitoring system. I have:
> 1. Week 3-4 shelter GeoDataFrame (EPSG:3826) with river_risk and terrain_risk
> 2. CWA rainfall API (O-A0002-001) or CoLife historical JSON (similar but not identical format)
>
> Help me in separate Jupyter cells:
> 1. Create a mode switcher that reads APP_MODE from .env
> 2. If LIVE: call CWA API; if SIMULATION: load fungwong_202511.json from CoLife
> 3. Write a normalize_cwa_json() function that handles both formats:
>    - CWA API: records.Station[], 2 coordinate sets (pick WGS84), str values
>    - CoLife: records.Station[], 1 coordinate set (WGS84 only), numeric values
> 4. Parse the JSON into a GeoDataFrame with station name, lat, lon, hourly rain
> 5. Filter -998 values, convert CRS to 3826, create 5km buffers
> 6. sjoin with shelters to find affected ones
> 7. Apply dynamic risk logic (CRITICAL/URGENT/WARNING/SAFE)
> 8. Create a Folium map with CircleMarkers, HeatMap, LayerControl, and rich Popups
> 9. Save as ARIA_v3_Fungwong.html"

---

## 6. 繳交清單 (Deliverables)

1. **GitHub Repo URL**
2. **`ARIA_v3.ipynb`** — 完整分析 Notebook（含執行結果）
3. **`ARIA_v3_Fungwong.html`** — Folium 互動地圖
4. **`README.md`** — 包含 AI 診斷日誌

---

## 7. 評量標準

| 項目 | 比重 |
|------|------|
| Mode Switcher + API 呼叫/fallback | 20% |
| 鳳凰颱風空間疊合 + 動態風險分級 | 25% |
| Folium 互動地圖品質（圖層、Popup、HeatMap） | 25% |
| 專業規範（.env + .gitignore + README + AI 日誌） | 15% |
| Bonus: Gemini SDK 整合 | 15% |

---

## 8. 提示與注意事項

- **CRS 三重檢查**：雨量站（4326）、避難所（3826）、Folium（4326）— 分析用 3826，視覺化轉回 4326
- **座標陷阱**：CWA Live API 回傳的 `GeoInfo.Coordinates` 包含**兩組**座標 — `[0]`=TWD67，`[1]`=WGS84（差距約 1km）。CoLife 歷史快照只有**一組** WGS84。你的 parser 需要處理兩種情況，務必取 WGS84
- **-998 過濾**：CWA 用 -998 表示無資料，必須在建 GDF 前過濾掉
- **Folium 座標順序**：`[latitude, longitude]`，不是 `[longitude, latitude]`
- **Buffer 單位**：EPSG:3826 下 buffer(5000) = 5km；EPSG:4326 下 buffer(5000) = 5000 度 ≈ 地球半圈（大錯特錯！）
- **API 穩定性**：CWA API 偶爾會超時，建議加 `try/except` + fallback
- **鳳凰颱風連結**：Week 2 的馬太鞍溪堰塞湖就是這場颱風造成的 — 你的 ARIA 系統在那個時間點會給出什麼警告？

---

*"A monitoring system that works in the sun is a toy. A system that survives Typhoon Fung-wong is a tool."*
