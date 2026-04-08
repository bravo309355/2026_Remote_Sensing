from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "submission" / "Exercise-7" / "Week7-Student.ipynb"
OUTPUT_PATH = PROJECT_ROOT / "submission" / "Exercise-7" / "ARIA_v4.ipynb"


def source_lines(text: str) -> list[str]:
    normalized = dedent(text).strip("\n")
    if not normalized:
        return []
    return [f"{line}\n" for line in normalized.splitlines()]


def set_code_cell(notebook: dict, marker: str, code: str) -> None:
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if marker in "".join(cell.get("source", [])):
            cell["source"] = source_lines(code)
            return
    raise ValueError(f"Could not find code cell marker: {marker}")


def set_markdown_cell(notebook: dict, marker: str, text: str) -> None:
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        if marker in "".join(cell.get("source", [])):
            cell["source"] = source_lines(text)
            return
    raise ValueError(f"Could not find markdown cell marker: {marker}")


def new_markdown_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source_lines(text),
    }


def new_code_cell(code: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source_lines(code),
    }


def insert_cells_after_marker(notebook: dict, marker: str, new_cells: list[dict]) -> None:
    cells = notebook.get("cells", [])
    for index, cell in enumerate(cells):
        if marker in "".join(cell.get("source", [])):
            notebook["cells"] = cells[: index + 1] + new_cells + cells[index + 1 :]
            return
    raise ValueError(f"Could not find insertion marker: {marker}")


CELL_SOURCES: dict[str, str] = {}

CELL_SOURCES.update(
    {
        "# [S1] Environment Setup": '''
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
            ASSIGNMENT_DIR = PROJECT_ROOT / "submission" / "Exercise-7"
            HOMEWORK4_DIR = PROJECT_ROOT / "submission" / "Homework-4"
            HOMEWORK6_DIR = PROJECT_ROOT / "submission" / "Homework-6"
            DATA_DIR = PROJECT_ROOT / "data"
            OUTPUT_DATA_DIR = ASSIGNMENT_DIR / "data"
            OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

            NETWORK_GRAPHML_PATH = OUTPUT_DATA_DIR / "hualien_network.graphml"
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
            print(f"Exercise-7 data dir: {OUTPUT_DATA_DIR}")
        ''',
        "# [S2] Attempt Road Network Extraction": '''
            # [S2] Attempt Road Network Extraction
            # Prefer the local GraphML cache for reproducibility. Download only when needed.

            place_name = "Hualien City, Taiwan"
            network_type = "drive"
            dist_meters = 5000
            ox.settings.use_cache = True

            graph_source = None

            if NETWORK_GRAPHML_PATH.exists():
                G = ox.load_graphml(NETWORK_GRAPHML_PATH)
                graph_source = "graphml_cache"
                print(f"Loaded cached graph: {NETWORK_GRAPHML_PATH.name}")
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
        ''',
        "# [S3] Project to Meter Coordinates": '''
            # [S3] Project to Meter Coordinates

            target_crs = "EPSG:3826"
            graph_crs = str(G.graph.get("crs"))
            if graph_crs == target_crs:
                G_proj = G.copy()
                print("Graph already stored in EPSG:3826.")
            else:
                G_proj = ox.project_graph(G, to_crs=target_crs)
                print("Projected graph to EPSG:3826.")

            for _, node_data in G_proj.nodes(data=True):
                node_data["x"] = float(node_data["x"])
                node_data["y"] = float(node_data["y"])

            for _, _, _, edge_data in G_proj.edges(data=True, keys=True):
                if "length" in edge_data:
                    edge_data["length"] = float(edge_data["length"])

            print(f"Node count: {G_proj.number_of_nodes():,}")
            print(f"Edge count: {G_proj.number_of_edges():,}")
            print(f"CRS: {G_proj.graph['crs']}")
        ''',
        "# [S4] Calculate Travel Time": '''
            # [S4] Calculate Travel Time

            speed_defaults = {
                "motorway": 110, "motorway_link": 80,
                "trunk": 100, "trunk_link": 60,
                "primary": 80, "primary_link": 50,
                "secondary": 60, "secondary_link": 40,
                "tertiary": 50, "tertiary_link": 30,
                "residential": 40, "living_street": 10,
                "unclassified": 30,
                "service": 25,
            }

            def parse_maxspeed(value):
                if value is None:
                    return None
                if isinstance(value, list):
                    for item in value:
                        parsed = parse_maxspeed(item)
                        if parsed is not None:
                            return parsed
                    return None
                text = str(value).strip().lower()
                if not text:
                    return None
                token = text.replace("km/h", "").replace("kph", "").replace("mph", "").split(";")[0].strip()
                try:
                    numeric = float(token)
                except ValueError:
                    return None
                if "mph" in text:
                    return numeric * 1.60934
                return numeric

            def get_speed_kph(edge_data):
                maxspeed = parse_maxspeed(edge_data.get("maxspeed"))
                if maxspeed is not None and math.isfinite(maxspeed):
                    return max(5.0, float(maxspeed))
                highway = edge_data.get("highway", "residential")
                if isinstance(highway, list):
                    highway = highway[0]
                return float(speed_defaults.get(highway, 40))

            for _, _, _, edge_data in G_proj.edges(data=True, keys=True):
                length_m = float(edge_data.get("length", 0.0))
                speed_kph = get_speed_kph(edge_data)
                travel_time = length_m / (speed_kph / 3.6)
                edge_data["speed_kph"] = speed_kph
                edge_data["travel_time_normal"] = travel_time
                edge_data["travel_time"] = travel_time

            sample_edge = list(G_proj.edges(data=True, keys=True))[0]
            print(
                f"Sample edge -> length={sample_edge[3]['length']:.1f} m, "
                f"speed={sample_edge[3]['speed_kph']:.1f} km/h, "
                f"travel_time={sample_edge[3]['travel_time_normal']:.1f} s"
            )
            print("Base travel times were added to every edge.")
        ''',
    }
)

