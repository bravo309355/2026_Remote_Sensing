# AQI Monitoring Project (Python)

This project fetches Taiwan AQI data from the MOENV open data API, then:

- generates an AQI analysis CSV
- creates an interactive AQI map (Folium)
- calculates distance from Taipei Main Station to each monitoring site
- writes a run summary JSON with output/quality metadata

## Project Structure

```text
.
|- aqi_monitor.py                # Core AQI logic (fetch/process/export/map/summary/history)
|- main.py                       # CLI entrypoint (default behavior stays compatible)
|- debug_api.py                  # API response debug script (safe URL masking)
|- setup.py                      # Optional setup helper script
|- requirements.txt              # Runtime dependencies (flexible versions)
|- requirements-dev.txt          # Test dependencies
|- requirements-lock.txt         # Reproducible runtime lockfile
|- .env.example                  # Environment variable template (no secrets)
|- data/
|  \- aqi_history.csv            # Optional history output (created only with --save-history)
|- outputs/
|  |- aqi_analysis.csv           # Sample CSV output
|  |- aqi_map.html               # Sample map output
|  |- run_summary.json           # Sample run summary output
|  \- _validation/               # Local validation outputs (git-ignored)
|- tests/                        # Unit tests (pytest)
\- .github/workflows/ci.yml      # GitHub Actions CI (syntax + tests)
```

## Requirements

- Python 3.7+ (validated with Windows Python 3.10; syntax-checked with MSYS Python 3.11)

## Quick Start (Default Behavior)

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Create `.env` from template

```bash
copy .env.example .env
```

3. Edit `.env` and set your MOENV API key

```env
API_KEY_MOENV=your_moenv_api_key_here
```

4. Run the project (same default flow as before: fetch -> CSV -> map)

```bash
python main.py
```

## Outputs

- `outputs/aqi_analysis.csv`: AQI records with distance analysis
- `outputs/aqi_map.html`: Interactive AQI map (cluster + AQI layers)
- `outputs/run_summary.json`: Run metadata, output file metadata, and quality stats
- `data/aqi_history.csv`: Optional historical accumulation file (only when `--save-history`)

The repository keeps sample outputs for review. You can regenerate them by running the project.

## Run Summary (`run_summary.json`)

Each run summary includes:

- success status
- start/end time and duration
- CLI options used
- API response format and record count
- output file paths / existence / file sizes
- data quality statistics (valid coordinates, skipped markers, AQI bucket counts, etc.)
- non-fatal errors (for example history append failures)

## Data Quality Statistics

The pipeline computes non-fatal quality metrics and prints a summary to the console. Metrics include:

- fetched vs processed record counts
- valid / invalid coordinates
- non-numeric AQI count
- marker added/skipped counts
- AQI bucket counts (`good`, `moderate`, `unhealthy`, `unknown`)
- missing key field counts (`sitename`, `county`, `aqi`, `latitude`, `longitude`, `publishtime`)

## Advanced CLI Usage

Generate only CSV:

```bash
python main.py --csv-only
```

Generate only map:

```bash
python main.py --map-only
```

Write outputs to a custom folder:

```bash
python main.py --output-dir outputs_custom
```

Use timestamped output filenames (keeps fixed default behavior unless enabled):

```bash
python main.py --timestamped-output
```

Save history (append mode):

```bash
python main.py --save-history
```

Save history to a custom path:

```bash
python main.py --save-history --history-path data/custom_aqi_history.csv
```

Override map center (also used as distance reference point):

```bash
python main.py --center-lat 25.0330 --center-lon 121.5654 --map-zoom 9
```

## Validation / Debug

API format check (safe URL output: API key is masked):

```bash
python debug_api.py
```

Optional setup helper:

```bash
python setup.py
```

## Testing (Local)

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Run syntax check:

```bash
python -m py_compile aqi_monitor.py debug_api.py main.py setup.py
```

Run unit tests:

```bash
pytest -q
```

## CI (GitHub Actions)

The repository includes `.github/workflows/ci.yml` that runs on `push` and `pull_request`:

- dependency installation
- syntax check
- unit tests (`pytest`)

CI does not call the real AQI API and does not require secrets.

## Reproducible Environment (Lockfile)

You can install from the runtime lockfile for better reproducibility:

```bash
pip install -r requirements-lock.txt
```

Notes:

- `requirements.txt` is the flexible runtime dependency list.
- `requirements-lock.txt` is a tested runtime snapshot.
- `requirements-dev.txt` extends runtime dependencies with test tools.

## Security Notes

- `.env` is ignored by git and should never be committed.
- `.history/` is ignored by git because editor history snapshots may contain sensitive data.
- `outputs/_validation/` is ignored to keep local validation files out of commits.
- If secrets were previously stored in tracked history snapshots, rotate those API keys.

## Dependencies

- `requests`
- `python-dotenv`
- `folium`
- `pandas`
