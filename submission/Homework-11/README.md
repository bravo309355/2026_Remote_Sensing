# Homework 11: ARIA v8.0 — The Classification Engine

**Student:** Huang YongZhi
**Course:** NTU 遙測與空間資訊之分析與應用
**Case:** 秀林 / 太魯閣（Xiulin / Taroko）× 2024-04-03 花蓮地震（M7.4）
**Notebook:** `Week12_ARIA_v8_HuangYongZhi.ipynb`

---

## Abstract

針對秀林 / 太魯閣 BBOX `[121.40, 24.10, 121.80, 24.25]`（40.8 × 17.0 km），以 2024-08-27 Sentinel-2 L2A 影像（雲量 8.4%，AWS Element84 STAC）執行 5 類土地覆蓋分類。**K-means K=5** 找到森林/水體/裸地三個主導 cluster；**Random Forest（200 trees, 6 波段）** 達 **Test OA 77.3%、Kappa 0.685**。對 SWCB 官方崩塌判釋（207 多邊形、91.8 ha）做獨立驗證，得 **Recall 52.7%、Precision 0.83%、IoU 0.0082**。Precision 極低**不是模型壞掉**，而是訓練 ROI 的「Bare/Landslide」涵蓋天然河床、稀植區，而 SWCB 嚴格只記「震後新生崩塌」—— 類別語義落差是主因。Feature importance 顯示 **SWIR2 > SWIR1 > Blue**，反映太魯閣山區「植被含水量 vs 裸礫」的區辨需求，與課堂縱谷區的 Blue 主導完全不同。

---

## 任務涵蓋

| Task | 內容 | 占比 | 主要 Output |
|------|------|------|------------|
| Task 1 | K-means 非監督分類（K=5）+ cluster 光譜識別 | 15% | `output/kmeans_classification.png` |
| Task 2 | Random Forest 監督分類 + Feature Importance | 25% | `output/rf_classification.png`, `output/rf_feature_importance.png` |
| Task 3 | 內部精度 + SWCB 獨立驗證 | 35% | `output/confusion_matrix.png`, `output/swcb_overlay.png` |
| Task 4 | Area stats + Gemini AI 簡報 + 批判評估 | 25% | `output/class_area_stats.csv`, `output/ai_briefing.md` |

---

## 研究區與資料

**BBOX：** `[121.40, 24.10, 121.80, 24.25]` — 40.8 km × 17.0 km，涵蓋蘇花公路南段、清水斷崖、太魯閣國家公園、立霧溪流域；**東側包含太平洋海域（121.6°E 以東）**，這是水體類佔 41% 的主因。

**影像源：** AWS Element84 STAC v1（`https://earth-search.aws.element84.com/v1`，與 W12 課堂同步）。**BOA offset 校正**：AWS Element84 sentinel-2-l2a 聲明 `scale=0.0001, offset=-0.1`，stackstac 預設自動套用 → 改用 `img + 0.1` 還原 0-1 反射率（W12 踩過的雷）。

**選用影像：** `S2A_51QUG_20240827_0_L2A`（2024-08-27 10:41 LST，雲量 **8.4%**）。震後 5 個月（Phase 2）取得，原本 Phase 1（震後 2 個月）無滿足 CC<20% 的影像。

**訓練資料：** `Homework11_label.kmz`（26 個多邊形，5 類）— 用 Google Earth Pro 在 Taroko 區域手動繪製。

**獨立驗證：** `20240802新生崩塌地.kml`（SWCB 農業部水土保持署官方判釋）— 全臺 1,335 多邊形、研究區內 207 個（91.8 ha）。

---

## Task 1 結果

### K-means K=5 Cluster 識別

從 `kmeans.cluster_centers_` 直接取得各 cluster 平均光譜（`output/kmeans_classification.png` 左圖為分類圖、右圖為光譜曲線）：

| Cluster | 像素佔比 | 平均光譜重點 | NDVI | NDBI | 推測地物 |
|---------|---------|------------|------|------|---------|
| **C0** | 27.9% | NIR=**0.430**（最高） | **+0.868** | -0.342 | **健康森林**（中央山脈密林） |
| **C1** | 36.7% | 所有波段 ~0.06-0.09 | -0.015 | -0.004 | **水體**（太平洋 + 立霧溪深水） |
| **C2** | 1.3% | Blue=0.33, NIR=0.43, SWIR=0.34 | +0.125 | -0.013 | **雲殘留 / 極亮目標**（薄雲 + 大理岩 + 混凝土） |
| **C3** | 27.4% | NIR=0.312 | +0.833 | -0.276 | **次密林 / 部分復植區** |
| **C4** | 6.8% | 各波段 0.14-0.27，SWIR>NIR | +0.264 | -0.018 | **裸地 / 崩塌 / 河床** |

