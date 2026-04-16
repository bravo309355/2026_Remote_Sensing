from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSIGNMENT_DIR = PROJECT_ROOT / "submission" / "Exercise-7"
NOTEBOOK_PATH = ASSIGNMENT_DIR / "ARIA_v4.ipynb"
README_PATH = ASSIGNMENT_DIR / "README.md"
ACCESSIBILITY_CSV_PATH = ASSIGNMENT_DIR / "accessibility_table.csv"
GRAPHML_PATH = ASSIGNMENT_DIR / "data" / "hualien_network.graphml"
SUMMARY_PATH = ASSIGNMENT_DIR / "outputs_summary.txt"

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

REQUIRED_NOTEBOOK_MARKERS = [
    "Primary rainfall source:",
    "Required layer accessibility table:",
    "Stretch contingency scenario constructed from observed spatial rainfall pattern.",
    "Combined required + stretch table saved to:",
    "Final README refreshed at:",
]


def summarize_notebook(nb: dict) -> tuple[list[str], list[str]]:
    lines: list[str] = [f"Total cells: {len(nb.get('cells', []))}\n"]
    error_lines: list[str] = []
    marker_hits = {marker: False for marker in REQUIRED_NOTEBOOK_MARKERS}

    for index, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        outputs = cell.get("outputs", [])
        texts: list[str] = []
        for output in outputs:
            if output.get("output_type") == "error":
                error_lines.append(
                    f"Cell {index}: {output.get('ename')}: {output.get('evalue')}"
                )
            text = output.get("text")
            if text:
                texts.extend(text if isinstance(text, list) else [text])
            plain = (output.get("data") or {}).get("text/plain")
            if plain:
                texts.extend(plain if isinstance(plain, list) else [plain])

        joined = "".join(texts).strip()
        if joined:
            snippet = joined[:800]
            lines.append(f"--- Cell {index} ---\n")
            lines.append(snippet + "\n\n")
            for marker in marker_hits:
                if marker in joined:
                    marker_hits[marker] = True

    lines.append("Notebook marker checks:\n")
    for marker, hit in marker_hits.items():
        lines.append(f"- {marker}: {hit}\n")
    if error_lines:
        lines.append("Notebook errors:\n")
        for item in error_lines:
            lines.append(f"- {item}\n")
    else:
        lines.append("Notebook errors: none\n")

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
        levels = sorted(df["analysis_level"].dropna().astype(str).unique().tolist())
        lines.append(f"Analysis levels present: {levels}\n")

    if "scenario_name" in df.columns:
        scenarios = sorted(df["scenario_name"].dropna().astype(str).unique().tolist())
        lines.append(f"Scenario names present: {scenarios}\n")

    if {"analysis_level", "facility_type"}.issubset(df.columns):
        stretch_rows = df.loc[df["analysis_level"].astype(str) == "stretch"]
        lines.append(f"Stretch rows: {len(stretch_rows)}\n")
        shelter_rows = stretch_rows.loc[stretch_rows["facility_type"].astype(str) == "shelter"]
        lines.append(f"Stretch shelter rows: {len(shelter_rows)}\n")


def summarize_files(lines: list[str]) -> None:
    lines.append(f"GraphML exists: {GRAPHML_PATH.exists()} ({GRAPHML_PATH.name})\n")
    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
        lines.append(f"README exists: True ({README_PATH.name})\n")
        lines.append(f"README has Required Layer Completion: {'## Required Layer Completion' in text}\n")
        lines.append(f"README has Stretch Enhancements: {'## Stretch Enhancements' in text}\n")
        lines.append(f"README has contingency note: {'stress-test contingency scenario' in text}\n")
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
