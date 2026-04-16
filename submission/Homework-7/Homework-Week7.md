# Week 7 Assignment: ARIA v4.0 (The Accessible Auditor)

Submission Deadline: Before next class

---

## 1. Scenario

The commander not only wants to know "where are the danger zones," but more critically, "**which areas have become isolated islands**."

Typhoon Fung-wong (鳳凰颱風) created extreme rainfall of 130.5 mm/hr in Su'ao (蘇澳), causing flooding on Suhua Highway and road breaks in the mountain regions of Hualien. Your task is to upgrade the ARIA system to assess through network analysis how "**accessibility collapses during disasters**."

**Key Differences from In-Class Lab:**
- Lab 1 used NTU campus for bottleneck analysis → **This assignment uses real road networks in Hualien City / Xiulin Township (秀林鄉)**
- Lab 2 used simplified congestion_factor → **This assignment integrates real rainfall data from Week 5/Week 6**
- Lab computed isochrones from a single origin → **This assignment compares accessibility changes for multiple critical facilities**

---

## 2. Data Sources

### A. Road Network Data
- **OSMnx**: Fetch road network for Hualien City (or designated township in Hualien County) from OpenStreetMap
- Use `network_type='drive'`, save as `.graphml`

### B. Results from Previous Weeks
- **Week 3 Shelters** GeoDataFrame (includes river distance classification)
- **Week 4 Terrain Risk** (mean_elevation, max_slope, terrain_risk)
- **Week 5 Rainfall Data** (Typhoon Fung-wong `fungwong_202511.json`)
- **Week 6 Kriging Output** (`kriging_rainfall.tif`, recommended but optional)

### C. Township Administrative Boundaries
- TGOS (National Land Survey and Mapping Center) township/city boundary shapefiles

---

## 3. Core Requirements

Must submit in **`.ipynb` (Jupyter Notebook)** format.

### A. Road Network Extraction and Archiving

1. Fetch the road network for **Hualien City** (or specified administrative area) for vehicle traffic
2. Project to EPSG:3826 (meter coordinates)
3. Calculate `travel_time = length / (speed / 3.6)` for each road segment
   - `speed` from OSM `maxspeed` attribute; default 40 km/h if missing
4. Save as `.graphml` file (to avoid repeated downloads)

### B. Bottleneck and Risk Diagnosis

1. Calculate **Betweenness Centrality (介數中心性)** of the road network
2. Identify the **Top 5 bottleneck nodes** by centrality
3. Overlay Top 5 nodes with terrain_risk from Week 4:
   - Use `gpd.sjoin()` or nearest-neighbor approach to determine terrain_risk for Top 5 nodes
   - Identify the **most vulnerable transportation hubs** (high centrality + high terrain_risk)
4. Visualize: Show Top 5 nodes on road network map (color = terrain_risk)

### C. Dynamic Accessibility Analysis

1. **Define rainfall → congestion mapping function** `rain_to_congestion(rain_mm)`:
   - Use the formula from class: `travel_time_adj = length / (speed × (1 − cf))`
   - Design rainfall classifications yourself (refer to class Slide 12)
2. **Specify rainfall data source** (choose one):
   - **Option A** (recommended): Use Week 6's `kriging_rainfall.tif`, sample at road segment midpoints via raster sampling
   - **Option B**: Use Week 5's rainfall station data, buffer + sjoin to road segments
3. Select **5 key facilities** (shelters or hospitals), calculate for each:
   - **Pre-disaster isochrones** (5 minutes + 10 minutes, using original `travel_time`)
   - **Post-disaster isochrones** (5 minutes + 10 minutes, using `travel_time_adj`)
   - **Area shrinkage ratio**: `shrinkage = 1 − (A_after / A_before)`
4. Organize into **Accessibility Impact Table**:

   | Facility | Pre-Disaster 5min (km²) | Post-Disaster 5min (km²) | Shrinkage % | Pre-Disaster 10min | Post-Disaster 10min | Shrinkage % |
   |----------|------------------------|------------------------|------------|-------------------|-------------------|-----------|
   | ... | ... | ... | ... | ... | ... | ... |

### D. AI Strategy Briefing (Bonus)

1. Install `google-generativeai` package
2. Send the accessibility impact table + Top 5 bottlenecks + isolated facility information to your preferred AI tool (ChatGPT / Gemini / Claude all acceptable)
3. Prompt specification: Require AI to take the role of "Hualien County Disaster Prevention Command Center Transportation Advisor"
4. AI report should include:
   - Priority road segments requiring clearance and reasoning
   - Alternative rescue methods for isolated areas (helicopter, rubber boats, etc.)
   - Resource allocation priority order

