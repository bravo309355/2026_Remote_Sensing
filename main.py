import argparse

from aqi_monitor import DEFAULT_MAP_ZOOM, run_pipeline


def build_parser():
    parser = argparse.ArgumentParser(
        description="AQI monitoring pipeline (CSV + map + run summary)."
    )
    parser.add_argument("--output-dir", default="outputs", help="Directory for output files.")
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--csv-only", action="store_true", help="Generate only CSV output.")
    output_mode.add_argument("--map-only", action="store_true", help="Generate only map output.")
    parser.add_argument(
        "--timestamped-output",
        action="store_true",
        help="Append timestamp to CSV/map/summary output filenames.",
    )
    parser.add_argument(
        "--save-history",
        action="store_true",
        help="Append processed records to history CSV.",
    )
    parser.add_argument(
        "--history-path",
        default="data/aqi_history.csv",
        help="Path for history CSV when --save-history is enabled.",
    )
    parser.add_argument("--center-lat", type=float, help="Map center latitude (paired with --center-lon).")
    parser.add_argument("--center-lon", type=float, help="Map center longitude (paired with --center-lat).")
    parser.add_argument(
        "--map-zoom",
        type=int,
        default=DEFAULT_MAP_ZOOM,
        help=f"Initial map zoom level (default: {DEFAULT_MAP_ZOOM}).",
    )
    return parser


def validate_args(parser, args):
    if (args.center_lat is None) != (args.center_lon is None):
        parser.error("--center-lat and --center-lon must be provided together")
    return args


def parse_args(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return validate_args(parser, args)


def cli_main(argv=None):
    args = parse_args(argv)
    result = run_pipeline(
        output_dir=args.output_dir,
        csv_only=args.csv_only,
        map_only=args.map_only,
        timestamped_output=args.timestamped_output,
        save_history=args.save_history,
        history_path=args.history_path,
        center_lat=args.center_lat,
        center_lon=args.center_lon,
        map_zoom=args.map_zoom,
    )
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(cli_main())
