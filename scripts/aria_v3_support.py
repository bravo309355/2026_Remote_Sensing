from __future__ import annotations

import html
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import rioxarray
from branca.element import Element
from folium.plugins import HeatMap
from rasterstats import zonal_stats
from shapely.geometry import mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_CRS = "EPSG:3826"
DEFAULT_TARGET_COUNTIES = ["花蓮縣", "宜蘭縣"]
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
CWA_DATASET_ID = "O-A0002-001"
CWA_DATASET_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{CWA_DATASET_ID}"
RISK_PRIORITY = {"CRITICAL": 0, "URGENT": 1, "WARNING": 2, "SAFE": 3}


@dataclass
class ARIAV3Config:
    river_shp_path: Path
    shelter_csv_path: Path
    township_shp_path: Path
    dem_path: Path
    simulation_data_path: Path
    target_counties: list[str]
    slope_threshold: float
    elevation_low: float
    buffer_high: float
    county_buffer: float
    output_dir: Path
    submission_dir: Path
    app_mode: str
    rain_buffer_m: float
    warning_rain_mm: float
    critical_rain_mm: float
    cwa_api_key: str | None
    live_timeout_s: float
    gemini_api_key: str | None
    gemini_model: str
    gemini_request_delay_s: float
    rebuild_static_baseline: bool


