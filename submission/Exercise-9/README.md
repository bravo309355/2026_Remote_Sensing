# Week 9: Change Detection & Validation — ARIA v6.0

**Course**: 遙測空間資訊分析與應用 (Remote Sensing Analysis & Applications)
**Institution**: National Taiwan University
**Student**: Huang YongZhi
**Case study**: 馬太鞍溪堰塞湖 (Typhoon Colo, 2025-08~09)

## 目的

以 Sentinel-2 光學影像進行災前 / 災中 / 災後三景變遷偵測，比較 NDVI 與 NDWI 在堰塞湖偵測上的表現，並以多來源驗證資料計算偵測準確度。

## 目錄結構

```
Exercise-9/
├── Week9-Student.ipynb                 主要 notebook (完整執行結果)
├── Week9-Student_origin.ipynb          原始教學模板
├── validation_points.geojson           講師提供 60 點 (field-corrected)
├── validation_points_student.geojson   學生 GEP 25 點 (2022-11-13 VHR 標註)
├── output/
│   ├── Mataan_validation_20221113.kml  GEP 原始標註檔
│   ├── ARIA_v6_0_Disaster_Report.txt   最終災害報告
│   ├── AI_Advisor_Prompt_Template.txt  LLM 輔助決策 prompt 模板
│   └── *.png                           各階段視覺化成果
└── README.md                           本檔
```

## 資料來源

| 來源 | 用途 | 時間 |
|------|------|------|
| Sentinel-2 L2A (Planetary Computer) | 三景光譜影像 | Pre: 2025-06-15 / Mid: 2025-09-11 / Post: 2025-10-16 |
| Sentinel-2 L2A | 時間對齊的閥值校正 | 2022-11-11 |
| Google Earth Pro (2022-11-13 VHR) | 學生自行標註 25 驗證點 | 2022-11-13 |
| 講師提供 geojson | 60 field-corrected 驗證點 | - |

## 主要分析流程

1. **S1-S4**: 環境設定、STAC 查詢、影像下載、NDVI / NDWI 計算
2. **S5**: 三類差異圖產出（全區 2×2、上游特寫、4×5 閥值敏感度 grid）
3. **S6**: 閥值敏感度曲線掃描
4. **S7**: 建立水體偵測 mask (2×2：純偵測 / 衛星疊圖)
5. **S8-S11**: 講師 60 點驗證 → 混淆矩陣 + OA / PA / UA / Kappa
6. **S11b (Homework Task 3 Stage 1)**: 25 GEP 點對 Pre scene 校正
7. **S11d (Stage 1 時間對齊版)**: 25 GEP 點對 2022-11-11 S2 校正
8. **S11c (Stage 2)**: 同樣 25 點對 Mid scene 災後偵測（有警告提示）
9. **S12**: F1 vs 閥值掃描 → 最佳化閥值
10. **S13**: 三區信心圖 (High / Low / None)
11. **S14**: ARIA v6.0 報告產出
12. **S15**: AI Advisor prompt 模板

## 關鍵結果

### 講師 60 點驗證 (Mid scene, NDWI > 0.1)
| 指標 | 值 |
|------|-----|
| Overall Accuracy | 0.900 |
| Producer's Accuracy | 0.600 |
| User's Accuracy | 1.000 |
| Cohen's Kappa | 0.692 (Substantial) |

### 學生 GEP 25 點 — 閥值校正對比
| 驗證設計 | OA | PA | UA | Kappa |
|----------|-----|-----|-----|-------|
| vs 2025-06 Pre (時間不對齊) | 0.760 | 0.250 | 1.000 | 0.312 |
| **vs 2022-11-11 S2 (時間對齊)** | **0.840** | **0.500** | **1.000** | **0.576** |
| vs 2025-09 Mid (僅示範 / 有警告) | 0.680 | 0.000 | 0.000 | 0.000 |

**關鍵洞察**:
- 時間對齊使 PA 從 0.25 翻倍至 0.50 → 驗證資料時間一致性至關重要
- OA 0.84 接近通過門檻 0.85，剩餘差距反映 **10 m 解析度對窄河道的物理限制**（mixed pixel）
- NDWI 比 NDVI 對堰塞湖更敏感：ΔNDWI (+0.021) vs ΔNDVI (-0.029)，且 NDWI 空間訊號集中
- SCL 雲遮 mask 有效消除假性水體訊號

## 輸出圖檔

| 檔案 | 內容 |
|------|------|
| W9_L1_difference_maps.png | 2×2 差異圖 (ΔNDVI/ΔNDWI × Mid-Pre/Post-Mid) |
| W9_L1_cloudmask_errorcase.png | 雲遮罩錯誤案例 3-panel (無遮罩 / 有遮罩 / AOI zoom) |
| W9_L1_upstream_closeup.png | 馬太鞍溪上游 3-panel 特寫 (RGB + ΔNDWI) |
| W9_L1_threshold_grid_aoi.png | 4×5 閥值敏感度 grid (NDVI/NDWI × 純偵測/衛星疊圖) |
| W9_L1_threshold_sensitivity.png | 閥值掃描折線圖 |
| W9_L2_masks.png | 水體偵測 mask 2×2 (純/衛星) |
| W9_L2_confusion_matrix.png | 60 點混淆矩陣熱圖 |
| W9_L2_f1_threshold.png | F1 vs 閥值曲線 |
| W9_L2_confidence_map.png | 三區信心圖 |
| W9_L2_student_gep_points.png | GEP 25 點疊於 Pre NDWI |
| W9_L2_student_gep_2022.png | GEP 25 點疊於時間對齊的 2022-11-11 NDWI |

## 圖軸座標

所有空間圖框已統一使用**經緯度座標** (Longitude °E / Latitude °N)，由 UTM 51N (EPSG:32651) 透過 pyproj 轉換得出。

## 字型設定

`Microsoft JhengHei` 為主要字型，能同時涵蓋繁體中文、Latin 字母、希臘字母 (Δ)、減號、箭頭等所需字符。所有程式中的 em-dash / en-dash / Unicode minus 均已統一為 ASCII hyphen。

## 執行環境

- Python 3.9 (conda env: `geopandas`)
- 主要套件: `pystac-client`, `planetary-computer`, `stackstac`, `xarray`, `pyproj`, `scikit-learn`, `matplotlib`, `seaborn`
- nbconvert 執行指令:
  ```bash
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=1200 Week9-Student.ipynb
  ```

## Homework Task 完成狀況

- [x] Task 1: NDVI / NDWI 差異圖 + 閥值敏感度
- [x] Task 2: 60 點驗證 + 混淆矩陣 + 三區信心圖 + ARIA 報告
- [x] Task 3 (Optional): Google Earth Pro 自行標註 25 驗證點 + 兩階段驗證
- [x] Task 3b: 時間對齊的 2022-11-11 S2 閥值校正
