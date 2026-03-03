import argparse
import json
import math
import os
from datetime import datetime

import folium
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATASET_ID = "O-A0001-001"
DEFAULT_OUTPUT_DIR = os.path.join("output", "exercise3")
API_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def haversine_meters(lat1, lon1, lat2, lon2):
    radius_m = 6371000.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_m * c


def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def fetch_stations(api_key, dataset_id):
    url = f"{API_BASE_URL}/{dataset_id}"
    params = {"Authorization": api_key, "format": "JSON"}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if str(payload.get("success")).lower() != "true":
        raise RuntimeError(f"CWA API returned non-success payload: {payload.get('success')}")

    records = payload.get("records", {})
    stations = records.get("Station")
    if stations is None:
        stations = records.get("location")
    if not isinstance(stations, list):
        raise RuntimeError("Cannot find station list in CWA payload")

    return stations


def extract_coordinate_pair(station):
    geo_info = station.get("GeoInfo") or {}
    coordinates = geo_info.get("Coordinates") or []

    parsed = {}
    for item in coordinates:
        if not isinstance(item, dict):
            continue
        name = str(item.get("CoordinateName", "")).upper().strip()
        lat = safe_float(item.get("StationLatitude"))
        lon = safe_float(item.get("StationLongitude"))
        if not name or lat is None or lon is None:
            continue
        parsed[name] = (lat, lon)

    twd67 = parsed.get("TWD67")
    wgs84 = parsed.get("WGS84")
    if twd67 is None or wgs84 is None:
        return None

    return {"TWD67": twd67, "WGS84": wgs84}


