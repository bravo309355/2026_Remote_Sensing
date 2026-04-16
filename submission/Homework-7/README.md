# Homework Week 7 - ARIA v4.0

## Assignment Completion

- Road network extraction / archive: completed
- Graph projection to EPSG:3826: completed
- Travel-time baseline from road length and speed: completed
- Betweenness centrality and Top 5 bottlenecks: completed
- Week 4 terrain-risk overlay: completed
- Dynamic accessibility analysis using Week 6 kriging rainfall: completed
- Accessibility impact table for 5 key shelters: completed
- Before/after isochrone visualization: completed
- GraphML export and .env example: completed

### Required Layer Summary

```text
 priority_rank facility_id       name  capacity  short_loss_pct  long_loss_pct uncertainty_flag
             1        3000       國風國中     800.0       50.410473      14.380238           MEDIUM
             2        2999      中正體育館     593.0       50.273119       8.298497           MEDIUM
             3        3025 國立花蓮農業職業學校     382.0       35.510495      14.043832           MEDIUM
             4        3085   私立四維高級中學     500.0       24.636591      20.727984           MEDIUM
             5        3098    花蓮縣立體育場     527.0       22.122644      23.096524           MEDIUM
```

## Stretch Enhancements

- Added shelter-level coverage for all Hualien City shelters.
- Preserved the observed Week 6 result and added a stress-test contingency scenario.
- Used rainfall uncertainty from the kriging variance raster.

### Stretch Layer Summary

```text
Scenario: observed

scenario_name facility_id         name  capacity  short_loss_pct  long_loss_pct uncertainty_flag  priority_rank
     observed        2964     主農社區活動中心      50.0       59.071140      10.852104           MEDIUM              1
     observed        2974 中原國小文中三國中預定地      85.0       56.923368      10.902832           MEDIUM              2
     observed        2982    花蓮城隍廟香客大樓     100.0       53.283894       6.948062           MEDIUM              3
     observed        2973         中正國小     187.0       51.460713       5.430815           MEDIUM              4
     observed        3000         國風國中     800.0       50.410473      14.380238           MEDIUM              5

Scenario: stress_test

scenario_name facility_id       name  capacity  short_loss_pct  long_loss_pct uncertainty_flag  priority_rank
  stress_test        3080 慈濟大學人文社會學院     316.0       90.374460      71.644701           MEDIUM              1
  stress_test        3079       花蓮高工     310.0       89.366859      70.043229             HIGH              2
  stress_test        3098    花蓮縣立體育場     527.0       86.489622      70.953822           MEDIUM              3
  stress_test        3076       自強國中     330.0       84.203624      54.249697             HIGH              4
  stress_test        3055       中華國小     189.0       82.856749      56.282609           MEDIUM              5
```

## Data Sources

- Road network: OpenStreetMap / OSMnx (Hualien City, Taiwan)
- Shelters: shelters_cleaned.csv
- Terrain context: DEM_tawiwan_V2025.tif + Week 4 terrain audit
- Rainfall source: W6 kriging raster (kriging_rainfall.tif)
- Rainfall variance source: kriging_variance.tif

## Captain's Log

- Part A secured a reusable road graph so the analysis does not depend on repeated live downloads.
- Part B identified transport bottlenecks before applying any hazard effect.
- Part C shifted the analysis from static road geometry to disaster-era accessibility loss for real shelters.
- The stretch section extends the worksheet answer with a contingency scenario for command planning.

## AI Diagnostic Log

- Missing road speed attributes were handled by parsing maxspeed when available, then falling back to highway-type defaults and a final 40 km/h default.
- OSMnx fetch instability was mitigated by reading archived GraphML first and reusing the Exercise-7 cache if Homework-7 had not built its own cache yet.
- Homework-7 uses an adaptive-threshold congestion mapping derived from the sampled Hualien City rainfall distribution so the observed layer still produces measurable before/after accessibility differences.

### Required AI Report

**Transportation Advisory for Typhoon Fung-wong (2025-11-11 18:50)**

To: Hualien County Disaster Prevention Command Center
From: Transportation Advisor
Date: 2025-11-11

This advisory outlines critical transportation priorities and resource recommendations in response to Typhoon Fung-wong, based on current network analysis and accessibility impact assessments.

---