**判讀討論：**
- **容易解讀**：C0（森林）、C1（水體）—— NDVI 極端對立（+0.87 vs -0.02），K-means 切得乾淨
- **難解讀**：
  - C2（佔比 1.3%，亮目標混合）—— K-means 沒辦法分辨「亮因為是雲」vs「亮因為是大理岩裸岩」vs「亮因為是混凝土」
  - C0 vs C3 都是植被，差異只有 NIR 強度 → 可能是「密林 vs 稀疏林」**或**「平地 vs 山陰坡同種植被」

這正是非監督分類的限制：**告訴你「光譜長得像」，但「物理上是什麼」要靠 RF 釐清**。

---

## Task 2 結果

### Random Forest 訓練樣本

| Class ID | 名稱 | 多邊形數 | 訓練像素 | 評估 |
|----------|------|---------|---------|------|
| 0 | Water | 5 | 177 | ✅ |
| 1 | Forest | 5 | 302 | ✅ |
| 2 | Cropland | 5 | 116 | ✅ |
| 3 | Bare/Landslide | 6 | 445 | ✅ |
| 4 | Built-up | 5 | 82 | 🔶 偏少 |
| **合計** | — | **26** | **1,122** | — |

80/20 split → 訓練 897 / 測試 225。

### 模型表現

| Metric | 值 |
|---|---|
| Training Accuracy | 100.00%（RF 易過配） |
| **Test Accuracy** | **77.33%** |
| OOB Accuracy | 82.83% |
| **Cohen's Kappa** | **0.6852**（substantial agreement） |

**OOB vs Test 差 -5.5%** —— OOB 略高，這是因為 OOB 包含整個訓練集的 bagging-based 抽樣，分布更接近整體；Test 是 stratified split 後的 20% holdout，可能採到較難的邊界樣本。

### Per-class Performance

| 類別 | Precision | Recall | F1 | Support |
|------|-----------|--------|----|---------|
| Water | 0.675 | 0.750 | 0.71 | 36 |
| **Forest** | **0.917** | **0.902** | **0.91** | 61 |
| Cropland | 0.800 | 0.696 | 0.74 | 23 |
| Bare/Landslide | 0.747 | 0.798 | 0.77 | 89 |
| **Built-up** | **0.500** | **0.313** | **0.38** | **16** ⚠ |

**Built-up 是最弱類別**：只有 82 訓練 / 16 測試樣本，F1 0.38 —— 但 Taroko 地區建物本來就稀少（蘇花公路沿線少數聚落），這個結果反映**樣本量先天不足**而非模型缺陷。

**Macro F1 = 0.704** vs **Weighted F1 = 0.769**，Gap **+0.065 > 0.03** → 弱勢類別的 F1 被多數類別稀釋，建議實際應用時看 Macro 而非 Weighted。

### Feature Importance（與 W12 課堂完全不同！）

```
1. SWIR2  (B12): 0.250  ← 最高
2. SWIR1  (B11): 0.175
3. Blue   (B02): 0.165
4. NIR    (B08): 0.146
5. Green  (B03): 0.133
6. Red    (B04): 0.131
```

**W12 課堂（花蓮縱谷都市平原）**：Blue 第一、NIR 中等
**HW11 太魯閣山區海岸**：SWIR2 第一、NIR 中等、Blue 第三

**解讀**：太魯閣大量森林 → 模型需要 SWIR2 來區分「乾燥裸礫 vs 健康植被」（兩者在可見光接近但 SWIR2 差很多）。縱谷區則靠 Blue 把建物 vs 水體 vs 植被分開。**Feature importance 是「對這個場景」的局部解釋，不是普世真理。**

### K-means vs Random Forest

見 `output/kmeans_vs_rf_comparison.png`（三圖並列）。主要差異：
- K-means C1（水體）涵蓋了 36.7% 像素 —— 包含太平洋海域。Random Forest 把同樣的區域正確切成 Water(41.2%) 和 Bare(11.7%)、Cropland(9.3%)
- K-means C2（亮目標）的零碎雲邊緣 → RF 大多正確歸為 Bare 或 Built-up
- K-means C0+C3 兩個森林 cluster → RF 合併為單一 Forest 類別

---

## Task 3 結果

### Part A — 內部精度

混淆矩陣熱力圖：`output/confusion_matrix.png`

主要混淆對：
1. **Cropland (23) 漏判** → 7 個被誤判為 Bare/Landslide → Cropland recall 只有 69.6%
2. **Built-up (16) 漏判嚴重** → 11 個被誤判（多為 Bare/Landslide 或 Water）→ recall 31.3%
3. **Water (36)** 9 個被誤判為其他（Bare/Built-up），可能是淺水/海岸線像素

