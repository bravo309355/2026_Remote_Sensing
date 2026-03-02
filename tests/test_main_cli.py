import pytest

import main as cli_entry
from aqi_monitor import build_output_paths


def test_parse_args_defaults():
    args = cli_entry.parse_args([])
    assert args.output_dir == "outputs"
    assert args.csv_only is False
    assert args.map_only is False
    assert args.timestamped_output is False
    assert args.save_history is False
    assert args.history_path == "data/aqi_history.csv"
    assert args.center_lat is None
    assert args.center_lon is None
    assert args.map_zoom == 7


def test_csv_and_map_only_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        cli_entry.parse_args(["--csv-only", "--map-only"])


def test_center_lat_lon_must_be_paired():
    with pytest.raises(SystemExit):
        cli_entry.parse_args(["--center-lat", "25.0"])
    with pytest.raises(SystemExit):
        cli_entry.parse_args(["--center-lon", "121.0"])


def test_timestamped_output_naming_rule():
    paths = build_output_paths(
        output_dir="outputs",
        timestamped=True,
        timestamp_token="20260226_123456",
    )
    assert paths["csv"].endswith("aqi_analysis_20260226_123456.csv")
    assert paths["map"].endswith("aqi_map_20260226_123456.html")
    assert paths["summary"].endswith("run_summary_20260226_123456.json")
