from __future__ import annotations

import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = PROJECT_ROOT / "scripts" / "ARIA_v3.ipynb"
SUBMISSION_NOTEBOOK_PATH = PROJECT_ROOT / "submission" / "Homework-5" / "ARIA_v3.ipynb"


def source(text: str) -> list[str]:
    text = text.strip("\n")
    if not text:
        return []
    return [line + "\n" for line in text.splitlines()]


def markdown_cell(text: str) -> dict[str, object]:
    return {"cell_type": "markdown", "metadata": {}, "source": source(text)}


def code_cell(text: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source(text),
    }


def build_notebook() -> dict[str, object]:
    cells = [
        markdown_cell(
            """
# ARIA v3 Homework 5

This notebook rebuilds a formal Homework 5 pipeline for **花蓮縣 + 宜蘭縣**.
It does **not** reuse `Week5-Student.ipynb` as the source of truth.

**What this notebook does**

1. Load Homework 5 config from the repo-root `.env`
2. Rebuild the Week 3 + Week 4 static baseline for Hualien and Yilan shelters
3. Normalize CWA / CoLife rainfall JSON into one schema
4. Apply nearest-station matching + 5 km heavy-rain buffers
5. Classify `CRITICAL / URGENT / WARNING / SAFE`
6. Render and save `ARIA_v3_Fungwong.html`
7. Optionally generate Gemini advice for the top 3 impacted shelters
"""
        ),
        markdown_cell(
            """
## Captain's Log 1

Resolve the repo root first, then import the reusable Week 5 support module from `scripts/`.
The notebook reads the repo-root `.env`; it does not duplicate secrets inside `submission/`.
"""
        ),
        code_cell(
            """
from pathlib import Path
import sys
import pandas as pd

candidate = Path.cwd().resolve()
search_roots = [candidate, *candidate.parents]
PROJECT_ROOT = next(
    (path for path in search_roots if (path / "scripts").exists() and (path / "data").exists()),
    candidate,
)
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from aria_v3_support import (
    build_config_from_env,
    build_folium_map,
    generate_gemini_advice,
    load_or_build_static_baseline,
    load_rainfall_payload,
    rainfall_records_to_gdf,
    normalize_cwa_json,
    apply_dynamic_risk,
    save_outputs,
    top_impacted_shelters,
)

config = build_config_from_env(PROJECT_ROOT / ".env")
print("PROJECT_ROOT =", PROJECT_ROOT)
print("APP_MODE =", config.app_mode)
print("TARGET_COUNTIES =", config.target_counties)
print("OUTPUT_DIR =", config.output_dir)
print("SUBMISSION_DIR =", config.submission_dir)
"""
        ),
        markdown_cell(
            """
## Captain's Log 2

Rebuild the Week 3 + Week 4 static baseline for both counties.
This is the formal Homework 5 baseline, so it includes river distance, DEM-derived terrain stats,
Week 4 `risk_level`, and a new explicit `terrain_risk` field.
"""
        ),
        code_cell(
            """
static_baseline = load_or_build_static_baseline(config)
display(
    static_baseline[
        [
            "shelter_id",
            "name",
            "county_name",
            "town_name",
            "distance_to_river_m",
            "mean_elevation",
            "max_slope",
            "risk_level",
            "terrain_risk",
        ]
    ].head(10)
)
print("Static shelter count:", len(static_baseline))
print(static_baseline["county_name"].value_counts())
"""
        ),
        markdown_cell(
            """
## Captain's Log 3

Load the rainfall payload in either LIVE or SIMULATION mode, then normalize both formats into one table.
This step also removes `-998` records and keeps only Hualien / Yilan stations.
"""
        ),
        code_cell(
            """
payload, rain_source, fallback_used = load_rainfall_payload(config)
stations_4326 = rainfall_records_to_gdf(normalize_cwa_json(payload), config.target_counties)
print("Rain source:", rain_source)
print("Fallback used:", fallback_used)
display(stations_4326[["station_id", "station_name", "county_name", "town_name", "rain_1hr", "obs_time"]].head(10))
print("Rain station count:", len(stations_4326))
"""
        ),
        markdown_cell(
            """
## Captain's Log 4

Apply nearest-station matching first for popup context, then overlay 5 km heavy-rain buffers for dynamic risk.
The final Homework 5 classification is:

- `CRITICAL`: rain > 80 mm in buffer
- `URGENT`: rain > 40 mm in buffer and `terrain_risk == HIGH`
- `WARNING`: rain > 40 mm in buffer or `terrain_risk == HIGH`
- `SAFE`: otherwise
"""
        ),
        code_cell(
            """
dynamic_shelters, stations_3826 = apply_dynamic_risk(static_baseline, stations_4326, config)
dynamic_shelters, gemini_status = generate_gemini_advice(dynamic_shelters, config)
display(
    dynamic_shelters[
        [
            "name",
            "county_name",
            "terrain_risk",
            "dynamic_risk",
            "nearest_station_name",
            "nearest_station_rain_1hr",
            "max_rain_1hr_in_buffer",
            "gemini_advice",
        ]
    ].head(15)
)
print(dynamic_shelters["dynamic_risk"].value_counts())
print("Gemini status:", gemini_status)
"""
        ),
        markdown_cell(
            """
## Captain's Log 5

Render the Folium map, save all Week 5 outputs, and preview the most impacted shelters.
The HTML saved to `submission/Homework-5/ARIA_v3_Fungwong.html` is the formal submission artifact.
"""
        ),
        code_cell(
            """
fmap = build_folium_map(config, dynamic_shelters, stations_4326)
paths = save_outputs(config, static_baseline, stations_4326, dynamic_shelters, fmap)
summary_table = top_impacted_shelters(dynamic_shelters)[
    [
        "name",
        "county_name",
        "dynamic_risk",
        "terrain_risk",
        "max_rain_1hr_in_buffer",
        "nearest_station_name",
        "nearest_station_rain_1hr",
        "gemini_advice",
    ]
]
display(summary_table)
print(paths)
fmap
"""
        ),
        markdown_cell(
            """
## Captain's Log 6

Final QA reminders:

- `.env` stays at repo root and should not be copied into `submission/`
- `Week5-Student.ipynb` remains untouched
- If LIVE mode fails, the notebook should still succeed via simulation fallback
- If `GEMINI_API_KEY` is absent, the bonus section should skip cleanly
"""
        ),
    ]

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUBMISSION_NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = build_notebook()
    NOTEBOOK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(NOTEBOOK_PATH, SUBMISSION_NOTEBOOK_PATH)
    print(f"Saved notebook: {NOTEBOOK_PATH}")
    print(f"Copied notebook: {SUBMISSION_NOTEBOOK_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
