# Exercise 2 - CWA CRS Compare

Prompt:
- 氣象站 API 每個測站有兩組座標，請都當成 WGS84 畫在同一張圖，並統計差距

## Result
- Dataset: `O-A0001-001`
- Stations fetched: 835
- Stations with both TWD67 and WGS84: 835
- Mean distance: 855.0 m
- Median distance: 850.8 m
- Min/Max distance: 580.9 m / 3682.7 m
- Difference from 850 m (mean): +5.0 m

Conclusion:
- TWD67 vs WGS84 station coordinates are approximately 850 meters apart on average.

Generated files:
- `output/exercise2/cwa_station_crs_diff.csv`
- `output/exercise2/cwa_station_crs_stats.json`
- `output/exercise2/cwa_station_crs_map.html`
