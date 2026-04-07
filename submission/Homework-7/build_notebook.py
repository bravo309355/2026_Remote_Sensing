import json
import os

input_path = "d:/YongZhi/2026_RS/submission/Exercise-7/Week7-Student.ipynb"
output_path = "d:/YongZhi/2026_RS/submission/Homework-7/ARIA_v4.ipynb"

with open(input_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb.get("cells", []):
    if cell["cell_type"] != "code":
        continue
    source = "".join(cell["source"])
    
    if "# [S6] Terrain Risk Overlay" in source:
        new_source = """# [S6] Terrain Risk Overlay (Advanced Option)
from shapely.geometry import Point
import geopandas as gpd

# Step 1: Convert Top 5 Nodes to GeoDataFrame
top_5_gdf = gpd.GeoDataFrame(
    [{'node_id': nid, 'centrality': cv,
      'geometry': Point(G_proj.nodes[nid]['x'], G_proj.nodes[nid]['y'])}
     for nid, cv in top_5_nodes],
    crs=G_proj.graph['crs']
)
print(f"✅ Top 5 Node(s) GeoDataFrame Establishment complete")
print(top_5_gdf[['node_id', 'centrality']])

# Step 2 (Optional): Overlay W4 Terrain risk - skipped if data not available
# terrain_gdf = gpd.read_file('path/to/terrain_risk.geojson')
# top_5_with_risk = gpd.sjoin(top_5_gdf, terrain_gdf, how='left', predicate='within')
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

    elif "# [S8] Define rain_to_congestion Function" in source:
        new_source = """# [S8] Define rain_to_congestion Function

def rain_to_congestion(rainfall_mm, method='threshold'):
    if method == 'threshold':
        if rainfall_mm < 10:
            return 0.0
        elif rainfall_mm < 40:
            return 0.3
        elif rainfall_mm < 80:
            return 0.6
        else:
            return 0.9
    elif method == 'exponential':
        import math
        return 0.95 * (1 - math.exp(-rainfall_mm/50.0))
    elif method == 'linear':
        return min(rainfall_mm / 100 * 0.9, 0.95)
    return 0.0

# Testing
rain_test = [0, 10, 40, 80, 100, 130.5]
for rain in rain_test:
    cf = rain_to_congestion(rain, method='threshold')
    print(f"Rainfall {rain:.1f} mm/hr → Congestion Factor {cf}")
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")
        
    elif "# [S9] Load Rainfall Data" in source:
        new_source = """# [S9] Load Rainfall Data

print("✅ Rainfall data reading skipped; using simulated random data in S10")
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

    elif "# [S11] Calculate Isochrones + Isochrone Polygons" in source:
        new_source = """# [S11] Calculate Isochrones + Isochrone Polygons

from shapely.geometry import MultiPoint, Point, Polygon

def compute_isochrone(G, source_node, weight_attr, time_seconds):
    try:
        distances = nx.single_source_dijkstra_path_length(
            G, source_node, weight=weight_attr, cutoff=time_seconds
        )
    except Exception:
        distances = {}
    reachable_nodes = set(distances.keys())
    return reachable_nodes, distances

def nodes_to_polygon(G, nodes):
    if len(nodes) < 3:
        return None, 0.0
    points = [Point(G.nodes[n]['x'], G.nodes[n]['y']) for n in nodes]
    mp = MultiPoint(points)
    polygon = mp.convex_hull
    if polygon.geom_type == 'Polygon':
        return polygon, polygon.area
    return None, 0.0

def get_adaptive_thresholds(G, source_node, weight_attr):
    \"\"\"
    Adaptive thresholds. Minimum: 5 min (short), 10 min (long).
    \"\"\"
    MIN_SHORT = 5 * 60
    MIN_LONG  = 10 * 60
    try:
        all_times = dict(nx.single_source_dijkstra_path_length(
            G, source_node, weight=weight_attr
        ))
        max_time = max(all_times.values()) if all_times else MIN_LONG * 2
    except Exception:
        max_time = MIN_LONG * 2
    t_short = max(max_time * 0.35, MIN_SHORT)
    t_long  = max(max_time * 0.65, MIN_LONG)
    return t_short, t_long

print(\"✅ compute_isochrone(), nodes_to_polygon(), get_adaptive_thresholds() Definition complete\")
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

    elif "# [S12] Calculate Accessibility Benefit-Cost Table" in source:
        new_source = source + """
accessibility_table.to_csv("accessibility_table.csv", index=False)
print("✅ Saved to accessibility_table.csv")
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")
        
    elif "# [S15] Save Road Network as GraphML" in source:
        new_source = """# [S15] Save Road Network as GraphML

import os
import osmnx as ox
os.makedirs("data", exist_ok=True)
graphml_path = "data/hualien_network.graphml"
ox.save_graphml(G_proj, graphml_path)
print("✅ Road network saved as GraphML")
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

    elif "# [S16] Prepare AI Tool Invocation" in source:
        new_source = """# [S16] Prepare AI Tool Invocation

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load specific .env
load_dotenv("D:/YongZhi/2026_RS/.env")
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    print("✅ AI API Key Configured")
else:
    print("❌ API Key not found!")
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")

    elif "# [S17] Generate AI Strategic Report" in source:
        new_source = """# [S17] Generate AI Strategic Report

top_5_info = "\\n".join([
    f"#{i}: Node(s) {node_id}, Centrality={cent:.4f}" 
    for i, (node_id, cent) in enumerate(top_5_nodes[:5], 1)
])

iso_table_str = accessibility_table.to_string()

prompt = f\"\"\"You are a traffic advisor for the Hualien County Disaster Prevention Command Center.

Below are the road network analysis results for Typhoon Fenghuang:

[Bottleneck intersection(s) Top 5]
{top_5_info}

[accessibilitybenefit-costtable]
{iso_table_str}

[AnalyzeTask(s)]
Please provide professional advice as a disaster prevention specialist,Provide the following recommendations:
1. most priority need rescue via road segment and/accessibility other reason
2. Alternative rescue methods for isolated areas (Helicopter, Rubber boats, etc.)
3. Resource allocation priority order
\"\"\"

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    print("\\n🤖 AI Strategy Report:")
    print(response.text)
except Exception as e:
    print("Could not generate report:", e)
"""
        cell["source"] = [line + "\n" for line in new_source.split("\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\n")
        
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook generated.")
