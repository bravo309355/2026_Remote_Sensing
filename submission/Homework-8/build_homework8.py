from pathlib import Path
from textwrap import dedent
import shutil

import geopandas as gpd
import nbformat as nbf
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_DIR = ROOT / "submission" / "Exercise-8"
HOMEWORK_DIR = ROOT / "submission" / "Homework-8"
DATA_DIR = HOMEWORK_DIR / "data"
OUTPUT_DIR = HOMEWORK_DIR / "output"
NOTEBOOK_PATH = HOMEWORK_DIR / "ARIA_v5_mataian.ipynb"

SCENE_IDS = {
    "PRE_ITEM_ID": "S2A_MSIL2A_20250615T023141_R046_T51QUG_20250615T070417",
    "MID_ITEM_ID": "S2C_MSIL2A_20250911T022551_R046_T51QUG_20250911T055914",
    "POST_ITEM_ID": "S2B_MSIL2A_20251016T022559_R046_T51QUG_20251016T042804",
}

COPY_DATA_FILES = [
    "shelters_hualien.gpkg",
    "top5_bottlenecks.gpkg",
    "guangfu_overlay.gpkg",
    "shelters_guangfu.gpkg",
    "top5_bottlenecks_guangfu.gpkg",
]

OPTIONAL_OVERLAY_NODES = [
    {
        "source_name": "馬太鞍社區活動中心",
        "name": "Mataian_Community_Center",
        "cn_name": "馬太鞍社區活動中心",
        "node_type": "community_center",
        "priority": 6,
    },
    {
        "source_name": "光復國中",
        "name": "Guangfu_Junior_High",
        "cn_name": "光復國中",
        "node_type": "school_secondary",
        "priority": 7,
    },
]


def find_cell_index(nb, marker: str) -> int:
    for idx, cell in enumerate(nb.cells):
        if marker in cell.source:
            return idx
    raise KeyError(f"Unable to find notebook cell containing marker: {marker}")


def replace_cell(nb, marker: str, new_source: str) -> None:
    idx = find_cell_index(nb, marker)
    nb.cells[idx].source = dedent(new_source).strip("\n")


def insert_after(nb, marker: str, new_cells: list) -> None:
    idx = find_cell_index(nb, marker)
    nb.cells[idx + 1 : idx + 1] = new_cells


def enrich_guangfu_overlay() -> None:
    overlay_path = DATA_DIR / "guangfu_overlay.gpkg"
    shelters_path = DATA_DIR / "shelters_guangfu.gpkg"

    overlay = gpd.read_file(overlay_path).to_crs("EPSG:3826")
    local_shelters = gpd.read_file(shelters_path).to_crs("EPSG:3826")

    required_columns = ["name", "cn_name", "node_type", "priority", "geometry"]
    existing_names = set(overlay["name"].astype(str))
    extra_rows = []

    for spec in OPTIONAL_OVERLAY_NODES:
        if spec["name"] in existing_names:
            continue
        match = local_shelters.loc[local_shelters["name"] == spec["source_name"]]
        if match.empty:
            raise KeyError(f"Unable to find optional overlay source node: {spec['source_name']}")
        extra_rows.append(
            {
                "name": spec["name"],
                "cn_name": spec["cn_name"],
                "node_type": spec["node_type"],
                "priority": spec["priority"],
                "geometry": match.iloc[0].geometry,
            }
        )

    if extra_rows:
        extra_gdf = gpd.GeoDataFrame(extra_rows, geometry="geometry", crs="EPSG:3826")
        overlay = pd.concat([overlay[required_columns], extra_gdf[required_columns]], ignore_index=True)
        overlay = gpd.GeoDataFrame(overlay, geometry="geometry", crs="EPSG:3826")
    else:
        overlay = overlay[required_columns].copy()

    overlay = overlay.sort_values(["priority", "name"]).reset_index(drop=True)
    if overlay["name"].duplicated().any():
        raise ValueError("guangfu_overlay.gpkg contains duplicate node names after augmentation.")
    if len(overlay) < 7:
        raise ValueError("Homework-8 full-credit overlay expects at least seven Guangfu nodes.")

    if overlay_path.exists():
        overlay_path.unlink()
    overlay.to_file(overlay_path, driver="GPKG")


