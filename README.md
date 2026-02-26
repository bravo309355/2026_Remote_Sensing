# AQI Monitoring Project (Python)

This project fetches Taiwan AQI data from the MOENV open data API, then:

- generates an AQI analysis CSV
- creates an interactive AQI map (Folium)
- calculates distance from Taipei Main Station to each monitoring site

## Project Structure

```text
.
├── aqi_monitor.py         # Core AQI logic (fetch/process/export/map)
├── main.py                # Standard entrypoint wrapper
├── debug_api.py           # API response debug script
├── setup.py               # Environment/setup helper script
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template (no secrets)
├── data/                  # Optional data directory (reserved)
├── outputs/               # Sample outputs and generated results
│   └── _validation/       # Local validation outputs (ignored by git)
└── README.md
```

## Requirements

- Python 3.7+ (tested locally with Python 3.11.x)

## Quick Start

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

4. Run the project (standard entrypoint)

```bash
python main.py
```

## Outputs

- `outputs/aqi_analysis.csv`: AQI records with distance analysis
- `outputs/aqi_map.html`: Interactive AQI map

The repository keeps sample output files for review. You can regenerate them by running the project.

## Validation / Debug

- API format check:

```bash
python debug_api.py
```

- Setup helper (optional):

```bash
python setup.py
```

## Security Notes

- `.env` is ignored by git and should never be committed.
- `.history/` is ignored by git because editor history snapshots may contain sensitive data.
- If secrets were previously stored in tracked history snapshots, rotate those API keys.

## Dependencies

- `requests`
- `python-dotenv`
- `folium`
- `pandas`
