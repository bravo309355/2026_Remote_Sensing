from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import folium
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
DISPLAY_CRS = "EPSG:4326"
ANALYSIS_CRS = "EPSG:3826"
RISK_ORDER = ["high", "medium", "low", "safe"]
RISK_COLORS = {
    "high": "#c62828",
    "medium": "#ef6c00",
    "low": "#f9a825",
    "safe": "#2e7d32",
}


@dataclass
class ARIAConfig:
    river_shp_path: Path
    shelter_csv_path: Path
    township_shp_path: Path
    population_xls_path: Path
    buffer_high: int
    buffer_med: int
    buffer_low: int
    gap_ratio: float
    output_dir: Path
    submission_dir: Path


@dataclass
class ARIAResult:
    cleaning_summary_path: Path
    population_summary_path: Path
    township_summary_path: Path
    top10_path: Path
    risk_json_path: Path
    risk_html_path: Path
    risk_png_path: Path
    submission_dir: Path


def project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def normalize_name(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace(" ", "").replace("\u3000", "").strip()
    return text.lstrip("※")


def to_int(value: Any) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if not value:
            return 0
    return int(float(value))


def read_csv_with_fallback(path: Path, encodings: Iterable[str]) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Unable to read CSV: {path}")


def load_shelter_table(path: Path) -> pd.DataFrame:
    raw = read_csv_with_fallback(path, ["utf-8", "utf-8-sig", "cp950", "big5"])
    required = ["序號", "避難收容處所名稱", "預計收容人數", "經度", "緯度", "室內"]
    missing = [column for column in required if column not in raw.columns]
    if missing:
        raise KeyError(f"Missing shelter columns: {missing}")

    shelters = pd.DataFrame(
        {
            "shelter_id": raw["序號"].astype(str).str.strip(),
            "name": raw["避難收容處所名稱"].fillna("").astype(str).str.strip(),
            "capacity": pd.to_numeric(raw["預計收容人數"], errors="coerce").fillna(0).astype(int),
            "longitude": pd.to_numeric(raw["經度"], errors="coerce"),
            "latitude": pd.to_numeric(raw["緯度"], errors="coerce"),
            "is_indoor": raw["室內"].fillna("").astype(str).str.strip().eq("是"),
        }
    )
    return shelters


def split_zero_and_null_coordinates(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    invalid_mask = (
        df["longitude"].isna()
        | df["latitude"].isna()
        | df["longitude"].eq(0)
        | df["latitude"].eq(0)
    )
    return df.loc[~invalid_mask].copy(), df.loc[invalid_mask].copy()


def load_townships(path: Path) -> gpd.GeoDataFrame:
    townships = gpd.read_file(path)
    fields = ["TOWNCODE", "COUNTYNAME", "TOWNNAME", "geometry"]
    missing = [field for field in fields if field not in townships.columns]
    if missing:
        raise KeyError(f"Missing township columns: {missing}")
    townships = townships[fields].copy()
    townships["COUNTYNAME"] = townships["COUNTYNAME"].map(normalize_name)
    townships["TOWNNAME"] = townships["TOWNNAME"].map(normalize_name)
    return townships


def build_shelter_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs=DISPLAY_CRS,
    )


def geometry_union(series: gpd.GeoSeries):
    union_all = getattr(series, "union_all", None)
    if callable(union_all):
        return union_all()
    return series.unary_union


def filter_shelters_in_taiwan(
    shelters_gdf: gpd.GeoDataFrame, townships_gdf: gpd.GeoDataFrame
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    aligned = shelters_gdf.to_crs(townships_gdf.crs)
    land_mask = geometry_union(townships_gdf.geometry)
    inside_mask = aligned.geometry.intersects(land_mask)
    return shelters_gdf.loc[inside_mask].copy(), shelters_gdf.loc[~inside_mask].copy()


def parse_population_sheets(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for sheet_name, frame in sheets.items():
        county_name = normalize_name(sheet_name)
        if county_name == "總計":
            continue
        detail = frame.iloc[4:, :5].copy()
        detail = detail.dropna(how="all")
        for _, row in detail.iterrows():
            town_name = normalize_name(row.iloc[0])
            if not town_name or town_name == county_name:
                continue
            population_value = row.iloc[2]
            if pd.isna(population_value):
                continue
            rows.append(
                {
                    "COUNTYNAME": county_name,
                    "TOWNNAME": town_name,
                    "households": to_int(row.iloc[1]),
                    "population": to_int(population_value),
                    "male": to_int(row.iloc[3]),
                    "female": to_int(row.iloc[4]),
                }
            )
    population = pd.DataFrame(rows)
    if population.empty:
        raise ValueError("Population workbook did not produce any township rows.")
    population = population.drop_duplicates(subset=["COUNTYNAME", "TOWNNAME"]).reset_index(drop=True)
    return population


def load_population_table(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None, header=None, engine="xlrd")
    return parse_population_sheets(sheets)


def merge_population_with_townships(
    townships: gpd.GeoDataFrame, population: pd.DataFrame
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    merged = townships.merge(population, on=["COUNTYNAME", "TOWNNAME"], how="left", indicator=True)
    audit = merged.loc[
        merged["_merge"] != "both",
        ["TOWNCODE", "COUNTYNAME", "TOWNNAME", "_merge"],
    ].copy()
    merged = merged.drop(columns="_merge")
    for column in ["households", "population", "male", "female"]:
        merged[column] = merged[column].fillna(0).astype(int)
    return merged, audit


def load_rivers(path: Path) -> gpd.GeoDataFrame:
    rivers = gpd.read_file(path)
    if rivers.crs is None:
        raise ValueError("River shapefile has no CRS.")
    return rivers.to_crs(ANALYSIS_CRS)


def build_risk_zones(
    rivers: gpd.GeoDataFrame, config: ARIAConfig
) -> tuple[gpd.GeoDataFrame, dict[str, gpd.GeoDataFrame]]:
    river_union = geometry_union(rivers.geometry)
    river_gdf = gpd.GeoDataFrame({"layer": ["rivers"]}, geometry=[river_union], crs=rivers.crs)
    high_geom = geometry_union(rivers.geometry.buffer(config.buffer_high))
    med_outer = geometry_union(rivers.geometry.buffer(config.buffer_med))
    low_outer = geometry_union(rivers.geometry.buffer(config.buffer_low))
    zones = {
        "high": gpd.GeoDataFrame({"risk_level": ["high"]}, geometry=[high_geom], crs=rivers.crs),
        "medium": gpd.GeoDataFrame(
            {"risk_level": ["medium"]},
            geometry=[med_outer.difference(high_geom)],
            crs=rivers.crs,
        ),
        "low": gpd.GeoDataFrame(
            {"risk_level": ["low"]},
            geometry=[low_outer.difference(med_outer)],
            crs=rivers.crs,
        ),
    }
    return river_gdf, zones


def assign_risk_levels(
    shelters: gpd.GeoDataFrame, zones: dict[str, gpd.GeoDataFrame]
) -> gpd.GeoDataFrame:
    result = shelters.copy()
    result["risk_level"] = "safe"
    for level in ["high", "medium", "low"]:
        joined = gpd.sjoin(
            result[["geometry"]],
            zones[level],
            how="inner",
            predicate="within",
        )
        hit_index = joined.index.unique()
        result.loc[result.index.isin(hit_index) & result["risk_level"].eq("safe"), "risk_level"] = level
    return result


def attach_townships(
    shelters: gpd.GeoDataFrame, townships: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    left = shelters.reset_index(drop=True).copy()
    left["row_id"] = left.index
    joined = gpd.sjoin(
        left[["row_id", "geometry"]],
        townships[["TOWNCODE", "COUNTYNAME", "TOWNNAME", "geometry"]],
        how="left",
        predicate="intersects",
    )
    joined = joined.sort_values(["row_id", "TOWNCODE"]).drop_duplicates(subset=["row_id"])
    merged = left.merge(
        joined[["row_id", "TOWNCODE", "COUNTYNAME", "TOWNNAME"]],
        on="row_id",
        how="left",
    )
    return merged.drop(columns="row_id")


def summarize_by_township(
    shelters: gpd.GeoDataFrame, townships: gpd.GeoDataFrame, gap_ratio: float
) -> pd.DataFrame:
    counts = (
        shelters.pivot_table(
            index="TOWNCODE",
            columns="risk_level",
            values="shelter_id",
            aggfunc="count",
            fill_value=0,
        )
        .reindex(columns=RISK_ORDER, fill_value=0)
        .rename(columns={level: f"{level}_count" for level in RISK_ORDER})
        .reset_index()
    )
    capacities = (
        shelters.pivot_table(
            index="TOWNCODE",
            columns="risk_level",
            values="capacity",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=RISK_ORDER, fill_value=0)
        .rename(columns={level: f"{level}_capacity" for level in RISK_ORDER})
        .reset_index()
    )

    summary = townships.drop(columns="geometry").copy()
    summary = summary.merge(counts, on="TOWNCODE", how="left")
    summary = summary.merge(capacities, on="TOWNCODE", how="left")

    count_columns = [f"{level}_count" for level in RISK_ORDER]
    capacity_columns = [f"{level}_capacity" for level in RISK_ORDER]
    for column in count_columns + capacity_columns:
        summary[column] = summary[column].fillna(0).astype(int)

    summary["risk_capacity"] = (
        summary["high_capacity"] + summary["medium_capacity"] + summary["low_capacity"]
    )
    summary["safe_capacity"] = summary["safe_capacity"].astype(int)
    summary["required_safe_capacity"] = (summary["population"] * gap_ratio).round(2)
    summary["capacity_gap"] = (
        summary["required_safe_capacity"] - summary["safe_capacity"]
    ).clip(lower=0)
    summary["gap_flag"] = summary["capacity_gap"] > 0
    summary = summary.sort_values(
        by=["capacity_gap", "high_count", "risk_capacity", "TOWNNAME"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    return summary


def to_native_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in df.to_dict(orient="records"):
        native: dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, pd.Timestamp):
                native[key] = value.isoformat()
            elif pd.isna(value):
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


def create_interactive_map(
    townships: gpd.GeoDataFrame,
    rivers: gpd.GeoDataFrame,
    zones: dict[str, gpd.GeoDataFrame],
    shelters: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    townships_display = townships.to_crs(DISPLAY_CRS).copy()
    townships_display["geometry"] = townships_display.geometry.simplify(0.0002, preserve_topology=True)
    rivers_display = rivers.to_crs(DISPLAY_CRS).copy()
    rivers_display["geometry"] = rivers_display.geometry.simplify(0.0002, preserve_topology=True)
    zones_display = {}
    for level, zone in zones.items():
        display_zone = zone.to_crs(DISPLAY_CRS).copy()
        display_zone["geometry"] = display_zone.geometry.simplify(0.0002, preserve_topology=True)
        zones_display[level] = display_zone
    shelters_display = shelters.to_crs(DISPLAY_CRS)

    aria_map = folium.Map(location=[23.7, 121.0], zoom_start=7, tiles="CartoDB positron")

    township_group = folium.FeatureGroup(name="Townships", show=True)
    folium.GeoJson(
        townships_display,
        style_function=lambda _: {"color": "#7f8c8d", "weight": 0.5, "fillOpacity": 0.0},
    ).add_to(township_group)
    township_group.add_to(aria_map)

    river_group = folium.FeatureGroup(name="Rivers", show=True)
    folium.GeoJson(
        rivers_display,
        style_function=lambda _: {
            "color": "#1565c0",
            "weight": 1.0,
            "fillColor": "#1e88e5",
            "fillOpacity": 0.35,
        },
    ).add_to(river_group)
    river_group.add_to(aria_map)

    for level in ["high", "medium", "low"]:
        zone_group = folium.FeatureGroup(name=f"{level.title()} Risk Buffer", show=True)
        folium.GeoJson(
            zones_display[level],
            style_function=lambda _, color=RISK_COLORS[level]: {
                "color": color,
                "weight": 1.0,
                "fillColor": color,
                "fillOpacity": 0.18,
            },
        ).add_to(zone_group)
        zone_group.add_to(aria_map)

    for level in RISK_ORDER:
        group = folium.FeatureGroup(name=f"{level.title()} Shelters", show=True)
        subset = shelters_display.loc[shelters_display["risk_level"] == level]
        popup = folium.GeoJsonPopup(
            fields=["name", "risk_level", "capacity", "COUNTYNAME", "TOWNNAME"],
            aliases=["Name", "Risk", "Capacity", "County", "Township"],
            localize=True,
            labels=True,
        )
        folium.GeoJson(
            subset[["name", "risk_level", "capacity", "COUNTYNAME", "TOWNNAME", "geometry"]].to_json(),
            marker=folium.CircleMarker(
                radius=3,
                color=RISK_COLORS[level],
                weight=1,
                fill=True,
                fill_color=RISK_COLORS[level],
                fill_opacity=0.9,
            ),
            popup=popup,
        ).add_to(group)
        group.add_to(aria_map)

    folium.LayerControl(collapsed=False).add_to(aria_map)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aria_map.save(output_path)


def create_static_chart(summary: pd.DataFrame, output_path: Path) -> None:
    top10 = summary.head(10).copy()
    if top10.empty:
        raise ValueError("Top 10 summary is empty.")
    top10 = top10.iloc[::-1]
    labels = top10["COUNTYNAME"] + top10["TOWNNAME"]

    plt.rcParams["font.sans-serif"] = [
        "Microsoft JhengHei",
        "Taipei Sans TC Beta",
        "Noto Sans CJK TC",
        "SimHei",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))

    left = pd.Series(0, index=top10.index)
    for level in ["low", "medium", "high"]:
        column = f"{level}_count"
        axes[0].barh(labels, top10[column], left=left, color=RISK_COLORS[level], label=level.title())
        left = left + top10[column]
    axes[0].set_title("Top 10 Townships by Shelter Risk Counts")
    axes[0].set_xlabel("Shelter Count")
    axes[0].legend()

    axes[1].barh(labels, top10["required_safe_capacity"], color="#90caf9", label="Required Safe Capacity")
    axes[1].barh(labels, top10["safe_capacity"], color="#2e7d32", alpha=0.85, label="Available Safe Capacity")
    axes[1].set_title("Top 10 Township Capacity Gaps")
    axes[1].set_xlabel("People")
    axes[1].legend()

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def package_submission(
    config: ARIAConfig, risk_json_path: Path, risk_html_path: Path, risk_png_path: Path
) -> None:
    config.submission_dir.mkdir(parents=True, exist_ok=True)
    copy_if_exists(SCRIPTS_DIR / "ARIA.ipynb", config.submission_dir / "ARIA.ipynb")
    copy_if_exists(PROJECT_ROOT / "README.md", config.submission_dir / "README.md")
    copy_if_exists(risk_json_path, config.submission_dir / "shelter_risk_audit.json")
    copy_if_exists(risk_html_path, config.submission_dir / "risk_map.html")
    copy_if_exists(risk_png_path, config.submission_dir / "risk_map.png")


def build_config_from_env() -> ARIAConfig:
    load_dotenv(PROJECT_ROOT / ".env")
    return ARIAConfig(
        river_shp_path=project_path(os.getenv("RIVER_SHP_PATH", "data/RIVERPOLY/riverpoly/riverpoly.shp")),
        shelter_csv_path=project_path(os.getenv("SHELTER_CSV_PATH", "data/避難收容處所點位檔案v9.csv")),
        township_shp_path=project_path(
            os.getenv(
                "TOWNSHIP_SHP_PATH",
                "data/鄉(鎮、市、區)界線1140318/TOWN_MOI_1140318.shp",
            )
        ),
        population_xls_path=project_path(
            os.getenv("POPULATION_XLS_PATH", "data/鄉鎮戶數及人口數-115年2月.xls")
        ),
        buffer_high=int(os.getenv("BUFFER_HIGH", "500")),
        buffer_med=int(os.getenv("BUFFER_MED", "1000")),
        buffer_low=int(os.getenv("BUFFER_LOW", "2000")),
        gap_ratio=float(os.getenv("GAP_RATIO", "0.2")),
        output_dir=project_path(os.getenv("OUTPUT_DIR", "outputs/aria")),
        submission_dir=project_path(os.getenv("SUBMISSION_DIR", "submission/Homework-3")),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Homework 3 ARIA pipeline")
    parser.add_argument("--river-shp-path")
    parser.add_argument("--shelter-csv-path")
    parser.add_argument("--township-shp-path")
    parser.add_argument("--population-xls-path")
    parser.add_argument("--buffer-high", type=int)
    parser.add_argument("--buffer-med", type=int)
    parser.add_argument("--buffer-low", type=int)
    parser.add_argument("--gap-ratio", type=float)
    parser.add_argument("--output-dir")
    parser.add_argument("--submission-dir")
    return parser


def config_from_args(argv: list[str] | None = None) -> ARIAConfig:
    base = build_config_from_env()
    args = build_parser().parse_args(argv)
    return ARIAConfig(
        river_shp_path=project_path(args.river_shp_path) if args.river_shp_path else base.river_shp_path,
        shelter_csv_path=project_path(args.shelter_csv_path) if args.shelter_csv_path else base.shelter_csv_path,
        township_shp_path=project_path(args.township_shp_path) if args.township_shp_path else base.township_shp_path,
        population_xls_path=project_path(args.population_xls_path) if args.population_xls_path else base.population_xls_path,
        buffer_high=args.buffer_high if args.buffer_high is not None else base.buffer_high,
        buffer_med=args.buffer_med if args.buffer_med is not None else base.buffer_med,
        buffer_low=args.buffer_low if args.buffer_low is not None else base.buffer_low,
        gap_ratio=args.gap_ratio if args.gap_ratio is not None else base.gap_ratio,
        output_dir=project_path(args.output_dir) if args.output_dir else base.output_dir,
        submission_dir=project_path(args.submission_dir) if args.submission_dir else base.submission_dir,
    )


def run_aria_pipeline(config: ARIAConfig) -> ARIAResult:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.submission_dir.mkdir(parents=True, exist_ok=True)

    shelters_raw = load_shelter_table(config.shelter_csv_path)
    shelters_nonzero, zero_or_null = split_zero_and_null_coordinates(shelters_raw)
    shelters_geo = build_shelter_geodataframe(shelters_nonzero)

    townships_geo = load_townships(config.township_shp_path)
    shelters_valid_geo, outside_geo = filter_shelters_in_taiwan(shelters_geo, townships_geo)

    cleaning_summary = {
        "raw_shelter_rows": int(len(shelters_raw)),
        "removed_null_or_zero_coordinate_rows": int(len(zero_or_null)),
        "removed_outside_taiwan_land_mask_rows": int(len(outside_geo)),
        "valid_shelter_rows": int(len(shelters_valid_geo)),
    }
    cleaning_summary_path = config.output_dir / "cleaning_summary.json"
    write_json(cleaning_summary_path, cleaning_summary)

    population = load_population_table(config.population_xls_path)
    population_summary_path = config.output_dir / "population_summary.csv"
    population.to_csv(population_summary_path, index=False, encoding="utf-8-sig")

    townships_analysis = townships_geo.to_crs(ANALYSIS_CRS)
    townships_population, population_audit = merge_population_with_townships(townships_analysis, population)
    population_audit_path = config.output_dir / "population_join_audit.csv"
    population_audit.to_csv(population_audit_path, index=False, encoding="utf-8-sig")

    rivers_analysis = load_rivers(config.river_shp_path)
    rivers_union, zones = build_risk_zones(rivers_analysis, config)

    shelters_analysis = shelters_valid_geo.to_crs(ANALYSIS_CRS)
    shelters_analysis = assign_risk_levels(shelters_analysis, zones)
    shelters_analysis = attach_townships(shelters_analysis, townships_population)

    summary = summarize_by_township(shelters_analysis, townships_population, config.gap_ratio)
    township_summary_path = config.output_dir / "township_summary.csv"
    summary.to_csv(township_summary_path, index=False, encoding="utf-8-sig")

    top10 = summary.head(10).copy()
    top10_path = config.output_dir / "top10_townships.csv"
    top10.to_csv(top10_path, index=False, encoding="utf-8-sig")

    risk_json_path = config.output_dir / "shelter_risk_audit.json"
    json_df = (
        shelters_analysis[
            ["shelter_id", "name", "risk_level", "capacity", "COUNTYNAME", "TOWNNAME", "longitude", "latitude"]
        ]
        .rename(columns={"COUNTYNAME": "county_name", "TOWNNAME": "town_name"})
        .sort_values(by=["shelter_id"])
        .reset_index(drop=True)
    )
    write_json(risk_json_path, to_native_records(json_df))

    risk_html_path = config.output_dir / "risk_map.html"
    create_interactive_map(townships_population, rivers_union, zones, shelters_analysis, risk_html_path)

    risk_png_path = config.output_dir / "risk_map.png"
    create_static_chart(summary, risk_png_path)

    package_submission(config, risk_json_path, risk_html_path, risk_png_path)

    return ARIAResult(
        cleaning_summary_path=cleaning_summary_path,
        population_summary_path=population_summary_path,
        township_summary_path=township_summary_path,
        top10_path=top10_path,
        risk_json_path=risk_json_path,
        risk_html_path=risk_html_path,
        risk_png_path=risk_png_path,
        submission_dir=config.submission_dir,
    )


def main(argv: list[str] | None = None) -> int:
    config = config_from_args(argv)
    result = run_aria_pipeline(config)
    print(f"Cleaning summary: {result.cleaning_summary_path}")
    print(f"Population summary: {result.population_summary_path}")
    print(f"Township summary: {result.township_summary_path}")
    print(f"Top 10 summary: {result.top10_path}")
    print(f"Shelter JSON: {result.risk_json_path}")
    print(f"Interactive map: {result.risk_html_path}")
    print(f"Static chart: {result.risk_png_path}")
    print(f"Submission folder: {result.submission_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