def project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def normalize_name(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace(" ", "").replace("\u3000", "").replace("台", "臺").strip()


def geometry_union(series: gpd.GeoSeries):
    union_all = getattr(series, "union_all", None)
    if callable(union_all):
        return union_all()
    return series.unary_union


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def find_one(base: Path, pattern: str) -> Path:
    matches = sorted(base.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"Could not find {pattern!r} under {base}")
    return matches[0]


def _normalize_counties(value: str | None) -> list[str]:
    if not value:
        return [normalize_name(item) for item in DEFAULT_TARGET_COUNTIES]
    return [part for part in (normalize_name(piece) for piece in value.split(",")) if part]


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def build_config_from_env(env_path: Path | None = None) -> ARIAV3Config:
    env = load_env_file(env_path or (PROJECT_ROOT / ".env"))
    data_dir = project_path(env.get("DATA_DIR", "data"))
    return ARIAV3Config(
        river_shp_path=project_path(env.get("RIVER_SHP_PATH", str(find_one(data_dir, "**/riverpoly.shp")))),
        shelter_csv_path=project_path(env.get("SHELTER_CSV_PATH", str(find_one(data_dir, "*v9.csv")))),
        township_shp_path=project_path(
            env.get("TOWNSHIP_SHP_PATH", str(find_one(data_dir, "**/TOWN_MOI_1140318.shp")))
        ),
        dem_path=project_path(env.get("DEM_PATH", "data/DEM_tawiwan_V2025.tif")),
        simulation_data_path=project_path(env.get("SIMULATION_DATA", "data/scenarios/fungwong_202511.json")),
        target_counties=_normalize_counties(env.get("TARGET_COUNTIES") or env.get("TARGET_COUNTY")),
        slope_threshold=float(env.get("SLOPE_THRESHOLD", "30")),
        elevation_low=float(env.get("ELEVATION_LOW", "50")),
        buffer_high=float(env.get("BUFFER_HIGH", "500")),
        county_buffer=float(env.get("COUNTY_BUFFER", "1000")),
        output_dir=project_path(env.get("OUTPUT_DIR", "outputs/aria_v3")),
        submission_dir=project_path(env.get("SUBMISSION_DIR", "submission/Homework-5")),
        app_mode=env.get("APP_MODE", "SIMULATION").strip().upper() or "SIMULATION",
        rain_buffer_m=float(env.get("RAIN_BUFFER_M", "5000")),
        warning_rain_mm=float(env.get("WARNING_RAIN_MM", "40")),
        critical_rain_mm=float(env.get("CRITICAL_RAIN_MM", "80")),
        cwa_api_key=env.get("CWA_API_KEY") or env.get("API_KEY_CWA") or None,
        live_timeout_s=float(env.get("LIVE_TIMEOUT_S", "12")),
        gemini_api_key=env.get("GEMINI_API_KEY") or None,
        gemini_model=env.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        gemini_request_delay_s=float(env.get("GEMINI_REQUEST_DELAY_S", "1.5")),
        rebuild_static_baseline=env.get("REBUILD_STATIC_BASELINE", "0").strip().lower() in {"1", "true", "yes"},
    )


def load_shelter_table(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, encoding="utf-8")
    return pd.DataFrame(
        {
            "shelter_id": raw.iloc[:, 0].astype(str).str.strip(),
            "county_hint": raw.iloc[:, 1].fillna("").astype(str).str.strip(),
            "longitude": pd.to_numeric(raw.iloc[:, 4], errors="coerce"),
            "latitude": pd.to_numeric(raw.iloc[:, 5], errors="coerce"),
            "name": raw.iloc[:, 6].fillna("").astype(str).str.strip(),
            "capacity": pd.to_numeric(raw.iloc[:, 8], errors="coerce").fillna(0).astype(int),
        }
    )


def split_zero_and_null_coordinates(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    invalid = (
        df["longitude"].isna()
        | df["latitude"].isna()
        | df["longitude"].eq(0)
        | df["latitude"].eq(0)
    )
    return df.loc[~invalid].copy(), df.loc[invalid].copy()


def build_shelter_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )


def load_townships(path: Path) -> gpd.GeoDataFrame:
    townships = gpd.read_file(path)
    if townships.crs is None:
        raise ValueError("Township shapefile is missing a CRS.")
    townships = townships.to_crs(ANALYSIS_CRS)
    townships["COUNTYNAME"] = townships["COUNTYNAME"].map(normalize_name)
    townships["TOWNNAME"] = townships["TOWNNAME"].map(normalize_name)
    return townships[["COUNTYNAME", "TOWNNAME", "geometry"]].copy()


def load_rivers(path: Path) -> gpd.GeoDataFrame:
    rivers = gpd.read_file(path)
    if rivers.crs is None:
        raise ValueError("River shapefile is missing a CRS.")
    return rivers.to_crs(ANALYSIS_CRS)


def filter_shelters_on_land(
    shelters: gpd.GeoDataFrame,
    townships: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    shelters_analysis = shelters.to_crs(ANALYSIS_CRS)
    land_mask = geometry_union(townships.geometry)
    inside = shelters_analysis.geometry.intersects(land_mask)
    return shelters_analysis.loc[inside].copy(), shelters_analysis.loc[~inside].copy()


def attach_townships(shelters: gpd.GeoDataFrame, townships: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    left = shelters.reset_index(drop=True).copy()
    left["row_id"] = left.index
    joined = gpd.sjoin(
        left[["row_id", "geometry"]],
        townships[["COUNTYNAME", "TOWNNAME", "geometry"]],
        how="left",
        predicate="intersects",
    )
    joined = joined.sort_values(["row_id", "COUNTYNAME", "TOWNNAME"]).drop_duplicates(subset=["row_id"])
    merged = left.merge(joined[["row_id", "COUNTYNAME", "TOWNNAME"]], on="row_id", how="left")
    return merged.drop(columns="row_id")


def build_target_boundary(townships: gpd.GeoDataFrame, county_name: str) -> gpd.GeoDataFrame:
    target = normalize_name(county_name)
    county_rows = townships.loc[townships["COUNTYNAME"] == target].copy()
    if county_rows.empty:
        raise ValueError(f"Could not find county {county_name!r} in township boundaries.")
    dissolved = county_rows.dissolve().reset_index(drop=True)
    dissolved["COUNTYNAME"] = target
    return dissolved[["COUNTYNAME", "geometry"]]


def compute_slope_degrees(elevation: np.ndarray, pixel_size: float = 20.0) -> np.ndarray:
    filled = np.array(elevation, dtype="float64")
    finite = np.isfinite(filled)
    if not finite.any():
        return np.full_like(filled, np.nan, dtype="float64")
    fill_value = float(np.nanmedian(filled[finite]))
    filled[~finite] = fill_value
    dy, dx = np.gradient(filled, pixel_size, pixel_size)
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    slope[~finite] = np.nan
    return slope


def zonal_stats_for_buffers(
    buffers: gpd.GeoDataFrame,
    elevation: np.ndarray,
    slope: np.ndarray,
    affine,
) -> pd.DataFrame:
    elevation_nodata = np.where(np.isfinite(elevation), elevation, -9999)
    slope_nodata = np.where(np.isfinite(slope), slope, -9999)
    elev_stats = zonal_stats(buffers.geometry, elevation_nodata, affine=affine, nodata=-9999, stats=["mean", "std"])
    slope_stats = zonal_stats(buffers.geometry, slope_nodata, affine=affine, nodata=-9999, stats=["max"])
    return pd.DataFrame(
        {
            "shelter_id": buffers["shelter_id"].astype(str).tolist(),
            "mean_elevation": [row.get("mean") for row in elev_stats],
            "std_elevation": [row.get("std") for row in elev_stats],
            "max_slope": [row.get("max") for row in slope_stats],
        }
    )


def classify_risk(
    river_distance_m: float,
    max_slope: float | None,
    mean_elevation: float | None,
    slope_threshold: float,
    elevation_low: float,
) -> str:
    if river_distance_m < 500 and pd.notna(max_slope) and max_slope > slope_threshold:
        return "very_high"
    if river_distance_m < 500 or (pd.notna(max_slope) and max_slope > slope_threshold):
        return "high"
    if river_distance_m < 1000 and pd.notna(mean_elevation) and mean_elevation < elevation_low:
        return "medium"
    return "low"


def clip_dem_to_geometry(dem_path: Path, geometry, clip_crs: str) -> Any:
    dem = rioxarray.open_rasterio(dem_path, masked=True).squeeze(drop=True)
    if dem.rio.crs is None:
        dem = dem.rio.write_crs(ANALYSIS_CRS)
    if str(dem.rio.crs) != ANALYSIS_CRS:
        dem = dem.rio.reproject(ANALYSIS_CRS)
    return dem.rio.clip([mapping(geometry)], clip_crs, drop=True)


def build_static_baseline_for_county(
    config: ARIAV3Config,
    county_name: str,
    shelters_land: gpd.GeoDataFrame,
    townships: gpd.GeoDataFrame,
    rivers: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    normalized_county = normalize_name(county_name)
    county_boundary = build_target_boundary(townships, normalized_county)
    county_buffer_geom = county_boundary.geometry.iloc[0].buffer(config.county_buffer)
    rivers_in_county = gpd.sjoin(rivers, county_boundary[["geometry"]], how="inner", predicate="intersects")
    if rivers_in_county.empty:
        raise ValueError(f"River sanity check failed for {county_name}.")

    target_shelters = shelters_land.loc[shelters_land["COUNTYNAME"] == normalized_county].copy()
    if target_shelters.empty:
        raise ValueError(f"No shelters found in {county_name}.")

    river_union = geometry_union(rivers_in_county.geometry)
    target_shelters["distance_to_river_m"] = target_shelters.geometry.distance(river_union)
    target_shelters["river_distance_category"] = np.select(
        [
            target_shelters["distance_to_river_m"] < 500,
            target_shelters["distance_to_river_m"] < 1000,
        ],
        ["<500m", "500-1000m"],
        default=">=1000m",
    )

    dem = clip_dem_to_geometry(config.dem_path, county_buffer_geom, ANALYSIS_CRS)
    elevation = np.asarray(dem.values, dtype="float64")
    resolution = dem.rio.resolution()
    pixel_size = abs(float(resolution[0])) if resolution and resolution[0] else 20.0
    slope = compute_slope_degrees(elevation, pixel_size=pixel_size)

    shelter_buffers = target_shelters[["shelter_id", "geometry"]].copy()
    shelter_buffers["geometry"] = shelter_buffers.geometry.buffer(config.buffer_high)
    stats = zonal_stats_for_buffers(shelter_buffers, elevation, slope, dem.rio.transform())
    target_shelters = target_shelters.merge(stats, on="shelter_id", how="left")
    target_shelters["risk_level"] = target_shelters.apply(
        lambda row: classify_risk(
            river_distance_m=float(row["distance_to_river_m"]),
            max_slope=row["max_slope"],
            mean_elevation=row["mean_elevation"],
            slope_threshold=config.slope_threshold,
            elevation_low=config.elevation_low,
        ),
        axis=1,
    )
    target_shelters["terrain_risk"] = np.where(
        pd.to_numeric(target_shelters["max_slope"], errors="coerce") > config.slope_threshold,
        "HIGH",
        "LOW",
    )
    target_shelters["used_dem_path"] = str(config.dem_path)
    target_shelters["county_name"] = target_shelters["COUNTYNAME"]
    target_shelters["town_name"] = target_shelters["TOWNNAME"]
    return target_shelters


def build_static_baseline(config: ARIAV3Config) -> gpd.GeoDataFrame:
    rivers = load_rivers(config.river_shp_path)
    townships = load_townships(config.township_shp_path)
    shelters_raw = load_shelter_table(config.shelter_csv_path)
    shelters_valid, _ = split_zero_and_null_coordinates(shelters_raw)
    shelters_geo = build_shelter_geodataframe(shelters_valid)
    shelters_land, _ = filter_shelters_on_land(shelters_geo, townships)
    shelters_land = attach_townships(shelters_land, townships)
    frames = [
        build_static_baseline_for_county(config, county_name, shelters_land, townships, rivers)
        for county_name in config.target_counties
    ]
    combined = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry="geometry", crs=ANALYSIS_CRS)
    combined["shelter_id"] = combined["shelter_id"].astype(str)
    return combined


def static_baseline_cache_path(config: ARIAV3Config) -> Path:
    return config.output_dir / "static_baseline.geojson"


def save_geodataframe_geojson(path: Path, gdf: gpd.GeoDataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    gdf.to_crs("EPSG:4326").to_file(path, driver="GeoJSON")


def load_or_build_static_baseline(config: ARIAV3Config) -> gpd.GeoDataFrame:
    cache_path = static_baseline_cache_path(config)
    if cache_path.exists() and not config.rebuild_static_baseline:
        return gpd.read_file(cache_path).to_crs(ANALYSIS_CRS)
    baseline = build_static_baseline(config)
    save_geodataframe_geojson(cache_path, baseline)
    return baseline


def extract_wgs84_coordinate(coordinates: list[dict[str, Any]] | None) -> tuple[float | None, float | None]:
    coords = coordinates or []
    candidate = None
    for item in coords:
        lat = _coerce_float(item.get("StationLatitude"))
        lon = _coerce_float(item.get("StationLongitude"))
        if lat is not None and lon is not None:
            candidate = (lat, lon)
    return candidate if candidate else (None, None)


def normalize_cwa_json(raw: dict[str, Any]) -> list[dict[str, Any]]:
    stations = ((raw or {}).get("records") or {}).get("Station") or []
    normalized: list[dict[str, Any]] = []
    for station in stations:
        geo_info = station.get("GeoInfo") or {}
        lat, lon = extract_wgs84_coordinate(geo_info.get("Coordinates"))
        rain_1hr = _coerce_float(((station.get("RainfallElement") or {}).get("Past1hr") or {}).get("Precipitation"))
        normalized.append(
            {
                "station_id": str(station.get("StationId", "")).strip(),
                "station_name": str(station.get("StationName", "")).strip(),
                "county_name": normalize_name(geo_info.get("CountyName") or station.get("CountyName") or ""),
                "town_name": normalize_name(geo_info.get("TownName") or station.get("TownName") or ""),
                "lat": lat,
                "lon": lon,
                "rain_1hr": rain_1hr,
                "obs_time": ((station.get("ObsTime") or {}).get("DateTime") or "").strip(),
            }
        )
    return normalized


def rainfall_records_to_gdf(records: list[dict[str, Any]], target_counties: list[str]) -> gpd.GeoDataFrame:
    df = pd.DataFrame.from_records(records)
    if df.empty:
        raise ValueError("The normalized rainfall record list is empty.")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["rain_1hr"] = pd.to_numeric(df["rain_1hr"], errors="coerce")
    df["county_name"] = df["county_name"].map(normalize_name)
    df["town_name"] = df["town_name"].map(normalize_name)
    df = df.loc[
        df["lat"].notna()
        & df["lon"].notna()
        & df["rain_1hr"].notna()
        & df["rain_1hr"].ne(-998)
        & df["station_name"].fillna("").astype(str).str.strip().ne("")
    ].copy()
    normalized_targets = {normalize_name(item) for item in target_counties}
    df = df.loc[df["county_name"].isin(normalized_targets)].copy()
    if df.empty:
        raise ValueError("No rainfall stations remain after filtering to the target counties.")
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")


def fetch_live_cwa_json(config: ARIAV3Config) -> dict[str, Any]:
    if not config.cwa_api_key:
        raise ValueError("Missing CWA API key.")
    response = requests.get(
        CWA_DATASET_URL,
        headers={"Authorization": config.cwa_api_key},
        params={"format": "JSON"},
        timeout=config.live_timeout_s,
    )
    response.raise_for_status()
    return response.json()


def load_simulation_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rainfall_payload(config: ARIAV3Config) -> tuple[dict[str, Any], str, bool]:
    if config.app_mode == "LIVE":
        try:
            return fetch_live_cwa_json(config), "LIVE", False
        except Exception:
            return load_simulation_json(config.simulation_data_path), "SIMULATION_FALLBACK", True
    return load_simulation_json(config.simulation_data_path), "SIMULATION", False


def attach_nearest_station_info(
    shelters_3826: gpd.GeoDataFrame,
    stations_3826: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    nearest = gpd.sjoin_nearest(
        shelters_3826,
        stations_3826[
            ["station_id", "station_name", "county_name", "town_name", "rain_1hr", "obs_time", "geometry"]
        ],
        how="left",
        distance_col="nearest_station_distance_m",
    )
    nearest = nearest.rename(
        columns={
            "county_name_left": "county_name",
            "town_name_left": "town_name",
            "station_id": "nearest_station_id",
            "station_name": "nearest_station_name",
            "county_name_right": "nearest_station_county_name",
            "town_name_right": "nearest_station_town_name",
            "rain_1hr": "nearest_station_rain_1hr",
            "obs_time": "nearest_station_obs_time",
        }
    )
    return nearest.drop(columns=["index_right"], errors="ignore")


def summarize_buffer_impacts(
    shelters_3826: gpd.GeoDataFrame,
    stations_3826: gpd.GeoDataFrame,
    warning_rain_mm: float,
    rain_buffer_m: float,
) -> pd.DataFrame:
    heavy = stations_3826.loc[stations_3826["rain_1hr"] > warning_rain_mm].copy()
    if heavy.empty:
        return pd.DataFrame(columns=["shelter_id", "max_rain_1hr_in_buffer", "impact_station_name"])

    heavy["geometry"] = heavy.geometry.buffer(rain_buffer_m)
    joined = gpd.sjoin(
        shelters_3826[["shelter_id", "geometry"]],
        heavy[["station_name", "rain_1hr", "geometry"]],
        how="left",
        predicate="within",
    ).dropna(subset=["station_name"])
    if joined.empty:
        return pd.DataFrame(columns=["shelter_id", "max_rain_1hr_in_buffer", "impact_station_name"])

    strongest = joined.sort_values(
        ["shelter_id", "rain_1hr", "station_name"], ascending=[True, False, True]
    ).drop_duplicates(subset=["shelter_id"])
    return strongest.rename(
        columns={"rain_1hr": "max_rain_1hr_in_buffer", "station_name": "impact_station_name"}
    )[["shelter_id", "max_rain_1hr_in_buffer", "impact_station_name"]]


def classify_dynamic_risk(
    max_rain_1hr_in_buffer: float | None,
    terrain_risk: str,
    warning_rain_mm: float,
    critical_rain_mm: float,
) -> str:
    terrain_high = str(terrain_risk).upper() == "HIGH"
    max_rain = _coerce_float(max_rain_1hr_in_buffer)
    if max_rain is not None and max_rain > critical_rain_mm:
        return "CRITICAL"
    if max_rain is not None and max_rain > warning_rain_mm and terrain_high:
        return "URGENT"
    if (max_rain is not None and max_rain > warning_rain_mm) or terrain_high:
        return "WARNING"
    return "SAFE"


def apply_dynamic_risk(
    static_baseline_3826: gpd.GeoDataFrame,
    stations_4326: gpd.GeoDataFrame,
    config: ARIAV3Config,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    stations_3826 = stations_4326.to_crs(ANALYSIS_CRS)
    shelters = attach_nearest_station_info(static_baseline_3826, stations_3826)
    impacts = summarize_buffer_impacts(
        shelters,
        stations_3826,
        warning_rain_mm=config.warning_rain_mm,
        rain_buffer_m=config.rain_buffer_m,
    )
    enriched = shelters.merge(impacts, on="shelter_id", how="left")
    enriched["dynamic_risk"] = enriched.apply(
        lambda row: classify_dynamic_risk(
            row.get("max_rain_1hr_in_buffer"),
            str(row.get("terrain_risk", "")),
            config.warning_rain_mm,
            config.critical_rain_mm,
        ),
        axis=1,
    )
    enriched["dynamic_risk_priority"] = enriched["dynamic_risk"].map(RISK_PRIORITY)
    return enriched, stations_3826


def top_impacted_shelters(dynamic_shelters: gpd.GeoDataFrame, top_n: int = 3) -> gpd.GeoDataFrame:
    return dynamic_shelters.sort_values(
        by=[
            "dynamic_risk_priority",
            "max_rain_1hr_in_buffer",
            "max_slope",
            "nearest_station_rain_1hr",
            "capacity",
        ],
        ascending=[True, False, False, False, False],
        na_position="last",
    ).head(top_n)


def build_gemini_prompt(row: pd.Series) -> str:
    return (
        "你是花蓮宜蘭防災指揮中心的災害防救專家顧問。\n"
        f"避難所: {row.get('name', 'Unknown shelter')}\n"
        f"地形風險: {row.get('terrain_risk', 'UNKNOWN')} (max_slope: {row.get('max_slope', 'N/A')})\n"
        f"最近雨量站: {row.get('nearest_station_name', 'N/A')} "
        f"(時雨量: {row.get('nearest_station_rain_1hr', 'N/A')} mm)\n"
        f"動態風險等級: {row.get('dynamic_risk', 'SAFE')}\n\n"
        "請用 3 句中文給出具體、簡短、可執行的應變建議。"
    )


def _is_gemini_quota_error(exc: Exception) -> bool:
    normalized = str(exc).lower()
    return "resource_exhausted" in normalized or "quota" in normalized or "429" in normalized


def _summarize_gemini_error(exc: Exception) -> str:
    normalized = str(exc).lower()
    if _is_gemini_quota_error(exc):
        return "暫時無法取得（Gemini quota exceeded）"
    if "permission" in normalized or "authentication" in normalized or "api key" in normalized or "403" in normalized:
        return "暫時無法取得（Gemini authentication failed）"
    if "timeout" in normalized:
        return "暫時無法取得（Gemini request timed out）"
    return "暫時無法取得（Gemini request failed）"


def generate_gemini_advice(
    dynamic_shelters: gpd.GeoDataFrame,
    config: ARIAV3Config,
) -> tuple[gpd.GeoDataFrame, str]:
    result = dynamic_shelters.copy()
    result["gemini_advice"] = ""
    if not config.gemini_api_key:
        return result, "skipped: GEMINI_API_KEY not configured"

    try:
        from google import genai
    except Exception as exc:  # pragma: no cover
        return result, f"skipped: google-genai import failed ({exc})"

    try:
        client = genai.Client(api_key=config.gemini_api_key)
    except Exception as exc:  # pragma: no cover
        return result, f"skipped: Gemini client init failed ({exc})"

    messages: dict[str, str] = {}
    top_rows = list(top_impacted_shelters(result).iterrows())
    delay_s = max(0.0, float(config.gemini_request_delay_s))
    for index, (_, row) in enumerate(top_rows):
        try:
            response = client.models.generate_content(
                model=config.gemini_model,
                contents=build_gemini_prompt(row),
            )
            messages[str(row["shelter_id"])] = (getattr(response, "text", "") or "").strip()
        except Exception as exc:  # pragma: no cover
            summary = _summarize_gemini_error(exc)
            messages[str(row["shelter_id"])] = summary
            if _is_gemini_quota_error(exc):
                for _, remaining_row in top_rows[index + 1 :]:
                    messages[str(remaining_row["shelter_id"])] = summary
                break
        if delay_s > 0 and index < len(top_rows) - 1:
            time.sleep(delay_s)

    result["gemini_advice"] = result["shelter_id"].astype(str).map(messages).fillna("")
    return result, f"generated advice for {len(messages)} shelters"


def county_boundary_geojson(config: ARIAV3Config) -> gpd.GeoDataFrame:
    townships = load_townships(config.township_shp_path)
    normalized = {normalize_name(value) for value in config.target_counties}
    subset = townships.loc[townships["COUNTYNAME"].isin(normalized)].copy()
    dissolved = subset.dissolve(by="COUNTYNAME", as_index=False)
    return dissolved.to_crs("EPSG:4326")


def _rain_color(rain_1hr: float) -> str:
    if rain_1hr > 80:
        return "#c62828"
    if rain_1hr > 40:
        return "#ef6c00"
    if rain_1hr > 10:
        return "#fdd835"
    return "#43a047"


def _rain_radius(rain_1hr: float) -> float:
    return max(4.0, min(18.0, 4.0 + float(rain_1hr) / 10.0))


def _safe_text(value: Any) -> str:
    if value is None:
        return "N/A"
    text = str(value).strip()
    return html.escape(text) if text else "N/A"


def _popup_html(row: pd.Series) -> str:
    advice = _safe_text(row.get("gemini_advice")) if row.get("gemini_advice") else "SKIPPED / N/A"
    return "".join(
        [
            f"<b>{_safe_text(row.get('name'))}</b><br>",
            f"縣市 / 鄉鎮: {_safe_text(row.get('county_name'))} / {_safe_text(row.get('town_name'))}<br>",
            f"Terrain Risk: {_safe_text(row.get('terrain_risk'))}<br>",
            f"Max Slope: {_safe_text(row.get('max_slope'))}<br>",
            f"Dynamic Risk: {_safe_text(row.get('dynamic_risk'))}<br>",
            f"最近站: {_safe_text(row.get('nearest_station_name'))}<br>",
            f"最近站時雨量: {_safe_text(row.get('nearest_station_rain_1hr'))} mm<br>",
            f"影響圈最大時雨量: {_safe_text(row.get('max_rain_1hr_in_buffer'))} mm<br>",
            f"Gemini 建議: {advice}",
        ]
    )


def _shelter_div_icon(color: str, highlighted: bool) -> folium.DivIcon:
    size = 18 if highlighted else 14
    border_color = "#111827" if highlighted else "#ffffff"
    html_markup = f"""
    <div style="
        width: {size}px;
        height: {size}px;
        border-radius: 50%;
        background: {color};
        border: 2px solid {border_color};
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.35);
    "></div>
    """
    return folium.DivIcon(
        html=html_markup,
        icon_size=(size, size),
        icon_anchor=(size // 2, size // 2),
        class_name="aria-shelter-marker",
    )


def build_folium_map(
    config: ARIAV3Config,
    dynamic_shelters_3826: gpd.GeoDataFrame,
    stations_4326: gpd.GeoDataFrame,
) -> folium.Map:
    shelters_4326 = dynamic_shelters_3826.to_crs("EPSG:4326").copy()
    highlighted_marker_names: list[str] = []
    highlighted_ids = set(
        top_impacted_shelters(
            shelters_4326.loc[shelters_4326["gemini_advice"].fillna("").astype(str).str.strip().ne("")]
        )["shelter_id"].astype(str).tolist()
    )
    county_outline = county_boundary_geojson(config)
    center = county_outline.unary_union.centroid

    fmap = folium.Map(
        location=[center.y, center.x],
        zoom_start=9,
        tiles="CartoDB positron",
        control_scale=True,
    )

    county_group = folium.FeatureGroup(name="花宜縣界", show=True)
    folium.GeoJson(
        county_outline,
        style_function=lambda _: {"color": "#1e3a8a", "weight": 2, "fillOpacity": 0.04},
        tooltip=folium.GeoJsonTooltip(fields=["COUNTYNAME"], aliases=["County"]),
    ).add_to(county_group)
    county_group.add_to(fmap)

    rain_group = folium.FeatureGroup(name="Rainfall Stations", show=True)
    for _, row in stations_4326.iterrows():
        rain_1hr = float(row["rain_1hr"])
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=_rain_radius(rain_1hr),
            color=_rain_color(rain_1hr),
            fill=True,
            fill_color=_rain_color(rain_1hr),
            fill_opacity=0.8,
            weight=1,
            tooltip=f"{_safe_text(row['station_name'])}: {rain_1hr:.1f} mm",
        ).add_to(rain_group)
    rain_group.add_to(fmap)

    heat_data = [[row.geometry.y, row.geometry.x, float(row["rain_1hr"])] for _, row in stations_4326.iterrows()]
    HeatMap(heat_data, name="Rainfall HeatMap", show=False, radius=20, blur=16, min_opacity=0.25).add_to(fmap)

    shelter_group = folium.FeatureGroup(name="Shelter Risk", show=True)
    for _, row in shelters_4326.iterrows():
        color = {
            "CRITICAL": "#b71c1c",
            "URGENT": "#ef6c00",
            "WARNING": "#fbc02d",
            "SAFE": "#2e7d32",
        }.get(str(row.get("dynamic_risk", "SAFE")).upper(), "#2e7d32")
        is_highlighted = str(row.get("shelter_id", "")) in highlighted_ids
        popup_kwargs = {"max_width": 420}
        if is_highlighted:
            popup_kwargs.update({"sticky": True})
        marker = folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon=_shelter_div_icon(color, is_highlighted),
            tooltip=f"{_safe_text(row.get('name'))} | {_safe_text(row.get('dynamic_risk'))}",
            popup=folium.Popup(_popup_html(row), **popup_kwargs),
        )
        marker.add_to(shelter_group)
        if is_highlighted:
            highlighted_marker_names.append(marker.get_name())
    shelter_group.add_to(fmap)

    if highlighted_marker_names:
        map_var_name = fmap.get_name()
        marker_refs = ", ".join(f'"{name}"' for name in highlighted_marker_names)
        auto_open_script = f"""
        window.addEventListener("load", function() {{
            var mapObject = window["{map_var_name}"];
            if (!mapObject || !mapObject.whenReady) {{
                return;
            }}
            mapObject.whenReady(function() {{
                window.setTimeout(function() {{
                    [{marker_refs}].forEach(function(markerName) {{
                        var marker = window[markerName];
                    if (marker && marker.openPopup) {{
                        marker.openPopup();
                    }}
                    }});
                }}, 350);
            }});
        }});
        """
        fmap.get_root().script.add_child(Element(auto_open_script))

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap


def copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())


def save_outputs(
    config: ARIAV3Config,
    static_baseline: gpd.GeoDataFrame,
    stations_4326: gpd.GeoDataFrame,
    dynamic_shelters: gpd.GeoDataFrame,
    fmap: folium.Map,
) -> dict[str, Path]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.submission_dir.mkdir(parents=True, exist_ok=True)
    static_path = static_baseline_cache_path(config)
    rainfall_path = config.output_dir / "rainfall_stations.geojson"
    audit_path = config.output_dir / "dynamic_risk_audit.csv"
    html_path = config.output_dir / "ARIA_v3_Fungwong.html"
    submission_html_path = config.submission_dir / "ARIA_v3_Fungwong.html"

    save_geodataframe_geojson(static_path, static_baseline)
    save_geodataframe_geojson(rainfall_path, stations_4326)
    dynamic_shelters.drop(columns="geometry").to_csv(audit_path, index=False, encoding="utf-8-sig")
    fmap.save(str(html_path))
    copy_if_exists(html_path, submission_html_path)
    return {
        "static_baseline_path": static_path,
        "rainfall_geojson_path": rainfall_path,
        "dynamic_audit_path": audit_path,
        "map_html_path": html_path,
        "submission_map_html_path": submission_html_path,
    }


def run_pipeline(config: ARIAV3Config | None = None) -> dict[str, Any]:
    active_config = config or build_config_from_env()
    active_config.output_dir.mkdir(parents=True, exist_ok=True)
    active_config.submission_dir.mkdir(parents=True, exist_ok=True)

    static_baseline = load_or_build_static_baseline(active_config)
    payload, rain_source, fallback_used = load_rainfall_payload(active_config)
    stations_4326 = rainfall_records_to_gdf(normalize_cwa_json(payload), active_config.target_counties)
    dynamic_shelters, stations_3826 = apply_dynamic_risk(static_baseline, stations_4326, active_config)
    dynamic_shelters, gemini_status = generate_gemini_advice(dynamic_shelters, active_config)
    fmap = build_folium_map(active_config, dynamic_shelters, stations_4326)
    paths = save_outputs(active_config, static_baseline, stations_4326, dynamic_shelters, fmap)
    summary = {
        "rain_source": rain_source,
        "fallback_used": fallback_used,
        "station_count": int(len(stations_4326)),
        "shelter_count": int(len(dynamic_shelters)),
        "risk_counts": dynamic_shelters["dynamic_risk"].value_counts().to_dict(),
        "gemini_status": gemini_status,
    }
    return {
        "config": active_config,
        "payload": payload,
        "stations_4326": stations_4326,
        "stations_3826": stations_3826,
        "static_baseline": static_baseline,
        "dynamic_shelters": dynamic_shelters,
        "map": fmap,
        "paths": paths,
        "summary": summary,
    }


def main() -> int:
    results = run_pipeline()
    print(json.dumps(results["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