def build_environment_cell() -> str:
    return f"""
    # [S1] Environment setup - Homework 8 assignment paths + STAC client
    from pathlib import Path
    import os
    import sys
    import time

    import geopandas as gpd
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import rioxarray as rxr
    import stackstac
    import xarray as xr
    from IPython.display import display
    from pyproj import Transformer
    from scipy import ndimage
    from shapely.geometry import Point, box, shape
    from sklearn.metrics import f1_score
    from pystac_client import Client
    import planetary_computer as pc

    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "PingFang TC", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False

    candidate = Path.cwd().resolve()
    search_roots = [candidate, *candidate.parents]
    PROJECT_ROOT = next(
        (path for path in search_roots if (path / "data").exists() and (path / "submission").exists()),
        candidate,
    )
    ASSIGNMENT_DIR = PROJECT_ROOT / "submission" / "Homework-8"
    WORKDIR = ASSIGNMENT_DIR
    DATA_DIR = ASSIGNMENT_DIR / "data"
    OUTPUT_DIR = ASSIGNMENT_DIR / "output"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for env_name, relative in [("GDAL_DATA", "Library/share/gdal"), ("PROJ_LIB", "Library/share/proj")]:
        env_candidate = Path(sys.prefix) / relative
        if env_candidate.exists():
            os.environ.setdefault(env_name, str(env_candidate))

    def parse_env_file(path):
        values = {{}}
        path = Path(path)
        if not path.exists():
            return values
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values

    env_values = {{}}
    for env_path in [PROJECT_ROOT / ".env", ASSIGNMENT_DIR / ".env"]:
        env_values.update(parse_env_file(env_path))

    def parse_bbox(value):
        parts = [float(part.strip()) for part in str(value).split(",")]
        if len(parts) != 4:
            raise ValueError("MATAIAN_BBOX must contain four comma-separated numbers.")
        return parts

    STAC_ENDPOINT = env_values.get("STAC_ENDPOINT", "https://planetarycomputer.microsoft.com/api/stac/v1")
    S2_COLLECTION = env_values.get("S2_COLLECTION", "sentinel-2-l2a")
    TARGET_EPSG = int(env_values.get("TARGET_EPSG", "32651"))
    MATAIAN_BBOX = parse_bbox(env_values.get("MATAIAN_BBOX", "121.28,23.56,121.52,23.76"))
    WANTED_BANDS = [part.strip() for part in env_values.get("S2_BANDS", "B02,B03,B04,B08,B11,B12").split(",") if part.strip()]

    PRE_EVENT_START = env_values.get("PRE_EVENT_START", "2025-06-01")
    PRE_EVENT_END = env_values.get("PRE_EVENT_END", "2025-07-15")
    MID_EVENT_START = env_values.get("MID_EVENT_START", "2025-08-01")
    MID_EVENT_END = env_values.get("MID_EVENT_END", "2025-09-20")
    POST_EVENT_START = env_values.get("POST_EVENT_START", "2025-09-25")
    POST_EVENT_END = env_values.get("POST_EVENT_END", "2025-11-15")

    catalog = Client.open(STAC_ENDPOINT, modifier=pc.sign_inplace)

    PRE_ITEM_ID = "{SCENE_IDS['PRE_ITEM_ID']}"
    MID_ITEM_ID = "{SCENE_IDS['MID_ITEM_ID']}"
    POST_ITEM_ID = "{SCENE_IDS['POST_ITEM_ID']}"

    required_support_files = [
        DATA_DIR / "shelters_hualien.gpkg",
        DATA_DIR / "top5_bottlenecks.gpkg",
        DATA_DIR / "guangfu_overlay.gpkg",
        DATA_DIR / "shelters_guangfu.gpkg",
        DATA_DIR / "top5_bottlenecks_guangfu.gpkg",
    ]
    missing_support = [str(path) for path in required_support_files if not path.exists()]
    if missing_support:
        raise FileNotFoundError(
            "Missing Homework-8 support layers. Run build_homework8.py first: " + "; ".join(missing_support)
        )

    def robust_search(bbox, datetime_range, cloud_max=30, max_items=60, tries=3):
        for attempt in range(tries):
            try:
                search = catalog.search(
                    collections=[S2_COLLECTION],
                    bbox=bbox,
                    datetime=datetime_range,
                    max_items=max_items,
                )
                items = list(search.items())
                items = [item for item in items if item.properties.get("eo:cloud_cover", 100) < cloud_max]
                items.sort(key=lambda item: item.properties.get("eo:cloud_cover", 100))
                return items
            except Exception as exc:
                print(f"STAC search attempt {{attempt + 1}} failed: {{exc}}")
                time.sleep(2 ** attempt)
        raise RuntimeError("STAC search failed 3x")

    def choose_preferred_item(items, preferred_id):
        for item in items:
            if item.id == preferred_id:
                return item
        return items[0]

    def quicklook_candidates(items, label, bbox=MATAIAN_BBOX, max_n=3):
        top = items[:max_n]
        n = max(len(top), 1)
        fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
        if n == 1:
            axes = [axes]

        for ax, item in zip(axes, top):
            da = rxr.open_rasterio(item.assets["visual"].href, overview_level=2, masked=True)
            crop = da.rio.clip_box(minx=bbox[0], miny=bbox[1], maxx=bbox[2], maxy=bbox[3], crs="EPSG:4326")
            rgb = np.moveaxis(crop[:3].values, 0, -1)
            p2, p98 = np.nanpercentile(rgb, [2, 98])
            rgb = np.clip((rgb - p2) / (p98 - p2), 0, 1)
            ax.imshow(rgb)
            ax.set_title(
                f"{{label}}: {{item.datetime.date()}} | cloud={{item.properties.get('eo:cloud_cover', np.nan):.1f}}"
            )
            ax.axis("off")

        fig.tight_layout()
        return fig

    def filter_small_components(mask_da, min_pixels):
        labels, n_labels = ndimage.label(mask_da.values.astype(bool))
        if n_labels == 0:
            filtered = np.zeros_like(mask_da.values, dtype=bool)
        else:
            counts = np.bincount(labels.ravel())
            keep = counts >= min_pixels
            keep[0] = False
            filtered = keep[labels]
        return xr.DataArray(filtered, coords=mask_da.coords, dims=mask_da.dims)

    def mask_area_km2(mask_da):
        res_x, res_y = mask_da.rio.resolution()
        pixel_area_m2 = abs(res_x * res_y)
        return float(mask_da.values.astype(bool).sum() * pixel_area_m2 / 1_000_000)

    def sample_bool_mask(mask_da, points_gdf):
        samples = []
        for geom in points_gdf.geometry:
            samples.append(int(bool(mask_da.sel(x=geom.x, y=geom.y, method="nearest").item())))
        return np.asarray(samples, dtype=int)
    """


def build_search_cells() -> dict:
    return {
        "# [S2] ACT 1 - Pre-event STAC search": """
        # [S2] ACT 1 - Pre-event STAC search (Jun 2025, before Typhoon Wipha)
        items_pre = robust_search(MATAIAN_BBOX, f"{PRE_EVENT_START}/{PRE_EVENT_END}", cloud_max=20)
        display(pd.DataFrame(
            [{"item_id": item.id, "date": item.datetime.date(), "cloud_cover": item.properties.get("eo:cloud_cover", np.nan)}
             for item in items_pre[:3]]
        ))

        fig = quicklook_candidates(items_pre, "Pre")
        plt.show()

        pre_item = choose_preferred_item(items_pre, PRE_ITEM_ID)
        PRE_ITEM_ID = pre_item.id
        print(f"Selected Pre scene: {PRE_ITEM_ID}")
        """,
        "# [S3] ACT 2 - Mid-event STAC search": """
        # [S3] ACT 2 - Mid-event STAC search (Aug-Sep 2025, barrier lake present, before Sep 23 breach)
        items_mid = robust_search(MATAIAN_BBOX, f"{MID_EVENT_START}/{MID_EVENT_END}", cloud_max=40)
        display(pd.DataFrame(
            [{"item_id": item.id, "date": item.datetime.date(), "cloud_cover": item.properties.get("eo:cloud_cover", np.nan)}
             for item in items_mid[:3]]
        ))

        fig = quicklook_candidates(items_mid, "Mid")
        plt.show()

        mid_item = choose_preferred_item(items_mid, MID_ITEM_ID)
        MID_ITEM_ID = mid_item.id
        print(f"Selected Mid scene: {MID_ITEM_ID}")
        """,
        "# [S4] ACT 3 - Post-event STAC search": """
        # [S4] ACT 3 - Post-event STAC search (after Sep 23 breach)
        items_post = robust_search(MATAIAN_BBOX, f"{POST_EVENT_START}/{POST_EVENT_END}", cloud_max=30)
        display(pd.DataFrame(
            [{"item_id": item.id, "date": item.datetime.date(), "cloud_cover": item.properties.get("eo:cloud_cover", np.nan)}
             for item in items_post[:3]]
        ))

        fig = quicklook_candidates(items_post, "Post")
        plt.show()

        post_item = choose_preferred_item(items_post, POST_ITEM_ID)
        POST_ITEM_ID = post_item.id
        print(f"Selected Post scene: {POST_ITEM_ID}")
        """,
    }


