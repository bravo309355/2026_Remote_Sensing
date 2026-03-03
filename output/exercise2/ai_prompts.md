# AI Prompts Log

## Prompt 1
- User prompt: `氣象站 API 每個測站有兩組座標，請都當成 WGS84 畫在同一張圖，並統計差距`
- AI response summary:
  - Used CWA dataset `O-A0001-001` (current weather station observations).
  - Parsed each station's `GeoInfo.Coordinates` for `TWD67` and `WGS84`.
  - Treated both coordinate pairs as WGS84 and computed per-station offset distance.
  - Generated outputs:
    - `output/exercise2/cwa_station_crs_diff.csv`
    - `output/exercise2/cwa_station_crs_stats.json`
    - `output/exercise2/cwa_station_crs_map.html`
  - Key result:
    - Mean offset: `855.042 m`
    - Median offset: `850.764 m`
    - Conclusion: `TWD67 vs WGS84 ≈ 850 m`
