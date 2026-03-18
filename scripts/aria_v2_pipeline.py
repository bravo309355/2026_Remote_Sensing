from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

QGIS_ROOT = Path(r"C:\Program Files\QGISQT6 3.40.14")
PROJ_DIR = QGIS_ROOT / "share" / "proj"
GDAL_DATA_DIR = QGIS_ROOT / "apps" / "gdal" / "share" / "gdal"
if PROJ_DIR.exists():
    os.environ.setdefault("PROJ_LIB", str(PROJ_DIR))
if GDAL_DATA_DIR.exists():
    os.environ.setdefault("GDAL_DATA", str(GDAL_DATA_DIR))

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LightSource
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from osgeo import gdal, ogr, osr

gdal.UseExceptions()
plt.rcParams["font.sans-serif"] = [
    "Microsoft JhengHei",
    "Taipei Sans TC Beta",
    "Noto Sans CJK TC",
    "SimHei",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
ANALYSIS_CRS = "EPSG:3826"
TARGET_COUNTY_DEFAULT = "\u82b1\u84ee\u7e23"
RISK_ORDER = ["very_high", "high", "medium", "low"]
RISK_COLORS = {
    "very_high": "#8e0000",
    "high": "#d32f2f",
    "medium": "#f57c00",
    "low": "#388e3c",
}


@dataclass
class ARIAV2Config:
    river_shp_path: Path
    shelter_csv_path: Path
    township_shp_path: Path
    dem_path: Path
    fallback_dem_path: Path | None
    target_county: str
    slope_threshold: float
    elevation_low: float
    buffer_high: float
    county_buffer: float
    output_dir: Path
    submission_dir: Path


@dataclass
class RasterSubset:
    array: np.ndarray
    county_mask: np.ndarray
    geotransform: tuple[float, float, float, float, float, float]
    projection_wkt: str


def project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def normalize_name(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace(" ", "").replace("\u3000", "").replace("\u53f0", "\u81fa").strip()


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
        raise FileNotFoundError(f"Could not find file matching pattern {pattern!r} under {base}")
    return matches[0]


def build_config_from_env() -> ARIAV2Config:
    env = load_env_file(PROJECT_ROOT / ".env")
    data_dir = project_path(env.get("DATA_DIR", "data"))
    river_path = project_path(env.get("RIVER_SHP_PATH", str(find_one(data_dir, "**/riverpoly.shp"))))
    shelter_path = project_path(env.get("SHELTER_CSV_PATH", str(find_one(data_dir, "*v9.csv"))))
    township_path = project_path(
        env.get("TOWNSHIP_SHP_PATH", str(find_one(data_dir, "**/TOWN_MOI_1140318.shp")))
    )
    dem_path = project_path(env.get("DEM_PATH", "data/DEM_tawiwan_V2025.tif"))
    fallback_text = env.get("FALLBACK_DEM_PATH", "data/Hualien_dem_merge.tif")
    fallback_path = project_path(fallback_text) if fallback_text else None
    return ARIAV2Config(
        river_shp_path=river_path,
        shelter_csv_path=shelter_path,
        township_shp_path=township_path,
        dem_path=dem_path,
        fallback_dem_path=fallback_path,
        target_county=normalize_name(env.get("TARGET_COUNTY", TARGET_COUNTY_DEFAULT)),
        slope_threshold=float(env.get("SLOPE_THRESHOLD", "30")),
        elevation_low=float(env.get("ELEVATION_LOW", "50")),
        buffer_high=float(env.get("BUFFER_HIGH", "500")),
        county_buffer=float(env.get("COUNTY_BUFFER", "1000")),
        output_dir=project_path(env.get("OUTPUT_DIR", "outputs/aria_v2")),
        submission_dir=project_path(env.get("SUBMISSION_DIR", "submission/Homework-4")),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Homework 4 ARIA v2 outputs.")
    parser.add_argument("--target-county")
    parser.add_argument("--dem-path")
    parser.add_argument("--fallback-dem-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--submission-dir")
    parser.add_argument("--buffer-high", type=float)
    parser.add_argument("--slope-threshold", type=float)
    parser.add_argument("--elevation-low", type=float)
    parser.add_argument("--county-buffer", type=float)
    return parser


def config_from_args(argv: list[str] | None = None) -> ARIAV2Config:
    base = build_config_from_env()
    args = build_parser().parse_args(argv)
    fallback_dem_path = base.fallback_dem_path
    if args.fallback_dem_path:
        fallback_dem_path = project_path(args.fallback_dem_path)
    return ARIAV2Config(
        river_shp_path=base.river_shp_path,
        shelter_csv_path=base.shelter_csv_path,
        township_shp_path=base.township_shp_path,
        dem_path=project_path(args.dem_path) if args.dem_path else base.dem_path,
        fallback_dem_path=fallback_dem_path,
        target_county=normalize_name(args.target_county) if args.target_county else base.target_county,
        slope_threshold=args.slope_threshold if args.slope_threshold is not None else base.slope_threshold,
        elevation_low=args.elevation_low if args.elevation_low is not None else base.elevation_low,
        buffer_high=args.buffer_high if args.buffer_high is not None else base.buffer_high,
        county_buffer=args.county_buffer if args.county_buffer is not None else base.county_buffer,
        output_dir=project_path(args.output_dir) if args.output_dir else base.output_dir,
        submission_dir=project_path(args.submission_dir) if args.submission_dir else base.submission_dir,
    )


def load_shelter_table(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, encoding="utf-8")
    shelter_id = raw.iloc[:, 0].astype(str).str.strip()
    county_hint = raw.iloc[:, 1].fillna("").astype(str).str.strip()
    longitude = pd.to_numeric(raw.iloc[:, 4], errors="coerce")
    latitude = pd.to_numeric(raw.iloc[:, 5], errors="coerce")
    name = raw.iloc[:, 6].fillna("").astype(str).str.strip()
    capacity = pd.to_numeric(raw.iloc[:, 8], errors="coerce").fillna(0).astype(int)
    return pd.DataFrame(
        {
            "shelter_id": shelter_id,
            "county_hint": county_hint,
            "longitude": longitude,
            "latitude": latitude,
            "name": name,
            "capacity": capacity,
        }
    )


def split_zero_and_null_coordinates(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    invalid_mask = (
        df["longitude"].isna()
        | df["latitude"].isna()
        | df["longitude"].eq(0)
        | df["latitude"].eq(0)
    )
    return df.loc[~invalid_mask].copy(), df.loc[invalid_mask].copy()


def build_shelter_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )


def load_townships(path: Path) -> gpd.GeoDataFrame:
    townships = gpd.read_file(path).to_crs(ANALYSIS_CRS)
    townships["COUNTYNAME"] = townships["COUNTYNAME"].map(normalize_name)
    townships["TOWNNAME"] = townships["TOWNNAME"].map(normalize_name)
    return townships[["COUNTYCODE", "COUNTYNAME", "TOWNCODE", "TOWNNAME", "geometry"]].copy()


def load_rivers(path: Path) -> gpd.GeoDataFrame:
    rivers = gpd.read_file(path)
    if rivers.crs is None:
        raise ValueError("River shapefile does not have a CRS.")
    return rivers.to_crs(ANALYSIS_CRS)


def filter_shelters_on_land(
    shelters: gpd.GeoDataFrame, townships: gpd.GeoDataFrame
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
        townships[["COUNTYNAME", "TOWNNAME", "TOWNCODE", "geometry"]],
        how="left",
        predicate="intersects",
    )
    joined = joined.sort_values(["row_id", "TOWNCODE"]).drop_duplicates(subset=["row_id"])
    merged = left.merge(
        joined[["row_id", "COUNTYNAME", "TOWNNAME", "TOWNCODE"]],
        on="row_id",
        how="left",
    )
    return merged.drop(columns="row_id")


def build_target_boundary(townships: gpd.GeoDataFrame, target_county: str) -> gpd.GeoDataFrame:
    county_rows = townships.loc[townships["COUNTYNAME"] == normalize_name(target_county)].copy()
    if county_rows.empty:
        raise ValueError(f"Target county {target_county!r} was not found in the township dataset.")
    return county_rows.dissolve().reset_index(drop=True)


def dataset_bounds(dataset: gdal.Dataset) -> tuple[float, float, float, float]:
    geotransform = dataset.GetGeoTransform()
    min_x = geotransform[0]
    max_y = geotransform[3]
    max_x = min_x + dataset.RasterXSize * geotransform[1]
    min_y = max_y + dataset.RasterYSize * geotransform[5]
    return min_x, min_y, max_x, max_y


def bounds_cover(container: tuple[float, float, float, float], inner: tuple[float, float, float, float]) -> bool:
    return (
        container[0] <= inner[0]
        and container[1] <= inner[1]
        and container[2] >= inner[2]
        and container[3] >= inner[3]
    )


def choose_dem_dataset(config: ARIAV2Config, county_buffer_bounds: tuple[float, float, float, float]) -> tuple[gdal.Dataset, Path]:
    primary = gdal.Open(str(config.dem_path))
    if primary is None:
        if config.fallback_dem_path and config.fallback_dem_path.exists():
            fallback = gdal.Open(str(config.fallback_dem_path))
            if fallback is not None:
                return fallback, config.fallback_dem_path
        raise FileNotFoundError(f"Unable to open DEM: {config.dem_path}")
    if not bounds_cover(dataset_bounds(primary), county_buffer_bounds) and config.fallback_dem_path and config.fallback_dem_path.exists():
        # Keep the requested DEM as the default path. The analysis only needs valid
        # coverage for the clipped county footprint and 500m shelter buffers, not full
        # coverage of the county_buffer bounding box.
        return primary, config.dem_path
    if config.fallback_dem_path and config.fallback_dem_path.exists():
        fallback = gdal.Open(str(config.fallback_dem_path))
        if primary is None and fallback is not None:
            return fallback, config.fallback_dem_path
    return primary, config.dem_path


def projection_wkt_or_fallback(dataset: gdal.Dataset) -> str:
    projection = dataset.GetProjectionRef()
    if projection and projection.strip():
        return projection
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3826)
    return srs.ExportToWkt()


def window_from_bounds(
    bounds: tuple[float, float, float, float],
    geotransform: tuple[float, float, float, float, float, float],
    raster_width: int,
    raster_height: int,
) -> tuple[int, int, int, int]:
    min_x, min_y, max_x, max_y = bounds
    origin_x, pixel_w, _, origin_y, _, pixel_h = geotransform
    pixel_h_abs = abs(pixel_h)
    x_start = max(0, int(math.floor((min_x - origin_x) / pixel_w)))
    x_stop = min(raster_width, int(math.ceil((max_x - origin_x) / pixel_w)))
    y_start = max(0, int(math.floor((origin_y - max_y) / pixel_h_abs)))
    y_stop = min(raster_height, int(math.ceil((origin_y - min_y) / pixel_h_abs)))
    if x_stop <= x_start or y_stop <= y_start:
        raise ValueError("Requested geometry does not intersect the raster extent.")
    return x_start, y_start, x_stop - x_start, y_stop - y_start


def rasterize_geometry(
    geometry,
    width: int,
    height: int,
    geotransform: tuple[float, float, float, float, float, float],
    projection_wkt: str,
) -> np.ndarray:
    raster_driver = gdal.GetDriverByName("MEM")
    mask_ds = raster_driver.Create("", width, height, 1, gdal.GDT_Byte)
    mask_ds.SetGeoTransform(geotransform)
    mask_ds.SetProjection(projection_wkt)
    mask_band = mask_ds.GetRasterBand(1)
    mask_band.Fill(0)

    vector_driver = ogr.GetDriverByName("MEM") or ogr.GetDriverByName("Memory")
    vector_ds = vector_driver.CreateDataSource("")
    srs = osr.SpatialReference()
    srs.ImportFromWkt(projection_wkt)
    layer = vector_ds.CreateLayer("mask", srs=srs, geom_type=ogr.wkbUnknown)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(ogr.CreateGeometryFromWkt(geometry.wkt))
    layer.CreateFeature(feature)
    gdal.RasterizeLayer(mask_ds, [1], layer, burn_values=[1])
    array = mask_band.ReadAsArray().astype(bool)

    feature = None
    layer = None
    vector_ds = None
    mask_band = None
    mask_ds = None
    return array


def read_raster_subset(dataset: gdal.Dataset, geometry) -> RasterSubset:
    band = dataset.GetRasterBand(1)
    geotransform = dataset.GetGeoTransform()
    projection_wkt = projection_wkt_or_fallback(dataset)
    x_off, y_off, x_size, y_size = window_from_bounds(
        geometry.bounds,
        geotransform,
        dataset.RasterXSize,
        dataset.RasterYSize,
    )
    array = band.ReadAsArray(x_off, y_off, x_size, y_size).astype(float)
    no_data = band.GetNoDataValue()
    if no_data is not None:
        array[array == no_data] = np.nan
    subset_gt = (
        geotransform[0] + x_off * geotransform[1],
        geotransform[1],
        geotransform[2],
        geotransform[3] + y_off * geotransform[5],
        geotransform[4],
        geotransform[5],
    )
    county_mask = rasterize_geometry(geometry, x_size, y_size, subset_gt, projection_wkt)
    return RasterSubset(array=array, county_mask=county_mask, geotransform=subset_gt, projection_wkt=projection_wkt)


def compute_slope_degrees(elevation: np.ndarray, pixel_size: float = 20.0) -> np.ndarray:
    working = elevation.copy()
    if np.isnan(working).all():
        return np.full_like(working, np.nan, dtype=float)
    fill_value = float(np.nanmean(working))
    working = np.where(np.isfinite(working), working, fill_value)
    dy, dx = np.gradient(working, pixel_size)
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    slope[~np.isfinite(elevation)] = np.nan
    return slope


def zonal_stats_for_buffers(
    buffers: gpd.GeoDataFrame,
    elevation: np.ndarray,
    slope: np.ndarray,
    geotransform: tuple[float, float, float, float, float, float],
    projection_wkt: str,
) -> pd.DataFrame:
    width = elevation.shape[1]
    height = elevation.shape[0]
    records: list[dict[str, Any]] = []
    for shelter_id, geometry in zip(buffers["shelter_id"], buffers.geometry):
        try:
            x_off, y_off, x_size, y_size = window_from_bounds(geometry.bounds, geotransform, width, height)
        except ValueError:
            records.append(
                {
                    "shelter_id": shelter_id,
                    "mean_elevation": None,
                    "std_elevation": None,
                    "max_slope": None,
                }
            )
            continue
        local_gt = (
            geotransform[0] + x_off * geotransform[1],
            geotransform[1],
            geotransform[2],
            geotransform[3] + y_off * geotransform[5],
            geotransform[4],
            geotransform[5],
        )
        local_mask = rasterize_geometry(geometry, x_size, y_size, local_gt, projection_wkt)
        elev_values = elevation[y_off : y_off + y_size, x_off : x_off + x_size][local_mask]
        slope_values = slope[y_off : y_off + y_size, x_off : x_off + x_size][local_mask]
        elev_values = elev_values[np.isfinite(elev_values)]
        slope_values = slope_values[np.isfinite(slope_values)]
        records.append(
            {
                "shelter_id": shelter_id,
                "mean_elevation": float(np.mean(elev_values)) if elev_values.size else None,
                "std_elevation": float(np.std(elev_values)) if elev_values.size else None,
                "max_slope": float(np.max(slope_values)) if slope_values.size else None,
            }
        )
    return pd.DataFrame(records)


def classify_risk(
    river_distance_m: float,
    max_slope: float | None,
    mean_elevation: float | None,
    slope_threshold: float,
    elevation_low: float,
) -> str:
    slope_value = float("nan") if max_slope is None else float(max_slope)
    elev_value = float("nan") if mean_elevation is None else float(mean_elevation)
    if river_distance_m < 500 and np.isfinite(slope_value) and slope_value > slope_threshold:
        return "very_high"
    if river_distance_m < 500 or (np.isfinite(slope_value) and slope_value > slope_threshold):
        return "high"
    if river_distance_m < 1000 and np.isfinite(elev_value) and elev_value < elevation_low:
        return "medium"
    return "low"


def create_terrain_map(
    output_path: Path,
    extent: tuple[float, float, float, float],
    county_boundary: gpd.GeoDataFrame,
    rivers_in_county: gpd.GeoDataFrame,
    shelters: gpd.GeoDataFrame,
    elevation_masked: np.ndarray,
) -> None:
    display = elevation_masked.copy()
    if np.isnan(display).all():
        raise ValueError("Masked DEM is empty; cannot create terrain map.")
    fill_value = float(np.nanmean(display))
    light_source = LightSource(azdeg=315, altdeg=45)
    shaded = light_source.hillshade(np.where(np.isfinite(display), display, fill_value), vert_exag=1, dx=20, dy=20)

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(display, extent=extent, origin="upper", cmap="terrain", alpha=0.95)
    ax.imshow(shaded, extent=extent, origin="upper", cmap="gray", alpha=0.35)
    rivers_in_county.plot(ax=ax, color="#4fc3f7", alpha=0.18, linewidth=0, zorder=2)
    rivers_in_county.boundary.plot(ax=ax, color="#1565c0", linewidth=0.35, alpha=0.55, zorder=3)
    county_boundary.boundary.plot(ax=ax, color="#102a43", linewidth=1.4)
    for level in RISK_ORDER:
        subset = shelters.loc[shelters["risk_level"] == level]
        if subset.empty:
            continue
        subset.plot(
            ax=ax,
            markersize=18,
            color=RISK_COLORS[level],
            alpha=0.85,
            zorder=4,
        )
    ax.set_title("ARIA v2 Terrain Risk Map")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    map_handles = [
        Patch(facecolor="#4fc3f7", edgecolor="#1565c0", alpha=0.25, label="River Polygons"),
        Line2D([0], [0], marker="o", linestyle="", color=RISK_COLORS["very_high"], markersize=6, label="Very High"),
        Line2D([0], [0], marker="o", linestyle="", color=RISK_COLORS["high"], markersize=6, label="High"),
        Line2D([0], [0], marker="o", linestyle="", color=RISK_COLORS["medium"], markersize=6, label="Medium"),
        Line2D([0], [0], marker="o", linestyle="", color=RISK_COLORS["low"], markersize=6, label="Low"),
    ]
    ax.legend(handles=map_handles, loc="upper right")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def create_top10_scatter(output_path: Path, shelters: gpd.GeoDataFrame, slope_threshold: float) -> None:
    rank = {"very_high": 0, "high": 1, "medium": 2, "low": 3}
    top10 = shelters.copy()
    top10["risk_rank"] = top10["risk_level"].map(rank)
    top10 = top10.sort_values(
        by=["risk_rank", "max_slope", "distance_to_river_m"],
        ascending=[True, False, True],
    ).head(10)
    top10 = top10.copy()
    top10["display_name"] = top10["name"].str.slice(0, 28)
    fig, ax = plt.subplots(figsize=(12, 7.5))
    bars = ax.barh(
        top10["display_name"],
        top10["max_slope"],
        color=top10["risk_level"].map(RISK_COLORS),
        alpha=0.88,
    )
    for bar, (_, row) in zip(bars, top10.iterrows()):
        elev_text = "nan" if pd.isna(row["mean_elevation"]) else f"{row['mean_elevation']:.0f}"
        river_text = "nan" if pd.isna(row["distance_to_river_m"]) else f"{row['distance_to_river_m']:.0f}"
        label = f"elev {elev_text}m | river {river_text}m"
        ax.text(
            bar.get_width() + 0.8,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            fontsize=8,
            alpha=0.85,
        )
    ax.axvline(slope_threshold, color="#455a64", linestyle="--", linewidth=1.0, label="Slope Threshold")
    ax.set_title("Top 10 Terrain Risk Shelters")
    ax.set_xlabel("Max Slope (degrees)")
    ax.set_ylabel("Shelter")
    ax.invert_yaxis()
    ax.set_xlim(0, max(top10["max_slope"].max() * 1.28, slope_threshold * 1.2))
    bar_handles = [
        Line2D([0], [0], marker="s", linestyle="", color=RISK_COLORS["very_high"], markersize=8, label="Very High"),
        Line2D([0], [0], marker="s", linestyle="", color=RISK_COLORS["high"], markersize=8, label="High"),
        Line2D([0], [0], marker="s", linestyle="", color=RISK_COLORS["medium"], markersize=8, label="Medium"),
        Line2D([0], [0], marker="s", linestyle="", color=RISK_COLORS["low"], markersize=8, label="Low"),
        Line2D([0], [0], color="#455a64", linestyle="--", linewidth=1.0, label="Slope Threshold"),
    ]
    ax.legend(handles=bar_handles, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=True, borderaxespad=0.6)
    fig.tight_layout(rect=(0, 0, 0.86, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def to_native_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in df.to_dict(orient="records"):
        native: dict[str, Any] = {}
        for key, value in record.items():
            if pd.isna(value):
                native[key] = None
            elif hasattr(value, "item"):
                native[key] = value.item()
            else:
                native[key] = value
        records.append(native)
    return records


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def run_pipeline(config: ARIAV2Config) -> dict[str, Path]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.submission_dir.mkdir(parents=True, exist_ok=True)

    shelters_raw = load_shelter_table(config.shelter_csv_path)
    shelters_valid, shelters_invalid = split_zero_and_null_coordinates(shelters_raw)
    shelters_geo = build_shelter_geodataframe(shelters_valid)

    townships = load_townships(config.township_shp_path)
    shelters_land, shelters_outside = filter_shelters_on_land(shelters_geo, townships)
    shelters_land = attach_townships(shelters_land, townships)

    county_boundary = build_target_boundary(townships, config.target_county)
    county_buffer_geom = county_boundary.geometry.iloc[0].buffer(config.county_buffer)

    rivers = load_rivers(config.river_shp_path)
    rivers_in_county = gpd.sjoin(rivers, county_boundary[["geometry"]], how="inner", predicate="intersects")
    if rivers_in_county.empty:
        raise ValueError("River sanity check failed: the river polygons do not intersect the target county.")

    target_shelters = shelters_land.loc[shelters_land["COUNTYNAME"] == config.target_county].copy()
    if target_shelters.empty:
        raise ValueError(f"No shelters were found inside {config.target_county}.")

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

    dataset, used_dem_path = choose_dem_dataset(config, county_buffer_geom.bounds)
    raster_subset = read_raster_subset(dataset, county_buffer_geom)
    slope = compute_slope_degrees(raster_subset.array)
    masked_elevation = np.where(raster_subset.county_mask, raster_subset.array, np.nan)

    shelter_buffers = target_shelters[["shelter_id", "geometry"]].copy()
    shelter_buffers["geometry"] = shelter_buffers.geometry.buffer(config.buffer_high)
    stats = zonal_stats_for_buffers(
        shelter_buffers,
        raster_subset.array,
        slope,
        raster_subset.geotransform,
        raster_subset.projection_wkt,
    )
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
    target_shelters["risk_rank"] = target_shelters["risk_level"].map(
        {"very_high": 0, "high": 1, "medium": 2, "low": 3}
    )

    audit_df = (
        target_shelters[
            [
                "shelter_id",
                "name",
                "COUNTYNAME",
                "TOWNNAME",
                "capacity",
                "distance_to_river_m",
                "river_distance_category",
                "mean_elevation",
                "std_elevation",
                "max_slope",
                "risk_rank",
                "risk_level",
            ]
        ]
        .rename(columns={"COUNTYNAME": "county_name", "TOWNNAME": "town_name"})
        .sort_values(
            by=["risk_rank", "max_slope", "distance_to_river_m", "shelter_id"],
            ascending=[True, False, True, True],
        )
        .drop(columns="risk_rank")
        .reset_index(drop=True)
    )

    risk_json_path = config.output_dir / "terrain_risk_audit.json"
    write_json(risk_json_path, to_native_records(audit_df))

    min_x, pixel_w, _, max_y, _, pixel_h = raster_subset.geotransform
    extent = (
        min_x,
        min_x + raster_subset.array.shape[1] * pixel_w,
        max_y + raster_subset.array.shape[0] * pixel_h,
        max_y,
    )
    map_png_path = config.output_dir / "terrain_risk_map.png"
    create_terrain_map(map_png_path, extent, county_boundary, rivers_in_county, target_shelters, masked_elevation)

    scatter_png_path = config.output_dir / "terrain_risk_top10_scatter.png"
    create_top10_scatter(scatter_png_path, target_shelters, config.slope_threshold)

    summary_path = config.output_dir / "terrain_run_summary.json"
    write_json(
        summary_path,
        {
            "target_county": config.target_county,
            "dem_path_requested": str(config.dem_path),
            "dem_path_used": str(used_dem_path),
            "valid_shelters_after_coordinate_cleaning": int(len(shelters_valid)),
            "removed_shelters_null_or_zero_coordinates": int(len(shelters_invalid)),
            "removed_shelters_outside_land_mask": int(len(shelters_outside)),
            "target_county_shelters": int(len(target_shelters)),
            "rivers_in_county": int(len(rivers_in_county)),
            "nan_mean_elevation_rows": int(target_shelters["mean_elevation"].isna().sum()),
            "nan_max_slope_rows": int(target_shelters["max_slope"].isna().sum()),
        },
    )

    copy_if_exists(PROJECT_ROOT / "ARIA_v2.ipynb", config.submission_dir / "ARIA_v2.ipynb")
    copy_if_exists(PROJECT_ROOT / "README.md", config.submission_dir / "README.md")
    copy_if_exists(risk_json_path, config.submission_dir / "terrain_risk_audit.json")
    copy_if_exists(map_png_path, config.submission_dir / "terrain_risk_map.png")
    return {
        "risk_json_path": risk_json_path,
        "map_png_path": map_png_path,
        "scatter_png_path": scatter_png_path,
        "summary_path": summary_path,
        "submission_dir": config.submission_dir,
    }


def main(argv: list[str] | None = None) -> int:
    config = config_from_args(argv)
    results = run_pipeline(config)
    for key, value in results.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