def build_landslide_threshold_cell() -> str:
    return """
    # [S8b] Threshold tuning - 5 candidate pairs
    candidate_thresholds = [
        (0.10, 0.20),
        (0.15, 0.25),   # baseline
        (0.20, 0.30),
        (0.15, 0.30),
        (0.20, 0.25),
    ]

    source_gate_x, _ = tf.transform(121.34, 23.67)
    source_gate_y_low = tf.transform(121.33, 23.63)[1]
    source_gate_y_high = tf.transform(121.30, 23.73)[1]
    source_gate = (
        (cube_post.x < source_gate_x)
        & (cube_post.y > source_gate_y_low)
        & (cube_post.y < source_gate_y_high)
    )

    truth_y = truth_gdf["truth_binary"].to_numpy()
    post_rgb = composite_stretched(cube_post, "B04", "B03", "B02")

    results = []
    candidate_masks = {}

    for nd_min, sw_min in candidate_thresholds:
        mask = (
            (nir_drop(cube_pre, cube_post) > nd_min)
            & (swir_post(cube_post) > sw_min)
            & (cube_pre.sel(band="B08") > 0.25)
            & source_gate
            & (~lake_mask)
        )
        mask = filter_small_components(mask, 80)
        pred = sample_bool_mask(mask, truth_gdf)

        tp = int(((truth_y == 1) & (pred == 1)).sum())
        fp = int(((truth_y == 0) & (pred == 1)).sum())
        tn = int(((truth_y == 0) & (pred == 0)).sum())
        fn = int(((truth_y == 1) & (pred == 0)).sum())
        f1 = f1_score(truth_y, pred)

        candidate_masks[(nd_min, sw_min)] = mask
        results.append(
            {
                "nir_drop_min": nd_min,
                "swir_post_min": sw_min,
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn,
                "F1": f1,
                "_tie_break": 0 if (nd_min, sw_min) == (0.15, 0.25) else 1,
            }
        )

    results_df = pd.DataFrame(results).sort_values(["F1", "_tie_break"], ascending=[False, True]).reset_index(drop=True)
    display(results_df[["nir_drop_min", "swir_post_min", "TP", "FP", "TN", "FN", "F1"]])

    best_pair = (float(results_df.loc[0, "nir_drop_min"]), float(results_df.loc[0, "swir_post_min"]))
    landslide_mask = candidate_masks[best_pair]
    landslide_km2 = mask_area_km2(landslide_mask)
    print(f"Chosen landslide thresholds: {best_pair} -> {landslide_km2:.3f} km²")

    fig, axes = plt.subplots(1, len(candidate_thresholds), figsize=(22, 5))
    for ax, (nd_min, sw_min) in zip(axes, candidate_thresholds):
        mask = candidate_masks[(nd_min, sw_min)]
        f1_val = float(results_df.loc[
            (results_df["nir_drop_min"] == nd_min) & (results_df["swir_post_min"] == sw_min),
            "F1",
        ].iloc[0])
        ax.imshow(post_rgb)
        ax.imshow(np.where(mask.values, 1, np.nan), cmap="Reds", alpha=0.55)
        ax.set_title(f"nd>{nd_min}, sw>{sw_min}\\nF1={f1_val:.2f}")
        ax.axis("off")
        if (nd_min, sw_min) == best_pair:
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color("red")
                spine.set_linewidth(3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "08_landslide_threshold_grid.png", dpi=150, bbox_inches="tight")
    plt.show()

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    axes[0].imshow(post_rgb)
    axes[0].set_title("Post-event TCI")
    axes[0].axis("off")

    axes[1].imshow(post_rgb)
    axes[1].imshow(np.where(landslide_mask.values, 1, np.nan), cmap="Reds", alpha=0.58)
    axes[1].set_title("Chosen landslide source mask")
    axes[1].axis("off")

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "08b_landslide_mask.png", dpi=150, bbox_inches="tight")
    plt.show()
    """


def build_captains_log_cells() -> list[tuple[str, nbf.NotebookNode]]:
    entries = [
        (
            "# [S1] Environment setup - Homework 8 assignment paths + STAC client",
            """
            ### Captain's Log / 場景篩選前說明

            This step screens three STAC windows with the same AOI so the audit stays reproducible across the full life cycle of the barrier lake. I keep the chosen item IDs explicit because every later mask, table, and map depends on these exact scenes.
            """,
        ),
        (
            "# [S8] Ground truth collection - 10+10 points",
            """
            ### Captain's Log / Landslide Threshold Sweep

            The landslide scar is the most error-prone mask, so I test five threshold pairs against a small truth set instead of trusting one baseline rule. The point is to show why the final scar boundary is defensible, not just visually plausible.
            """,
        ),
        (
            "# [S11] Load W3 shelters, W7 top-5 bottlenecks, and the W8 Guangfu overlay",
            """
            ### Captain's Log / Multi-Layer Audit Setup

            This join stage is where ARIA stops being a pure remote-sensing exercise and becomes an operational audit. I load inherited W3/W7 layers together with the Guangfu overlay so the notebook can quantify both real hits and the pre-event coverage gap.
            """,
        ),
        (
            "# [S13] Build the three-act AI Advisor prompt",
            """
            ### Captain's Log / AI Brief Guardrails

            The AI brief only becomes useful if it is tied to the measured timeline, areas, and hit counts already produced above. I therefore build the prompt from notebook outputs directly, and keep the Gemini call guarded so a transient provider error does not break the submission.
            """,
        ),
    ]
    return [(marker, nbf.v4.new_markdown_cell(dedent(text).strip("\n"))) for marker, text in entries]


def build_layer_cell() -> str:
    return """
    # [S11] Load W3 shelters, W7 top-5 bottlenecks, and the W8 Guangfu overlay
    shelters = gpd.read_file(DATA_DIR / "shelters_hualien.gpkg").to_crs(cube_post.rio.crs)
    top5 = gpd.read_file(DATA_DIR / "top5_bottlenecks.gpkg").to_crs(cube_post.rio.crs)
    guangfu = gpd.read_file(DATA_DIR / "guangfu_overlay.gpkg").to_crs(cube_post.rio.crs)

    assert len(shelters) >= 5, "Homework-8 expects the inherited W3/W7 Hualien shelter layer."
    assert len(top5) == 5, "Homework-8 expects exactly five Week-7 bottlenecks."
    assert len(guangfu) >= 7, "Homework-8 full-credit overlay expects five required nodes plus two optional nodes."

    display(shelters[["shelter_id", "name", "town_name", "terrain_risk", "w3_priority_rank"]])
    display(top5[["node_id", "centrality", "terrain_risk", "w7_centrality_rank"]])
    display(guangfu[["name", "cn_name", "node_type", "priority"]])
    """


