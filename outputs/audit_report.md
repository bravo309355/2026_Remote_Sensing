# Audit Report

- Generated on: 2026-03-05
- Source A: `d:/YongZhi/2026_RS/data/dropped_outliers_log.csv`
- Source B: `d:/YongZhi/2026_RS/data/dropped_records_audit_report.csv`

## Cross-check Summary
- Rows in A: **126**
- Rows in B: **126**
- Matching key definition: `district + shelter_name + lon + lat + is_indoor`
- Matched rows: **126**
- Only in A: **0**
- Only in B: **0**
- Reason text mismatches: **0**

## Findings
- The two files are fully consistent at row-key level (126/126 matched).
- In B (`dropped_records_audit_report.csv`), address is blank for most rows: **125** rows have address in A but empty in B.
- Reason distribution is dominated by `bbox violation`; `Zero coordinate` appears **3** times.
- `is_indoor` in dropped records: `True=122`, `False=4`.

## Top Removal Reasons
| Reason | Count |
|---|---:|
| 桃園市 bbox violation | 24 |
| 苗栗縣 bbox violation | 17 |
| 高雄市 bbox violation | 13 |
| 臺中市 bbox violation | 13 |
| 南投縣 bbox violation | 13 |
| 嘉義縣 bbox violation | 11 |
| 彰化縣 bbox violation | 7 |
| 臺東縣 bbox violation | 5 |
| 新竹縣 bbox violation | 3 |
| Zero coordinate | 3 |
| 嘉義市 bbox violation | 3 |
| 金門縣 bbox violation | 2 |

## District Hotspots (Top 12)
| District | Count |
|---|---:|
| 桃園市新屋區 | 22 |
| 南投縣仁愛鄉 | 11 |
| 苗栗縣三義鄉 | 8 |
| 苗栗縣苑裡鎮 | 8 |
| 高雄市桃源區 | 6 |
| 彰化縣二林鎮 | 5 |
| 臺中市霧峰區 | 4 |
| 高雄市那瑪夏區 | 3 |
| 嘉義市西區 | 3 |
| 嘉義縣竹崎鄉 | 3 |
| 臺東縣長濱鄉 | 3 |
| 金門縣烏坵鄉 | 2 |

## Repeated Suspicious Coordinates
- Coordinate groups with frequency > 1: **8**
| Lon | Lat | Count | Example shelters |
|---:|---:|---:|---|
| 121.533012 | 25.042385 | 34 | 龍騰活動中心 / 雙潭活動中心 / 鯉魚潭活動中心室內 |
| 120.366378 | 23.366378 | 5 | 西平社區活動中心 / 香田國小 / 中西社區活動中心 |
| 121.196369 | 24.172426 | 3 | 基督長老教會 / 力行活動中心 / 大洋部落真耶穌教會 |
| 120.000000 | 23.000000 | 2 | 寶山國小 / 同安國小 |
| 120.804600 | 23.218000 | 2 | 台灣基督長老教會南布中會復興教會 / 高雄市桃源區樟山國民小學復興分校 |

## Recommendations
- If traceability is required, keep address fields in report B instead of dropping them.
- Add a dedicated rule for repeated fallback coordinates (for example, `121.533012, 25.042385`).
