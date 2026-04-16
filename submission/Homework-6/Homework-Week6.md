# Week 6 Assignment: Prediction Shootout + Project Proposal

# 第 6 週作業：空間預測對決 + 期末專案提案

**繳交期限：下次上課前**

---

## 1. 任務情境 (Scenario)

指揮官說：「不同類型的降雨事件，空間分布完全不同。你能用同一套工具分析不同事件嗎？哪種方法在什麼情境下表現最好？」

你的任務分為兩部分：
- **Part A**：自選兩個降雨事件，分別執行 Kriging vs Random Forest 的完整比較，並分析兩事件的 Variogram 差異
- **Part B**：繳交期末專案提案大綱

---

## 2. Part A: 雙事件內插比較 (60%)

### A0. 資料蒐集（重要！）

1. 前往 [CoLife 歷史資料庫](https://history.colife.org.tw/#/?cd=%2F%E6%B0%A3%E8%B1%A1%2F%E4%B8%AD%E5%A4%AE%E6%B0%A3%E8%B1%A1%E7%BD%B2_%E9%9B%A8%E9%87%8F%E7%AB%99) → 氣象 → 中央氣象署_雨量站
2. **自選兩個不同的降雨事件**，下載對應月份的雨量資料
3. 兩個事件應具有**不同的降雨特性**，例如：
   - 颱風（集中型強降雨）vs 梅雨鋒面（均勻型降雨）
   - 登陸型颱風 vs 外圍環流型颱風
   - 夏季午後雷陣雨 vs 冬季東北季風降雨

**事件挑選建議**（不限於此，可自行探索）：

| 事件類型 | 參考事件 | CoLife 月份 | 降雨特性 |
|----------|----------|-------------|----------|
| 登陸型強颱 | 凱米颱風 2024/7/25 | 202407 | 宜蘭登陸，全區普降大雨 |
| 課堂範例 | 鳳凰颱風 2024/11/11 | 202411 | 蘇澳極端值，分布極度右偏 |
| 梅雨/豪雨 | 自行查詢 EMIC 歷年災害 | 視事件而定 | 均勻型，Sill 低、Range 大 |

> **提示**：[全民防災 e 點通 — 歷年災害專區](https://bear.emic.gov.tw/MY2/disasterInfo) 可查詢歷年颱風與豪雨事件紀錄，幫助你挑選事件。

4. 每個事件篩選**花蓮縣+宜蘭縣**測站，過濾 -998 / 0 值
5. 轉為 EPSG:3826（**Kriging 必須使用公尺座標**）

### A1. Variogram 分析（兩個事件各做一次）

1. 對每個事件分別建立至少 **2 種 Variogram 模型**（如 spherical + exponential），比較擬合結果
2. 產出 **Variogram 比較圖**：實驗點 + 兩種擬合曲線
3. 選擇最佳模型，**說明選擇理由**（1-2 句）
4. **比較兩事件的 Variogram 參數差異**（Sill、Range、Nugget），用 1-2 句解釋為什麼不同
   - 提示：回想課堂 Slide 4 的口訣「Sill 看天氣、Nugget 看儀器、Range 看地理」

### A2. 四種方法內插（兩個事件各做一次）

1. 在 **1000m 解析度**網格上執行以下四種內插：
   - Nearest Neighbor
   - IDW
   - Ordinary Kriging（使用最佳 Variogram 模型）
   - Random Forest（`n_estimators=200`, `min_samples_leaf=3`）
2. 每個事件產出 **2×2 四圖並列**比較圖（與課堂 Lab 1 相同格式）
3. 產出 **Kriging vs RF 差異圖**（Kriging - RF，使用 RdBu_r colormap）

### A3. 不確定性分析

1. 對每個事件產出 **Sigma Map**：Kriging variance 視覺化（Blues colormap）
2. 寫一段 **300 字以內的比較分析**，回答：
   - 兩個事件的 Sigma Map 有什麼差異？為什麼？
   - 哪種類型的降雨事件，Kriging 的預測信心較高？
   - 如果你是指揮官，在高 variance 區域會做什麼決策？
   - Random Forest 能提供類似的不確定性資訊嗎？為什麼？

### A4. GeoTIFF 輸出（擇一事件即可）

1. 將 Kriging 結果儲存為 `kriging_rainfall.tif`（EPSG:3826）
2. 將 Kriging variance 儲存為 `kriging_variance.tif`（EPSG:3826）
3. 將 RF 結果儲存為 `rf_rainfall.tif`（EPSG:3826）
4. **注意 y 軸翻轉**：numpy row 0 = south → GeoTIFF row 0 = north（需 `np.flipud()`）

### A5. (加分) 跨事件綜合比較

- 將兩事件的 Variogram 參數整理成表格：

| 參數 | 事件 1 | 事件 2 | 差異原因 |
|------|--------|--------|----------|
| Sill | | | |
| Range | | | |
| Nugget | | | |
| Best Model | | | |

- 回答：「如果你只能用一組 Variogram 參數套用到未來所有事件，你會怎麼選？為什麼這樣做有風險？」

---

## 3. Part B: 期末專案提案 (40%)

### 分組

- 自由分組，建議 **3-4 人**，也可 1-2 人獨立或小組進行（期望產出不因人數調降）
- **角色建議**（多人組建議分配）：
  - **Data Captain**（資料工程師）：API 串接、資料清洗
  - **Spatial Architect**（模型建築師）：Kriging、Zonal Stats、疊合
  - **AI UX Lead**（AI 顧問 + 視覺化）：Gemini 整合、Folium 儀表板

### 提案大綱格式（1 頁 A4）

```
# 期末專案提案：[專案名稱]

## 組員
- 姓名1（學號）— Data Captain
- 姓名2（學號）— Spatial Architect
- 姓名3（學號）— AI UX Lead
- 姓名4（學號）— 負責項目（如適用）

## 研究問題
用一句話描述你要回答的防災問題。
例：「鳳凰颱風期間，花蓮縣哪些避難所因為地形和降雨的雙重風險最需要優先撤離？」

## 資料來源
1. [資料名稱] — [來源 URL] — [格式/筆數]
2. [資料名稱] — [來源 URL] — [格式/筆數]

## 分析方法
1. [方法1]：簡述用途
2. [方法2]：簡述用途

## 內插策略
你的專案會用 Kriging、ML、還是兩者並用？為什麼？
（根據本週作業的雙事件比較經驗，說明你的選擇依據）

## Gemini SDK 使用計畫
你打算在什麼場景使用 Gemini？（如：審計分析邏輯、產生決策建議、解讀異常值）

## 預期產出
- [ ] Jupyter Notebook
- [ ] Folium 互動地圖 / 分析圖表
- [ ] Gemini SDK 決策建議整合
- [ ] 防災決策建議

## 風險評估
最可能遇到的技術困難是什麼？你的備案是什麼？
```

---

## 4. 技術要求提醒

- **CRS**：Kriging 的 x, y 必須是 EPSG:3826（公尺）。用 EPSG:4326 的經緯度會讓距離計算完全錯誤
- **pykrige 的 x/y**：`x` = Easting，`y` = Northing。容易搞混，先用少量點測試確認方向
- **GeoTIFF y 軸**：寫入前用 `np.flipud()` 翻轉
- **RF 特徵**：X = [easting, northing]，不是 [lat, lon]
- **-998 過濾**：Kriging 對離群值非常敏感
- **CoLife JSON 格式**：下載後需要解析 JSON，篩選目標日期+時段的雨量紀錄

---

## 5. 推薦的 Vibe Coding Prompt

> "I have CWA rainfall station data (JSON from CoLife) for [your event name and date].
> Help me:
> 1. Parse the JSON, filter to 花蓮+宜蘭 stations, remove -998 and 0 values
> 2. Convert to EPSG:3826
> 3. Compare four interpolation methods on a 1000m grid:
>    - Nearest Neighbor (scipy NearestNDInterpolator)
>    - IDW (manual implementation with scipy.spatial.distance.cdist, power=2)
>    - Ordinary Kriging (pykrige, compare spherical vs exponential variogram)
>    - Random Forest (scikit-learn, features = [easting, northing])
>
> Then create: (1) 2×2 comparison plot, (2) Kriging vs RF difference map,
> (3) Sigma Map from Kriging variance, (4) export all as GeoTIFF.
>
> CRS rules: all in EPSG:3826. pykrige x = Easting, y = Northing.
> GeoTIFF needs np.flipud() before writing."

---

## 6. 繳交清單 (Deliverables)

### Part A
1. **`Week6_Shootout.ipynb`** — 完整分析 Notebook（含兩個事件的執行結果）
2. **事件 1 & 2 的 Variogram 比較圖**（各一張）
3. **事件 1 & 2 的四種方法比較圖**（各一張 2×2）
4. **事件 1 & 2 的 Sigma Map**（各一張）
5. **GeoTIFF 輸出**（擇一事件：kriging_rainfall.tif、kriging_variance.tif、rf_rainfall.tif）
6. **CoLife 原始資料檔**（你下載的 JSON 檔案）

### Part B
7. **期末專案提案大綱**（1 頁 A4，含分組名單 + 角色分配）

---

## 7. 評量標準

| 項目 | 比重 |
|------|------|
| 資料蒐集 + 事件選擇合理性 | 10% |
| Variogram 分析 + 跨事件比較 | 15% |
| 四種方法內插 + 比較視覺化 | 15% |
| 不確定性分析（Sigma Map + 文字比較） | 10% |
| GeoTIFF 輸出 | 10% |
| 期末專案提案品質 | 30% |
| 專業規範（Markdown/AI 日誌） | 10% |

---

## 8. 資料來源

- **CoLife 歷史資料庫**：[https://history.colife.org.tw/](https://history.colife.org.tw/#/?cd=%2F%E6%B0%A3%E8%B1%A1%2F%E4%B8%AD%E5%A4%AE%E6%B0%A3%E8%B1%A1%E7%BD%B2_%E9%9B%A8%E9%87%8F%E7%AB%99) → 氣象 → 中央氣象署_雨量站 → 選擇對應月份
- **歷年災害查詢**：[全民防災 e 點通](https://bear.emic.gov.tw/MY2/disasterInfo) — 查詢歷年颱風與豪雨事件，幫助挑選分析對象
- **課堂範例資料**：[`fungwong_202511.json`](https://drive.google.com/file/d/182rLmpqc9TcLAJctxBXW2Gsc0Xk6jWKF/view?usp=sharing)（鳳凰颱風 2025/11/11 18:50，僅供參考，作業請自選事件）

---

*"The same tool, different storms, different answers. That's why parameter tuning matters."*