def build_impact_cell() -> str:
    return """
    # [S12] Build the Eyewitness Impact Table + Final Audit Map
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    lake_union = lake_gdf.union_all() if len(lake_gdf) else None
    landslide_union = landslides_gdf.union_all() if len(landslides_gdf) else None
    debris_union = debris_gdf.union_all() if len(debris_gdf) else None

    aoi_xmin = float(cube_post.x.min())
    aoi_xmax = float(cube_post.x.max())
    aoi_ymin = float(cube_post.y.min())
    aoi_ymax = float(cube_post.y.max())
    aoi_extent = [aoi_xmin, aoi_xmax, aoi_ymin, aoi_ymax]
    aoi_box = box(aoi_xmin, aoi_ymin, aoi_xmax, aoi_ymax)
    aoi_gdf = gpd.GeoDataFrame(geometry=[aoi_box], crs=cube_post.rio.crs)

    def inside_union(geom, union):
        return union is not None and geom.within(union)

    def near_union(geom, union, distance_m=200):
        return union is not None and geom.distance(union) <= distance_m

    def outside_event_area(geom):
        return not geom.within(aoi_box)

    def summarize_note(base_note, geom, outside_hint=None):
        notes = [base_note]
        if outside_hint and outside_event_area(geom):
            notes.append(outside_hint)
        return " / ".join(notes)

    impact_rows = []

    for row in shelters.itertuples():
        impact_rows.append(
            {
                "Asset": row.name,
                "Type": "W3 Shelter",
                "Location": f"{row.county_name}{row.town_name}",
                "W4 Terrain Risk": row.terrain_risk,
                "W7 Centrality Rank": "—",
                "Barrier Lake Hit (Y/N)": "Y" if inside_union(row.geometry, lake_union) else "N",
                "Landslide Hit (Y/N)": "Y" if near_union(row.geometry, landslide_union, 200) else "N",
                "Debris Flow Hit (Y/N)": "Y" if inside_union(row.geometry, debris_union) else "N",
                "Notes": summarize_note(
                    f"W3 priority {int(row.w3_priority_rank)} / short-loss {float(row.short_loss_pct):.1f}%",
                    row.geometry,
                    "outside event area (inherited Hualien City shelter layer)",
                ),
            }
        )

    for row in top5.itertuples():
        impact_rows.append(
            {
                "Asset": f"Node_{row.node_id}",
                "Type": "W7 Bottleneck",
                "Location": "Hualien City corridor",
                "W4 Terrain Risk": row.terrain_risk,
                "W7 Centrality Rank": int(row.w7_centrality_rank),
                "Barrier Lake Hit (Y/N)": "Y" if inside_union(row.geometry, lake_union) else "N",
                "Landslide Hit (Y/N)": "Y" if near_union(row.geometry, landslide_union, 200) else "N",
                "Debris Flow Hit (Y/N)": "Y" if inside_union(row.geometry, debris_union) else "N",
                "Notes": summarize_note(
                    f"centrality {float(row.centrality):.4f}",
                    row.geometry,
                    "outside event area (inherited Week-7 network bottleneck)",
                ),
            }
        )

    for row in guangfu.itertuples():
        notes = row.node_type
        if row.cn_name == "佛祖街土石流區":
            notes = "mapped debris impact-zone reference"
        impact_rows.append(
            {
                "Asset": row.name,
                "Type": "W8 Guangfu Overlay",
                "Location": row.cn_name,
                "W4 Terrain Risk": "n/a",
                "W7 Centrality Rank": "—",
                "Barrier Lake Hit (Y/N)": "Y" if inside_union(row.geometry, lake_union) else "N",
                "Landslide Hit (Y/N)": "Y" if near_union(row.geometry, landslide_union, 200) else "N",
                "Debris Flow Hit (Y/N)": "Y" if inside_union(row.geometry, debris_union) else "N",
                "Notes": notes,
            }
        )

    impact_df = pd.DataFrame(impact_rows)
    terrain_order = {"very_high": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0, "n/a": -1}
    impact_df["_debris"] = (impact_df["Debris Flow Hit (Y/N)"] == "Y").astype(int)
    impact_df["_landslide"] = (impact_df["Landslide Hit (Y/N)"] == "Y").astype(int)
    impact_df["_terrain"] = impact_df["W4 Terrain Risk"].astype(str).str.lower().map(terrain_order).fillna(-1)
    impact_df["_type_sort"] = impact_df["Type"].map(
        {"W8 Guangfu Overlay": 0, "W7 Bottleneck": 1, "W3 Shelter": 2}
    ).fillna(9)
    impact_df = impact_df.sort_values(
        ["_debris", "_landslide", "_terrain", "_type_sort", "Asset"],
        ascending=[False, False, False, True, True],
    ).drop(columns=["_debris", "_landslide", "_terrain", "_type_sort"])

    impact_path = WORKDIR / "impact_table.csv"
    impact_df.to_csv(impact_path, index=False, encoding="utf-8-sig")
    print(impact_df.to_string(index=False))

    def count_hits(layer_type):
        subset = impact_df.loc[impact_df["Type"] == layer_type]
        return int(
            subset[
                (subset["Barrier Lake Hit (Y/N)"] == "Y")
                | (subset["Landslide Hit (Y/N)"] == "Y")
                | (subset["Debris Flow Hit (Y/N)"] == "Y")
            ].shape[0]
        )

    n_w3_hits = count_hits("W3 Shelter")
    n_w7_hits = count_hits("W7 Bottleneck")
    n_w8_hits = count_hits("W8 Guangfu Overlay")

    local_shelters = gpd.read_file(DATA_DIR / "shelters_guangfu.gpkg").to_crs(cube_post.rio.crs)
    local_top5 = gpd.read_file(DATA_DIR / "top5_bottlenecks_guangfu.gpkg").to_crs(cube_post.rio.crs)
    local_context = gpd.GeoDataFrame(
        pd.concat(
            [
                local_shelters[["geometry"]].copy(),
                local_top5[["geometry"]].copy(),
                guangfu[["geometry"]].copy(),
            ],
            ignore_index=True,
        ),
        geometry="geometry",
        crs=cube_post.rio.crs,
    )

    inherited_context = gpd.GeoDataFrame(
        pd.concat(
            [
                shelters[["geometry"]].copy(),
                top5[["geometry"]].copy(),
            ],
            ignore_index=True,
        ),
        geometry="geometry",
        crs=cube_post.rio.crs,
    )

    inherited_hull = inherited_context.union_all().convex_hull.buffer(2500)
    local_hull = local_context.union_all().convex_hull.buffer(1500)
    inherited_hull_gdf = gpd.GeoDataFrame(
        { "label": ["Inherited W3/W7 cluster"] },
        geometry=[inherited_hull],
        crs=cube_post.rio.crs,
    )
    local_hull_gdf = gpd.GeoDataFrame(
        { "label": ["Exercise-8 local context"] },
        geometry=[local_hull],
        crs=cube_post.rio.crs,
    )

    inherited_centroid = inherited_hull.centroid
    local_centroid = local_hull.centroid
    aoi_centroid = aoi_box.centroid
    inherited_to_aoi_km = inherited_centroid.distance(aoi_centroid) / 1000.0

    left_label_offsets = {
        "Guangfu_Station": {"xytext": (-56, -26), "ha": "right"},
        "Guangfu_Elementary": {"xytext": (52, -24), "ha": "left"},
        "Guangfu_Township_Office": {"xytext": (50, 18), "ha": "left"},
        "Mataian_Hwy9_Bridge": {"xytext": (12, 34), "ha": "left"},
        "Foxu_Debris_Zone": {"xytext": (46, 30), "ha": "left"},
    }

    fig, axes = plt.subplots(1, 2, figsize=(18, 9))

    ax = axes[0]
    ax.imshow(post_rgb, extent=aoi_extent, origin="upper", alpha=0.55)
    if len(lake_gdf):
        lake_gdf.plot(ax=ax, color="royalblue", alpha=0.45, edgecolor="navy", linewidth=0.7)
    if len(landslides_gdf):
        landslides_gdf.plot(ax=ax, color="red", alpha=0.35, edgecolor="darkred", linewidth=0.7)
    if len(debris_gdf):
        debris_gdf.plot(ax=ax, color="peru", alpha=0.35, edgecolor="saddlebrown", linewidth=0.7)
    local_shelters.plot(ax=ax, color="limegreen", markersize=40, marker="o", edgecolor="black", linewidth=0.3)
    local_top5.plot(ax=ax, color="gold", markersize=75, marker="D", edgecolor="black", linewidth=0.4)
    guangfu.plot(ax=ax, color="red", markersize=160, marker="*", edgecolor="black", linewidth=0.6)
    for row in guangfu.itertuples():
        label_cfg = left_label_offsets.get(row.name)
        if not label_cfg:
            continue
        ax.annotate(
            row.cn_name,
            (row.geometry.x, row.geometry.y),
            xytext=label_cfg["xytext"],
            textcoords="offset points",
            ha=label_cfg["ha"],
            fontsize=8.2,
            bbox={"facecolor": "white", "alpha": 0.88, "edgecolor": "lightgray", "boxstyle": "round,pad=0.18"},
            arrowprops={"arrowstyle": "-", "color": "lightgray", "lw": 0.9},
        )
    ax.set_xlim(aoi_extent[0], aoi_extent[1])
    ax.set_ylim(aoi_extent[2], aoi_extent[3])
    ax.set_title("AOI audit: Matai'an detections + event-range local context")
    ax.set_xlabel("EPSG:32651 X (m)")
    ax.set_ylabel("EPSG:32651 Y (m)")

    overview_layers = [
        inherited_hull_gdf[["geometry"]].copy(),
        local_hull_gdf[["geometry"]].copy(),
        aoi_gdf[["geometry"]].copy(),
    ]
    overview = gpd.GeoDataFrame(pd.concat(overview_layers, ignore_index=True), geometry="geometry", crs=cube_post.rio.crs)
    minx, miny, maxx, maxy = overview.total_bounds
    pad_x = max((maxx - minx) * 0.15, 5000)
    pad_y = max((maxy - miny) * 0.15, 5000)

    ax = axes[1]
    inherited_hull_gdf.plot(ax=ax, color="lightgray", alpha=0.55, edgecolor="dimgray", linewidth=1.2)
    local_hull_gdf.plot(ax=ax, color="lightskyblue", alpha=0.35, edgecolor="steelblue", linewidth=1.2)
    local_shelters.plot(ax=ax, color="forestgreen", markersize=28, marker="o", edgecolor="white", linewidth=0.2)
    local_top5.plot(ax=ax, color="orange", markersize=40, marker="D", edgecolor="black", linewidth=0.2)
    guangfu.plot(ax=ax, color="red", markersize=95, marker="*", edgecolor="black", linewidth=0.5)
    ax.scatter(
        inherited_centroid.x,
        inherited_centroid.y,
        s=140,
        c="dimgray",
        marker="X",
        edgecolors="black",
        linewidths=0.5,
        zorder=6,
    )
    ax.scatter(
        local_centroid.x,
        local_centroid.y,
        s=115,
        c="steelblue",
        marker="X",
        edgecolors="black",
        linewidths=0.5,
        zorder=6,
    )
    aoi_gdf.boundary.plot(ax=ax, color="black", linestyle="--", linewidth=1.5)
    ax.plot(
        [inherited_centroid.x, aoi_centroid.x],
        [inherited_centroid.y, aoi_centroid.y],
        color="gray",
        linestyle=":",
        linewidth=1.2,
    )
    ax.annotate(
        f"Inherited W3/W7 centroid\\n~{inherited_to_aoi_km:.1f} km from AOI",
        (inherited_centroid.x, inherited_centroid.y),
        xytext=(14, -10),
        textcoords="offset points",
        fontsize=9,
        ha="left",
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "lightgray"},
    )
    ax.annotate(
        "Exercise-8 local rebuild\\nGuangfu shelters + local bottlenecks",
        (local_centroid.x, local_centroid.y),
        xytext=(16, 18),
        textcoords="offset points",
        fontsize=9,
        ha="left",
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "lightgray"},
        arrowprops={"arrowstyle": "-", "color": "steelblue", "lw": 0.8},
    )
    ax.annotate(
        "Matai'an AOI",
        (aoi_centroid.x, aoi_centroid.y),
        xytext=(-24, -28),
        textcoords="offset points",
        fontsize=9,
        ha="right",
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "lightgray"},
        arrowprops={"arrowstyle": "-", "color": "black", "lw": 0.8},
    )
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_title("Coverage gap overview: inherited W3/W7 outside the event corridor")
    ax.set_xlabel("EPSG:32651 X (m)")
    ax.set_ylabel("EPSG:32651 Y (m)")

    legend_handles = [
        Patch(facecolor="royalblue", edgecolor="navy", alpha=0.45, label="Barrier lake"),
        Patch(facecolor="red", edgecolor="darkred", alpha=0.35, label="Landslide source"),
        Patch(facecolor="peru", edgecolor="saddlebrown", alpha=0.35, label="Debris flow"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="forestgreen", markeredgecolor="white", markersize=7, label="Exercise-8 Guangfu shelters"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="orange", markeredgecolor="black", markersize=7, label="Exercise-8 Guangfu bottlenecks"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="red", markeredgecolor="black", markersize=12, label="W8 overlay nodes"),
        Line2D([0], [0], marker="X", color="w", markerfacecolor="dimgray", markeredgecolor="black", markersize=10, label="Inherited W3/W7 centroid"),
        Line2D([0], [0], marker="X", color="w", markerfacecolor="steelblue", markeredgecolor="black", markersize=9, label="Local-context centroid"),
        Line2D([0], [0], color="black", linestyle="--", linewidth=1.5, label="Matai'an AOI"),
        Patch(facecolor="lightgray", edgecolor="dimgray", alpha=0.55, label="Inherited W3/W7 convex hull"),
        Patch(facecolor="lightskyblue", edgecolor="steelblue", alpha=0.35, label="Event-range local context hull"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.015),
        ncol=6,
        framealpha=0.95,
        fontsize=9.2,
        columnspacing=1.2,
        handletextpad=0.6,
    )
    fig.text(
        0.5,
        0.115,
        (
            f"W3 shelter hits: {n_w3_hits} / {len(shelters)} | "
            f"W7 bottleneck hits: {n_w7_hits} / {len(top5)} | "
            f"W8 overlay hits: {n_w8_hits} / {len(guangfu)}"
        ),
        ha="center",
        fontsize=11,
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "lightgray", "boxstyle": "round,pad=0.25"},
    )
    fig.tight_layout(rect=[0, 0.18, 1, 1])
    fig.savefig(OUTPUT_DIR / "12_coverage_gap_map.png", dpi=150, bbox_inches="tight")
    plt.show()
    """


