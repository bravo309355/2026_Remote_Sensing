import csv
import json
import math
import os
import uuid
from datetime import datetime
from html import escape

import folium
import pandas as pd
import requests
from dotenv import load_dotenv
from folium.plugins import MarkerCluster

load_dotenv()

DEFAULT_BASE_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
DEFAULT_REFERENCE_COORDS = (25.0478, 121.5170)  # Taipei Main Station
DEFAULT_MAP_CENTER = (23.8, 121.0)
DEFAULT_MAP_ZOOM = 7

AQI_BUCKET_ORDER = ["good", "moderate", "unhealthy", "unknown"]
AQI_BUCKET_LABELS = {
    "good": "AQI 0-50",
    "moderate": "AQI 51-100",
    "unhealthy": "AQI 101+",
    "unknown": "AQI Unknown",
}
AQI_BUCKET_COLORS = {
    "good": "green",
    "moderate": "yellow",
    "unhealthy": "red",
    "unknown": "gray",
}


def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def is_missing(value):
    if value is None:
        return True
    if isinstance(value, str) and value.strip() in {"", "null", "None", "nan", "NaN"}:
        return True
    return False


def format_value(value):
    if is_missing(value):
        return "N/A"
    return str(value)


def format_distance(value):
    numeric = safe_float(value)
    if numeric is None:
        return "N/A"
    return f"{numeric:.2f} km"


def aqi_bucket_key(aqi_value):
    aqi = safe_int(aqi_value)
    if aqi is None:
        return "unknown"
    if aqi <= 50:
        return "good"
    if aqi <= 100:
        return "moderate"
    return "unhealthy"


def normalize_api_records(data):
    if isinstance(data, list):
        return data, "list"
    if isinstance(data, dict) and "records" in data and isinstance(data["records"], list):
        return data["records"], "dict.records"
    raise ValueError("Invalid API response format")


def build_output_paths(output_dir="outputs", timestamped=False, timestamp_token=None):
    token = timestamp_token or datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{token}" if timestamped else ""
    return {
        "csv": os.path.join(output_dir, f"aqi_analysis{suffix}.csv"),
        "map": os.path.join(output_dir, f"aqi_map{suffix}.html"),
        "summary": os.path.join(output_dir, f"run_summary{suffix}.json"),
    }