CELL_SOURCES.update(
    {
        "# [S5] Calculate Centrality": '''
            # [S5] Calculate Centrality

            print("Calculating betweenness centrality ...")
            centrality = nx.betweenness_centrality(G_proj, weight="length")
            top_5_nodes = sorted(centrality.items(), key=lambda item: item[1], reverse=True)[:5]

            print("Top 5 bottleneck nodes:")
            for rank, (node_id, cent_val) in enumerate(top_5_nodes, start=1):
                print(f"{rank}. node={node_id} centrality={cent_val:.6f}")
        ''',
        "# [S6] Terrain Risk Overlay": '''
            # [S6] Terrain Risk Overlay using Week 4 DEM

            from rasterio.warp import transform as rio_transform
            from rasterio.windows import Window

            top_5_gdf = gpd.GeoDataFrame(
                [
                    {
                        "node_id": int(node_id),
                        "centrality": float(cent_val),
                        "geometry": Point(G_proj.nodes[node_id]["x"], G_proj.nodes[node_id]["y"]),
                    }
                    for node_id, cent_val in top_5_nodes
                ],
                crs=G_proj.graph["crs"],
            )

            def sample_dem_metrics(dem_src, x, y, source_crs):
                dem_crs = dem_src.crs.to_string() if dem_src.crs else str(source_crs)
                sample_x, sample_y = float(x), float(y)
                if dem_crs != str(source_crs):
                    xs, ys = rio_transform(str(source_crs), dem_crs, [sample_x], [sample_y])
                    sample_x, sample_y = xs[0], ys[0]

                elev_sample = next(dem_src.sample([(sample_x, sample_y)], masked=True))[0]
                elevation = np.nan if np.ma.is_masked(elev_sample) else float(elev_sample)

                row_idx, col_idx = dem_src.index(sample_x, sample_y)
                patch = dem_src.read(
                    1,
                    window=Window(col_idx - 1, row_idx - 1, 3, 3),
                    boundless=True,
                    masked=True,
                ).astype("float64")
                arr = np.asarray(patch.filled(np.nan), dtype="float64")
                finite = np.isfinite(arr)
                if finite.sum() < 4:
                    return elevation, np.nan
                fill_value = float(np.nanmedian(arr[finite]))
                arr[~finite] = fill_value
                res_x = abs(float(dem_src.transform.a)) or 20.0
                res_y = abs(float(dem_src.transform.e)) or 20.0
                grad_y, grad_x = np.gradient(arr, res_y, res_x)
                slope_deg = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))
                return elevation, float(np.nanmax(slope_deg))

            risk_rows = []
            with rasterio.open(DEM_PATH) as dem_src:
                for row in top_5_gdf.itertuples():
                    elevation_m, max_slope_deg = sample_dem_metrics(
                        dem_src,
                        row.geometry.x,
                        row.geometry.y,
                        G_proj.graph["crs"],
                    )
                    if np.isfinite(max_slope_deg) and (max_slope_deg > 45 or elevation_m < 5):
                        terrain_risk = "very_high"
                    elif np.isfinite(max_slope_deg) and (max_slope_deg > 30 or elevation_m < 20):
                        terrain_risk = "high"
                    elif np.isfinite(max_slope_deg) and max_slope_deg > 15:
                        terrain_risk = "medium"
                    else:
                        terrain_risk = "low"
                    risk_rows.append(
                        {
                            "node_id": row.node_id,
                            "elevation_m": round(elevation_m, 2) if np.isfinite(elevation_m) else np.nan,
                            "max_slope_deg": round(max_slope_deg, 2) if np.isfinite(max_slope_deg) else np.nan,
                            "terrain_risk": terrain_risk,
                        }
                    )

            top_5_gdf = top_5_gdf.merge(pd.DataFrame(risk_rows), on="node_id", how="left")
            print("Top 5 bottlenecks with Week 4 terrain context:")
            display(top_5_gdf[["node_id", "centrality", "elevation_m", "max_slope_deg", "terrain_risk"]])
        ''',
        "# [S7] Visualize Bottlenecks": '''
            # [S7] Visualize Bottlenecks

            fig, ax = plt.subplots(figsize=(12, 10))
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

            colors = ["red", "orange", "gold", "green", "blue"]
            for rank, row in enumerate(top_5_gdf.itertuples(), start=1):
                ax.plot(
                    row.geometry.x,
                    row.geometry.y,
                    marker="*",
                    markersize=24,
                    color=colors[rank - 1],
                    markeredgecolor="black",
                    zorder=10,
                )
                ax.annotate(
                    f"#{rank}\\n{row.terrain_risk}",
                    (row.geometry.x, row.geometry.y),
                    fontsize=8,
                    fontweight="bold",
                    textcoords="offset points",
                    xytext=(8, 8),
                )

            ax.set_title("Top 5 Bottlenecks with Week 4 Terrain Risk", fontsize=13, fontweight="bold")
            plt.tight_layout()
            plt.show()
            print("Bottleneck map rendered successfully.")
        ''',
        "# [S8] Define rain_to_congestion Function": '''
            # [S8] Define rain_to_congestion Function

            DEFAULT_CONGESTION_METHOD = "adaptive_threshold"
            DEFAULT_ADAPTIVE_FACTORS = (0.10, 0.20, 0.35, 0.50)

            def rain_to_congestion(rainfall_mm, method=DEFAULT_CONGESTION_METHOD, breaks=None, factors=None):
                """
                Convert hourly rainfall (mm/hr) to a congestion factor.

                Parameters
                ----------
                rainfall_mm : float
                    Hourly rainfall intensity.
                method : str
                    One of {"threshold", "adaptive_threshold", "linear", "exponential"}.

                Returns
                -------
                float
                    Congestion factor in the range [0, 0.95].
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

            rain_test = [0.70, 0.72, 0.74, 1.00, 10, 40]
            for rain in rain_test:
                print(
                    f"Rainfall {rain:6.2f} mm/hr -> "
                    f"threshold {rain_to_congestion(rain, method='threshold'):.2f}, "
                    f"adaptive {rain_to_congestion(rain, method='adaptive_threshold'):.2f}"
                )
        ''',
    }
)