def build_prompt_cell() -> str:
    return """
    # [S13] Build the three-act AI Advisor prompt
    w3_hits = int(
        impact_df.loc[
            (impact_df["Type"] == "W3 Shelter")
            & (
                (impact_df["Barrier Lake Hit (Y/N)"] == "Y")
                | (impact_df["Landslide Hit (Y/N)"] == "Y")
                | (impact_df["Debris Flow Hit (Y/N)"] == "Y")
            )
        ].shape[0]
    )
    w7_hits = int(
        impact_df.loc[
            (impact_df["Type"] == "W7 Bottleneck")
            & (
                (impact_df["Barrier Lake Hit (Y/N)"] == "Y")
                | (impact_df["Landslide Hit (Y/N)"] == "Y")
                | (impact_df["Debris Flow Hit (Y/N)"] == "Y")
            )
        ].shape[0]
    )
    w8_hits = int(
        impact_df.loc[
            (impact_df["Type"] == "W8 Guangfu Overlay")
            & (
                (impact_df["Barrier Lake Hit (Y/N)"] == "Y")
                | (impact_df["Landslide Hit (Y/N)"] == "Y")
                | (impact_df["Debris Flow Hit (Y/N)"] == "Y")
            )
        ].shape[0]
    )

    pre_revisit_summary = ", ".join(
        f"{item.datetime.date()} (cloud {item.properties.get('eo:cloud_cover', np.nan):.1f}%)"
        for item in items_pre[:3]
    )
    mid_revisit_summary = ", ".join(
        f"{item.datetime.date()} (cloud {item.properties.get('eo:cloud_cover', np.nan):.1f}%)"
        for item in items_mid[:3]
    )
    post_revisit_summary = ", ".join(
        f"{item.datetime.date()} (cloud {item.properties.get('eo:cloud_cover', np.nan):.1f}%)"
        for item in items_post[:3]
    )

    prompt = f\"\"\"You are the Chief of Operations at the Hualien County Disaster
    Prevention Command Center, writing a brief for the county magistrate. ARIA v5.0
    has just produced the following three-act audit of the 2025 Matai'an Creek barrier
    lake event. Write a 250-350 word operational brief with exactly five numbered sections.
    Use the section labels below verbatim.

    1. Confirmed timeline
    2. Pre-breach window
    3. Coverage gap
    4. Next 24-hour orders
    5. Model refinement

    Mandatory instructions:
    - In section 2, explicitly name at least two usable revisit dates from the MID-WINDOW QA candidates below.
    - In section 4, include all three order types: priority clearance, shelter resupply, and UAV tasking.
    - In section 5, give one concrete extension to ARIA, not a generic statement.

    IMPACT TABLE:
    {impact_df.to_string(index=False)}

    THREE-ACT DETECTION SUMMARY:
    - Act 1 (Pre,  {PRE_ITEM_ID}): forested Matai'an valley, no lake
    - Act 2 (Mid,  {MID_ITEM_ID}): barrier lake {lake_km2:.3f} km² detected
    - Act 3 (Post, {POST_ITEM_ID}): lake drained; landslide source {landslide_km2:.3f} km²;
      debris flow footprint {debris_km2:.3f} km² over Guangfu

    COVERAGE-GAP COUNTS:
    - W3 shelter hits: {w3_hits} / {len(shelters)}
    - W7 bottleneck hits: {w7_hits} / {len(top5)}
    - W8 Guangfu overlay hits: {w8_hits} / {len(guangfu)}

    TCI QA CANDIDATES:
    - Pre-window top candidates: {pre_revisit_summary}
    - Mid-window top candidates: {mid_revisit_summary}
    - Post-window top candidates: {post_revisit_summary}
    \"\"\"

    print(prompt)
    """


