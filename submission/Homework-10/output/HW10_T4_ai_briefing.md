# AI Strategic Briefing — Gemini Response

**Model**: gemini-2.5-flash-lite

## Prompt

```
You are an emergency management advisor for Hualien County during Typhoon Fung-wong (2025-11).
Based on these ARIA v7.0 sensor fusion results, generate a strategic briefing in 繁體中文 covering:

1. Which areas require IMMEDIATE evacuation? (priority by confidence class)
2. How should rescue resources be allocated between High Confidence vs SAR Only zones?
3. What are the limitations of this assessment? (be specific about SAR shadow, DEM staleness in the upstream collapse zone, and the cloud-cover constraint on optical validation)
4. What additional data would improve confidence within 24-48 hours? (be specific — name actual data products / sensors)

Keep the briefing under 400 words. Use bullet points where appropriate.


ARIA v7.0 Sensor Fusion Results — Hualien × Typhoon Fung-wong (2025-11)
======================================================================

Study area: bbox [121.28, 23.56, 121.52, 23.76] (lat/lon, ~24×22 km, includes Matai'an watershed + Hualien plain)
Pre-event:  Sentinel-1 ascending 2025-10-30 (clear baseline)
Post-event: Sentinel-1 ascending 2025-11-05 (3 days after Fung-wong peak)
Optical:    Sentinel-2 2025-11-15 (89% cloud-masked) — peak day 2025-11-02 was 100% cloud (光學完全失明)

Thresholds:
- SAR: VV < -18.0 dB (ARIA literature default)
- NDWI: > 0.0 (lowered from 0.3 because Fung-wong sediment load)
- Slope filter: > 25.0° excluded (DEM caveat: Matai'an upstream may be inaccurate after 2025/7 collapse)

Fusion results (after topographic correction):
- High Confidence (SAR ∩ NDWI):     0.11 km²
- SAR Only (cloudy areas):           0.25 km²
- Optical Only (no SAR support):     2.52 km²
- False positives removed by slope:  1.86 km²

```

## Response

**花蓮縣颱風「鳳凰」（2025-11）應變行動簡報**

**日期：** 2025年11月6日
**報告人：** ARIA 災防顧問

**緊急疏散區域 (依據信心等級優先順序)：**

*   **高信心區域 (SAR ∩ NDWI)：** 面積 0.11 平方公里。此區域顯示 SAR 和 NDWI 數據高度一致，應為確定性的淹水或潛在土石流影響區域。
*   **SAR Only 區域 (雲層遮蔽)：** 面積 0.25 平方公里。儘管光學影像受雲層影響，SAR 數據仍顯示異常，應視為高風險區域，需優先關注。

**搜救資源分配建議：**

*   **優先派遣至「高信心區域」：** 儘管面積較小，但其結果的確定性最高，需立即投入資源進行搜救及評估。
*   **同步關注「SAR Only 區域」：** 這些區域存在潛在風險，應規劃資源進行初步偵察與風險評估，一旦光學影像清晰或有進一步資訊，可迅速投入搜救。

**本評估之限制：**

*   **SAR 陰影 (SAR Shadow)：** 由於地形遮蔽，部分區域的 SAR 訊號可能受影響，導致實際災情可能被低估。
*   **DEM 的陳舊性 (DEM Staleness)：** 位於崩塌上游區域的數位高程模型 (DEM) 可能因 2025 年 7 月的崩塌事件而不準確，影響淹水模擬的精度。
*   **雲層遮蔽的光學驗證限制：** Sentinel-2 光學影像有 89% 被雲層遮蔽，尤其在風災高峰期的 11 月 2 日，光學影像完全無法使用，大幅限制了地面災情的光學驗證能力。

**建議於 24-48 小時內蒐集之額外數據以提升信心：**

*   **高解析度光學影像：** 如 PlanetScope 或 WorldView 等商業衛星影像，能提供更高空間解析度，有助於辨識小型淹水區域及地表變異。
*   **SAR 乾涉測量 (InSAR) 數據：** 於風災前後蒐集 Sentinel-1 或 NISAR 數據，進行 InSAR 分析，可精確偵測地表變形（如潛在的山體滑坡）。
*   **無人機 (UAV) 影像：** 若情況允許，部署配備 RGB 和熱紅外攝影機的無人機，能提供精確的局部災情回報，尤其是在 SAR 陰影區域。
*   **即時地面感測器數據：** 若有部署之雨量計、水位計、或地變感測器，應即時匯入以驗證 SAR 預測。