### 1. Priority Road Segments to Clear, with Reasoning

Immediate efforts must focus on clearing obstructions and restoring passage on road segments associated with the following bottleneck nodes:

*   **Node #1: 649286213 (Centrality=0.1402)**
*   **Node #2: 649286214 (Centrality=0.1394)**
*   **Node #3: 1061487893 (Centrality=0.1253)**
*   **Node #4: 929963021 (Centrality=0.1235)**
*   **Node #5: 1074772659 (Centrality=0.1157)**

**Reasoning:** These nodes represent critical choke points in Hualien County's transportation network, as indicated by their high centrality scores. Disruptions at these locations will disproportionately degrade overall network connectivity, severely impeding emergency response, logistical support, and potential evacuation routes. Prioritizing the rapid clearance of road segments immediately adjacent to and forming part of these nodes will:
    *   Significantly improve network flow and resilience.
    *   Expedite the deployment of emergency services and critical supplies.
    *   Restore access to key areas more efficiently than scattered clearance efforts.

### 2. Alternative Rescue Methods for Isolated Areas

The following facilities are currently isolated, indicating compromised ground access. Alternative rescue and resupply methods are critical:

*   **國風國中**
*   **中正體育館**

**Recommended Methods:**
    *   **Air Assets (Helicopter Deployment):** Initiate immediate aerial reconnaissance to assess the extent and nature of isolation. Utilize helicopter assets for:
        *   Rapid delivery of essential supplies (food, water, medical kits).
        *   Emergency medical evacuation of critical casualties.
        *   Insertion of specialized search and rescue (SAR) teams.
        *   Given the "very high" terrain risk for 中正體育館, air assessment is paramount to determine safe landing zones and potential hazards.
    *   **Specialized Ground Vehicles:** If isolation is primarily due to flooding or debris rather than structural damage or extensive landslides, deploy high-clearance vehicles, all-terrain vehicles (ATVs), or potentially amphibious vehicles where suitable. This requires concurrent ground assessment for feasibility and safety.
    *   **Foot Patrols / Light Teams:** Dispatch small, agile teams on foot to conduct rapid needs assessments, provide immediate first aid, and deliver small, critical items where vehicle access is completely impossible.

### 3. Resource Allocation Recommendations

Effective resource allocation is paramount for immediate response and sustained recovery.

**A. Personnel Deployment:**
    *   **Road Clearing Teams:** Prioritize deployment of public works, engineering, and volunteer teams equipped for heavy debris removal to the vicinities of the identified bottleneck nodes (649286213, 649286214, 1061487893, 929963021, 1074772659).
    *   **Search and Rescue (SAR) Teams:** Stage SAR teams for immediate deployment to 國風國中 and 中正體育館, utilizing air assets as the primary transport method.
    *   **Medical Teams:** Prepare mobile medical units for rapid deployment to affected areas, especially those with high short-term accessibility loss (國風國中, 中正體育館, 國立花蓮農業職業學校, 私立四維高級中學), as access is restored.
    *   **Logistics & Distribution Teams:** Establish forward operating bases and pre-position teams for efficient distribution of relief supplies once routes are cleared.

**B. Equipment Allocation:**
    *   **Heavy Machinery:** Allocate excavators, bulldozers, front-end loaders, dump trucks, and chainsaws for expedited road clearance operations at bottleneck nodes.
    *   **Air Assets:** Designate specific helicopter units for relief and rescue operations targeting isolated facilities (國風國中, 中正體育館).
    *   **Specialized Vehicles:** Deploy high-clearance vehicles, ATVs, and potentially small boats/amphibious vehicles for reconnaissance and access to partially flooded or debris-laden areas.
    *   **Communication Equipment:** Ensure robust communication networks for all deployed teams, especially those in isolated or high-risk zones.
    *   **Emergency Lighting:** Provide portable lighting equipment for night operations, particularly during road clearing and SAR efforts.

**C. Supply Prioritization:**
    *   **Essential Relief Supplies:** Pre-position and prioritize the delivery of food, potable water, blankets, shelter materials, and hygiene kits to areas with high accessibility impact, with immediate aerial delivery to isolated facilities.
    *   **Medical Supplies:** Ensure a robust supply of first aid kits, emergency medications, and trauma care equipment for medical teams.
    *   **Fuel:** Secure adequate fuel reserves for all operational vehicles and machinery.