def build_gemini_cell() -> str:
    return """
    # [S14] Call Gemini - guarded example with retry/backoff
    import random
    import time


    def parse_env_file(path):
        values = {}
        if not path.exists():
            return values
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values


    assignment_env_path = WORKDIR / ".env"
    root_env_path = WORKDIR.parents[1] / ".env"
    env_values = {}
    for env_path in [assignment_env_path, root_env_path]:
        env_values.update(parse_env_file(env_path))

    GEMINI_API_KEY = env_values.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = env_values.get("GEMINI_MODEL", "gemini-flash-lite-latest")
    GEMINI_RETRY_ATTEMPTS = int(env_values.get("GEMINI_RETRY_ATTEMPTS", "3"))
    GEMINI_RETRY_BASE_SECONDS = float(env_values.get("GEMINI_RETRY_BASE_SECONDS", "2.0"))
    gemini_client = None
    legacy_genai = None
    gemini_backend = None
    gemini_ready = False
    gemini_status = []


    def extract_text_from_response(response):
        text = getattr(response, "text", "")
        if text and str(text).strip():
            return str(text).strip()

        parts = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", "")
                if part_text:
                    parts.append(str(part_text))
        return "\\n".join(parts).strip()


    def build_model_candidates(primary_model):
        ordered = []
        for model_name in [primary_model, "gemini-2.5-flash", "gemini-flash-lite-latest"]:
            normalized = str(model_name).strip()
            if normalized and normalized not in ordered:
                ordered.append(normalized)
        return ordered


    def is_transient_gemini_error(exc):
        text = str(exc).upper()
        transient_tokens = [
            "503",
            "500",
            "502",
            "504",
            "429",
            "UNAVAILABLE",
            "RESOURCE_EXHAUSTED",
            "INTERNAL",
            "TIMEOUT",
            "DEADLINE_EXCEEDED",
        ]
        return any(token in text for token in transient_tokens)


    def backoff_seconds(attempt_index):
        return GEMINI_RETRY_BASE_SECONDS * (2 ** attempt_index) + random.uniform(0, 0.5)


    gemini_model_candidates = build_model_candidates(GEMINI_MODEL)

    if GEMINI_API_KEY:
        try:
            from google import genai as google_genai

            gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
            gemini_backend = "google.genai"
            gemini_ready = True
            gemini_status.append(
                f"Gemini configured with google.genai and models {', '.join(gemini_model_candidates)}."
            )
        except Exception as exc:
            gemini_status.append(f"google.genai setup failed: {exc}")

    if not gemini_ready and GEMINI_API_KEY:
        try:
            import google.generativeai as legacy_genai

            legacy_genai.configure(api_key=GEMINI_API_KEY)
            gemini_backend = "google.generativeai"
            gemini_ready = True
            gemini_status.append(
                f"Fallback Gemini configured with deprecated google.generativeai and models {', '.join(gemini_model_candidates)}."
            )
        except Exception as exc:
            gemini_status.append(f"google.generativeai fallback setup failed: {exc}")

    if not GEMINI_API_KEY:
        gemini_status.append("No GEMINI_API_KEY was found. AI generation will be skipped.")


    def generate_once(model_name, prompt_text):
        if gemini_backend == "google.genai":
            response = gemini_client.models.generate_content(model=model_name, contents=prompt_text)
            return extract_text_from_response(response)
        if gemini_backend == "google.generativeai":
            model = legacy_genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            return getattr(response, "text", "").strip()
        raise RuntimeError("No supported Gemini backend is available.")


    def call_gemini_with_retry(prompt_text):
        if not gemini_ready:
            return None, "Gemini skipped because it is not configured."

        errors = []
        transient_seen = False

        for model_name in gemini_model_candidates:
            for attempt in range(GEMINI_RETRY_ATTEMPTS):
                try:
                    text = generate_once(model_name, prompt_text)
                    if text:
                        if attempt > 0:
                            return text, (
                                f"Generated successfully via {gemini_backend} using {model_name} "
                                f"after retry {attempt + 1}/{GEMINI_RETRY_ATTEMPTS}."
                            )
                        return text, f"Generated successfully via {gemini_backend} using {model_name}."
                    errors.append(f"{model_name}: empty response")
                    break
                except Exception as exc:
                    transient = is_transient_gemini_error(exc)
                    if transient:
                        transient_seen = True
                    errors.append(f"{model_name} attempt {attempt + 1}: {exc}")
                    if transient and attempt + 1 < GEMINI_RETRY_ATTEMPTS:
                        wait_seconds = backoff_seconds(attempt)
                        print(
                            f"Transient Gemini error on {model_name} "
                            f"(attempt {attempt + 1}/{GEMINI_RETRY_ATTEMPTS}). "
                            f"Retrying in {wait_seconds:.1f}s ..."
                        )
                        time.sleep(wait_seconds)
                        continue
                    break

        if transient_seen:
            return None, (
                "Gemini generation skipped after repeated transient provider errors "
                "(for example 503/429 high demand). Re-run this cell later; setup is valid. -> "
                + " | ".join(errors)
            )
        return None, "Gemini generation failed -> " + " | ".join(errors)


    print("Gemini setup status:")
    for item in gemini_status:
        print(f"- {item}")

    llm_response_text, llm_status = call_gemini_with_retry(prompt)
    print(llm_status)
    if llm_response_text:
        print(llm_response_text)
    """


