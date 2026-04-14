from pathlib import Path
import json

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TARGET_EPSG = 32651
GUANGFU_POINT = (23.6663549, 121.4211642)  # lat, lon
GUANGFU_DIST_M = 4000
GUANGFU_SHELTER_BBOX = (121.38, 23.63, 121.46, 23.71)  # minx, miny, maxx, maxy in EPSG:4326

GUANGFU_OVERLAY = [
    {
        "name": "Guangfu_Station",
        "cn_name": "\u5149\u5fa9\u8eca\u7ad9",
        "node_type": "transport",
        "priority": 1,
        "geometry": Point(121.4211642, 23.6663549),
    },
    {
        "name": "Guangfu_Elementary",
        "cn_name": "\u5149\u5fa9\u570b\u5c0f",
        "node_type": "school",
        "priority": 2,
        "geometry": Point(121.4263921, 23.6741430),
    },
    {
        "name": "Guangfu_Township_Office",
        "cn_name": "\u5149\u5fa9\u9109\u516c\u6240",
        "node_type": "government",
        "priority": 3,
        "geometry": Point(121.4232842, 23.6693798),
    },
    {
        "name": "Mataian_Hwy9_Bridge",
        "cn_name": "\u53f09\u7dda\u99ac\u592a\u978d\u6eaa\u6a4b",
        "node_type": "bridge",
        "priority": 4,
        "geometry": Point(121.4090737, 23.6887424),
    },
    {
        "name": "Foxu_Debris_Zone",
        "cn_name": "\u4f5b\u7956\u8857\u571f\u77f3\u6d41\u5340",
        "node_type": "impact_zone",
        "priority": 5,
        "geometry": Point(121.4370190, 23.6771822),
    },
]


def build_guangfu_overlay_layer() -> Path:
    gdf = gpd.GeoDataFrame(GUANGFU_OVERLAY, crs="EPSG:4326")
    out_path = DATA_DIR / "guangfu_overlay.gpkg"
    gdf.to_file(out_path, driver="GPKG")
    return out_path


def build_guangfu_shelters_layer() -> Path:
    shelters_path = REPO_ROOT / "submission" / "Homework-3" / "shelter_risk_audit.json"
    shelter_records = json.loads(shelters_path.read_text(encoding="utf-8"))
    shelters = pd.DataFrame(shelter_records)

    shelters["longitude"] = shelters["longitude"].astype(float)
    shelters["latitude"] = shelters["latitude"].astype(float)
    shelters["capacity"] = shelters["capacity"].fillna(0).astype(int)
    shelters = shelters.rename(columns={"risk_level": "terrain_risk"})

    selected = shelters.loc[
        shelters["longitude"].between(GUANGFU_SHELTER_BBOX[0], GUANGFU_SHELTER_BBOX[2])
        & shelters["latitude"].between(GUANGFU_SHELTER_BBOX[1], GUANGFU_SHELTER_BBOX[3])
    ].copy()

    if selected.empty:
        raise RuntimeError("No Guangfu shelters found inside the configured bbox.")

    gdf = gpd.GeoDataFrame(
        selected,
        geometry=gpd.points_from_xy(selected["longitude"], selected["latitude"]),
        crs="EPSG:4326",
    )
    gdf_utm = gdf.to_crs(f"EPSG:{TARGET_EPSG}")

    station = gpd.GeoSeries([Point(GUANGFU_POINT[1], GUANGFU_POINT[0])], crs="EPSG:4326").to_crs(
        f"EPSG:{TARGET_EPSG}"
    )[0]
    risk_order = {"high": 3, "medium": 2, "low": 1, "safe": 0}
    gdf_utm["risk_score"] = gdf_utm["terrain_risk"].map(risk_order).fillna(0)
    gdf_utm["distance_to_station_m"] = gdf_utm.geometry.distance(station)
    gdf_utm = gdf_utm.sort_values(
        ["risk_score", "capacity", "distance_to_station_m"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    gdf_utm["priority_rank"] = gdf_utm.index + 1

    keep_cols = [
        "shelter_id",
        "name",
        "capacity",
        "county_name",
        "town_name",
        "terrain_risk",
        "priority_rank",
        "distance_to_station_m",
        "longitude",
        "latitude",
        "geometry",
    ]
    out_path = DATA_DIR / "shelters_guangfu.gpkg"
    gdf_utm[keep_cols].to_crs("EPSG:4326").to_file(out_path, driver="GPKG")
    return out_path


def build_guangfu_bottlenecks_layer() -> Path:
    ox.settings.requests_timeout = 180
    ox.settings.use_cache = True

    graph = ox.graph_from_point(GUANGFU_POINT, dist=GUANGFU_DIST_M, network_type="drive", simplify=True)
    graph = ox.project_graph(graph, to_crs=f"EPSG:{TARGET_EPSG}")
    undirected = ox.convert.to_undirected(graph)

    centrality = nx.betweenness_centrality(undirected, weight="length", normalized=True)

    rows = []
    for node_id, score in centrality.items():
        node = undirected.nodes[node_id]
        rows.append(
            {
                "node_id": str(node_id),
                "centrality": float(score),
                "degree": int(undirected.degree[node_id]),
                "terrain_risk": "high",
                "geometry": Point(float(node["x"]), float(node["y"])),
            }
        )

    nodes_gdf = gpd.GeoDataFrame(rows, crs=f"EPSG:{TARGET_EPSG}")
    nodes_gdf = nodes_gdf.sort_values("centrality", ascending=False).reset_index(drop=True)

    picked = []
    min_spacing_m = 250
    for row in nodes_gdf.itertuples():
        if any(row.geometry.distance(existing.geometry) < min_spacing_m for existing in picked):
            continue
        picked.append(row)
        if len(picked) == 5:
            break

    if len(picked) < 5:
        raise RuntimeError("Unable to derive 5 distinct Guangfu bottlenecks from the local graph.")

    top5 = gpd.GeoDataFrame(
        [
            {
                "node_id": row.node_id,
                "centrality": row.centrality,
                "degree": row.degree,
                "terrain_risk": row.terrain_risk,
                "priority_rank": rank,
                "geometry": row.geometry,
            }
            for rank, row in enumerate(picked, start=1)
        ],
        crs=f"EPSG:{TARGET_EPSG}",
    )

    out_path = DATA_DIR / "top5_bottlenecks_guangfu.gpkg"
    top5.to_file(out_path, driver="GPKG")
    return out_path


def main() -> None:
    built = [
        build_guangfu_overlay_layer(),
        build_guangfu_shelters_layer(),
        build_guangfu_bottlenecks_layer(),
    ]
    for path in built:
        print(path)


if __name__ == "__main__":
    main()
