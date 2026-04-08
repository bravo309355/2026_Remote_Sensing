from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


HOMEWORK_DIR = Path(__file__).resolve().parent
NOTEBOOK_PATH = HOMEWORK_DIR / "ARIA_v4.ipynb"
README_PATH = HOMEWORK_DIR / "README.md"
ACCESSIBILITY_CSV_PATH = HOMEWORK_DIR / "accessibility_table.csv"
GRAPHML_PATH = HOMEWORK_DIR / "data" / "hualien_network.graphml"
SUMMARY_PATH = HOMEWORK_DIR / "outputs_summary.txt"

REQUIRED_COLUMNS = [
    "analysis_level",
    "facility_type",
    "facility_id",
    "name",
    "capacity",
    "terrain_risk",
    "nearest_node",
    "rainfall_mm",
    "rainfall_variance",
    "uncertainty_flag",
    "pre_short_km2",
    "post_short_km2",
    "short_loss_pct",
    "pre_long_km2",
    "post_long_km2",
    "long_loss_pct",
    "priority_rank",
]

REQUIRED_MARKERS = [
    "Homework-7 data dir:",
    "Required layer accessibility table (5 key facilities):",
    "Observed isolated facilities:",
    "Stretch contingency scenario constructed from observed spatial rainfall pattern.",
    "Final README refreshed at:",
]


def summarize_notebook(nb: dict) -> tuple[list[str], list[str]]:
    lines: list[str] = [f"Total cells: {len(nb.get('cells', []))}\n"]
    error_lines: list[str] = []
    marker_hits = {marker: False for marker in REQUIRED_MARKERS}

    for index, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        texts: list[str] = []
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                error_lines.append(f"Cell {index}: {output.get('ename')}: {output.get('evalue')}")
            text = output.get("text")
            if text:
                texts.extend(text if isinstance(text, list) else [text])
            plain = (output.get("data") or {}).get("text/plain")
            if plain:
                texts.extend(plain if isinstance(plain, list) else [plain])
        joined = "".join(texts).strip()
        if joined:
            lines.append(f"--- Cell {index} ---\n")
            lines.append(joined[:800] + "\n\n")
            for marker in marker_hits:
                if marker in joined:
                    marker_hits[marker] = True

    lines.append("Notebook marker checks:\n")
    for marker, hit in marker_hits.items():
        lines.append(f"- {marker}: {hit}\n")
    lines.append("Notebook errors:\n" if error_lines else "Notebook errors: none\n")
    for item in error_lines:
        lines.append(f"- {item}\n")
    return lines, error_lines


def summarize_csv(lines: list[str]) -> None:
    if not ACCESSIBILITY_CSV_PATH.exists():
        lines.append(f"CSV exists: False ({ACCESSIBILITY_CSV_PATH.name})\n")
        return
    df = pd.read_csv(ACCESSIBILITY_CSV_PATH)
    lines.append(f"CSV exists: True ({ACCESSIBILITY_CSV_PATH.name})\n")
    lines.append(f"CSV rows: {len(df)}\n")
    lines.append(f"CSV columns: {', '.join(df.columns)}\n")
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    lines.append(f"Missing required columns: {missing_columns if missing_columns else 'none'}\n")
    if "analysis_level" in df.columns:
        lines.append(f"Analysis levels present: {sorted(df['analysis_level'].dropna().astype(str).unique().tolist())}\n")
    if "scenario_name" in df.columns:
        lines.append(f"Scenario names present: {sorted(df['scenario_name'].dropna().astype(str).unique().tolist())}\n")
    if {"analysis_level", "facility_type"}.issubset(df.columns):
        required_rows = df.loc[df["analysis_level"].astype(str) == "required"]
        stretch_rows = df.loc[df["analysis_level"].astype(str) == "stretch"]
        lines.append(f"Required rows: {len(required_rows)}\n")
        lines.append(f"Stretch rows: {len(stretch_rows)}\n")


def summarize_files(lines: list[str]) -> None:
    lines.append(f"GraphML exists: {GRAPHML_PATH.exists()} ({GRAPHML_PATH.name})\n")
    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
        has_captains_log = "## Captain's Log" in text
        lines.append(f"README exists: True ({README_PATH.name})\n")
        lines.append(f"README has Assignment Completion: {'## Assignment Completion' in text}\n")
        lines.append(f"README has Captain's Log: {has_captains_log}\n")
        lines.append(f"README has AI Diagnostic Log: {'## AI Diagnostic Log' in text}\n")
    else:
        lines.append(f"README exists: False ({README_PATH.name})\n")


def main() -> None:
    if not NOTEBOOK_PATH.exists():
        SUMMARY_PATH.write_text(f"Notebook not found: {NOTEBOOK_PATH}\n", encoding="utf-8")
        print(f"Notebook not found: {NOTEBOOK_PATH}")
        return

    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    lines, error_lines = summarize_notebook(notebook)
    summarize_csv(lines)
    summarize_files(lines)
    SUMMARY_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"Done. Written to {SUMMARY_PATH.name}")
    if error_lines:
        print("Notebook contains errors.")
    else:
        print("Notebook contains no error outputs.")


if __name__ == "__main__":
    main()