class AQIMonitor:
    def __init__(
        self,
        api_key=None,
        base_url=DEFAULT_BASE_URL,
        reference_coords=None,
        map_center=None,
    ):
        self.api_key = api_key or os.getenv("API_KEY_MOENV")
        if not self.api_key:
            raise ValueError(
                "API_KEY_MOENV not found in environment variables")

        self.base_url = base_url
        self.aqi_data = None
        self.processed_df = None
        self.taipei_station_coords = reference_coords or DEFAULT_REFERENCE_COORDS
        self.default_map_center = map_center or DEFAULT_MAP_CENTER
        self.last_fetch_metadata = {
            "base_url": self.base_url,
            "response_format": None,
            "records_count": 0,
            "fetch_success": False,
        }
        self.last_map_stats = {
            "map_markers_added": 0, "map_markers_skipped": 0}
        self.last_quality_stats = {}
        self.last_run_summary = None

    def fetch_aqi_data(self):
        """Fetch real-time AQI data from MOENV API."""
        try:
            params = {"api_key": self.api_key, "format": "json"}
            response = requests.get(
                self.base_url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            payload = response.json()
            records, response_format = normalize_api_records(payload)

            self.aqi_data = records
            self.processed_df = None
            self.last_fetch_metadata = {
                "base_url": self.base_url,
                "response_format": response_format,
                "records_count": len(records),
                "fetch_success": True,
                "http_status": response.status_code,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
            }
            print(
                f"Successfully fetched {len(records)} monitoring stations data")
            return True
        except requests.exceptions.RequestException as exc:
            self.last_fetch_metadata = {
                "base_url": self.base_url,
                "response_format": None,
                "records_count": 0,
                "fetch_success": False,
                "error": str(exc),
            }
            print(f"API request failed: {exc}")
            return False
        except json.JSONDecodeError as exc:
            self.last_fetch_metadata = {
                "base_url": self.base_url,
                "response_format": None,
                "records_count": 0,
                "fetch_success": False,
                "error": f"JSON decode error: {exc}",
            }
            print(f"JSON decode error: {exc}")
            return False
        except Exception as exc:
            self.last_fetch_metadata = {
                "base_url": self.base_url,
                "response_format": None,
                "records_count": 0,
                "fetch_success": False,
                "error": str(exc),
            }
            print(f"Unexpected error: {exc}")
            return False

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates using Haversine formula (km)."""
        radius_km = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c

    def get_aqi_color(self, aqi_value):
        """Get marker color based on AQI value."""
        return AQI_BUCKET_COLORS[aqi_bucket_key(aqi_value)]

    def build_processed_dataframe(self):
        """Build processed DataFrame with distance calculation."""
        if not self.aqi_data:
            return pd.DataFrame()
        if self.processed_df is not None:
            return self.processed_df.copy()

        processed_data = []
        for station in self.aqi_data:
            if not isinstance(station, dict):
                continue
            try:
                processed_station = station.copy()
                lat = safe_float(processed_station.get("latitude"))
                lon = safe_float(processed_station.get("longitude"))
                if lat in (None, 0.0) or lon in (None, 0.0):
                    distance = "N/A"
                else:
                    distance = round(
                        self.calculate_distance(
                            self.taipei_station_coords[0],
                            self.taipei_station_coords[1],
                            lat,
                            lon,
                        ),
                        2,
                    )
                processed_station["distance_from_taipei_km"] = distance
                processed_data.append(processed_station)
            except Exception:
                # Preserve behavior by skipping malformed records without stopping the run.
                continue

        df = pd.DataFrame(processed_data)
        if not df.empty:
            important_cols = [
                "sitename",
                "county",
                "aqi",
                "distance_from_taipei_km",
                "latitude",
                "longitude",
            ]
            existing_important = [
                col for col in important_cols if col in df.columns]
            other_cols = [
                col for col in df.columns if col not in existing_important]
            df = df[existing_important + other_cols]

        self.processed_df = df.copy()
        return df

    def compute_quality_stats(self, df=None):
        """Compute non-fatal data quality statistics for reporting."""
        if df is None:
            df = self.build_processed_dataframe()
        df = df.copy()
        raw_records = self.aqi_data or []

        valid_coordinates = 0
        invalid_coordinates = 0
        non_numeric_aqi = 0
        aqi_bucket_counts = {key: 0 for key in AQI_BUCKET_ORDER}

        if not df.empty:
            for record in df.to_dict("records"):
                lat = safe_float(record.get("latitude"))
                lon = safe_float(record.get("longitude"))
                if lat in (None, 0.0) or lon in (None, 0.0):
                    invalid_coordinates += 1
                else:
                    valid_coordinates += 1

                bucket = aqi_bucket_key(record.get("aqi"))
                aqi_bucket_counts[bucket] += 1
                if safe_int(record.get("aqi")) is None:
                    non_numeric_aqi += 1

        missing_key_fields_counts = {}
        for key in ["sitename", "county", "aqi", "latitude", "longitude", "publishtime"]:
            missing_key_fields_counts[key] = sum(
                1 for item in raw_records if not isinstance(item, dict) or is_missing(item.get(key))
            )

        stats = {
            "records_fetched_total": len(raw_records),
            "records_processed_for_csv": int(len(df.index)),
            "records_with_valid_coordinates": valid_coordinates,
            "records_missing_or_invalid_coordinates": invalid_coordinates,
            "records_with_non_numeric_aqi": non_numeric_aqi,
            "map_markers_added": int(self.last_map_stats.get("map_markers_added", 0)),
            "map_markers_skipped": int(self.last_map_stats.get("map_markers_skipped", 0)),
            "aqi_bucket_counts": aqi_bucket_counts,
            "missing_key_fields_counts": missing_key_fields_counts,
        }
        self.last_quality_stats = stats
        return stats

    def _build_popup_html(self, record):
        rows = [
            ("County", record.get("county")),
            ("AQI", record.get("aqi")),
            ("Status", record.get("status")),
            ("Primary Pollutant", record.get("pollutant")),
            ("PM2.5", record.get("pm2.5")),
            ("PM10", record.get("pm10")),
            ("Publish Time", record.get("publishtime")),
            ("Distance", format_distance(record.get("distance_from_taipei_km"))),
        ]
        row_html = "".join(
            f"<tr><th style='text-align:left;padding-right:8px'>{escape(label)}</th>"
            f"<td>{escape(format_value(value))}</td></tr>"
            for label, value in rows
        )
        site_name = escape(format_value(record.get("sitename")))
        return (
            "<div style='font-family:Arial,sans-serif;min-width:220px;'>"
            f"<h4 style='margin:0 0 8px 0'>{site_name}</h4>"
            "<table style='font-size:12px;border-collapse:collapse;'>"
            f"{row_html}</table></div>"
        )

    def create_aqi_map(
        self,
        save_path="outputs/aqi_map.html",
        df=None,
        map_center=None,
        zoom_start=DEFAULT_MAP_ZOOM,
        shelter_file=r"D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv",
        shelter_analysis_path=None,
    ):
        """Create Folium map with AQI markers, clustering, and layer control."""
        if not self.aqi_data:
            print("No AQI data available. Please fetch data first.")
            return None

        if df is None:
            df = self.build_processed_dataframe()
        if df.empty:
            print("No valid AQI data rows available for map generation.")
            return None

        def shelter_key(name, lon, lat):
            return (str(name or "").strip(), round(float(lon), 6), round(float(lat), 6))

        risk_meta = {
            "High Risk": {"color": "#d73027", "label": "High Risk"},
            "Warning": {"color": "#ff8c00", "label": "Warning"},
            "Normal": {"color": "#2ca25f", "label": "Normal"},
            "Unknown": {"color": "#8f8f8f", "label": "Unknown"},
        }

        def traffic_light_badge(risk_label):
            meta = risk_meta.get(risk_label, risk_meta["Unknown"])
            red = "#d73027" if risk_label == "High Risk" else "#d8d8d8"
            amber = "#ff8c00" if risk_label == "Warning" else "#d8d8d8"
            green = "#2ca25f" if risk_label == "Normal" else "#d8d8d8"
            return (
                "<span style='display:inline-flex;align-items:center;gap:3px;"
                "margin-left:6px;padding:1px 6px;border-radius:10px;background:#f5f5f5;"
                "border:1px solid #ddd;font-size:11px;vertical-align:middle;'>"
                "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
                f"background:{red};'></span>"
                "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
                f"background:{amber};'></span>"
                "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
                f"background:{green};'></span>"
                f"<span style='margin-left:2px;color:{meta['color']};'>{escape(meta['label'])}</span>"
                "</span>"
            )

        risk_lookup = {}
        if shelter_analysis_path and os.path.exists(shelter_analysis_path):
            try:
                with open(shelter_analysis_path, "r", encoding="utf-8-sig") as rf:
                    risk_reader = csv.DictReader(rf)
                    for risk_row in risk_reader:
                        try:
                            key = shelter_key(
                                risk_row.get("避難收容處所名稱", ""),
                                risk_row.get("經度", 0),
                                risk_row.get("緯度", 0),
                            )
                        except (TypeError, ValueError):
                            continue
                        risk_lookup[key] = {
                            "risk_label": risk_row.get("risk_label", "Normal"),
                            "nearest_station": risk_row.get("nearest_station", ""),
                            "nearest_aqi": risk_row.get("nearest_aqi", ""),
                            "distance_km": risk_row.get("distance_km", ""),
                        }
            except Exception as exc:
                print(f"Failed to load shelter risk analysis CSV: {exc}")

        center = list(map_center or self.default_map_center)
        aqi_map = folium.Map(location=center, zoom_start=zoom_start)

        legend_html = '''
    <div style="
        position: fixed;
        top: 10px;
        right: 10px;
        width: 260px;
        background: white;
        border: 2px solid #666;
        z-index: 9999;
        font-size: 13px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        border-radius: 5px;
    ">
      <b>AQI Legend (測站狀態)</b><br>
      <span style="color:green; font-size: 16px;">&#9679;</span> 0-50 (Good 良好)<br>
      <span style="color:#c9a000; font-size: 16px;">&#9679;</span> 51-100 (Moderate 普通)<br>
      <span style="color:red; font-size: 16px;">&#9679;</span> 101+ (Unhealthy 不良)<br>
      <span style="color:gray; font-size: 16px;">&#9679;</span> Unknown (未知)<br>
      <hr style="margin:6px 0; border: 0; border-top: 1px solid #ccc;">
      <b>Shelters (避難收容處所)</b><br>
      <div style="margin: 4px 0;">
        <i class="fa fa-home" style="color: white; background-color: #38AADD; padding: 4px; border-radius: 50%; width: 22px; height: 22px; text-align: center; line-height: 14px; box-shadow: 0 0 2px rgba(0,0,0,0.5);"></i>
        Indoor (室內)
      </div>
      <div style="margin: 4px 0;">
        <i class="fa fa-tree" style="color: white; background-color: #F69730; padding: 4px; border-radius: 50%; width: 22px; height: 22px; text-align: center; line-height: 14px; box-shadow: 0 0 2px rgba(0,0,0,0.5);"></i>
        Outdoor (室外)
      </div>
      <hr style="margin:6px 0; border: 0; border-top: 1px solid #ccc;">
      <b>Shelter Risk Label</b><br>
      <span style="color:#d73027; font-size: 16px;">&#9679;</span> High Risk<br>
      <span style="color:#ff8c00; font-size: 16px;">&#9679;</span> Warning<br>
      <span style="color:#2ca25f; font-size: 16px;">&#9679;</span> Normal<br>
    </div>
    '''
        aqi_map.get_root().html.add_child(folium.Element(legend_html))

        # 1) AQI layer groups
        layer_groups = {}
        clusters = {}
        for bucket in AQI_BUCKET_ORDER:
            group = folium.FeatureGroup(name=AQI_BUCKET_LABELS[bucket], show=True)
            layer_groups[bucket] = group
            clusters[bucket] = MarkerCluster().add_to(group)

        markers_added = 0
        markers_skipped = 0

        for record in df.to_dict("records"):
            lat = safe_float(record.get("latitude"))
            lon = safe_float(record.get("longitude"))
            if lat in (None, 0.0) or lon in (None, 0.0):
                markers_skipped += 1
                continue

            bucket = aqi_bucket_key(record.get("aqi"))
            color = self.get_aqi_color(record.get("aqi"))

            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(self._build_popup_html(record), max_width=320),
                color="white",
                weight=1.5,
                fill=True,
                fillColor=color,
                fillOpacity=0.85,
                tooltip=f"{format_value(record.get('sitename'))} - AQI: {format_value(record.get('aqi'))}",
            )
            marker.add_to(clusters[bucket])
            markers_added += 1

        # 2) Shelter groups by indoor/outdoor
        shelter_group_indoor = folium.FeatureGroup(name="Shelters (Indoor)", show=True)
        shelter_group_outdoor = folium.FeatureGroup(name="Shelters (Outdoor)", show=True)
        cluster_indoor = MarkerCluster().add_to(shelter_group_indoor)
        cluster_outdoor = MarkerCluster().add_to(shelter_group_outdoor)

        # 3) Shelter groups by risk label
        risk_order = ["High Risk", "Warning", "Normal"]
        risk_marker_styles = {
            "High Risk": {"color": "#d73027", "radius": 7},
            "Warning": {"color": "#ff8c00", "radius": 6},
            "Normal": {"color": "#2ca25f", "radius": 5},
        }
        shelter_risk_groups = {
            label: folium.FeatureGroup(name=f"Shelter Risk: {label}", show=False)
            for label in risk_order
        }
        risk_clusters = {
            label: MarkerCluster().add_to(group)
            for label, group in shelter_risk_groups.items()
        }

        shelters_added = 0
        shelters_with_risk = 0
        if os.path.exists(shelter_file):
            with open(shelter_file, "r", encoding="utf-8-sig") as sf:
                s_reader = csv.DictReader(sf)
                for s_row in s_reader:
                    try:
                        s_lat = float(s_row.get("緯度", 0))
                        s_lon = float(s_row.get("經度", 0))
                    except ValueError:
                        continue
                    
                    if s_lat == 0 or s_lon == 0:
                        continue
                        
                    is_indoor = s_row.get("is_indoor", "") == "True"
                    name = s_row.get("避難收容處所名稱", "Unknown")

                    s_color = "cadetblue" if is_indoor else "orange"
                    s_icon = "home" if is_indoor else "tree"
                    target_cluster = cluster_indoor if is_indoor else cluster_outdoor
                    key = shelter_key(name, s_lon, s_lat)
                    risk_info = risk_lookup.get(key, {})
                    risk_label = risk_info.get("risk_label", "Unknown")
                    risk_badge = traffic_light_badge(risk_label)

                    popup_lines = [
                        f"<b>{escape(name)}</b>{risk_badge}",
                        "Indoor" if is_indoor else "Outdoor",
                    ]
                    popup_lines.append(f"Risk: {escape(str(risk_label))}")
                    if risk_label != "Unknown":
                        popup_lines.append(
                            f"Nearest station: {escape(format_value(risk_info.get('nearest_station')))}"
                        )
                        popup_lines.append(
                            f"Nearest AQI: {escape(format_value(risk_info.get('nearest_aqi')))}"
                        )
                    tooltip_html = (
                        f"<span>{traffic_light_badge(risk_label)}</span>"
                        f"<span style='margin-left:4px'>{escape(name)}</span>"
                    )

                    folium.Marker(
                        location=[s_lat, s_lon],
                        popup=folium.Popup("<br>".join(popup_lines), max_width=320),
                        icon=folium.Icon(color=s_color, icon=s_icon, prefix="fa"),
                        tooltip=folium.Tooltip(tooltip_html, sticky=True),
                    ).add_to(target_cluster)
                    shelters_added += 1

                    if risk_label in risk_clusters:
                        style = risk_marker_styles[risk_label]
                        folium.CircleMarker(
                            location=[s_lat, s_lon],
                            radius=style["radius"],
                            color=style["color"],
                            weight=1.5,
                            fill=True,
                            fillColor=style["color"],
                            fillOpacity=0.75,
                            tooltip=f"{name} | {risk_label}",
                        ).add_to(risk_clusters[risk_label])
                        shelters_with_risk += 1
        else:
            print(f"Shelter file not found: {shelter_file}")

        # 4) Add groups to map
        shelter_group_indoor.add_to(aqi_map)
        shelter_group_outdoor.add_to(aqi_map)
        for label in risk_order:
            shelter_risk_groups[label].add_to(aqi_map)
        for bucket in AQI_BUCKET_ORDER:
            layer_groups[bucket].add_to(aqi_map)

        # 5) Grouped layer control
        from folium.plugins import GroupedLayerControl
        grouped_layers = {
            "空氣品質觀測站 (AQI)": [layer_groups[b] for b in AQI_BUCKET_ORDER],
            "避難收容處所 (Shelters)": [shelter_group_indoor, shelter_group_outdoor],
            "避難所風險標籤 (Risk Label)": [shelter_risk_groups[label] for label in risk_order],
        }
        GroupedLayerControl(
            groups=grouped_layers,
            exclusive_groups=False,
            collapsed=False,
        ).add_to(aqi_map)

        # 6) Left-side layer tree panel (simple data tree with checkbox toggles)
        tree_html = """
    <div id="layer-tree-panel" style="
        position: fixed;
        top: 150px;
        left: 10px;
        width: 230px;
        max-height: 62vh;
        overflow-y: auto;
        background: rgba(255,255,255,0.96);
        border: 2px solid #666;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        z-index: 9998;
        font-size: 13px;
        padding: 10px 10px 8px 10px;
        line-height: 1.35;
    ">
      <div style="font-weight:bold;margin-bottom:6px;">資料樹 / Layer Tree</div>
      <div style="margin-bottom:6px;">
        <label><input type="checkbox" id="tree-aqi-parent" checked> AQI 測站</label>
        <div style="margin-left:16px;">
          <label><input type="checkbox" id="tree-aqi-good" checked> AQI 0-50</label><br>
          <label><input type="checkbox" id="tree-aqi-moderate" checked> AQI 51-100</label><br>
          <label><input type="checkbox" id="tree-aqi-unhealthy" checked> AQI 101+</label><br>
          <label><input type="checkbox" id="tree-aqi-unknown" checked> AQI Unknown</label>
        </div>
      </div>
      <div style="margin-bottom:6px;">
        <label><input type="checkbox" id="tree-shelter-parent" checked> 避難所</label>
        <div style="margin-left:16px;">
          <label><input type="checkbox" id="tree-shelter-indoor" checked> Indoor</label><br>
          <label><input type="checkbox" id="tree-shelter-outdoor" checked> Outdoor</label>
        </div>
      </div>
      <div>
        <label><input type="checkbox" id="tree-risk-parent"> 風險標籤</label>
        <div style="margin-left:16px;">
          <label><input type="checkbox" id="tree-risk-high"> High Risk</label><br>
          <label><input type="checkbox" id="tree-risk-warning"> Warning</label><br>
          <label><input type="checkbox" id="tree-risk-normal"> Normal</label>
        </div>
      </div>
    </div>
    """
        aqi_map.get_root().html.add_child(folium.Element(tree_html))

        tree_js = f"""
        (function initLayerTree() {{
            if (
                typeof {aqi_map.get_name()} === "undefined" ||
                typeof {layer_groups["good"].get_name()} === "undefined" ||
                typeof {shelter_group_indoor.get_name()} === "undefined"
            ) {{
                setTimeout(initLayerTree, 120);
                return;
            }}

            var mapObj = {aqi_map.get_name()};
            var layerRefs = {{
                "tree-aqi-good": {layer_groups["good"].get_name()},
                "tree-aqi-moderate": {layer_groups["moderate"].get_name()},
                "tree-aqi-unhealthy": {layer_groups["unhealthy"].get_name()},
                "tree-aqi-unknown": {layer_groups["unknown"].get_name()},
                "tree-shelter-indoor": {shelter_group_indoor.get_name()},
                "tree-shelter-outdoor": {shelter_group_outdoor.get_name()},
                "tree-risk-high": {shelter_risk_groups["High Risk"].get_name()},
                "tree-risk-warning": {shelter_risk_groups["Warning"].get_name()},
                "tree-risk-normal": {shelter_risk_groups["Normal"].get_name()}
            }};

            var parentRefs = {{
                "tree-aqi-parent": ["tree-aqi-good", "tree-aqi-moderate", "tree-aqi-unhealthy", "tree-aqi-unknown"],
                "tree-shelter-parent": ["tree-shelter-indoor", "tree-shelter-outdoor"],
                "tree-risk-parent": ["tree-risk-high", "tree-risk-warning", "tree-risk-normal"]
            }};

            function setLayerVisible(layerId, visible) {{
                var layer = layerRefs[layerId];
                if (!layer) return;
                if (visible) {{
                    if (!mapObj.hasLayer(layer)) {{
                        mapObj.addLayer(layer);
                    }}
                }} else {{
                    if (mapObj.hasLayer(layer)) {{
                        mapObj.removeLayer(layer);
                    }}
                }}
            }}

            function syncParentStates() {{
                Object.keys(parentRefs).forEach(function(parentId) {{
                    var parent = document.getElementById(parentId);
                    if (!parent) return;
                    var childIds = parentRefs[parentId];
                    var checkedCount = childIds.reduce(function(total, childId) {{
                        var child = document.getElementById(childId);
                        return total + ((child && child.checked) ? 1 : 0);
                    }}, 0);
                    parent.checked = checkedCount === childIds.length;
                    parent.indeterminate = checkedCount > 0 && checkedCount < childIds.length;
                }});
            }}

            Object.keys(layerRefs).forEach(function(layerId) {{
                var node = document.getElementById(layerId);
                if (!node) return;
                setLayerVisible(layerId, node.checked);
                node.addEventListener("change", function() {{
                    setLayerVisible(layerId, this.checked);
                    syncParentStates();
                }});
            }});

            Object.keys(parentRefs).forEach(function(parentId) {{
                var parent = document.getElementById(parentId);
                if (!parent) return;
                parent.addEventListener("change", function() {{
                    var checked = this.checked;
                    this.indeterminate = false;
                    parentRefs[parentId].forEach(function(childId) {{
                        var child = document.getElementById(childId);
                        if (!child) return;
                        child.checked = checked;
                        setLayerVisible(childId, checked);
                    }});
                    syncParentStates();
                }});
            }});

            syncParentStates();
        }})();
        """
        aqi_map.get_root().script.add_child(folium.Element(tree_js))

        ensure_parent_dir(save_path)
        aqi_map.save(save_path)
        self.last_map_stats = {
            "map_markers_added": markers_added,
            "map_markers_skipped": markers_skipped,
        }
        print(f"Shelter markers added: {shelters_added} (risk-labeled: {shelters_with_risk})")
        print(f"AQI map saved to {save_path}")
        return save_path

    def save_data_to_csv(self, save_path="outputs/aqi_analysis.csv", df=None):
        """Save AQI data with distance calculation to CSV file."""
        if not self.aqi_data:
            print("No AQI data available. Please fetch data first.")
            return False

        try:
            if df is None:
                df = self.build_processed_dataframe()

            ensure_parent_dir(save_path)
            df.to_csv(save_path, index=False, encoding="utf-8-sig")
            print(f"AQI analysis data saved to {save_path}")

            if "distance_from_taipei_km" in df.columns:
                valid_distances = pd.to_numeric(
                    df["distance_from_taipei_km"], errors="coerce"
                ).dropna()
                if not valid_distances.empty:
                    print("Distance statistics:")
                    print(f"  Closest station: {valid_distances.min():.2f} km")
                    print(
                        f"  Farthest station: {valid_distances.max():.2f} km")
                    print(
                        f"  Average distance: {valid_distances.mean():.2f} km")
            return True
        except Exception as exc:
            print(f"Error saving CSV: {exc}")
            return False

    def append_history(self, df, history_path, run_meta):
        """Append processed records to a history CSV (append-only)."""
        if df is None or df.empty:
            return {"history_path": history_path, "history_rows_appended": 0}

        history_df = df.copy()
        history_df["run_timestamp"] = run_meta.get("run_timestamp")
        history_df["run_id"] = run_meta.get("run_id")

        ensure_parent_dir(history_path)
        if os.path.exists(history_path):
            existing_df = pd.read_csv(history_path, encoding="utf-8-sig")
            combined_df = pd.concat(
                [existing_df, history_df], ignore_index=True, sort=False)
        else:
            combined_df = history_df

        combined_df.to_csv(history_path, index=False, encoding="utf-8-sig")
        return {
            "history_path": history_path,
            "history_rows_appended": int(len(history_df.index)),
            "history_total_rows": int(len(combined_df.index)),
        }

    def build_run_summary(
        self,
        run_started_at,
        run_finished_at,
        options,
        output_paths,
        success,
        errors=None,
    ):
        """Build a run summary dict with output metadata and quality stats."""
        errors = list(errors or [])
        duration_seconds = round(
            (run_finished_at - run_started_at).total_seconds(), 3)

        def output_meta(path):
            exists = os.path.exists(path)
            return {
                "path": path,
                "exists": exists,
                "size_bytes": os.path.getsize(path) if exists else None,
            }

        summary = {
            "success": bool(success),
            "run_started_at": run_started_at.isoformat(timespec="seconds"),
            "run_finished_at": run_finished_at.isoformat(timespec="seconds"),
            "duration_seconds": duration_seconds,
            "options": options,
            "api": {
                "base_url": self.base_url,
                "response_format": self.last_fetch_metadata.get("response_format"),
                "records_count": int(self.last_fetch_metadata.get("records_count", 0)),
                "fetch_success": bool(self.last_fetch_metadata.get("fetch_success", False)),
            },
            "outputs": {
                "csv": output_meta(output_paths["csv"]),
                "map": output_meta(output_paths["map"]),
                "summary": output_meta(output_paths["summary"]),
            },
            "quality": self.last_quality_stats or self.compute_quality_stats(),
            "errors": errors,
        }
        self.last_run_summary = summary
        return summary

    def save_run_summary(self, summary, save_path):
        """Save run summary to JSON."""
        ensure_parent_dir(save_path)
        with open(save_path, "w", encoding="utf-8") as file:
            json.dump(summary, file, ensure_ascii=False, indent=2)
        if "outputs" in summary and "summary" in summary["outputs"]:
            summary["outputs"]["summary"] = {
                "path": save_path,
                "exists": True,
                "size_bytes": os.path.getsize(save_path),
            }
            with open(save_path, "w", encoding="utf-8") as file:
                json.dump(summary, file, ensure_ascii=False, indent=2)
        return save_path

    def print_quality_summary(self, quality_stats):
        print("Quality summary:")
        print(f"  Records fetched: {quality_stats['records_fetched_total']}")
        print(
            f"  Records processed: {quality_stats['records_processed_for_csv']}")
        print(
            f"  Valid coordinates: {quality_stats['records_with_valid_coordinates']}")
        print(
            "  Invalid coordinates: "
            f"{quality_stats['records_missing_or_invalid_coordinates']}"
        )
        print(f"  Map markers added: {quality_stats['map_markers_added']}")
        print(f"  Map markers skipped: {quality_stats['map_markers_skipped']}")


def run_pipeline(
    output_dir="outputs",
    csv_only=False,
    map_only=False,
    timestamped_output=False,
    save_history=False,
    history_path="data/aqi_history.csv",
    center_lat=None,
    center_lon=None,
    map_zoom=DEFAULT_MAP_ZOOM,
    api_key=None,
):
    """Run the AQI pipeline with optional CLI-style parameters."""
    run_started_at = datetime.now()
    timestamp_token = run_started_at.strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp_token}_{uuid.uuid4().hex[:8]}"
    output_paths = build_output_paths(
        output_dir=output_dir,
        timestamped=timestamped_output,
        timestamp_token=timestamp_token,
    )
    errors = []

    options = {
        "output_dir": output_dir,
        "csv_only": bool(csv_only),
        "map_only": bool(map_only),
        "timestamped_output": bool(timestamped_output),
        "save_history": bool(save_history),
        "history_path": history_path,
        "center_lat": center_lat,
        "center_lon": center_lon,
        "map_zoom": int(map_zoom),
        "run_id": run_id,
    }

    if (center_lat is None) != (center_lon is None):
        raise ValueError("center-lat and center-lon must be provided together")

    reference_coords = (
        (float(center_lat), float(center_lon))
        if center_lat is not None and center_lon is not None
        else DEFAULT_REFERENCE_COORDS
    )
    map_center = reference_coords if center_lat is not None else DEFAULT_MAP_CENTER

    print("=== AQI Monitoring and Analysis ===")
    print(f"Output directory: {output_dir}")
    if timestamped_output:
        print(f"Timestamped outputs enabled ({timestamp_token})")

    monitor = AQIMonitor(
        api_key=api_key, reference_coords=reference_coords, map_center=map_center)

    fetch_success = monitor.fetch_aqi_data()
    csv_success = False
    map_success = False
    history_info = None
    df = pd.DataFrame()

    if fetch_success:
        df = monitor.build_processed_dataframe()

        csv_requested = not map_only
        map_requested = not csv_only

        if csv_requested:
            csv_success = monitor.save_data_to_csv(output_paths["csv"], df=df)
        else:
            csv_success = True

        if map_requested:
            map_path = monitor.create_aqi_map(
                output_paths["map"], df=df, map_center=map_center, zoom_start=map_zoom
            )
            map_success = bool(map_path)
        else:
            map_success = True

        if save_history:
            try:
                history_info = monitor.append_history(
                    df,
                    history_path=history_path,
                    run_meta={
                        "run_timestamp": run_started_at.isoformat(timespec="seconds"),
                        "run_id": run_id,
                    },
                )
                print(
                    "History updated: "
                    f"{history_info['history_rows_appended']} rows appended "
                    f"to {history_info['history_path']}"
                )
            except Exception as exc:
                errors.append(f"History append failed: {exc}")
                print(errors[-1])
    else:
        errors.append("AQI fetch failed")

    monitor.compute_quality_stats(df)
    monitor.last_fetch_metadata["history"] = history_info

    success = fetch_success and csv_success and map_success
    run_finished_at = datetime.now()
    summary = monitor.build_run_summary(
        run_started_at=run_started_at,
        run_finished_at=run_finished_at,
        options=options,
        output_paths=output_paths,
        success=success,
        errors=errors,
    )
    monitor.save_run_summary(summary, output_paths["summary"])
    monitor.print_quality_summary(summary["quality"])
    print(f"Run summary saved to {output_paths['summary']}")

    return {
        "success": success,
        "summary": summary,
        "paths": output_paths,
        "monitor": monitor,
    }


def main():
    """Backward-compatible default entrypoint (no CLI args)."""
    result = run_pipeline()
    return result["success"]


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