```python
# Bonus Prompt Example
prompt = f"""You are a transportation advisor at Hualien County Disaster Prevention Command Center.
Below are the road network analysis results from Typhoon Fung-wong (鳳凰颱風):
Top 5 Bottleneck Nodes: {top5_info}
Accessibility Impact Table: {accessibility_table}
Isolated Facilities: {isolated_shelters}

In professional disaster-prevention language, please provide:
1. Priority road segments to clear (with reasoning)
2. Alternative rescue methods for isolated areas
3. Resource allocation recommendations"""
```

### E. Professional Standards (Infrastructure First)

1. **Environment Variables**: Place congestion parameters and road network search radius in `.env`
2. **GraphML Archiving**: Fetch road network once, read from .graphml in subsequent runs
3. **Markdown Cells**: Write "Captain's Log" before each analysis step
4. **AI Diagnostic Log**: In README, describe how you solved at least one of the following:
   - "OSMnx fetch timeout or incomplete road network"
   - "Isochrone polygon shape anomalies (holes or oversized)"
   - "Kriging raster sampling returns nodata at road segment midpoints"
   - "NetworkXNoPath after road breaks — isolation detection logic"
   - "Missing road speed attributes — default value strategy"

---

## 4. Recommended Coding Prompt

> "I need to build ARIA v4.0 — a network-based disaster accessibility system. I have:
> 1. Week 3-4 shelter GeoDataFrame (EPSG:3826) with river_risk and terrain_risk
> 2. Week 5 rainfall JSON (Typhoon Fung-wong) or Week 6 Kriging GeoTIFF
>
> Help me in separate Jupyter cells:
> 1. Fetch Hualien city road network with OSMnx, project to EPSG:3826
> 2. Calculate travel_time for each edge (length / speed, default 40 km/h)
> 3. Compute betweenness centrality, find Top 5 bottleneck nodes
> 4. Overlay Top 5 with terrain_risk from W4
> 5. Define rain_to_congestion() mapping function
> 6. Sample Kriging raster at edge midpoints OR sjoin rainfall stations
> 7. Apply dynamic weights: travel_time_adj = length / (speed × (1-cf))
> 8. For 5 key shelters, compute 5-min and 10-min isochrones (before & after)
> 9. Calculate isochrone area shrinkage ratios
> 10. Save network as .graphml, create summary table"

---

## 5. Deliverables

1. **GitHub Repo URL**
2. **`ARIA_v4.ipynb`** — Complete analysis notebook (with execution results)
3. **`hualien_network.graphml`** — Road network data file
4. **`README.md`** — Includes AI diagnostic log
5. **Accessibility Impact Table** — Presented as DataFrame in notebook

---

## 6. Grading Rubric

| Item | Weight |
|------|--------|
| Road network extraction + basic travel time + GraphML archiving | 15% |
| Betweenness centrality + Top 5 bottlenecks + Week 4 overlay | 20% |
| Dynamic accessibility analysis (congestion + isochrones + shrinkage ratio) | 30% |
| Professional standards (.env + GraphML + README + AI log) | 15% |
| Visualization quality (road network map + before/after isochrone comparison) | 10% |
| Bonus: AI strategy briefing (any tool acceptable) | 10% |

---

## 7. Tips and Notes

- **CRS Consistency**: Road network (project_graph → 3826), shelters (3826), Kriging raster (3826) must all use the same CRS
- **Speed Default Values**: OSM's `maxspeed` is often missing. Use a dictionary to map highway types: primary=60, secondary=40, residential=30 km/h
- **Isochrone Polygons**: Use `alphashape` or `shapely.concave_hull()` to polygonize reachable nodes. Alpha parameter requires tuning (suggested 0.001-0.01)
- **Large Network Performance**: Hualien City has ~3000 nodes (quick); full county ~30000 nodes (centrality may take 1-2 minutes). This assignment only requires one township/city
- **Kriging Raster Sampling**: `rasterio.open().sample()` takes `(x, y)` coordinates in EPSG:3826 easting/northing
- **Road Break Detection**: `congestion_factor >= 0.95` can be treated as "impassable"; remove the segment and recalculate alternative routes
- **Folium Integration**: To place road network on an interactive Folium map, convert with `ox.graph_to_gdfs(G)` to GeoDataFrame, then add with `folium.GeoJson()`

---

*"A risk map tells you what is broken. A network analysis tells you if you can still save someone."*