**OOB vs Test**：差 -5.5%（Test 較低），在 OK 範圍內，沒有過度配適。

### Part B — SWCB 獨立驗證

```
SWCB 全臺崩塌多邊形:        1,335
裁切到研究區後:              207
SWCB 總崩塌面積（BBOX）:      91.8 ha
20m rasterize 後（all_touched=True）: 131.8 ha   ← 邊界放大效應
RF Bare/Landslide 預測面積:  7,449 ha            ← 嚴重過預測
```

| 指標 | 數值 | 解讀 |
|------|------|------|
| Recall (TP / (TP+FN)) | **0.5274** | **漏判率 47.3%** |
| Precision (TP / (TP+FP)) | **0.0083** | **誤報率 99.2%** ⚠⚠⚠ |
| IoU (Jaccard) | 0.0082 | 空間吻合度極低 |
| F1 | 0.0163 | — |

疊圖：`output/swcb_overlay.png`（綠=TP / 紅=FN / 黃=FP）

#### 必答討論

**1. 為什麼 IoU < 1？我的 IoU 怎麼這麼低？**

主因是**類別定義落差**（最重要）：
- 我的 "Bare/Landslide" 包含**所有看起來裸的地表**（崩塌、河床、稀植區）
- SWCB 只記**「震後新生」的崩塌** —— 窄義
- → 我把整片立霧溪河床都歸為崩塌（佔大量 FP）

次因（重要性遞減）：
- **時序差**：影像 2024-08-27 vs SWCB 2024-08-02，間隔 25 天
- **空間解析度差**：Sentinel-2 20m vs SWCB ~1-2m，邊界誤差被 `all_touched=True` 進一步放大
- **訓練樣本未對齊**：我的 Bare ROI 在三棧溪/立霧溪畫了多個多邊形，但**沒有刻意排除天然河床**

**2. FN（漏判崩塌）集中在哪？**

從 `swcb_overlay.png` 紅色點觀察：
- **太魯閣峽谷深處（121.55-121.59°E）**：山陰側強烈地形陰影 → 反射率低 → RF 誤判為 Forest 暗區
- **窄長型線狀崩塌（沿溪溝或道路邊坡）**：寬度 < 20m，單一像素吃不到細節
- **雲遮罩邊緣附近**：半透明雲影響反射率，被歸到 Water 或暗 Forest

**3. External SWCB vs Internal test，哪個更可信？**

| 角度 | Internal 77.3% OA | SWCB IoU 0.008 |
|---|---|---|
| 衡量什麼 | 訓練類別**一致性**（我教什麼學什麼）| **外部效度**（我學的對真實世界對嗎）|
| 為什麼數字差這麼大 | 同分布的 holdout 自然高 | 類別定義落差暴露無遺 |

**結論**：SWCB 外部驗證**更值得相信**作為「模型對應用問題的回答品質」的指標 —— 但要正確解讀：它說的是「**訓練類別語義 ≠ 應用要回答的問題**」，不是「模型很爛」。

**改進方法**：
1. 重新標註 ROI，**嚴格只挑震後新生崩塌**作為 Bare/Landslide 類訓練樣本
2. 或接受 RF 是「general bare ground detector」，**用作崩塌偵測的篩選上限**，後端再用 (a) DEM 變化偵測 (b) 震前 NDVI 比對 篩出真正崩塌

---

## Task 4 結果

### 各類別面積（`output/class_area_stats.csv`）

| Class | Pixels | Area (ha) | Area (km²) | % of valid |
|-------|--------|-----------|-----------|-----------|
| Water | 656,769 | 26,270.76 | 262.71 | **41.21%** |
| Forest | 589,400 | 23,576.00 | 235.76 | 36.98% |
| Bare/Landslide | 186,232 | 7,449.28 | 74.49 | 11.68% |
| Cropland | 148,185 | 5,927.40 | 59.27 | 9.30% |
| Built-up | 13,274 | 530.96 | 5.31 | 0.83% |

**注意**：Water 佔 41% 是因為 BBOX 東半部（121.62-121.80°E）涵蓋大片太平洋海域。
**警示**：Bare/Landslide 74.5 km² 是嚴重高估，見 Task 3 Part B 討論 —— 真實「震後新生崩塌」依 SWCB 只有 ~0.9 km²。

### Gemini AI 簡報摘要

完整內容於 `output/ai_briefing.md`。Gemini 採用 `gemini-2.5-flash` 模型成功回應，產出 5 段結構：(1) 土地覆蓋概況 (2) 崩塌面積與分布 (3) SWCB 比對 (4) 後續分析建議 (5) 不確定性說明。

### LLM 批判評估

詳見 notebook 內 Task 4 結尾的 markdown cell。摘要 5 點：

