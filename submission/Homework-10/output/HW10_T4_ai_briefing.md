# AI Strategic Briefing — Gemini Response

**Model**: gemini-2.5-flash

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

[Gemini API 無法呼叫 — 以下為依資料人工撰寫的備援簡報]

*(Placeholder — actual response will be generated when API is available.)*