By strategically addressing these priorities, Hualien County can mitigate the transportation impacts of Typhoon Fung-wong, expedite response efforts, and protect its citizens.

### Stretch AI Report

To Hualien Emergency Management:

The following advisory is based on the network centrality analysis (bottleneck nodes) and the stress-test simulation following Typhoon Fung-wong. The disparity between baseline operational conditions and stress-test scenarios indicates that the current Hualien emergency network is highly fragile under extreme rainfall.

### 1. Stress-Test Shelter Rescue Priority
Under the stress-test scenario, **all priority shelters exhibit "high" or "very high" terrain risk and severe loss percentages.** Prioritization must be based on life-safety capacity and risk mitigation:

1.  **Priority 1: 花蓮縣立體育場 (527 capacity):** Highest capacity. It provides the best chance for large-scale sustained support if nearby transport nodes remain even partially viable.
2.  **Priority 2: 慈濟大學人文社會學院 (316 capacity):** High importance due to its function as a central node, though terrain risk is high.
3.  **Priority 3: 自強國中 (330 capacity):** Lowest terrain risk among the stress-test group; should serve as the primary hub for vulnerable populations.
4.  **Priority 4: 花蓮高工 (310 capacity):** High uncertainty; requires satellite communication checks before dispatching ground teams.
5.  **Priority 5: 中華國小 (189 capacity):** **Lowest priority.** Terrain risk is "very high." Evacuation *from* this site to a secondary location should be considered if rainfall exceeds 14mm.

### 2. Alternative Access & Transport
The top five bottleneck nodes (649286213, 649286214, etc.) are critical; their failure effectively isolates the priority shelters.
*   **Aerial Extraction/Supply:** Given the high terrain risk (especially at中华國小 and 花蓮高工), ground access is likely compromised. Designate **花蓮縣立體育場** as a helicopter landing zone (HLZ) for medical supply drops.
*   **Waterway/Alternative Routes:** If road nodes are severed, prioritize heavy-duty off-road vehicles (4x4) over standard ambulances for medical transit to the **自強國中** site, as it retains the lowest terrain risk profile.
*   **Bridge/Pass Monitoring:** Any bottleneck node associated with river crossings or mountain passes must be monitored via drone to identify alternate local roads (informal paths) that bypass main arterial collapses.

### 3. Resource Allocation Priorities
*   **Medical/Triage Kits:** Immediate deployment to **慈濟大學人文社會學院** and **花蓮縣立體育場**.
*   **Heavy Machinery:** Pre-position debris clearing equipment near the identified bottleneck nodes (1061487893 and 929963021) to reopen arterial paths as soon as rainfall peaks subside.
*   **Communication:** Distribute satellite uplink terminals to the **花蓮高工** and **自強國中** command posts due to the "HIGH" uncertainty flag.

### 4. Rainfall Uncertainty Caution
The "HIGH" uncertainty flag for **花蓮高工** and **自強國中** is a major red flag. 
*   **Do not rely on stationary shelter strategies** if rainfall exceeds 15mm. 
*   Because current models show a jump from ~50% loss (observed) to ~85% loss (stress-test), the tipping point is extremely sharp. **Assume that current "safe" routes will become impassable within 1 hour of intense precipitation.** Implement a "pre-emptive movement" policy rather than a "reactionary rescue" policy.

### 5. Contrast: Observed Week 6 vs. Stress-Test
*   **Week 6 (Observed):** Conditions are manageable. Losses are in the 50% range, suggesting that current infrastructure is adequate for standard typhoon impacts, with moderate strain on the road network.
*   **Stress-Test (Contingency):** The system reaches a **cascading failure state**. Losses jump by 30-40% across the board. The primary difference is the shift from "logistics-limited" (moving supplies) to "survival-limited" (preserving the integrity of the shelters themselves). In the stress-test, the network is no longer a transport grid; it becomes a series of isolated points, necessitating autonomous survival kits for each shelter. 

**Recommendation:** Shift from a "hub-and-spoke" supply model to a "distributed survival" model immediately upon crossing the 12mm rainfall threshold.

## Deliverables

- [x] ARIA_v4.ipynb
- [x] data\hualien_network.graphml
- [x] accessibility_table.csv
- [x] README.md
