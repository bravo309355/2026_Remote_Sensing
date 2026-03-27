from __future__ import annotations

from pathlib import Path

import pytest

from scripts.aria_v3_support import (
    build_config_from_env,
    classify_dynamic_risk,
    load_or_build_static_baseline,
    normalize_cwa_json,
    rainfall_records_to_gdf,
)


def test_normalize_cwa_json_handles_single_coordinate_payload() -> None:
    payload = {
        "records": {
            "Station": [
                {
                    "StationId": "466920",
                    "StationName": "蘇澳",
                    "ObsTime": {"DateTime": "2025-11-11T18:50:00+08:00"},
                    "GeoInfo": {
                        "CountyName": "宜蘭縣",
                        "TownName": "蘇澳鎮",
                        "Coordinates": [{"StationLatitude": 24.6, "StationLongitude": 121.85}],
                    },
                    "RainfallElement": {"Past1hr": {"Precipitation": 130.5}},
                }
            ]
        }
    }

    records = normalize_cwa_json(payload)
    assert records == [
        {
            "station_id": "466920",
            "station_name": "蘇澳",
            "county_name": "宜蘭縣",
            "town_name": "蘇澳鎮",
            "lat": 24.6,
            "lon": 121.85,
            "rain_1hr": 130.5,
            "obs_time": "2025-11-11T18:50:00+08:00",
        }
    ]


def test_normalize_cwa_json_prefers_last_valid_coordinate() -> None:
    payload = {
        "records": {
            "Station": [
                {
                    "StationId": "C0X123",
                    "StationName": "測站A",
                    "ObsTime": {"DateTime": "2025-11-11T18:50:00+08:00"},
                    "GeoInfo": {
                        "CountyName": "花蓮縣",
                        "TownName": "花蓮市",
                        "Coordinates": [
                            {"StationLatitude": "300000", "StationLongitude": "2700000"},
                            {"StationLatitude": "23.987", "StationLongitude": "121.601"},
                        ],
                    },
                    "RainfallElement": {"Past1hr": {"Precipitation": "43.5"}},
                }
            ]
        }
    }

    records = normalize_cwa_json(payload)
    gdf = rainfall_records_to_gdf(records, ["花蓮縣"])
    assert pytest.approx(gdf.iloc[0]["lat"]) == 23.987
    assert pytest.approx(gdf.iloc[0]["lon"]) == 121.601
    assert pytest.approx(gdf.iloc[0]["rain_1hr"]) == 43.5


def test_rainfall_records_to_gdf_filters_minus_998() -> None:
    records = [
        {
            "station_id": "A",
            "station_name": "A",
            "county_name": "花蓮縣",
            "town_name": "花蓮市",
            "lat": 23.9,
            "lon": 121.6,
            "rain_1hr": -998,
            "obs_time": "",
        },
        {
            "station_id": "B",
            "station_name": "B",
            "county_name": "花蓮縣",
            "town_name": "花蓮市",
            "lat": 23.95,
            "lon": 121.61,
            "rain_1hr": 18.5,
            "obs_time": "",
        },
    ]

    gdf = rainfall_records_to_gdf(records, ["花蓮縣"])
    assert list(gdf["station_id"]) == ["B"]


@pytest.mark.parametrize(
    ("rain", "terrain_risk", "expected"),
    [
        (None, "LOW", "SAFE"),
        (10, "HIGH", "WARNING"),
        (45, "LOW", "WARNING"),
        (45, "HIGH", "URGENT"),
        (95, "LOW", "CRITICAL"),
    ],
)
def test_classify_dynamic_risk_truth_table(rain: float | None, terrain_risk: str, expected: str) -> None:
    assert classify_dynamic_risk(rain, terrain_risk, warning_rain_mm=40, critical_rain_mm=80) == expected


def test_build_static_baseline_smoke(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    required = [
        project_root / "data" / "DEM_tawiwan_V2025.tif",
        project_root / "data" / "scenarios" / "fungwong_202511.json",
    ]
    if not all(path.exists() for path in required):
        pytest.skip("Full Homework 5 local data is not available in this checkout.")

    env_path = tmp_path / "week5.env"
    env_path.write_text(
        "\n".join(
            [
                f"DEM_PATH={project_root / 'data' / 'DEM_tawiwan_V2025.tif'}",
                f"SIMULATION_DATA={project_root / 'data' / 'scenarios' / 'fungwong_202511.json'}",
                "TARGET_COUNTIES=花蓮縣,宜蘭縣",
                f"OUTPUT_DIR={tmp_path / 'outputs'}",
                f"SUBMISSION_DIR={tmp_path / 'submission'}",
                "REBUILD_STATIC_BASELINE=1",
            ]
        ),
        encoding="utf-8",
    )

    config = build_config_from_env(env_path)
    baseline = load_or_build_static_baseline(config)
    assert not baseline.empty
    assert baseline.geometry.notna().all()
    assert {"花蓮縣", "宜蘭縣"}.issubset(set(baseline["county_name"]))
