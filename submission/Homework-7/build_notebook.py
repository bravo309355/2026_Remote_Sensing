from __future__ import annotations

import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = PROJECT_ROOT / "submission" / "Exercise-7" / "Week7-Student.ipynb"
BASE_BUILD_PATH = PROJECT_ROOT / "submission" / "Exercise-7" / "build_notebook.py"
OUTPUT_PATH = PROJECT_ROOT / "submission" / "Homework-7" / "ARIA_v4.ipynb"


def load_base_builder():
    spec = importlib.util.spec_from_file_location("exercise7_builder", BASE_BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load base builder from {BASE_BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_markdown_cell(notebook: dict, marker: str, text: str, base_module) -> None:
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        if marker in "".join(cell.get("source", [])):
            cell["source"] = base_module.source_lines(text)
            return
    raise ValueError(f"Could not find markdown cell marker: {marker}")


def main() -> None:
    base = load_base_builder()
    notebook = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    cell_sources = dict(base.CELL_SOURCES)

    cell_sources["# [S1] Environment Setup"] = """
        # [S1] Environment Setup
        import json
        import math
        import os
        from pathlib import Path

        import geopandas as gpd
        import matplotlib.pyplot as plt
        import networkx as nx
        import numpy as np
        import osmnx as ox
        import pandas as pd
        import rasterio
        import rioxarray
        from IPython.display import Markdown, display
        from matplotlib import rcParams
        from shapely.geometry import MultiPoint, Point

        import warnings
        warnings.filterwarnings("ignore")

        rcParams["font.sans-serif"] = ["Microsoft JhengHei", "DejaVu Sans"]
        rcParams["axes.unicode_minus"] = False

        candidate = Path.cwd().resolve()
        search_roots = [candidate, *candidate.parents]
        PROJECT_ROOT = next(
            (path for path in search_roots if (path / "data").exists() and (path / "submission").exists()),
            candidate,
        )
        ASSIGNMENT_DIR = PROJECT_ROOT / "submission" / "Homework-7"
        EXERCISE7_DIR = PROJECT_ROOT / "submission" / "Exercise-7"
        HOMEWORK4_DIR = PROJECT_ROOT / "submission" / "Homework-4"
        HOMEWORK6_DIR = PROJECT_ROOT / "submission" / "Homework-6"
        DATA_DIR = PROJECT_ROOT / "data"
        OUTPUT_DATA_DIR = ASSIGNMENT_DIR / "data"
        OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

        NETWORK_GRAPHML_PATH = OUTPUT_DATA_DIR / "hualien_network.graphml"
        EXERCISE7_GRAPHML_PATH = EXERCISE7_DIR / "data" / "hualien_network.graphml"
        ACCESSIBILITY_CSV_PATH = ASSIGNMENT_DIR / "accessibility_table.csv"
        README_PATH = ASSIGNMENT_DIR / "README.md"
        ROOT_ENV_PATH = PROJECT_ROOT / ".env"
        ASSIGNMENT_ENV_PATH = ASSIGNMENT_DIR / ".env"

        DEM_PATH = DATA_DIR / "DEM_tawiwan_V2025.tif"
        SHELTER_CSV_PATH = DATA_DIR / "shelters_cleaned.csv"
        TERRAIN_AUDIT_PATH = HOMEWORK4_DIR / "terrain_risk_audit.json"
        RAINFALL_RASTER_PATH = HOMEWORK6_DIR / "kriging_rainfall.tif"
        VARIANCE_RASTER_PATH = HOMEWORK6_DIR / "kriging_variance.tif"
        RAINFALL_JSON_FALLBACK = DATA_DIR / "scenarios" / "fungwong_202511.json"

        def parse_env_file(path):
            values = {}
            path = Path(path)
            if not path.exists():
                return values
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
            return values

        print(f"PROJECT_ROOT: {PROJECT_ROOT}")
        print(f"OSMnx: {ox.__version__}")
        print(f"NetworkX: {nx.__version__}")
        print(f"GeoPandas: {gpd.__version__}")
        print(f"Homework-7 data dir: {OUTPUT_DATA_DIR}")
    """

    cell_sources["# [S2] Attempt Road Network Extraction"] = """
        # [S2] Attempt Road Network Extraction
        # Prefer the local GraphML archive. Reuse the Exercise-7 cache if Homework-7 cache is not built yet.

        place_name = "Hualien City, Taiwan"
        network_type = "drive"
        dist_meters = 5000
        ox.settings.use_cache = True

        graph_source = None

        if NETWORK_GRAPHML_PATH.exists():
            G = ox.load_graphml(NETWORK_GRAPHML_PATH)
            graph_source = "homework_graphml_cache"
            print(f"Loaded cached graph: {NETWORK_GRAPHML_PATH.name}")
        elif EXERCISE7_GRAPHML_PATH.exists():
            G = ox.load_graphml(EXERCISE7_GRAPHML_PATH)
            graph_source = "exercise7_graphml_cache"
            print(f"Loaded shared cache from Exercise-7: {EXERCISE7_GRAPHML_PATH.name}")
        else:
            print(f"Attempting live road extraction for {place_name} ...")
            try:
                G = ox.graph_from_address(place_name, dist=dist_meters, network_type=network_type)
                graph_source = "live_osmnx"
                print("Road extraction succeeded from OpenStreetMap.")
            except Exception as exc:
                raise RuntimeError(
                    "Road network extraction failed and no cached GraphML was available."
                ) from exc

        print(f"Graph source: {graph_source}")
        print(f"Nodes: {G.number_of_nodes():,}")
        print(f"Edges: {G.number_of_edges():,}")
        print(f"Graph CRS: {G.graph.get('crs')}")
    """

    cell_sources["# [S8] Define rain_to_congestion Function"] = '''
        # [S8] Define rain_to_congestion Function

        DEFAULT_CONGESTION_METHOD = "adaptive_threshold"
        DEFAULT_ADAPTIVE_FACTORS = (0.10, 0.20, 0.35, 0.50)

        def rain_to_congestion(rainfall_mm, method=DEFAULT_CONGESTION_METHOD, breaks=None, factors=None):
            """
            Convert hourly rainfall to a congestion factor.

            Homework version:
            - keeps the absolute threshold option
            - adds an adaptive-threshold option based on sampled local rainfall quantiles
            """
            rainfall_mm = 0.0 if rainfall_mm is None or not math.isfinite(float(rainfall_mm)) else float(rainfall_mm)
            method = str(method).strip().lower()
            factors = DEFAULT_ADAPTIVE_FACTORS if factors is None else tuple(float(item) for item in factors)

            if method == "threshold":
                if rainfall_mm < 10:
                    cf = 0.0
                elif rainfall_mm < 40:
                    cf = 0.3
                elif rainfall_mm < 80:
                    cf = 0.6
                else:
                    cf = 0.9
            elif method == "adaptive_threshold":
                if breaks is None:
                    breaks = (0.71, 0.72, 0.74)
                b1, b2, b3 = [float(item) for item in breaks]
                cf1, cf2, cf3, cf4 = factors
                if rainfall_mm < b1:
                    cf = cf1
                elif rainfall_mm < b2:
                    cf = cf2
                elif rainfall_mm < b3:
                    cf = cf3
                else:
                    cf = cf4
            elif method == "linear":
                cf = rainfall_mm / 100.0 * 0.9
            elif method == "exponential":
                cf = 0.95 * (1 - math.exp(-rainfall_mm / 50.0))
            else:
                raise ValueError(f"Unsupported congestion method: {method}")

            return float(min(max(cf, 0.0), 0.95))

        print("Homework congestion mapping methods: threshold, adaptive_threshold, linear, exponential")
        for rain in [0.70, 0.72, 0.74, 1.00]:
            print(f"Adaptive example -> rainfall {rain:4.2f} mm/hr -> cf {rain_to_congestion(rain, method='adaptive_threshold'):.2f}")
    '''

    cell_sources["# [S10] Apply Dynamic Weights"] = '''
        # [S10] Apply Dynamic Weights

        def assign_node_rainfall_layers(G):
            rainfall_layer = {}
            variance_layer = {}

            if rainfall_dataset is not None:
                for node_id, node_data in G.nodes(data=True):
                    rainfall_mm = sample_raster_value(
                        rainfall_dataset,
                        node_data["x"],
                        node_data["y"],
                        G.graph["crs"],
                        default=np.nan,
                    )
                    variance_mm = sample_raster_value(
                        variance_dataset,
                        node_data["x"],
                        node_data["y"],
                        G.graph["crs"],
                        default=np.nan,
                    ) if variance_dataset is not None else np.nan
                    rainfall_layer[node_id] = float(max(rainfall_mm, 0.0)) if math.isfinite(rainfall_mm) else 0.0
                    variance_layer[node_id] = float(variance_mm) if math.isfinite(variance_mm) else np.nan
                return rainfall_layer, variance_layer

            if fallback_station_gdf is None or fallback_station_gdf.empty:
                raise RuntimeError("No rainfall raster or fallback station dataset was available.")

            stations_3826 = fallback_station_gdf.to_crs(G.graph["crs"]).copy()
            station_xy = np.column_stack([stations_3826.geometry.x.to_numpy(), stations_3826.geometry.y.to_numpy()])
            station_rain = stations_3826["rain_1hr"].to_numpy(dtype=float)

            for node_id, node_data in G.nodes(data=True):
                dx = station_xy[:, 0] - float(node_data["x"])
                dy = station_xy[:, 1] - float(node_data["y"])
                nearest_idx = int(np.argmin(dx * dx + dy * dy))
                rainfall_layer[node_id] = float(max(station_rain[nearest_idx], 0.0))
                variance_layer[node_id] = np.nan

            return rainfall_layer, variance_layer

        def variance_quantiles(values):
            clean = pd.Series([value for value in values if pd.notna(value)], dtype="float64")
            if clean.empty:
                return np.nan, np.nan
            return clean.quantile(0.25), clean.quantile(0.75)

        env_values = {}
        for env_path in [ASSIGNMENT_ENV_PATH, ROOT_ENV_PATH]:
            env_values.update(parse_env_file(env_path))

        congestion_method = str(env_values.get("CONGESTION_METHOD", DEFAULT_CONGESTION_METHOD)).strip().lower()
        adaptive_factors = tuple(
            float(env_values.get(key, default))
            for key, default in zip(
                ["CONGESTION_CF_1", "CONGESTION_CF_2", "CONGESTION_CF_3", "CONGESTION_CF_4"],
                DEFAULT_ADAPTIVE_FACTORS,
            )
        )

        node_rainfall_layer, node_variance_layer = assign_node_rainfall_layers(G_proj)
        variance_q1, variance_q3 = variance_quantiles(node_variance_layer.values())
        rainfall_distribution = pd.Series(list(node_rainfall_layer.values()), dtype="float64")
        adaptive_breaks = tuple(float(rainfall_distribution.quantile(q)) for q in [0.25, 0.50, 0.75])
        adaptive_breaks = (
            adaptive_breaks[0],
            max(adaptive_breaks[1], adaptive_breaks[0] + 1e-6),
            max(adaptive_breaks[2], adaptive_breaks[1] + 1e-6),
        )

        def variance_to_flag(value):
            if value is None or not pd.notna(value):
                return "UNKNOWN"
            if not pd.notna(variance_q1) or not pd.notna(variance_q3):
                return "MEDIUM"
            if float(value) >= float(variance_q3):
                return "HIGH"
            if float(value) <= float(variance_q1):
                return "LOW"
            return "MEDIUM"

        def apply_dynamic_weights(G, rainfall_layer, variance_layer, congestion_method="adaptive_threshold"):
            G_dyn = G.copy()
            for u, v, k, edge_data in G_dyn.edges(data=True, keys=True):
                rainfall_mm = float(np.nanmean([rainfall_layer.get(u, 0.0), rainfall_layer.get(v, 0.0)]))
                variance_mm = float(np.nanmean([variance_layer.get(u, np.nan), variance_layer.get(v, np.nan)]))
                congestion_factor = rain_to_congestion(
                    rainfall_mm,
                    method=congestion_method,
                    breaks=adaptive_breaks if congestion_method == "adaptive_threshold" else None,
                    factors=adaptive_factors if congestion_method == "adaptive_threshold" else None,
                )
                travel_time_normal = float(edge_data.get("travel_time_normal", edge_data.get("travel_time", 60.0)))

                if congestion_factor >= 0.95:
                    travel_time_adj = float("inf")
                else:
                    travel_time_adj = travel_time_normal / max(1e-6, 1 - congestion_factor)

                edge_data["rainfall_mm"] = rainfall_mm
                edge_data["rainfall_variance"] = variance_mm if math.isfinite(variance_mm) else np.nan
                edge_data["congestion_factor"] = congestion_factor
                edge_data["travel_time_adj"] = travel_time_adj
            return G_dyn

        G_dyn = apply_dynamic_weights(G_proj, node_rainfall_layer, node_variance_layer, congestion_method=congestion_method)

        edge_rainfall = pd.Series(
            [edge_data.get("rainfall_mm", 0.0) for _, _, _, edge_data in G_dyn.edges(data=True, keys=True)],
            dtype="float64",
        )
        congestion_series = pd.Series(
            [edge_data.get("congestion_factor", 0.0) for _, _, _, edge_data in G_dyn.edges(data=True, keys=True)],
            dtype="float64",
        )
        cf_counts = congestion_series.round(2).value_counts().sort_index()
        cf_summary = ", ".join([f"cf={index:.2f} -> {count}" for index, count in cf_counts.items()])

        print(f"Rainfall source used in dynamic weighting: {rainfall_source}")
        print(f"Congestion method: {congestion_method}")
        if congestion_method == "adaptive_threshold":
            print(
                "Adaptive rainfall breaks (mm/hr): "
                f"q25={adaptive_breaks[0]:.4f}, q50={adaptive_breaks[1]:.4f}, q75={adaptive_breaks[2]:.4f}"
            )
            print(
                "Adaptive congestion factors: "
                f"{adaptive_factors[0]:.2f}, {adaptive_factors[1]:.2f}, {adaptive_factors[2]:.2f}, {adaptive_factors[3]:.2f}"
            )
        print(
            "Edge rainfall summary (mm/hr): "
            f"min={edge_rainfall.min():.2f}, mean={edge_rainfall.mean():.2f}, max={edge_rainfall.max():.2f}"
        )
        print(f"Congestion factor counts: {cf_summary}")
        print("Dynamic travel times have been added to every edge.")
    '''

    cell_sources["# [S12] Calculate Accessibility Benefit-Cost Table"] = """
        # [S12] Calculate Accessibility Impact Table For 5 Key Facilities

        print("Captain's Log: The commander requested real facilities, not just abstract bottlenecks. Selecting 5 key shelters in Hualien City.")

        terrain_priority = {"very_high": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}

        terrain_audit = pd.DataFrame(json.loads(TERRAIN_AUDIT_PATH.read_text(encoding="utf-8")))
        terrain_audit["shelter_id"] = terrain_audit["shelter_id"].astype(str).str.strip()

        shelters_raw = pd.read_csv(SHELTER_CSV_PATH, encoding="utf-8")
        shelters_raw["shelter_id"] = shelters_raw.iloc[:, 0].astype(str).str.strip()
        shelters_raw["county_town"] = shelters_raw.iloc[:, 1].fillna("").astype(str).str.strip()
        shelters_raw["longitude"] = pd.to_numeric(shelters_raw.iloc[:, 4], errors="coerce")
        shelters_raw["latitude"] = pd.to_numeric(shelters_raw.iloc[:, 5], errors="coerce")
        shelters_raw["name"] = shelters_raw.iloc[:, 6].fillna("").astype(str).str.strip()
        shelters_raw["capacity"] = pd.to_numeric(shelters_raw.iloc[:, 8], errors="coerce")

        city_mask = shelters_raw["county_town"].str.contains("花蓮縣花蓮市", regex=False)
        city_shelters = shelters_raw.loc[city_mask].copy()
        city_shelters = city_shelters.merge(
            terrain_audit[
                [
                    "shelter_id",
                    "distance_to_river_m",
                    "river_distance_category",
                    "mean_elevation",
                    "std_elevation",
                    "max_slope",
                    "risk_level",
                ]
            ],
            on="shelter_id",
            how="left",
        )
        city_shelters["terrain_risk"] = city_shelters["risk_level"].fillna("unknown").astype(str).str.lower()
        city_shelters["_terrain_score"] = city_shelters["terrain_risk"].map(terrain_priority).fillna(0)

        required_facilities = city_shelters.sort_values(
            by=["capacity", "_terrain_score", "max_slope"],
            ascending=[False, False, False],
        ).head(5).copy()

        required_facilities_gdf = gpd.GeoDataFrame(
            required_facilities,
            geometry=gpd.points_from_xy(required_facilities["longitude"], required_facilities["latitude"]),
            crs="EPSG:4326",
        ).to_crs(G_proj.graph["crs"])

        required_facilities_gdf["nearest_node"] = ox.distance.nearest_nodes(
            G_proj,
            required_facilities_gdf.geometry.x.to_numpy(),
            required_facilities_gdf.geometry.y.to_numpy(),
        )
        required_facilities_gdf["rainfall_mm"] = required_facilities_gdf["nearest_node"].map(node_rainfall_layer).astype(float)
        required_facilities_gdf["rainfall_variance"] = required_facilities_gdf["nearest_node"].map(node_variance_layer)
        required_facilities_gdf["uncertainty_flag"] = required_facilities_gdf["rainfall_variance"].map(variance_to_flag)
        required_facilities_gdf["centrality"] = required_facilities_gdf["nearest_node"].map(centrality).fillna(0.0)

        required_records = []
        for row in required_facilities_gdf.itertuples():
            summary = summarize_accessibility(G_dyn, int(row.nearest_node), 5 * 60, 10 * 60)
            required_records.append(
                {
                    "analysis_level": "required",
                    "facility_type": "shelter",
                    "facility_id": str(row.shelter_id),
                    "name": row.name,
                    "capacity": float(row.capacity) if pd.notna(row.capacity) else np.nan,
                    "terrain_risk": row.terrain_risk,
                    "nearest_node": int(row.nearest_node),
                    "rainfall_mm": round(float(row.rainfall_mm), 2),
                    "rainfall_variance": round(float(row.rainfall_variance), 4) if pd.notna(row.rainfall_variance) else np.nan,
                    "uncertainty_flag": row.uncertainty_flag,
                    "centrality": round(float(row.centrality), 6),
                    "short_minutes": 5.0,
                    "long_minutes": 10.0,
                    "distance_to_river_m": float(row.distance_to_river_m) if pd.notna(row.distance_to_river_m) else np.nan,
                    "mean_elevation": float(row.mean_elevation) if pd.notna(row.mean_elevation) else np.nan,
                    "max_slope": float(row.max_slope) if pd.notna(row.max_slope) else np.nan,
                    **summary,
                }
            )

        required_accessibility_table = pd.DataFrame(required_records)
        required_accessibility_table = required_accessibility_table.sort_values(
            by=["short_loss_pct", "long_loss_pct", "capacity", "centrality"],
            ascending=[False, False, False, False],
        ).reset_index(drop=True)
        required_accessibility_table["priority_rank"] = np.arange(1, len(required_accessibility_table) + 1)

        isolated_mask = (required_accessibility_table["short_loss_pct"] >= 50.0) | (required_accessibility_table["long_loss_pct"] >= 50.0)
        isolated_facilities = required_accessibility_table.loc[isolated_mask, "name"].astype(str).tolist()

        accessibility_table = required_accessibility_table.copy()
        accessibility_table["scenario_name"] = "required_baseline"
        accessibility_table.to_csv(ACCESSIBILITY_CSV_PATH, index=False, encoding="utf-8-sig")

        print("Required layer accessibility table (5 key facilities):")
        display(
            required_accessibility_table[
                [
                    "priority_rank",
                    "facility_id",
                    "name",
                    "capacity",
                    "terrain_risk",
                    "pre_short_km2",
                    "post_short_km2",
                    "short_loss_pct",
                    "pre_long_km2",
                    "post_long_km2",
                    "long_loss_pct",
                    "uncertainty_flag",
                ]
            ]
        )
        print(f"Observed isolated facilities: {isolated_facilities if isolated_facilities else 'none'}")
        print(f"Saved required-layer accessibility table to: {ACCESSIBILITY_CSV_PATH}")
    """

    cell_sources["# [S13] Visualize Isochrone Comparison"] = """
        # [S13] Visualize Isochrone Comparison (Homework Required Layer)

        required_focus = required_accessibility_table.iloc[0]
        focus_row = required_facilities_gdf.loc[
            required_facilities_gdf["shelter_id"].astype(str) == str(required_focus["facility_id"])
        ].iloc[0]
        focus_node = int(required_focus["nearest_node"])
        short_seconds = int(required_focus["short_seconds"])
        long_seconds = int(required_focus["long_seconds"])

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        plot_configs = [
            (axes[0], "travel_time", "Pre-disaster shelter isochrone"),
            (axes[1], "travel_time_adj", "Post-disaster shelter isochrone"),
        ]

        for ax, weight_attr, title in plot_configs:
            ox.plot_graph(
                G_proj,
                ax=ax,
                node_size=5,
                node_color="lightgray",
                edge_color="gray",
                edge_linewidth=0.5,
                show=False,
                close=False,
            )
            reachable_short, _ = compute_isochrone(G_dyn, focus_node, weight_attr, short_seconds)
            reachable_long, _ = compute_isochrone(G_dyn, focus_node, weight_attr, long_seconds)
            poly_long, area_long = nodes_to_polygon(G_dyn, reachable_long)
            poly_short, area_short = nodes_to_polygon(G_dyn, reachable_short)

            if poly_long is not None:
                x_long, y_long = poly_long.exterior.xy
                ax.fill(x_long, y_long, alpha=0.20, color="royalblue", label=f"10 min ({area_long/1e6:.2f} km$^2$)")
            if poly_short is not None:
                x_short, y_short = poly_short.exterior.xy
                ax.fill(x_short, y_short, alpha=0.35, color="tomato", label=f"5 min ({area_short/1e6:.2f} km$^2$)")

            ax.scatter(
                [focus_row.geometry.x],
                [focus_row.geometry.y],
                s=120,
                color="gold",
                edgecolors="black",
                marker="*",
                label=focus_row["name"],
                zorder=10,
            )
            ax.set_title(title, fontsize=13, fontweight="bold")
            ax.legend(loc="lower right")

        plt.suptitle(
            f"Homework Layer: Key Facility {focus_row['name']} Before / After Accessibility",
            fontsize=15,
            fontweight="bold",
        )
        plt.tight_layout()
        plt.show()
        print("Required-layer isochrone comparison rendered.")
    """

    cell_sources["# [S17] Generate AI Strategic Report"] = '''
        # [S17] Generate AI Strategic Report

        top_5_info = "\\n".join(
            [
                f"#{rank}: node {node_id}, centrality={cent_val:.4f}"
                for rank, (node_id, cent_val) in enumerate(top_5_nodes, start=1)
            ]
        )
        required_prompt_table = required_accessibility_table[
            [
                "priority_rank",
                "name",
                "capacity",
                "terrain_risk",
                "short_loss_pct",
                "long_loss_pct",
                "uncertainty_flag",
            ]
        ].to_string(index=False)

        isolated_facility_text = ", ".join(isolated_facilities) if isolated_facilities else "None observed under the real Week 6 rainfall field."

        required_ai_prompt = f"""
        You are a transportation advisor at Hualien County Disaster Prevention Command Center.

        Event:
        {EVENT_LABEL}

        Top 5 Bottleneck Nodes:
        {top_5_info}

        Accessibility Impact Table:
        {required_prompt_table}

        Isolated Facilities:
        {isolated_facility_text}

        In professional disaster-prevention language, please provide:
        1. Priority road segments to clear, with reasoning.
        2. Alternative rescue methods for isolated areas.
        3. Resource allocation recommendations.
        """

        required_ai_report_text, required_ai_status = call_gemini_report(required_ai_prompt, "Required layer AI report")
        print(required_ai_status)
        if required_ai_report_text:
            print("\\nRequired layer AI report:")
            print(required_ai_report_text)
        else:
            print("\\nAI report was skipped. The notebook remains fully valid without it.")
    '''

    cell_sources["# [S14] .env Configuration Example"] = '''
        # [S14] .env Configuration Example

        env_example = """
        # Week 7 network analysis
        NETWORK_DIST=5000
        NETWORK_CRS=EPSG:3826
        CONGESTION_METHOD=adaptive_threshold
        CONGESTION_CF_1=0.10
        CONGESTION_CF_2=0.20
        CONGESTION_CF_3=0.35
        CONGESTION_CF_4=0.50

        # Rainfall inputs
        RAINFALL_SOURCE=week6_kriging
        RAINFALL_RASTER_PATH=submission/Homework-6/kriging_rainfall.tif
        RAINFALL_VARIANCE_PATH=submission/Homework-6/kriging_variance.tif
        RAINFALL_JSON_FALLBACK=data/scenarios/fungwong_202511.json

        # Optional AI settings
        GEMINI_API_KEY=
        GEMINI_MODEL=gemini-flash-lite-latest
        """.strip()

        env_example_path = ASSIGNMENT_DIR / ".env.example"
        env_example_path.write_text(env_example + "\\n", encoding="utf-8")

        print("Recommended .env configuration:")
        print(env_example.strip())
        print(f"Saved .env example to: {env_example_path}")
    '''

    cell_sources["# [S16] Prepare AI Tool Invocation"] = '''
        # [S16] Prepare AI Tool Invocation

        env_values = {}
        for env_path in [ASSIGNMENT_ENV_PATH, ROOT_ENV_PATH]:
            env_values.update(parse_env_file(env_path))

        GEMINI_API_KEY = env_values.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        GEMINI_MODEL = env_values.get("GEMINI_MODEL", "gemini-flash-lite-latest")
        gemini_client = None
        legacy_genai = None
        gemini_backend = None
        gemini_ready = False
        gemini_status = []
        gemini_model_candidates = []

        def extract_text_from_response(response):
            text = getattr(response, "text", "")
            if text and str(text).strip():
                return str(text).strip()

            parts = []
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", []) or []:
                    part_text = getattr(part, "text", "")
                    if part_text:
                        parts.append(str(part_text))
            return "\\n".join(parts).strip()

        def build_model_candidates(primary_model):
            ordered = []
            for model_name in [primary_model, "gemini-flash-lite-latest", "gemini-2.5-flash"]:
                normalized = str(model_name).strip()
                if normalized and normalized not in ordered:
                    ordered.append(normalized)
            return ordered

        gemini_model_candidates = build_model_candidates(GEMINI_MODEL)

        if GEMINI_API_KEY:
            try:
                from google import genai as google_genai
                gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
                gemini_backend = "google.genai"
                gemini_ready = True
                gemini_status.append(
                    f"Gemini configured with google.genai and models {', '.join(gemini_model_candidates)}."
                )
            except Exception as exc:
                gemini_status.append(f"google.genai setup failed: {exc}")

        if not gemini_ready and GEMINI_API_KEY:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=GEMINI_API_KEY)
                gemini_backend = "google.generativeai"
                gemini_ready = True
                gemini_status.append(
                    f"Fallback Gemini configured with deprecated google.generativeai and models {', '.join(gemini_model_candidates)}."
                )
            except Exception as exc:
                gemini_status.append(f"google.generativeai fallback setup failed: {exc}")

        if not GEMINI_API_KEY:
            gemini_status.append("No GEMINI_API_KEY was found. AI generation will be skipped.")

        def call_gemini_report(prompt, label):
            if not gemini_ready:
                return None, f"{label}: skipped because Gemini is not configured."
            errors = []
            try:
                for model_name in gemini_model_candidates:
                    try:
                        if gemini_backend == "google.genai":
                            response = gemini_client.models.generate_content(model=model_name, contents=prompt)
                            text = extract_text_from_response(response)
                        elif gemini_backend == "google.generativeai":
                            model = legacy_genai.GenerativeModel(model_name)
                            response = model.generate_content(prompt)
                            text = getattr(response, "text", "").strip()
                        else:
                            return None, f"{label}: no supported Gemini backend is available."

                        if text:
                            return text, f"{label}: generated successfully via {gemini_backend} using {model_name}."
                        errors.append(f"{model_name}: empty response")
                    except Exception as exc:
                        errors.append(f"{model_name}: {exc}")
                return None, f"{label}: generation failed via {gemini_backend} -> {' | '.join(errors)}"
            except Exception as exc:
                return None, f"{label}: generation failed via {gemini_backend} -> {exc}"

        print("AI preparation status:")
        for item in gemini_status:
            print(f"- {item}")
    '''

    cell_sources["# [S18] Generate README.md Framework"] = """
        # [S18] Generate README.md

        def format_top_rows(frame, columns, top_n=5):
            if frame is None or len(frame) == 0:
                return "No rows available."
            subset = frame.loc[:, columns].head(top_n).copy()
            return subset.to_string(index=False)

        def format_stretch_summary(stretch_table):
            if stretch_table is None or len(stretch_table) == 0:
                return "No stretch rows available."
            columns = ["scenario_name", "facility_id", "name", "capacity", "short_loss_pct", "long_loss_pct", "uncertainty_flag", "priority_rank"]
            available_columns = [column for column in columns if column in stretch_table.columns]
            sections = []
            if "scenario_name" in stretch_table.columns:
                for scenario_name in ["observed", "stress_test"]:
                    scenario_rows = stretch_table.loc[stretch_table["scenario_name"] == scenario_name]
                    if len(scenario_rows) == 0:
                        continue
                    sections.append(f"Scenario: {scenario_name}")
                    sections.append(scenario_rows.loc[:, available_columns].head(min(5, len(scenario_rows))).to_string(index=False))
            else:
                sections.append(stretch_table.loc[:, available_columns].head(min(5, len(stretch_table))).to_string(index=False))
            return "\\n\\n".join(sections)

        def write_final_readme(required_table, stretch_table=None, required_ai_text=None, stretch_ai_text=None):
            stretch_ready = stretch_table is not None and len(stretch_table) > 0
            lines = [
                "# Homework Week 7 - ARIA v4.0",
                "",
                "## Assignment Completion",
                "",
                "- Road network extraction / archive: completed",
                "- Graph projection to EPSG:3826: completed",
                "- Travel-time baseline from road length and speed: completed",
                "- Betweenness centrality and Top 5 bottlenecks: completed",
                "- Week 4 terrain-risk overlay: completed",
                "- Dynamic accessibility analysis using Week 6 kriging rainfall: completed",
                "- Accessibility impact table for 5 key shelters: completed",
                "- Before/after isochrone visualization: completed",
                "- GraphML export and .env example: completed",
                "",
                "### Required Layer Summary",
                "",
                "```text",
                format_top_rows(required_table, ["priority_rank", "facility_id", "name", "capacity", "short_loss_pct", "long_loss_pct", "uncertainty_flag"], top_n=min(5, len(required_table))),
                "```",
                "",
            ]

            if stretch_ready:
                lines.extend(
                    [
                        "## Stretch Enhancements",
                        "",
                        "- Added shelter-level coverage for all Hualien City shelters.",
                        "- Preserved the observed Week 6 result and added a stress-test contingency scenario.",
                        "- Used rainfall uncertainty from the kriging variance raster.",
                        "",
                        "### Stretch Layer Summary",
                        "",
                        "```text",
                        format_stretch_summary(stretch_table),
                        "```",
                        "",
                    ]
                )

            lines.extend(
                [
                    "## Data Sources",
                    "",
                    f"- Road network: OpenStreetMap / OSMnx ({place_name})",
                    f"- Shelters: {SHELTER_CSV_PATH.name}",
                    f"- Terrain context: {DEM_PATH.name} + Week 4 terrain audit",
                    f"- Rainfall source: {rainfall_source}",
                    f"- Rainfall variance source: {VARIANCE_RASTER_PATH.name if VARIANCE_RASTER_PATH.exists() else 'N/A'}",
                    "",
                    "## Captain's Log",
                    "",
                    "- Part A secured a reusable road graph so the analysis does not depend on repeated live downloads.",
                    "- Part B identified transport bottlenecks before applying any hazard effect.",
                    "- Part C shifted the analysis from static road geometry to disaster-era accessibility loss for real shelters.",
                    "- The stretch section extends the worksheet answer with a contingency scenario for command planning.",
                    "",
                    "## AI Diagnostic Log",
                    "",
                    "- Missing road speed attributes were handled by parsing maxspeed when available, then falling back to highway-type defaults and a final 40 km/h default.",
                    "- OSMnx fetch instability was mitigated by reading archived GraphML first and reusing the Exercise-7 cache if Homework-7 had not built its own cache yet.",
                    "- Homework-7 uses an adaptive-threshold congestion mapping derived from the sampled Hualien City rainfall distribution so the observed layer still produces measurable before/after accessibility differences.",
                    "",
                    "### Required AI Report",
                    "",
                    required_ai_text or "Skipped / unavailable",
                    "",
                    "### Stretch AI Report",
                    "",
                    stretch_ai_text or ("Pending stretch execution" if not stretch_ready else "Skipped / unavailable"),
                    "",
                    "## Deliverables",
                    "",
                    "- [x] ARIA_v4.ipynb",
                    f"- [x] {NETWORK_GRAPHML_PATH.relative_to(ASSIGNMENT_DIR)}",
                    f"- [x] {ACCESSIBILITY_CSV_PATH.name}",
                    f"- [x] {README_PATH.name}",
                    "",
                ]
            )
            README_PATH.write_text("\\n".join(lines).strip() + "\\n", encoding="utf-8")
            return README_PATH

        readme_path = write_final_readme(required_accessibility_table, required_ai_text=required_ai_report_text)
        print(f"README written to: {readme_path}")
    """

    for marker, code in cell_sources.items():
        base.set_code_cell(notebook, marker, code)

    replace_markdown_cell(
        notebook,
        "# Week 7 Assignment: ARIA v4.0 (The Accessible Auditor)",
        """
        # Homework Week 7: ARIA v4.0 (The Accessible Auditor)

        Captain's Log: The mission is to determine not only where the network is weak, but which critical facilities risk becoming isolated when disaster travel times collapse.
        """,
        base,
    )
    replace_markdown_cell(
        notebook,
        "## Part 0: Environment Setup",
        """
        ## Part 0: Environment Setup

        Captain's Log: Confirm the workspace, data paths, and analysis libraries before we push the road network into disaster mode.
        """,
        base,
    )
    replace_markdown_cell(
        notebook,
        "## Part A: Road Network Extraction & Travel Time Calculation",
        """
        ## Part A: Road Network Extraction & Travel Time Calculation

        Captain's Log: Secure a reproducible Hualien road graph, project it into meter coordinates, and build the baseline travel-time model.
        """,
        base,
    )
    replace_markdown_cell(
        notebook,
        "## Part B: Bottleneck & Risk Assessment",
        """
        ## Part B: Bottleneck & Risk Assessment

        Captain's Log: Identify the intersections the commander cannot afford to lose, then check whether terrain risk makes them even more fragile.
        """,
        base,
    )
    replace_markdown_cell(
        notebook,
        "## Part C: Dynamic Accessibility Analysis",
        """
        ## Part C: Dynamic Accessibility Analysis

        Captain's Log: Convert rainfall into degraded travel-time conditions and measure how fast access shrinks for key shelters.

        Note: Observed rainfall sampled from the Week 6 raster is very low over Hualien City, so this homework uses a more sensitive adaptive threshold to reveal relative accessibility differences under low-intensity rainfall. This is a sensitivity setting for analysis, not a claim that rainfall reached severe flood thresholds.
        """,
        base,
    )
    replace_markdown_cell(
        notebook,
        "## Part D: Visualization (Before & After Comparison)",
        """
        ## Part D: Visualization (Before & After Comparison)

        Captain's Log: Show the commander a direct before/after comparison for a key facility instead of leaving the result buried in a table.
        """,
        base,
    )
    replace_markdown_cell(
        notebook,
        "## Part E: Professional Standards (Infrastructure First)",
        """
        ## Part E: Professional Standards (Infrastructure First)

        Captain's Log: Archive the graph, document the environment, and leave a rerunnable notebook instead of a one-off demo.
        """,
        base,
    )
    replace_markdown_cell(
        notebook,
        "## Part F: AI Strategic Report (Optional, Bonus)",
        """
        ## Part F: AI Strategic Report (Optional, Bonus)

        Captain's Log: Hand the analysis to an AI advisor only after the numerical evidence is stable enough to defend.
        """,
        base,
    )

    if base.STRETCH_CELLS:
        base.insert_cells_after_marker(notebook, "# [S18]", list(base.STRETCH_CELLS))

    OUTPUT_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Notebook generated at: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
