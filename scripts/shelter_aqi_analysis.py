"""
Shelter-AQI analysis:
1) Link each shelter to nearest AQI station (Haversine)
2) Label risk
3) Export outputs/shelter_aqi_analysis.csv
4) Generate outputs/aqi_map.html with risk layer groups
"""

import csv
import math
import os

from aqi_monitor import AQIMonitor

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELTER_FILE = os.path.join(PROJECT_ROOT, "data", "shelters_cleaned.csv")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "outputs", "shelter_aqi_analysis.csv")
OUTPUT_MAP = os.path.join(PROJECT_ROOT, "outputs", "aqi_map.html")

# Scenario injection config
OVERRIDE_STATION = "林口"
OVERRIDE_AQI = 150


def haversine_km(lon1, lat1, lon2, lat2):
    """Calculate distance in km between two WGS84 points."""
    radius_km = 6371.0
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return radius_km * 2 * math.asin(math.sqrt(a))


def load_shelters(path):
    """Load cleaned shelter CSV."""
    shelters = []
    with open(path, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                lon = float(row.get("經度", 0))
                lat = float(row.get("緯度", 0))
            except (TypeError, ValueError):
                continue
            if lon == 0 or lat == 0:
                continue
            shelters.append(
                {
                    "name": row.get("避難收容處所名稱", ""),
                    "district": row.get("縣市及鄉鎮市區", ""),
                    "lon": lon,
                    "lat": lat,
                    "is_indoor": row.get("is_indoor", "True") == "True",
                }
            )
    return shelters


def fetch_aqi_stations():
    """Fetch AQI stations and return (monitor, stations)."""
    monitor = AQIMonitor()
    ok = monitor.fetch_aqi_data()
    if not ok:
        raise RuntimeError("Failed to fetch AQI data from MOENV API.")

    stations = []
    for index, record in enumerate(monitor.aqi_data):
        try:
            lat = float(record.get("latitude", 0))
            lon = float(record.get("longitude", 0))
            aqi = int(float(record.get("aqi", -1)))
        except (TypeError, ValueError):
            continue
        if lat == 0 or lon == 0:
            continue
        stations.append(
            {
                "name": record.get("sitename", ""),
                "county": record.get("county", ""),
                "lon": lon,
                "lat": lat,
                "aqi": aqi,
                "record_index": index,
            }
        )
    return monitor, stations


def should_inject_scenario(stations):
    """
    Decide whether to inject a simulated AQI spike.

    Required by assignment when all AQI are below 50.
    Also inject when no station exceeds 100 so the High Risk branch is testable.
    """
    values = [s["aqi"] for s in stations if isinstance(s.get("aqi"), int) and s["aqi"] >= 0]
    if not values:
        return False, "No valid AQI value found."
    peak = max(values)
    if peak < 50:
        return True, "All AQI values are below 50."
    if peak <= 100:
        return True, "No AQI value exceeds 100; inject to validate High Risk logic."
    return False, "Current AQI already includes >100 values."


def apply_override(stations, station_name, aqi_value, monitor=None):
    """Override a specific station's AQI (simulation)."""
    overridden = False
    for station in stations:
        if station_name in station["name"]:
            print(
                f"[OVERRIDE] {station['name']} AQI: {station['aqi']} -> {aqi_value} (SIMULATED)"
            )
            station["aqi"] = aqi_value
            if monitor is not None:
                try:
                    record = monitor.aqi_data[station["record_index"]]
                    record["aqi"] = str(aqi_value)
                except Exception:
                    pass
            overridden = True
    if not overridden:
        print(f"WARNING: Station '{station_name}' not found for override.")
    if overridden and monitor is not None:
        monitor.processed_df = None
    return overridden


def find_nearest_station(shelter, stations):
    """Find the nearest AQI station for a shelter using Haversine."""
    best_dist = float("inf")
    best_station = None
    for station in stations:
        dist = haversine_km(shelter["lon"], shelter["lat"], station["lon"], station["lat"])
        if dist < best_dist:
            best_dist = dist
            best_station = station
    return best_station, round(best_dist, 2)


def compute_risk_label(aqi_value, is_indoor):
    """
    Risk labeling:
      High Risk: nearest AQI > 100
      Warning: nearest AQI > 50 and outdoor
      Normal: otherwise
    """
    if aqi_value > 100:
        return "High Risk"
    if aqi_value > 50 and not is_indoor:
        return "Warning"
    return "Normal"


def inject_simulation_banner(map_path):
    """Inject a visible simulated-data banner at the top of map HTML."""
    if not os.path.exists(map_path):
        return
    with open(map_path, "r", encoding="utf-8") as file:
        html = file.read()
    marker = "SIMULATED_SCENARIO_BANNER"
    if marker in html:
        return
    banner = (
        f'<div id="{marker}" style="position:fixed;top:0;left:0;right:0;'
        "background:#ff5722;color:white;text-align:center;padding:8px 16px;"
        "font-size:14px;font-weight:bold;z-index:99999;"
        'box-shadow:0 2px 4px rgba(0,0,0,0.3);">'
        f"Simulated data: {OVERRIDE_STATION} AQI set to {OVERRIDE_AQI}</div>"
    )
    html = html.replace("<body>", f"<body>\n{banner}", 1)
    with open(map_path, "w", encoding="utf-8") as file:
        file.write(html)


def main():
    print("=" * 60)
    print("Shelter-AQI Risk Analysis")
    print("=" * 60)

    shelters = load_shelters(SHELTER_FILE)
    print(f"Loaded {len(shelters)} shelters")

    monitor, stations = fetch_aqi_stations()
    print(f"Fetched {len(stations)} AQI stations")

    scenario_applied = False
    should_inject, scenario_reason = should_inject_scenario(stations)
    if should_inject:
        print(f"[INFO] Scenario injection enabled: {scenario_reason}")
        scenario_applied = apply_override(
            stations, OVERRIDE_STATION, OVERRIDE_AQI, monitor=monitor
        )
    else:
        print(f"[INFO] Scenario injection skipped: {scenario_reason}")

    results = []
    for shelter in shelters:
        nearest, dist_km = find_nearest_station(shelter, stations)
        if nearest is None:
            continue
        results.append(
            {
                "避難收容處所名稱": shelter["name"],
                "縣市及鄉鎮市區": shelter["district"],
                "經度": shelter["lon"],
                "緯度": shelter["lat"],
                "is_indoor": shelter["is_indoor"],
                "nearest_station": nearest["name"],
                "nearest_aqi": nearest["aqi"],
                "distance_km": dist_km,
                "risk_label": compute_risk_label(nearest["aqi"], shelter["is_indoor"]),
            }
        )

    fieldnames = [
        "避難收容處所名稱",
        "縣市及鄉鎮市區",
        "經度",
        "緯度",
        "is_indoor",
        "nearest_station",
        "nearest_aqi",
        "distance_km",
        "risk_label",
    ]
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved {len(results)} rows to {OUTPUT_CSV}")

    high_risk = sum(1 for row in results if row["risk_label"] == "High Risk")
    warning = sum(1 for row in results if row["risk_label"] == "Warning")
    normal = sum(1 for row in results if row["risk_label"] == "Normal")
    print("Risk Summary:")
    print(f"  High Risk: {high_risk}")
    print(f"  Warning:   {warning}")
    print(f"  Normal:    {normal}")

    print("\nGenerating map...")
    df = monitor.build_processed_dataframe()
    map_path = monitor.create_aqi_map(
        save_path=OUTPUT_MAP,
        df=df,
        shelter_file=SHELTER_FILE,
        shelter_analysis_path=OUTPUT_CSV,
    )
    if map_path and scenario_applied:
        inject_simulation_banner(map_path)
        print("Simulation banner injected into map HTML.")
    print("[DONE] Analysis complete.")


if __name__ == "__main__":
    main()