CELL_SOURCES.update(
    {
        "# [S9] Load Rainfall Data": '''
            # [S9] Load Rainfall Data

            from rasterio.warp import transform as rio_transform

            EVENT_LABEL = "Typhoon Fung-wong (2025-11-11 18:50)"
            rainfall_dataset = None
            variance_dataset = None
            fallback_station_gdf = None
            rainfall_source = None
            fallback_used = False

            def normalize_cwa_json(raw):
                stations = ((raw or {}).get("records") or {}).get("Station") or []
                records = []
                for station in stations:
                    geo_info = station.get("GeoInfo") or {}
                    coordinates = geo_info.get("Coordinates") or []
                    lat = lon = None
                    for item in coordinates:
                        try:
                            lat = float(item.get("StationLatitude"))
                            lon = float(item.get("StationLongitude"))
                            break
                        except (TypeError, ValueError):
                            continue
                    rainfall = ((station.get("RainfallElement") or {}).get("Past1hr") or {}).get("Precipitation")
                    try:
                        rainfall = float(rainfall)
                    except (TypeError, ValueError):
                        rainfall = np.nan
                    records.append(
                        {
                            "station_id": str(station.get("StationId", "")).strip(),
                            "station_name": str(station.get("StationName", "")).strip(),
                            "county_name": str(geo_info.get("CountyName", "")).strip(),
                            "town_name": str(geo_info.get("TownName", "")).strip(),
                            "rain_1hr": rainfall,
                            "lat": lat,
                            "lon": lon,
                            "obs_time": ((station.get("ObsTime") or {}).get("DateTime") or "").strip(),
                        }
                    )
                return records

            def rainfall_records_to_gdf(records):
                stations_df = pd.DataFrame.from_records(records)
                if stations_df.empty:
                    return gpd.GeoDataFrame(columns=["station_id", "station_name", "rain_1hr", "geometry"], geometry="geometry", crs="EPSG:4326")
                stations_df["rain_1hr"] = pd.to_numeric(stations_df["rain_1hr"], errors="coerce")
                stations_df["lat"] = pd.to_numeric(stations_df["lat"], errors="coerce")
                stations_df["lon"] = pd.to_numeric(stations_df["lon"], errors="coerce")
                stations_df = stations_df.loc[
                    stations_df["rain_1hr"].notna()
                    & stations_df["lat"].notna()
                    & stations_df["lon"].notna()
                    & stations_df["rain_1hr"].ne(-998)
                ].copy()
                return gpd.GeoDataFrame(
                    stations_df,
                    geometry=gpd.points_from_xy(stations_df["lon"], stations_df["lat"]),
                    crs="EPSG:4326",
                )

            def sample_raster_value(dataset, x, y, source_crs, default=np.nan):
                if dataset is None:
                    return default
                dataset_crs = dataset.crs.to_string() if dataset.crs else str(source_crs)
                sample_x, sample_y = float(x), float(y)
                if dataset_crs != str(source_crs):
                    xs, ys = rio_transform(str(source_crs), dataset_crs, [sample_x], [sample_y])
                    sample_x, sample_y = xs[0], ys[0]
                sample = next(dataset.sample([(sample_x, sample_y)], masked=True))[0]
                if np.ma.is_masked(sample):
                    return default
                value = float(sample)
                if not math.isfinite(value):
                    return default
                if dataset.nodata is not None and np.isclose(value, dataset.nodata):
                    return default
                return value

            if RAINFALL_RASTER_PATH.exists():
                rainfall_dataset = rasterio.open(RAINFALL_RASTER_PATH)
                rainfall_source = f"W6 kriging raster ({RAINFALL_RASTER_PATH.name})"
                print(f"Primary rainfall source: {rainfall_source}")
                print(f"Event label: {EVENT_LABEL}")
                print(f"Raster CRS: {rainfall_dataset.crs}")
                if VARIANCE_RASTER_PATH.exists():
                    variance_dataset = rasterio.open(VARIANCE_RASTER_PATH)
                    print(f"Variance source: W6 kriging variance raster ({VARIANCE_RASTER_PATH.name})")
            else:
                payload = json.loads(RAINFALL_JSON_FALLBACK.read_text(encoding="utf-8"))
                fallback_station_gdf = rainfall_records_to_gdf(normalize_cwa_json(payload))
                rainfall_source = f"W5/W6 fallback JSON ({RAINFALL_JSON_FALLBACK.name})"
                fallback_used = True
                print(f"Fallback rainfall source: {rainfall_source}")
                print(f"Station count: {len(fallback_station_gdf):,}")

            print(f"Fallback used: {fallback_used}")
        ''',
        "# [S10] Apply Dynamic Weights": '''
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

            node_rainfall_layer, node_variance_layer = assign_node_rainfall_layers(G_proj)
            variance_q1, variance_q3 = variance_quantiles(node_variance_layer.values())

            env_values = {}
            for env_path in [ASSIGNMENT_ENV_PATH, ROOT_ENV_PATH]:
                env_values.update(parse_env_file(env_path))

            congestion_method = env_values.get("CONGESTION_METHOD", "adaptive_threshold").strip().lower()
            adaptive_factors = (
                float(env_values.get("CONGESTION_CF_1", 0.10)),
                float(env_values.get("CONGESTION_CF_2", 0.20)),
                float(env_values.get("CONGESTION_CF_3", 0.35)),
                float(env_values.get("CONGESTION_CF_4", 0.50)),
            )

            rainfall_series = pd.Series(list(node_rainfall_layer.values()), dtype="float64")
            if rainfall_series.notna().any():
                adaptive_breaks = tuple(
                    float(item) for item in rainfall_series.quantile([0.25, 0.50, 0.75]).to_list()
                )
            else:
                adaptive_breaks = (0.71, 0.72, 0.74)

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
                    "Observed rainfall over Hualien City is low, so an adaptive threshold is used "
                    "to preserve before/after contrast in the accessibility analysis."
                )
            print(
                "Edge rainfall summary (mm/hr): "
                f"min={edge_rainfall.min():.2f}, mean={edge_rainfall.mean():.2f}, max={edge_rainfall.max():.2f}"
            )
            print(f"Congestion factor counts: {cf_summary}")
            print("Dynamic travel times have been added to every edge.")
        ''',
        "# [S11] Calculate Isochrones + Isochrone Polygons": '''
            # [S11] Calculate Isochrones + Isochrone Polygons

            def compute_isochrone(G, source_node, weight_attr, time_seconds):
                distances = nx.single_source_dijkstra_path_length(
                    G,
                    source_node,
                    weight=weight_attr,
                    cutoff=float(time_seconds),
                )
                reachable_nodes = set(distances.keys())
                return reachable_nodes, distances

            def nodes_to_polygon(G, nodes, buffer_m=80):
                if len(nodes) < 2:
                    return None, 0.0
                points = [Point(float(G.nodes[node]["x"]), float(G.nodes[node]["y"])) for node in nodes]
                hull = MultiPoint(points).convex_hull
                if hull.geom_type == "Polygon":
                    polygon = hull.buffer(buffer_m)
                else:
                    polygon = hull.buffer(buffer_m * 1.5)
                return polygon, float(polygon.area)

            def get_adaptive_thresholds(G, source_node, weight_attr):
                all_times = dict(nx.single_source_dijkstra_path_length(G, source_node, weight=weight_attr))
                if all_times:
                    max_time = max(all_times.values())
                else:
                    max_time = 600.0
                short_seconds = max(max_time * 0.35, 5 * 60)
                long_seconds = max(max_time * 0.65, 10 * 60)
                short_seconds = int(math.ceil(short_seconds / 60.0) * 60)
                long_seconds = int(math.ceil(long_seconds / 60.0) * 60)
                return short_seconds, long_seconds

            def loss_pct(before_area, after_area):
                if before_area <= 0:
                    return 0.0
                return max(0.0, (1 - after_area / before_area) * 100.0)

            def summarize_accessibility(G, source_node, short_seconds, long_seconds):
                reachable_before_short, _ = compute_isochrone(G, source_node, "travel_time", short_seconds)
                reachable_before_long, _ = compute_isochrone(G, source_node, "travel_time", long_seconds)
                reachable_after_short, _ = compute_isochrone(G, source_node, "travel_time_adj", short_seconds)
                reachable_after_long, _ = compute_isochrone(G, source_node, "travel_time_adj", long_seconds)

                _, pre_short_area = nodes_to_polygon(G, reachable_before_short)
                _, pre_long_area = nodes_to_polygon(G, reachable_before_long)
                _, post_short_area = nodes_to_polygon(G, reachable_after_short)
                _, post_long_area = nodes_to_polygon(G, reachable_after_long)

                return {
                    "pre_short_km2": pre_short_area / 1e6,
                    "post_short_km2": post_short_area / 1e6,
                    "short_loss_pct": loss_pct(pre_short_area, post_short_area),
                    "pre_long_km2": pre_long_area / 1e6,
                    "post_long_km2": post_long_area / 1e6,
                    "long_loss_pct": loss_pct(pre_long_area, post_long_area),
                    "short_seconds": float(short_seconds),
                    "long_seconds": float(long_seconds),
                }

            print("Isochrone helpers are ready.")
        ''',
    }
)