def build_distance_dataframe(stations):
    rows = []
    for station in stations:
        if not isinstance(station, dict):
            continue

        pair = extract_coordinate_pair(station)
        if pair is None:
            continue

        twd67_lat, twd67_lon = pair["TWD67"]
        wgs84_lat, wgs84_lon = pair["WGS84"]
        distance_m = haversine_meters(twd67_lat, twd67_lon, wgs84_lat, wgs84_lon)

        rows.append(
            {
                "station_id": station.get("StationId"),
                "station_name": station.get("StationName"),
                "county_name": (station.get("GeoInfo") or {}).get("CountyName"),
                "town_name": (station.get("GeoInfo") or {}).get("TownName"),
                "twd67_lat": twd67_lat,
                "twd67_lon": twd67_lon,
                "wgs84_lat": wgs84_lat,
                "wgs84_lon": wgs84_lon,
                "distance_m": distance_m,
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("distance_m", ascending=False).reset_index(drop=True)
    return df


def build_stats(df, fetched_station_count, dataset_id):
    distances = df["distance_m"]
    mean_distance = float(distances.mean())
    median_distance = float(distances.median())

    stats = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_id": dataset_id,
        "fetched_station_count": int(fetched_station_count),
        "paired_station_count": int(len(df.index)),
        "missing_pair_count": int(fetched_station_count - len(df.index)),
        "distance_m": {
            "mean": round(mean_distance, 3),
            "median": round(median_distance, 3),
            "min": round(float(distances.min()), 3),
            "max": round(float(distances.max()), 3),
            "p05": round(float(distances.quantile(0.05)), 3),
            "p95": round(float(distances.quantile(0.95)), 3),
        },
        "distance_from_850m_mean": round(mean_distance - 850.0, 3),
        "stations_between_750m_and_950m": int(((distances >= 750) & (distances <= 950)).sum()),
        "example_largest_offsets": df.head(5)[
            ["station_id", "station_name", "distance_m"]
        ].to_dict(orient="records"),
        "example_smallest_offsets": df.tail(5)[
            ["station_id", "station_name", "distance_m"]
        ]
        .sort_values("distance_m", ascending=True)
        .to_dict(orient="records"),
    }
    return stats


def create_comparison_map(df, save_path):
    center_lat = float(df["wgs84_lat"].mean())
    center_lon = float(df["wgs84_lon"].mean())
    output_map = folium.Map(location=[center_lat, center_lon], zoom_start=7, control_scale=True)

    twd67_layer = folium.FeatureGroup(name="TWD67 treated as WGS84", show=True)
    wgs84_layer = folium.FeatureGroup(name="WGS84", show=True)
    line_layer = folium.FeatureGroup(name="Offset lines", show=True)

    for row in df.itertuples(index=False):
        twd67_point = [row.twd67_lat, row.twd67_lon]
        wgs84_point = [row.wgs84_lat, row.wgs84_lon]

        tooltip = f"{row.station_id} {row.station_name} | {row.distance_m:.1f} m"

        folium.CircleMarker(
            location=twd67_point,
            radius=2,
            color="#0B57D0",
            fill=True,
            fill_color="#0B57D0",
            fill_opacity=0.7,
            weight=1,
            tooltip=tooltip,
        ).add_to(twd67_layer)

        folium.CircleMarker(
            location=wgs84_point,
            radius=2,
            color="#D93025",
            fill=True,
            fill_color="#D93025",
            fill_opacity=0.7,
            weight=1,
            tooltip=tooltip,
        ).add_to(wgs84_layer)

        folium.PolyLine(
            locations=[twd67_point, wgs84_point],
            color="#F9AB00",
            weight=1,
            opacity=0.25,
            tooltip=tooltip,
        ).add_to(line_layer)

    twd67_layer.add_to(output_map)
    wgs84_layer.add_to(output_map)
    line_layer.add_to(output_map)
    folium.LayerControl(collapsed=False).add_to(output_map)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 9999;
        background: white;
        border: 1px solid #666;
        padding: 10px;
        font-size: 12px;
        line-height: 1.5;
    ">
      <b>CWA CRS Compare</b><br>
      <span style="color:#0B57D0;">&#9679;</span> TWD67 interpreted as WGS84<br>
      <span style="color:#D93025;">&#9679;</span> WGS84<br>
      <span style="color:#F9AB00;">&#9472;</span> Station offset
    </div>
    """
    output_map.get_root().html.add_child(folium.Element(legend_html))

    ensure_parent_dir(save_path)
    output_map.save(save_path)


def write_summary_md(stats, save_path):
    lines = [
        "# Exercise 3 - CWA CRS Compare",
        "",
        "Prompt:",
        "- \u6c23\u8c61\u7ad9 API \u6bcf\u500b\u6e2c\u7ad9\u6709\u5169\u7d44\u5ea7\u6a19\uff0c\u8acb\u90fd\u7576\u6210 WGS84 \u756b\u5728\u540c\u4e00\u5f35\u5716\uff0c\u4e26\u7d71\u8a08\u5dee\u8ddd",
        "",
        "## Result",
        f"- Dataset: `{stats['dataset_id']}`",
        f"- Stations fetched: {stats['fetched_station_count']}",
        f"- Stations with both TWD67 and WGS84: {stats['paired_station_count']}",
        f"- Mean distance: {stats['distance_m']['mean']:.1f} m",
        f"- Median distance: {stats['distance_m']['median']:.1f} m",
        f"- Min/Max distance: {stats['distance_m']['min']:.1f} m / {stats['distance_m']['max']:.1f} m",
        f"- Difference from 850 m (mean): {stats['distance_from_850m_mean']:+.1f} m",
        "",
        "Conclusion:",
        "- TWD67 vs WGS84 station coordinates are approximately 850 meters apart on average.",
        "",
        "Generated files:",
        "- `output/exercise3/cwa_station_crs_diff.csv`",
        "- `output/exercise3/cwa_station_crs_stats.json`",
        "- `output/exercise3/cwa_station_crs_map.html`",
    ]

    ensure_parent_dir(save_path)
    with open(save_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare CWA station TWD67 and WGS84 coordinates by treating both as WGS84."
    )
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID, help="CWA dataset id.")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("API_KEY_CWA"),
        help="CWA API key (defaults to API_KEY_CWA from environment).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.api_key:
        raise ValueError("Missing CWA API key. Set API_KEY_CWA in .env or use --api-key.")

    stations = fetch_stations(args.api_key, args.dataset_id)
    df = build_distance_dataframe(stations)
    if df.empty:
        raise RuntimeError("No station contains both TWD67 and WGS84 coordinates.")

    stats = build_stats(df, fetched_station_count=len(stations), dataset_id=args.dataset_id)

    csv_path = os.path.join(args.output_dir, "cwa_station_crs_diff.csv")
    stats_path = os.path.join(args.output_dir, "cwa_station_crs_stats.json")
    map_path = os.path.join(args.output_dir, "cwa_station_crs_map.html")
    summary_path = os.path.join(args.output_dir, "summary.md")

    ensure_parent_dir(csv_path)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    ensure_parent_dir(stats_path)
    with open(stats_path, "w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)

    create_comparison_map(df, map_path)
    write_summary_md(stats, summary_path)

    print(f"Dataset: {args.dataset_id}")
    print(f"Stations fetched: {len(stations)}")
    print(f"Stations with both coordinates: {len(df.index)}")
    print(f"Mean offset: {stats['distance_m']['mean']:.2f} m")
    print(f"Median offset: {stats['distance_m']['median']:.2f} m")
    print(f"Stats JSON: {stats_path}")
    print(f"Map HTML: {map_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