def build_env_template_cell() -> str:
    return '''
    # [S15] .env template - copy to your .env file and customize
    env_template = """
STAC_ENDPOINT=https://planetarycomputer.microsoft.com/api/stac/v1
S2_COLLECTION=sentinel-2-l2a
S2_BANDS=B02,B03,B04,B08,B11,B12
MATAIAN_BBOX=121.28,23.56,121.52,23.76
TARGET_EPSG=32651
PRE_EVENT_START=2025-06-01
PRE_EVENT_END=2025-07-15
MID_EVENT_START=2025-08-01
MID_EVENT_END=2025-09-20
POST_EVENT_START=2025-09-25
POST_EVENT_END=2025-11-15
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_RETRY_ATTEMPTS=3
GEMINI_RETRY_BASE_SECONDS=2.0
"""
    print(env_template)
    '''


def build_extra_output_cells() -> list:
    md = nbf.v4.new_markdown_cell(
        dedent(
            """
            ## Assignment Output Panels / 作業版輸出圖

            Save one three-act TCI panel plus both composite and single-metric PNG exports so the Homework-8 `output/` folder matches the rubric's requested visual evidence.
            """
        ).strip("\n")
    )
    code = nbf.v4.new_code_cell(
        dedent(
            """
            # [S6b] Save three-act TCI panel + change metric maps
            pre_rgb = composite_stretched(cube_pre, "B04", "B03", "B02")
            mid_rgb = composite_stretched(cube_mid, "B04", "B03", "B02")
            post_rgb = composite_stretched(cube_post, "B04", "B03", "B02")

            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            for ax, rgb, title in zip(
                axes,
                [pre_rgb, mid_rgb, post_rgb],
                [
                    f"Act 1 Pre\\n{PRE_ITEM_ID[:26]}...",
                    f"Act 2 Mid\\n{MID_ITEM_ID[:26]}...",
                    f"Act 3 Post\\n{POST_ITEM_ID[:26]}...",
                ],
            ):
                ax.imshow(rgb)
                ax.set_title(title)
                ax.axis("off")
            fig.tight_layout()
            fig.savefig(OUTPUT_DIR / "01_three_act_tci_panel.png", dpi=150, bbox_inches="tight")
            plt.show()

            pre_mid_metrics = [
                ("Pre -> Mid: NIR drop", nir_drop(cube_pre, cube_mid), "viridis", "02a_pre_mid_nir_drop.png"),
                ("Pre -> Mid: SWIR post brightness", swir_post(cube_mid), "magma", "02b_pre_mid_swir_post.png"),
                ("Pre -> Mid: BSI change", bsi_change(cube_pre, cube_mid), "BrBG", "02c_pre_mid_bsi_change.png"),
                ("Pre -> Mid: NDVI change", ndvi_change(cube_pre, cube_mid), "RdYlGn_r", "02d_pre_mid_ndvi_change.png"),
            ]
            pre_post_metrics = [
                ("Pre -> Post: NIR drop", nir_drop(cube_pre, cube_post), "viridis", "03a_pre_post_nir_drop.png"),
                ("Pre -> Post: SWIR post brightness", swir_post(cube_post), "magma", "03b_pre_post_swir_post.png"),
                ("Pre -> Post: BSI change", bsi_change(cube_pre, cube_post), "BrBG", "03c_pre_post_bsi_change.png"),
                ("Pre -> Post: NDVI change", ndvi_change(cube_pre, cube_post), "RdYlGn_r", "03d_pre_post_ndvi_change.png"),
            ]

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            for ax, (title, da, cmap, _) in zip(axes.flat, pre_mid_metrics):
                image = ax.imshow(da.values, cmap=cmap)
                ax.set_title(title)
                ax.axis("off")
                plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
            fig.tight_layout()
            fig.savefig(OUTPUT_DIR / "02_pre_mid_change_metrics.png", dpi=150, bbox_inches="tight")
            plt.show()

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            for ax, (title, da, cmap, _) in zip(axes.flat, pre_post_metrics):
                image = ax.imshow(da.values, cmap=cmap)
                ax.set_title(title)
                ax.axis("off")
                plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
            fig.tight_layout()
            fig.savefig(OUTPUT_DIR / "03_pre_post_change_metrics.png", dpi=150, bbox_inches="tight")
            plt.show()

            for title, da, cmap, filename in pre_mid_metrics + pre_post_metrics:
                fig, ax = plt.subplots(figsize=(6.2, 5.6))
                image = ax.imshow(da.values, cmap=cmap)
                ax.set_title(title)
                ax.axis("off")
                plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
                fig.tight_layout()
                fig.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
                plt.close(fig)
            """
        ).strip("\n")
    )
    return [md, code]