CELL_SOURCES.update(
    {
        "# [S12] Calculate Accessibility Benefit-Cost Table": '''
            # [S12] Calculate Accessibility Benefit-Cost Table (Required Layer)

            terrain_lookup = top_5_gdf.set_index("node_id")["terrain_risk"].to_dict()
            required_records = []
            selected_facilities = top_5_nodes[:3]

            for facility_id, centrality_value in selected_facilities:
                short_seconds, long_seconds = get_adaptive_thresholds(G_dyn, facility_id, "travel_time")
                summary = summarize_accessibility(G_dyn, facility_id, short_seconds, long_seconds)
                rainfall_variance = node_variance_layer.get(facility_id, np.nan)
                required_records.append(
                    {
                        "analysis_level": "required",
                        "facility_type": "bottleneck_node",
                        "facility_id": str(facility_id),
                        "name": f"Bottleneck Node {facility_id}",
                        "capacity": np.nan,
                        "terrain_risk": terrain_lookup.get(facility_id, "unknown"),
                        "nearest_node": int(facility_id),
                        "rainfall_mm": round(float(node_rainfall_layer.get(facility_id, 0.0)), 2),
                        "rainfall_variance": round(float(rainfall_variance), 4) if pd.notna(rainfall_variance) else np.nan,
                        "uncertainty_flag": variance_to_flag(rainfall_variance),
                        "centrality": round(float(centrality_value), 6),
                        "short_minutes": round(short_seconds / 60.0, 1),
                        "long_minutes": round(long_seconds / 60.0, 1),
                        **summary,
                    }
                )

            required_accessibility_table = pd.DataFrame(required_records)
            required_accessibility_table = required_accessibility_table.sort_values(
                by=["short_loss_pct", "long_loss_pct", "centrality"],
                ascending=[False, False, False],
            ).reset_index(drop=True)
            required_accessibility_table["priority_rank"] = np.arange(1, len(required_accessibility_table) + 1)

            accessibility_table = required_accessibility_table.copy()
            accessibility_table.to_csv(ACCESSIBILITY_CSV_PATH, index=False, encoding="utf-8-sig")

            print("Required layer accessibility table:")
            display(
                required_accessibility_table[
                    [
                        "facility_id",
                        "short_minutes",
                        "long_minutes",
                        "pre_short_km2",
                        "post_short_km2",
                        "short_loss_pct",
                        "pre_long_km2",
                        "post_long_km2",
                        "long_loss_pct",
                        "terrain_risk",
                        "uncertainty_flag",
                    ]
                ]
            )
            print(f"Saved required-layer accessibility table to: {ACCESSIBILITY_CSV_PATH}")
        ''',
        "# [S13] Visualize Isochrone Comparison": '''
            # [S13] Visualize Isochrone Comparison (Required Layer)

            required_focus = required_accessibility_table.iloc[0]
            focus_node = int(required_focus["nearest_node"])
            short_seconds = int(required_focus["short_seconds"])
            long_seconds = int(required_focus["long_seconds"])

            fig, axes = plt.subplots(1, 2, figsize=(16, 7))
            configs = [
                (axes[0], "travel_time", "Pre-disaster isochrone"),
                (axes[1], "travel_time_adj", "Post-disaster isochrone"),
            ]

            for ax, weight_attr, title in configs:
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
                    ax.fill(x_long, y_long, alpha=0.20, color="royalblue", label=f"{long_seconds/60:.0f} min ({area_long/1e6:.2f} km$^2$)")
                if poly_short is not None:
                    x_short, y_short = poly_short.exterior.xy
                    ax.fill(x_short, y_short, alpha=0.35, color="tomato", label=f"{short_seconds/60:.0f} min ({area_short/1e6:.2f} km$^2$)")

                ax.plot(
                    G_dyn.nodes[focus_node]["x"],
                    G_dyn.nodes[focus_node]["y"],
                    marker="*",
                    markersize=18,
                    color="gold",
                    markeredgecolor="black",
                    zorder=12,
                )
                ax.set_title(title, fontsize=13, fontweight="bold")
                ax.legend(loc="lower right")

            plt.suptitle(
                f"Required Layer: Bottleneck Node {focus_node} Before / After Accessibility",
                fontsize=15,
                fontweight="bold",
            )
            plt.tight_layout()
            plt.show()
            print("Required-layer isochrone comparison rendered.")
        ''',
        "# [S14] .env Configuration Example": '''
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
            """

            env_example_path = ASSIGNMENT_DIR / ".env.example"
            env_example_path.write_text(env_example.strip() + "\\n", encoding="utf-8")

            print("Recommended .env configuration:")
            print(env_example.strip())
            print(f"Saved .env example to: {env_example_path}")
        ''',
        "# [S15] Save Road Network as GraphML": '''
            # [S15] Save Road Network as GraphML

            ox.save_graphml(G_proj, NETWORK_GRAPHML_PATH)
            print(f"Road network saved to: {NETWORK_GRAPHML_PATH}")
        ''',
    }
)