1. ✅ **面積數字 100% 正確**（沒有捏造）
2. ⚠ **「Sentinel-2 10m 解析度」是事實錯誤**：訓練語料偏好覆寫了 prompt 上下文（典型 LLM 幻覺）
3. ⚠ **「優先看 Precision」是錯誤建議**：災害應變初期應優先 Recall（寧可誤報，不可漏掉）
4. 中等：後續分析建議是樣板話三件套，沒指出蘇花公路、立霧溪等具體地點（缺本地 GIS 圖層）
5. **驗收**：LLM 在「資料 → 敘事翻譯」做得好，但**對遙測領域指標的選擇仍偏通用視角**，需要人工把關

---

## ARIA v8.0 升級反思

| 維度 | v7.0 閾值法 | v8.0 分類器 |
|------|------------|------------|
| 輸入 | 單一指標 | 同時 6 波段 |
| 輸出 | 二元 | 多類 |
| 決策面 | 1D | 6D |
| 訓練資料 | 不需要 | 需要 ROI 標籤 |
| 對混合像素 | 無法處理 | 可（機率輸出） |

### 5 個關鍵教訓

1. **STAC provider 不是即插即用**：AWS Element84 的 BOA offset（scale=0.0001, offset=-0.1）stackstac 自動套用，原本「DN ÷ 10000」搬過來會壓掉 92% 像素。**遇到全部 NaN 先查 metadata，不是查 sklearn。**

2. **訓練樣本類別定義 = 應用問題的定義**：我的 RF 對 internal test 表現 77%，但對 SWCB 外部驗證 IoU 只有 0.008。**不是模型爛，是教的東西跟考的東西不一樣。**

3. **Feature Importance 隨研究區改變**：W12 縱谷 Blue 第一；HW11 太魯閣 SWIR2 第一、NIR 反而第五。**Feature importance 是局部解釋，不是普世真理。**

4. **Macro vs Weighted F1 落差揭露樣本失衡**：Built-up F1 0.38 被 Bare F1 0.77 稀釋，Weighted 看起來 0.77 不錯但 Macro 0.70 才是真實表現。**指揮官關心人命就絕對不能看 Weighted。**

5. **LLM 的不確定性表述會被訓練偏好覆寫**：Gemini 把我寫進 prompt 的「20m」改成「10m」。**任何 LLM 輸出必須對證原始資料**，不能信「它應該有看到」。

---

## 檔案結構

```
Homework-11/
├── Week12_ARIA_v8_HuangYongZhi.ipynb   # 主 notebook（含全部圖表與答案）
├── build_homework11.py                  # 構建腳本（重複生成 notebook 用）
├── README.md                            # 本檔
├── Homework-Week12.md                   # 老師作業說明
├── Homework11_label.kmz                 # 26 多邊形 5 類訓練 ROI
├── 20240802新生崩塌地.kml                # SWCB 1335 polys (207 在 BBOX 內)
├── .env                                 # GEMINI_API_KEY（不 commit）
├── .env.example                         # API key 範本
└── output/
    ├── study_area_rgb.png               # 研究區真色彩 + 假色彩
    ├── kmeans_classification.png        # Task 1: K-means + 光譜曲線
    ├── rf_classification.png            # Task 2: RF 分類圖（含 truth 對照）
    ├── rf_feature_importance.png        # Task 2: 6 波段重要性
    ├── kmeans_vs_rf_comparison.png      # Task 2: 三圖並列
    ├── confusion_matrix.png             # Task 3-A: 混淆矩陣
    ├── swcb_overlay.png                 # Task 3-B: TP / FN / FP 疊圖
    ├── class_area_stats.csv             # Task 4: 各類面積統計
    └── ai_briefing.md                   # Task 4: Gemini 完整 prompt + response
```

---

## 執行步驟（給未來複跑用）

```powershell
# 1. 準備檔案
#    - Homework11_label.kmz（5 類 ROI）
#    - 20240802新生崩塌地.kml（SWCB）
#    - .env（填入 GEMINI_API_KEY）

# 2. 跑 notebook（用 geopandas conda env）
cd D:\YongZhi\2026_RS\submission\Homework-11

$env:PYTHONIOENCODING='utf-8'
& "C:/Users/user/anaconda3/envs/geopandas/python.exe" -m jupyter nbconvert `
  --to notebook --execute --inplace --allow-errors `
  --ExecutePreprocessor.timeout=600 `
  --ExecutePreprocessor.kernel_name=python3 `
  Week12_ARIA_v8_HuangYongZhi.ipynb
```

---

*Note: 若要修改 cell 邏輯，請編輯 `build_homework11.py` 後重跑它（會覆蓋 .ipynb 為新版骨架），然後再用 nbconvert 重新執行取得輸出。* 
