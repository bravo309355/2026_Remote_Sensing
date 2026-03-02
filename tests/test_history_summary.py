import json
from datetime import datetime

import pandas as pd

from aqi_monitor import AQIMonitor


def test_append_history_creates_and_appends(tmp_path):
    monitor = AQIMonitor(api_key="dummy")
    history_path = tmp_path / "aqi_history.csv"

    df1 = pd.DataFrame([{"sitename": "A", "aqi": "10", "latitude": "25.0", "longitude": "121.0"}])
    df2 = pd.DataFrame(
        [{"sitename": "B", "aqi": "20", "latitude": "24.0", "longitude": "120.0", "pm2.5": "8"}]
    )

    info1 = monitor.append_history(
        df1,
        str(history_path),
        {"run_timestamp": "2026-02-26T10:00:00", "run_id": "run-1"},
    )
    info2 = monitor.append_history(
        df2,
        str(history_path),
        {"run_timestamp": "2026-02-26T11:00:00", "run_id": "run-2"},
    )

    history_df = pd.read_csv(history_path, encoding="utf-8-sig")
    assert info1["history_rows_appended"] == 1
    assert info2["history_rows_appended"] == 1
    assert len(history_df.index) == 2
    assert "run_timestamp" in history_df.columns
    assert "run_id" in history_df.columns
    assert "pm2.5" in history_df.columns


def test_run_summary_structure_and_save(tmp_path):
    monitor = AQIMonitor(api_key="dummy")
    monitor.aqi_data = [
        {
            "sitename": "A",
            "county": "Taipei",
            "aqi": "50",
            "latitude": "25.0",
            "longitude": "121.0",
            "publishtime": "2026-02-26 10:00:00",
        }
    ]
    df = monitor.build_processed_dataframe()
    monitor.last_map_stats = {"map_markers_added": 1, "map_markers_skipped": 0}
    monitor.last_fetch_metadata = {
        "base_url": monitor.base_url,
        "response_format": "list",
        "records_count": 1,
        "fetch_success": True,
    }
    monitor.compute_quality_stats(df)

    csv_path = tmp_path / "aqi_analysis.csv"
    map_path = tmp_path / "aqi_map.html"
    summary_path = tmp_path / "run_summary.json"
    csv_path.write_text("col\nvalue\n", encoding="utf-8")
    map_path.write_text("<html></html>", encoding="utf-8")

    summary = monitor.build_run_summary(
        run_started_at=datetime(2026, 2, 26, 10, 0, 0),
        run_finished_at=datetime(2026, 2, 26, 10, 0, 2),
        options={"csv_only": False, "map_only": False},
        output_paths={"csv": str(csv_path), "map": str(map_path), "summary": str(summary_path)},
        success=True,
        errors=[],
    )
    monitor.save_run_summary(summary, str(summary_path))

    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded["success"] is True
    assert "options" in loaded
    assert "api" in loaded
    assert "outputs" in loaded
    assert "quality" in loaded
    assert "errors" in loaded
    assert loaded["outputs"]["summary"]["exists"] is True
    assert loaded["outputs"]["summary"]["size_bytes"] > 0