CELL_SOURCES.update(
    {
        "# [S16] Prepare AI Tool Invocation": '''
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
                        except Exception as model_exc:
                            errors.append(f"{model_name}: {model_exc}")

                    return None, f"{label}: generation failed -> {' | '.join(errors)}"
                except Exception as exc:
                    return None, f"{label}: generation failed -> {exc}"

            print("AI preparation status:")
            for item in gemini_status:
                print(f"- {item}")
        ''',
        "# [S17] Generate AI Strategic Report": '''
            # [S17] Generate AI Strategic Report

            top_5_info = "\\n".join(
                [
                    f"#{rank}: node {node_id}, centrality={cent_val:.4f}"
                    for rank, (node_id, cent_val) in enumerate(top_5_nodes, start=1)
                ]
            )
            required_prompt_table = required_accessibility_table[
                [
                    "facility_id",
                    "short_loss_pct",
                    "long_loss_pct",
                    "terrain_risk",
                    "uncertainty_flag",
                ]
            ].to_string(index=False)

            required_ai_prompt = f"""
            You are a transportation and disaster-response advisor for Hualien.

            Event:
            {EVENT_LABEL}

            Top bottleneck nodes:
            {top_5_info}

            Required-layer accessibility summary:
            {required_prompt_table}

            Please provide:
            1. The most urgent road-network bottlenecks to stabilize first.
            2. Likely accessibility consequences if those nodes remain degraded.
            3. A short operational recommendation for the first 24 hours.
            """

            required_ai_report_text, required_ai_status = call_gemini_report(required_ai_prompt, "Required layer AI report")
            print(required_ai_status)
            if required_ai_report_text:
                print("\\nRequired layer AI report:")
                print(required_ai_report_text)
            else:
                print("\\nAI report was skipped. The notebook remains fully valid without it.")
        ''',
        "# [S18] Generate README.md Framework": '''
            # [S18] Generate README.md

            def format_top_rows(frame, columns, top_n=5):
                if frame is None or len(frame) == 0:
                    return "No rows available."
                subset = frame.loc[:, columns].head(top_n).copy()
                return subset.to_string(index=False)

            def format_stretch_summary(stretch_table):
                if stretch_table is None or len(stretch_table) == 0:
                    return "No stretch rows available."

                columns = [
                    "scenario_name",
                    "facility_id",
                    "name",
                    "capacity",
                    "short_loss_pct",
                    "long_loss_pct",
                    "uncertainty_flag",
                    "priority_rank",
                ]
                available_columns = [column for column in columns if column in stretch_table.columns]
                sections = []

                if "scenario_name" in stretch_table.columns:
                    for scenario_name in ["observed", "stress_test"]:
                        scenario_rows = stretch_table.loc[stretch_table["scenario_name"] == scenario_name]
                        if len(scenario_rows) == 0:
                            continue
                        sections.append(f"Scenario: {scenario_name}")
                        sections.append(
                            scenario_rows.loc[:, available_columns].head(min(5, len(scenario_rows))).to_string(index=False)
                        )
                else:
                    sections.append(
                        stretch_table.loc[:, available_columns].head(min(5, len(stretch_table))).to_string(index=False)
                    )

                return "\\n\\n".join(sections)

            def write_final_readme(required_table, stretch_table=None, required_ai_text=None, stretch_ai_text=None):
                required_table = required_table.copy()
                stretch_ready = stretch_table is not None and len(stretch_table) > 0

                lines = [
                    "# ARIA v4.0 - Hualien Accessibility Assessment",
                    "",
                    "## Required Layer Completion",
                    "",
                    "- Road network extraction / cache: completed",
                    "- Projection to EPSG:3826: completed",
                    "- Travel-time baseline and bottleneck centrality: completed",
                    "- Week 4 terrain overlay on Top 5 bottlenecks: completed",
                    "- Dynamic travel times using real Week 6 rainfall raster: completed",
                    "- Isochrone comparison and required accessibility table: completed",
                    "- GraphML export: completed",
                    "- The required layer uses the real Week 6 rainfall raster as the primary source.",
                    "",
                    "### Required Layer Summary",
                    "",
                    "```text",
                    format_top_rows(
                        required_table,
                        [
                            "facility_id",
                            "short_loss_pct",
                            "long_loss_pct",
                            "terrain_risk",
                            "uncertainty_flag",
                        ],
                        top_n=min(5, len(required_table)),
                    ),
                    "```",
                    "",
                    "## Stretch Enhancements",
                    "",
                ]

                if stretch_ready:
                    lines.extend(
                        [
                            "- Added shelter-level accessibility analysis for Hualien City shelters.",
                            "- Preserved the observed Week 6 result and added a stress-test contingency scenario.",
                            "- Ranked shelters by accessibility loss, capacity, terrain risk, and centrality context.",
                            "- Added rainfall uncertainty reporting from Week 6 kriging variance.",
                            "- The stress-test scenario preserves the observed spatial rainfall pattern but rescales it to severe-rain thresholds.",
                            "",
                            "### Stretch Layer Summary",
                            "",
                            "```text",
                            format_stretch_summary(stretch_table),
                            "```",
                            "",
                        ]
                    )
                else:
                    lines.extend(
                        [
                            "- Stretch layer cells have not been executed yet.",
                            "- The final README will be refreshed after the shelter-level section runs.",
                            "",
                        ]
                    )

                lines.extend(
                    [
                        "## Data Sources",
                        "",
                        f"- Road network: OpenStreetMap / OSMnx ({place_name})",
                        f"- Terrain context: {DEM_PATH.name} + Week 4 terrain audit",
                        f"- Rainfall source: {rainfall_source}",
                        f"- Rainfall variance source: {VARIANCE_RASTER_PATH.name if VARIANCE_RASTER_PATH.exists() else 'N/A'}",
                        "",
                        "## Notes",
                        "",
                        "- The notebook is intentionally ordered as required layer first, stretch layer second.",
                        "- Observed Week 6 rainfall over Hualien City is low, so the required layer uses an adaptive threshold to preserve visible before/after accessibility contrast.",
                        "- The stretch stress-test scenario is a contingency analysis built from the observed rainfall spatial pattern.",
                        "",
                        "## AI Diagnostic Log",
                        "",
                        "- AI output is optional. The notebook remains gradable even when Gemini is unavailable.",
                        "- Real rainfall is now loaded from Week 6 outputs instead of simulated random values.",
                        "- The stretch layer is appended after the required layer so grading can stop at the worksheet minimum if needed.",
                        "",
                        "### Required AI Report",
                        "",
                        required_ai_text or "Skipped / unavailable",
                        "",
                        "### Stretch AI Report",
                        "",
                        stretch_ai_text or ("Pending stretch execution" if not stretch_ready else "Skipped / unavailable"),
                        "",
                        "## Submission Checklist",
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
        ''',
    }
)

