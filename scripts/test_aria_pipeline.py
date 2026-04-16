import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

from scripts import aria_pipeline as aria


def test_normalize_name_removes_spaces_and_marker():
    assert aria.normalize_name("※ 尖 石 鄉") == "尖石鄉"
    assert aria.normalize_name(" 新 竹 縣 ") == "新竹縣"


def test_split_zero_and_null_coordinates():
    df = pd.DataFrame(
        {
            "shelter_id": ["1", "2", "3", "4"],
            "longitude": [121.0, 0.0, None, 121.2],
            "latitude": [24.8, 24.8, 24.7, 0.0],
        }
    )
    valid, invalid = aria.split_zero_and_null_coordinates(df)
    assert valid["shelter_id"].tolist() == ["1"]
    assert invalid["shelter_id"].tolist() == ["2", "3", "4"]


def test_filter_shelters_in_taiwan_keeps_boundary_points():
    townships = gpd.GeoDataFrame(
        {"TOWNCODE": ["A01"], "COUNTYNAME": ["新竹縣"], "TOWNNAME": ["竹北市"]},
        geometry=[Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
        crs="EPSG:4326",
    )
    shelters = gpd.GeoDataFrame(
        {"shelter_id": ["inside", "boundary", "outside"]},
        geometry=[Point(5, 5), Point(10, 5), Point(20, 20)],
        crs="EPSG:4326",
    )
    valid, invalid = aria.filter_shelters_in_taiwan(shelters, townships)
    assert sorted(valid["shelter_id"].tolist()) == ["boundary", "inside"]
    assert invalid["shelter_id"].tolist() == ["outside"]


def test_parse_population_sheets_skips_summary_and_county_total():
    sheets = {
        "總計": pd.DataFrame([[None] * 5 for _ in range(5)]),
        "新竹縣": pd.DataFrame(
            [
                [None, None, None, None, None],
                [None, None, None, None, None],
                [None, None, None, None, None],
                ["新竹縣", "242,257", "597,224", "303,817", "293,407"],
                ["竹 北 市", "90,551", "221,005", "109,740", "111,265"],
                ["※尖石鄉", "2,990", "9,449", "4,922", "4,527"],
            ]
        ),
    }
    population = aria.parse_population_sheets(sheets)
    assert population[["COUNTYNAME", "TOWNNAME"]].to_dict(orient="records") == [
        {"COUNTYNAME": "新竹縣", "TOWNNAME": "竹北市"},
        {"COUNTYNAME": "新竹縣", "TOWNNAME": "尖石鄉"},
    ]
    assert population["population"].tolist() == [221005, 9449]


def test_merge_population_with_townships_tracks_missing_rows():
    townships = gpd.GeoDataFrame(
        {
            "TOWNCODE": ["A01", "A02"],
            "COUNTYNAME": ["新竹縣", "新竹縣"],
            "TOWNNAME": ["竹北市", "北埔鄉"],
        },
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
        ],
        crs="EPSG:4326",
    )
    population = pd.DataFrame(
        {
            "COUNTYNAME": ["新竹縣"],
            "TOWNNAME": ["竹北市"],
            "households": [1],
            "population": [2],
            "male": [1],
            "female": [1],
        }
    )
    merged, audit = aria.merge_population_with_townships(townships, population)
    assert merged.loc[merged["TOWNCODE"] == "A01", "population"].item() == 2
    assert merged.loc[merged["TOWNCODE"] == "A02", "population"].item() == 0
    assert audit[["TOWNCODE", "COUNTYNAME", "TOWNNAME"]].to_dict(orient="records") == [
        {"TOWNCODE": "A02", "COUNTYNAME": "新竹縣", "TOWNNAME": "北埔鄉"}
    ]


def test_assign_risk_levels_honors_highest_priority():
    shelters = gpd.GeoDataFrame(
        {"shelter_id": ["1", "2", "3"]},
        geometry=[Point(1, 1), Point(6, 1), Point(20, 20)],
        crs="EPSG:3826",
    )
    zones = {
        "high": gpd.GeoDataFrame(geometry=[Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])], crs="EPSG:3826"),
        "medium": gpd.GeoDataFrame(geometry=[Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])], crs="EPSG:3826"),
        "low": gpd.GeoDataFrame(geometry=[Polygon([(0, 0), (15, 0), (15, 15), (0, 15)])], crs="EPSG:3826"),
    }
    result = aria.assign_risk_levels(shelters, zones)
    assert result.sort_values("shelter_id")["risk_level"].tolist() == ["high", "medium", "safe"]


def test_summarize_by_township_computes_capacity_gap_and_sorting():
    townships = gpd.GeoDataFrame(
        {
            "TOWNCODE": ["A01", "A02"],
            "COUNTYNAME": ["新竹縣", "臺北市"],
            "TOWNNAME": ["竹北市", "中正區"],
            "households": [100, 100],
            "population": [1000, 500],
            "male": [0, 0],
            "female": [0, 0],
        },
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
        ],
        crs="EPSG:3826",
    )
    shelters = gpd.GeoDataFrame(
        {
            "shelter_id": ["1", "2", "3"],
            "TOWNCODE": ["A01", "A01", "A02"],
            "capacity": [40, 60, 80],
            "risk_level": ["safe", "high", "safe"],
        },
        geometry=[Point(0, 0), Point(0, 0), Point(0, 0)],
        crs="EPSG:3826",
    )
    summary = aria.summarize_by_township(shelters, townships, gap_ratio=0.2)
    assert summary.iloc[0]["TOWNCODE"] == "A01"
    assert summary.iloc[0]["capacity_gap"] == 160
    assert summary.loc[summary["TOWNCODE"] == "A02", "capacity_gap"].item() == 20