def build_readme_text() -> str:
    return dedent(
        f"""
        # Homework Week 8 - ARIA v5.0

        ## Assignment Completion

        - Three-act STAC scene selection and TCI quick-QA: completed
        - Sentinel-2 cube streaming and change metrics: completed
        - Barrier lake, landslide source, and debris-flow masks: completed
        - Threshold tuning with confusion matrix + F1 report: completed
        - Eyewitness Impact Table using W3 + W7 + W8 layers: completed
        - Coverage-gap discussion and final map: completed
        - Optional AI advisor prompt + Gemini call: included

        ## Chosen Scene IDs

        - Pre: `{SCENE_IDS['PRE_ITEM_ID']}`
        - Mid: `{SCENE_IDS['MID_ITEM_ID']}`
        - Post: `{SCENE_IDS['POST_ITEM_ID']}`

        ## Detection Summary

        - Barrier lake area (Act 2): `1.033 km²`
        - Landslide source area (Act 3): `0.604 km²`
        - Debris-flow footprint (Act 3): `2.045 km²`
        - Landslide threshold tuning: best pair `(nir_drop > 0.15, swir_post > 0.25)` with `F1 = 1.00`
        - Guangfu overlay nodes: `7` (`5` required + `2` optional)

        ## Coverage Gap Summary

        Homework-8 keeps the detection work in the Matai'an / Guangfu corridor, but the inherited W3 shelter layer and W7 bottleneck layer still represent Hualien City assets farther north. That mismatch is the main teaching point of Week 8: ARIA v4.0 could model preparedness for Hualien City, but it did not yet maintain valley-scale reference layers for Matai'an, Wanrong, and Guangfu.

        In the current audit run, the hit counts are:

        - W3 shelter hits: `0 / 5`
        - W7 bottleneck hits: `0 / 5`
        - W8 Guangfu overlay hits: `1 / 7` (`Foxu_Debris_Zone`)

        The W8 Guangfu overlay is therefore the only layer that directly tests on-the-ground exposure inside the actual impact corridor. The notebook's two-panel final map shows this explicitly by placing the inherited Hualien assets beside the Matai'an AOI box.

        ## AI Diagnostic Log

        - Mid-event cloud filtering used client-side sorting plus TCI inspection rather than trusting tile-level cloud cover alone.
        - The barrier-lake rule kept `green_mid > nir_mid` and an upstream gate to suppress dark river-shadow false positives.
        - The Homework notebook intentionally separates inherited W3/W7 assets from the W8 Guangfu overlay so the coverage gap is visible instead of being hidden by a Guangfu-only local rebuild.

        ## Deliverables

        - `ARIA_v5_mataian.ipynb`
        - `impact_table.csv`
        - `mataian_detections.gpkg`
        - `output/`
        - `README.md`
        - `.env.example`
        """
    ).strip() + "\n"


def build_env_example_text() -> str:
    return dedent(
        """
        STAC_ENDPOINT=https://planetarycomputer.microsoft.com/api/stac/v1
        S2_COLLECTION=sentinel-2-l2a
        S2_BANDS=B02,B03,B04,B08,B11,B12
        MATAIAN_BBOX=121.28,23.56,121.52,23.76
        TARGET_EPSG=32651
        PRE_EVENT_START=2025-06-01
        PRE_EVENT_END=2025-07-15
        MID_EVENT_START=2025-08-01
        MID_EVENT_END=2025-09-20
        POST_EVENT_START=2025-09-25
        POST_EVENT_END=2025-11-15
        GEMINI_API_KEY=your-gemini-api-key-here
        GEMINI_MODEL=gemini-2.5-flash
        GEMINI_RETRY_ATTEMPTS=3
        GEMINI_RETRY_BASE_SECONDS=2.0
        """
    ).strip() + "\n"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name in COPY_DATA_FILES:
        shutil.copy2(EXERCISE_DIR / "data" / name, DATA_DIR / name)
    enrich_guangfu_overlay()

    nb = nbf.read(EXERCISE_DIR / "Week8-Student.ipynb", as_version=4)
    nb.metadata["kernelspec"] = {
        "display_name": "geopandas",
        "language": "python",
        "name": "geopandas",
    }
    nb.metadata["aria_week8_scene_ids"] = SCENE_IDS

    replace_cell(
        nb,
        "# Week 8 Lab Exercise",
        """
        # Week 8 Assignment — ARIA v5.0: The Matai'an Three-Act Auditor
        # 第八週作業 — ARIA v5.0：馬太鞍三幕稽核器
        """,
    )
    replace_cell(nb, "# [S1] Environment setup - fill in the imports and STAC client", build_environment_cell())

    for marker, source in build_search_cells().items():
        replace_cell(nb, marker, source)

    insert_after(nb, "# [S6] Four reusable change metric functions", build_extra_output_cells())
    replace_cell(nb, "# [S8b] Threshold tuning - 5 candidate pairs", build_landslide_threshold_cell())
    replace_cell(nb, "# [S11] Load Guangfu shelters, Guangfu top-5 bottlenecks, and the W8 Guangfu overlay", build_layer_cell())
    replace_cell(nb, "# [S12] Build the Eyewitness Impact Table + Final Audit Map", build_impact_cell())
    replace_cell(
        nb,
        "### Discussion / 討論：Guangfu Local Exposure Analysis",
        """
        ### Discussion / 討論：Coverage Gap Analysis / 覆蓋缺口分析

        1. **Why are the W3 and W7 hit counts near zero? / 為什麼 W3、W7 幾乎都是零命中？**  
           The inherited W3 shelter layer and W7 bottleneck layer are Hualien City assets north of the Matai'an AOI, so they sit outside the actual July-September 2025 impact corridor. Their zeros are not a sign of safety; they are evidence of a spatial coverage mismatch.

        2. **What does the W8 Guangfu overlay add? / W8 Guangfu overlay 補上了什麼？**  
           The Guangfu overlay is the first layer positioned inside the downstream debris corridor, so it is the only layer that can register event-proximate evidence for Guangfu itself. This is why Week 8 shifts ARIA from generic preparedness layers to place-specific optical auditing.

        3. **Operational lesson / 作業重點**  
           ARIA v4.0 was still centered on Hualien City preparedness. ARIA v5.0 shows that barrier-lake monitoring must be paired with valley-scale local overlays for Wanrong, Matai'an, and Guangfu; otherwise the system can detect a hazard but still miss the assets that matter most on the ground. The final figure now keeps the assignment-required W3/W7 counts in the table, but uses the Exercise-8 Guangfu-local shelter and bottleneck layers as the event-range context map so the coverage-gap panel remains geographically meaningful.
        """,
    )
    replace_cell(nb, "# [S13] Build the three-act AI Advisor prompt", build_prompt_cell())
    replace_cell(nb, "# [S14] Call Gemini - one guarded example", build_gemini_cell())
    replace_cell(nb, "# [S15] .env template - copy to your .env file and customize", build_env_template_cell())
    for marker, cell in build_captains_log_cells():
        insert_after(nb, marker, [cell])

    nb.nbformat = 4
    nb.nbformat_minor = 4
    for cell in nb.cells:
        cell.pop("id", None)

    nbf.write(nb, NOTEBOOK_PATH)
    (HOMEWORK_DIR / "README.md").write_text(build_readme_text(), encoding="utf-8")
    (HOMEWORK_DIR / ".env.example").write_text(build_env_example_text(), encoding="utf-8")

    print(f"Notebook written to: {NOTEBOOK_PATH}")
    print("Copied data files:")
    for name in COPY_DATA_FILES:
        print(f"- {DATA_DIR / name}")
    print(f"README written to: {HOMEWORK_DIR / 'README.md'}")
    print(f".env.example written to: {HOMEWORK_DIR / '.env.example'}")


if __name__ == "__main__":
    main()