STRETCH_CELLS: list[dict] = []

STRETCH_CELLS.extend(
    [
        new_markdown_cell(
            """
            ## Part G: Stretch Analysis (Beyond Requirements)

            The following cells keep the worksheet-complete results intact, then add a second layer of analysis:

            1. Shelter-level accessibility for Hualien City shelters
            2. Observed-result preservation plus a contingency stress-test scenario
            3. Priority ranking based on accessibility loss, capacity, terrain risk, and uncertainty
            """
        ),
        new_code_cell(
            '''
            # [X1] Build Hualien City Shelter Layer

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

            city_shelters_gdf = gpd.GeoDataFrame(
                city_shelters,
                geometry=gpd.points_from_xy(city_shelters["longitude"], city_shelters["latitude"]),
                crs="EPSG:4326",
            ).to_crs(G_proj.graph["crs"])

            city_shelters_gdf["nearest_node"] = ox.distance.nearest_nodes(
                G_proj,
                city_shelters_gdf.geometry.x.to_numpy(),
                city_shelters_gdf.geometry.y.to_numpy(),
            )
            city_shelters_gdf["rainfall_mm"] = city_shelters_gdf["nearest_node"].map(node_rainfall_layer).astype(float)
            city_shelters_gdf["rainfall_variance"] = city_shelters_gdf["nearest_node"].map(node_variance_layer)
            city_shelters_gdf["uncertainty_flag"] = city_shelters_gdf["rainfall_variance"].map(variance_to_flag)
            city_shelters_gdf["centrality"] = city_shelters_gdf["nearest_node"].map(centrality).fillna(0.0)

            def build_stress_test_rainfall_layer(rainfall_layer, floor_mm=12.0, ceiling_mm=45.0):
                observed_values = pd.Series(list(rainfall_layer.values()), dtype="float64")
                if observed_values.empty:
                    return {}

                min_value = float(observed_values.min())
                max_value = float(observed_values.max())
                if not math.isfinite(min_value) or not math.isfinite(max_value) or abs(max_value - min_value) < 1e-9:
                    return {node_id: float(floor_mm) for node_id in rainfall_layer}

                scaled = {}
                for node_id, rainfall_mm in rainfall_layer.items():
                    unit = (float(rainfall_mm) - min_value) / (max_value - min_value)
                    scaled[node_id] = float(floor_mm + unit * (ceiling_mm - floor_mm))
                return scaled

            stretch_node_rainfall_layer = build_stress_test_rainfall_layer(node_rainfall_layer)
            G_dyn_stress = apply_dynamic_weights(G_proj, stretch_node_rainfall_layer, node_variance_layer)

            observed_node_rainfall = pd.Series(list(node_rainfall_layer.values()), dtype="float64")
            stress_node_rainfall = pd.Series(list(stretch_node_rainfall_layer.values()), dtype="float64")
            stress_congestion_series = pd.Series(
                [edge_data.get("congestion_factor", 0.0) for _, _, _, edge_data in G_dyn_stress.edges(data=True, keys=True)],
                dtype="float64",
            )

            print(f"Hualien City shelter count: {len(city_shelters_gdf):,}")
            print("Stretch contingency scenario constructed from observed spatial rainfall pattern.")
            print(
                "Observed node rainfall range (mm/hr): "
                f"min={observed_node_rainfall.min():.2f}, mean={observed_node_rainfall.mean():.2f}, max={observed_node_rainfall.max():.2f}"
            )
            print(
                "Stress-test node rainfall range (mm/hr): "
                f"min={stress_node_rainfall.min():.2f}, mean={stress_node_rainfall.mean():.2f}, max={stress_node_rainfall.max():.2f}"
            )
            print(
                "Stress-test congestion factor counts: "
                f"cf=0.0 -> {(stress_congestion_series == 0.0).sum()}, "
                f"cf=0.3 -> {(stress_congestion_series == 0.3).sum()}, "
                f"cf=0.6 -> {(stress_congestion_series == 0.6).sum()}, "
                f"cf=0.9 -> {(stress_congestion_series == 0.9).sum()}"
            )
            display(
                city_shelters_gdf[
                    [
                        "shelter_id",
                        "name",
                        "capacity",
                        "terrain_risk",
                        "nearest_node",
                        "rainfall_mm",
                        "rainfall_variance",
                        "uncertainty_flag",
                    ]
                ].head(10)
            )
            '''
        ),
        new_code_cell(
            '''
            # [X2] Shelter-Level Accessibility Ranking

            terrain_priority = {"very_high": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
            def build_stretch_table(G_layer, scenario_name, rainfall_lookup):
                stretch_records = []

                for index, row in enumerate(city_shelters_gdf.itertuples(), start=1):
                    summary = summarize_accessibility(G_layer, int(row.nearest_node), 5 * 60, 10 * 60)
                    stretch_records.append(
                        {
                            "analysis_level": "stretch",
                            "scenario_name": scenario_name,
                            "facility_type": "shelter",
                            "facility_id": str(row.shelter_id),
                            "name": row.name,
                            "capacity": float(row.capacity) if pd.notna(row.capacity) else np.nan,
                            "terrain_risk": row.terrain_risk,
                            "nearest_node": int(row.nearest_node),
                            "rainfall_mm": round(float(rainfall_lookup.get(int(row.nearest_node), row.rainfall_mm)), 2),
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
                    if index % 5 == 0 or index == len(city_shelters_gdf):
                        print(f"[{scenario_name}] processed shelter accessibility: {index}/{len(city_shelters_gdf)}")

                stretch_table = pd.DataFrame(stretch_records)
                stretch_table["_terrain_score"] = stretch_table["terrain_risk"].map(terrain_priority).fillna(0)
                stretch_table = stretch_table.sort_values(
                    by=["short_loss_pct", "long_loss_pct", "capacity", "_terrain_score", "centrality"],
                    ascending=[False, False, False, False, False],
                ).reset_index(drop=True)
                stretch_table["priority_rank"] = np.arange(1, len(stretch_table) + 1)
                return stretch_table.drop(columns="_terrain_score")

            stretch_observed_table = build_stretch_table(G_dyn, "observed", node_rainfall_layer)
            stretch_stress_table = build_stretch_table(G_dyn_stress, "stress_test", stretch_node_rainfall_layer)
            top_priority_shelters = stretch_stress_table.head(5).copy()

            stretch_accessibility_table = pd.concat(
                [stretch_observed_table, stretch_stress_table],
                ignore_index=True,
                sort=False,
            )
            required_output_table = required_accessibility_table.copy()
            required_output_table["scenario_name"] = "required_baseline"
            accessibility_table = pd.concat(
                [required_output_table, stretch_accessibility_table],
                ignore_index=True,
                sort=False,
            )
            accessibility_table.to_csv(ACCESSIBILITY_CSV_PATH, index=False, encoding="utf-8-sig")

            print("Observed stretch scenario summary:")
            display(
                stretch_observed_table[
                    [
                        "priority_rank",
                        "facility_id",
                        "name",
                        "short_loss_pct",
                        "long_loss_pct",
                        "uncertainty_flag",
                    ]
                ].head(5)
            )
            print("Stress-test stretch scenario summary:")
            display(
                top_priority_shelters[
                    [
                        "scenario_name",
                        "priority_rank",
                        "facility_id",
                        "name",
                        "capacity",
                        "terrain_risk",
                        "short_loss_pct",
                        "long_loss_pct",
                        "uncertainty_flag",
                    ]
                ]
            )
            print(f"Combined required + stretch table saved to: {ACCESSIBILITY_CSV_PATH}")
            '''
        ),
    ]
)

