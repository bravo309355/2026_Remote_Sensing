from aqi_monitor import AQIMonitor


def make_monitor():
    return AQIMonitor(api_key="dummy")


def test_get_aqi_color_categories():
    monitor = make_monitor()
    assert monitor.get_aqi_color("20") == "green"
    assert monitor.get_aqi_color("75") == "yellow"
    assert monitor.get_aqi_color("150") == "red"
    assert monitor.get_aqi_color("N/A") == "gray"


def test_calculate_distance_basics():
    monitor = make_monitor()
    assert monitor.calculate_distance(25.0, 121.0, 25.0, 121.0) == 0
    distance = monitor.calculate_distance(25.0478, 121.5170, 25.129167, 121.760056)
    assert 20 < distance < 40


def test_compute_quality_stats_counts():
    monitor = make_monitor()
    monitor.aqi_data = [
        {
            "sitename": "A",
            "county": "Taipei",
            "aqi": "40",
            "latitude": "25.1",
            "longitude": "121.5",
            "publishtime": "2026-02-26 10:00:00",
        },
        {
            "sitename": "B",
            "county": "Taoyuan",
            "aqi": "N/A",
            "latitude": "0",
            "longitude": "0",
            "publishtime": "",
        },
        {
            "sitename": "",
            "county": "Keelung",
            "aqi": "120",
            "latitude": "25.12",
            "longitude": "121.76",
            "publishtime": "2026-02-26 10:00:00",
        },
    ]
    df = monitor.build_processed_dataframe()
    monitor.last_map_stats = {"map_markers_added": 2, "map_markers_skipped": 1}
    stats = monitor.compute_quality_stats(df)

    assert stats["records_fetched_total"] == 3
    assert stats["records_processed_for_csv"] == 3
    assert stats["records_with_valid_coordinates"] == 2
    assert stats["records_missing_or_invalid_coordinates"] == 1
    assert stats["records_with_non_numeric_aqi"] == 1
    assert stats["map_markers_added"] == 2
    assert stats["map_markers_skipped"] == 1
    assert stats["aqi_bucket_counts"]["good"] == 1
    assert stats["aqi_bucket_counts"]["unhealthy"] == 1
    assert stats["aqi_bucket_counts"]["unknown"] == 1
    assert stats["missing_key_fields_counts"]["sitename"] == 1
    assert stats["missing_key_fields_counts"]["publishtime"] == 1