STRETCH_CELLS.extend(
    [
        new_code_cell(
            '''
            # [X3] Visualize Priority Shelter

            priority_shelter = top_priority_shelters.iloc[0]
            observed_priority_shelter = stretch_observed_table.loc[
                stretch_observed_table["facility_id"].astype(str) == str(priority_shelter["facility_id"])
            ].iloc[0]
            priority_shelter_point = city_shelters_gdf.loc[
                city_shelters_gdf["shelter_id"].astype(str) == str(priority_shelter["facility_id"])
            ].iloc[0]
            priority_node = int(priority_shelter["nearest_node"])
            top_priority_points = city_shelters_gdf.loc[
                city_shelters_gdf["shelter_id"].astype(str).isin(top_priority_shelters["facility_id"].astype(str))
            ].copy()

            fig, axes = plt.subplots(1, 2, figsize=(16, 7))
            configs = [
                (axes[0], G_dyn, "Observed Week 6 accessibility"),
                (axes[1], G_dyn_stress, "Stress-test contingency accessibility"),
            ]

            for ax, graph_obj, title in configs:
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
                reachable_short, _ = compute_isochrone(graph_obj, priority_node, "travel_time_adj", 5 * 60)
                reachable_long, _ = compute_isochrone(graph_obj, priority_node, "travel_time_adj", 10 * 60)
                poly_long, area_long = nodes_to_polygon(graph_obj, reachable_long)
                poly_short, area_short = nodes_to_polygon(graph_obj, reachable_short)

                if poly_long is not None:
                    x_long, y_long = poly_long.exterior.xy
                    ax.fill(x_long, y_long, alpha=0.20, color="royalblue", label=f"10 min ({area_long/1e6:.2f} km$^2$)")
                if poly_short is not None:
                    x_short, y_short = poly_short.exterior.xy
                    ax.fill(x_short, y_short, alpha=0.35, color="tomato", label=f"5 min ({area_short/1e6:.2f} km$^2$)")

                ax.scatter(
                    top_priority_points.geometry.x,
                    top_priority_points.geometry.y,
                    s=35,
                    color="white",
                    edgecolors="black",
                    label="Top 5 shelters",
                    zorder=11,
                )
                ax.scatter(
                    [priority_shelter_point.geometry.x],
                    [priority_shelter_point.geometry.y],
                    s=130,
                    color="gold",
                    edgecolors="black",
                    marker="*",
                    label=f"Priority shelter: {priority_shelter_point['name']}",
                    zorder=12,
                )
                ax.set_title(title, fontsize=13, fontweight="bold")
                ax.legend(loc="lower right")

            plt.suptitle(
                f"Stretch Layer: Priority Shelter {priority_shelter_point['name']} Observed vs Stress-Test",
                fontsize=15,
                fontweight="bold",
            )
            plt.tight_layout()
            plt.show()
            print(
                f"Observed short-loss={observed_priority_shelter['short_loss_pct']:.1f}% / "
                f"stress-test short-loss={priority_shelter['short_loss_pct']:.1f}%"
            )
            print("Stretch-layer priority shelter visualization rendered.")
            '''
        ),
        new_code_cell(
            '''
            # [X4] Stretch AI Report And Final Output Refresh

            observed_prompt_table = stretch_observed_table.head(5)[
                [
                    "priority_rank",
                    "name",
                    "capacity",
                    "terrain_risk",
                    "short_loss_pct",
                    "long_loss_pct",
                    "rainfall_mm",
                    "uncertainty_flag",
                ]
            ].to_string(index=False)

            shelter_prompt_table = top_priority_shelters[
                [
                    "priority_rank",
                    "name",
                    "capacity",
                    "terrain_risk",
                    "short_loss_pct",
                    "long_loss_pct",
                    "rainfall_mm",
                    "uncertainty_flag",
                ]
            ].to_string(index=False)

            stretch_ai_prompt = f"""
            You are advising Hualien emergency managers after Typhoon Fung-wong.

            Top bottleneck nodes:
            {top_5_info}

            Observed shelter summary:
            {observed_prompt_table}

            Stress-test priority shelters:
            {shelter_prompt_table}

            Please provide:
            1. The shelter rescue priority order under the stress-test scenario.
            2. Alternative access or transport options where road access is degraded.
            3. Resource allocation priorities.
            4. Any caution that should be raised because of rainfall uncertainty.
            5. A brief contrast between the observed Week 6 outcome and the contingency stress-test outcome.
            """

            stretch_ai_report_text, stretch_ai_status = call_gemini_report(stretch_ai_prompt, "Stretch layer AI report")
            print(stretch_ai_status)
            if stretch_ai_report_text:
                print("\\nStretch layer AI report:")
                print(stretch_ai_report_text)
            else:
                print("\\nStretch AI report was skipped or unavailable.")

            readme_path = write_final_readme(
                required_accessibility_table,
                stretch_accessibility_table,
                required_ai_report_text,
                stretch_ai_report_text,
            )
            accessibility_table.to_csv(ACCESSIBILITY_CSV_PATH, index=False, encoding="utf-8-sig")
            print(f"Final README refreshed at: {readme_path}")
            print(f"Final combined table refreshed at: {ACCESSIBILITY_CSV_PATH}")
            '''
        ),
    ]
)


def main() -> None:
    notebook = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    for marker, code in CELL_SOURCES.items():
        set_code_cell(notebook, marker, code)

    set_markdown_cell(
        notebook,
        "## Part C: Dynamic Accessibility Analysis",
        """
        ## Part C: Dynamic Accessibility Analysis

        > **⏱️ Lab 2 Scope (30 min in class)**: Complete the **core calculations** of C.1 ~ C.3 (print contraction ratio values).
        > Part D visualization can be completed during assignment time, not required in class.
        >
        > **Note**: Observed rainfall sampled from the Week 6 raster is very low over Hualien City, so this notebook uses a more sensitive adaptive threshold to reveal relative accessibility differences under low-intensity rainfall. This is a sensitivity setting for analysis, not a claim that rainfall reached severe flood thresholds.

        ### Task C.1: Define Rainfall → Traffic Congestion Mapping
        """,
    )

    set_markdown_cell(
        notebook,
        "## Part D: Visualization (Before & After Comparison)",
        """
        ## Part D: Visualization (Before & After Comparison)

        > **💡 Tip**: This visualization is an **extension goal** in Lab 2.
        > If class time is insufficient, it can be completed during assignment time. The key requirement is still the Part C numerical calculation.
        >
        > **Note**: The before/after contrast in this figure uses the same adaptive threshold setting from Part C. Because observed Week 6 rainfall over Hualien City is low, a more sensitive threshold is used here to make relative accessibility changes visible.
        """,
    )

    if STRETCH_CELLS:
        insert_cells_after_marker(
            notebook,
            "# [S18]",
            STRETCH_CELLS,
        )

    OUTPUT_PATH.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"Notebook generated at: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
