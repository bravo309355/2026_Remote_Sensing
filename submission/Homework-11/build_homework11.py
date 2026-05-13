"""Construct Week12_ARIA_v8_HuangYongZhi.ipynb from cell sources defined here.

One-shot builder; running it overwrites the notebook in this folder.
After building, execute with the `geopandas` conda env:
    PYTHONIOENCODING=utf-8 \
    "C:/Users/user/anaconda3/envs/geopandas/python.exe" \
    -m jupyter nbconvert --to notebook --execute --inplace --allow-errors \
    --ExecutePreprocessor.timeout=600 \
    --ExecutePreprocessor.kernel_name=python3 \
    Week12_ARIA_v8_HuangYongZhi.ipynb
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "Week12_ARIA_v8_HuangYongZhi.ipynb"


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src}


def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src}


cells = []

# ───────────────────────────────────────────────────────────────────
# Title
# ───────────────────────────────────────────────────────────────────
cells.append(md("""# Week 12 Homework: ARIA v8.0 — The Classification Engine

**Student:** Huang YongZhi
**Course:** NTU 遙測與空間資訊之分析與應用
**Instructor:** Prof. Su Wen-Ray (蘇文瑞教授)
**Case Study:** 秀林 / 太魯閣（Xiulin / Taroko）研究區 × 2024-04-03 花蓮地震
**Notebook:** `Week12_ARIA_v8_HuangYongZhi.ipynb`

---

## ARIA v8.0 — The Classification Engine

延續 W8-W10 的 STAC API 工作流，這週把「閾值法」升級為「分類器」。
v7.0 用 NDVI > T、VV < T_dB 這類**單指標二元判定**；v8.0 引入 K-means + Random Forest，
**同時利用 6 個 Sentinel-2 波段**輸出 5 類土地覆蓋。

| Task | 占比 | 內容 | 主要 Output |
|------|------|------|------------|
| Task 1 | 15% | K-means 非監督分類（K=5）+ cluster 光譜識別 | `kmeans_classification.png` |
| Task 2 | 25% | Random Forest 監督分類 + Feature Importance | `rf_classification.png` |
| Task 3 | 35% | 內部精度（混淆矩陣）+ SWCB 獨立驗證 | `confusion_matrix.png`, `swcb_overlay.png` |
| Task 4 | 25% | Area stats + Gemini AI 簡報 + 批判評估 | `class_area_stats.csv`, `ai_briefing.md` |

### 研究區（與課堂 Demo 完全不同）

- **課堂 Demo**：花蓮縱谷壽豐/光復一帶（**都市 + 平原**，5 類分布均衡）
- **作業情境**：秀林 / 太魯閣（**山區 + 海岸**，森林+崩塌主導，農地+建物稀少）

BBOX `[121.40, 24.10, 121.80, 24.25]` ≈ 40 km × 17 km，涵蓋蘇花公路、太魯閣國家公園、清水斷崖、立霧溪流域。

### 與 W12 課堂練習的技術延續

- **STAC**：使用 **AWS Element84 Earth Search**（`https://earth-search.aws.element84.com/v1`）— 與課堂同步，無需 planetary_computer 簽章
- **BOA offset 修正**：AWS Element84 的 sentinel-2-l2a metadata 聲明 `scale=0.0001, offset=-0.1`，stackstac 預設會自動套用 → 不能再除 10000，改用 `+ 0.1` 還原傳統 0-1 反射率
- **KMZ 多檔載入**：自動掃描資料夾內所有 `.kmz`，每類別獨立檔案
"""))

# ───────────────────────────────────────────────────────────────────
# [S1] Setup + STAC catalog
# ───────────────────────────────────────────────────────────────────
cells.append(md("""## §0  環境設定 + STAC 連線

載入所需套件、設定中文字型、建立 AWS Element84 STAC catalog。"""))

cells.append(code("""# [S1] 環境設定 + STAC API 連線 + 研究區域定義
# =============================================================================

# --- 基本套件 ---
import os
import time
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

# --- 中文字型（Windows / macOS / Linux）---
import matplotlib.font_manager as fm
_cjk_candidates = [
    'Microsoft JhengHei', 'PingFang TC', 'Noto Sans CJK TC',
    'Heiti TC', 'WenQuanYi Micro Hei', 'Droid Sans Fallback',
]
_available = {f.name for f in fm.fontManager.ttflist}
_cjk_found = [f for f in _cjk_candidates if f in _available]
if _cjk_found:
    plt.rcParams['font.sans-serif'] = _cjk_found + ['DejaVu Sans']
    print(f'中文字型: {_cjk_found[0]}')
else:
    print('⚠ 未找到中文字型，中文標題可能顯示為方框')
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 110

# --- 遙測 / STAC ---
import pystac_client
import stackstac

# --- 機器學習 ---
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix, classification_report,
    accuracy_score, cohen_kappa_score, ConfusionMatrixDisplay,
)
from sklearn.model_selection import train_test_split

# --- 影像後處理 ---
from scipy.ndimage import median_filter

# --- GIS / 向量 ---
import geopandas as gpd
from shapely.geometry import Polygon, box
from rasterio.features import rasterize
from rasterio.transform import Affine, from_bounds
import pyproj
import zipfile, xml.etree.ElementTree as ET

# --- 工作目錄 + 輸出資料夾 ---
WORK_DIR = os.path.dirname(os.path.abspath('__file__')) if '__file__' in dir() else '.'
OUTPUT_DIR = os.path.join(WORK_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f'工作目錄: {WORK_DIR}')
print(f'輸出資料夾: {OUTPUT_DIR}')

# --- AWS Element84 STAC catalog（不需簽章）---
catalog = pystac_client.Client.open('https://earth-search.aws.element84.com/v1')
print(f'STAC catalog: {catalog.title}')

# --- 秀林 / 太魯閣研究區 ---
TAROKO_BBOX = [121.40, 24.10, 121.80, 24.25]
print(f'研究區 BBOX: {TAROKO_BBOX}')
print(f'  經度: {TAROKO_BBOX[0]:.2f}°E - {TAROKO_BBOX[2]:.2f}°E '
      f'(寬 {(TAROKO_BBOX[2] - TAROKO_BBOX[0]) * 111:.1f} km)')
print(f'  緯度: {TAROKO_BBOX[1]:.2f}°N - {TAROKO_BBOX[3]:.2f}°N '
      f'(高 {(TAROKO_BBOX[3] - TAROKO_BBOX[1]) * 111:.1f} km)')
"""))

# ───────────────────────────────────────────────────────────────────
# [S2] STAC search — progressive
# ───────────────────────────────────────────────────────────────────
cells.append(md("""## §1  搜尋震後 Sentinel-2 影像

漸進式策略：嚴格條件先試，找不到就放寬雲量門檻與時間區間。"""))

cells.append(code("""# [S2] 漸進式搜尋震後 Sentinel-2 影像
# =============================================================================
search_configs = [
    ('2024-04-15/2024-05-31', 20, 'Phase 1: 震後 2 個月，雲量 < 20%'),
    ('2024-04-03/2024-08-31', 30, 'Phase 2: 震後 5 個月，雲量 < 30%'),
    ('2024-04-03/2024-12-31', 50, 'Phase 3: 震後全年，雲量 < 50%'),
    ('2024-01-01/2024-12-31', 70, 'Phase 4: 2024 全年，雲量 < 70%'),
]

items = None
for dt_range, max_cc, desc in search_configs:
    print(f'嘗試 {desc}...')
    search = catalog.search(
        collections=['sentinel-2-l2a'],
        bbox=TAROKO_BBOX,
        datetime=dt_range,
        query={'eo:cloud_cover': {'lt': max_cc}},
    )
    items = search.item_collection()
    print(f'  → 找到 {len(items)} 景')
    if len(items) > 0:
        break

if len(items) == 0:
    raise RuntimeError('即使放寬條件仍找不到影像')

items_sorted = sorted(items, key=lambda x: x.properties['eo:cloud_cover'])
best_item = items_sorted[0]

print()
print('=== 選取的最佳影像 ===')
print(f'  影像 ID  : {best_item.id}')
print(f'  拍攝日期 : {best_item.datetime.strftime(\"%Y-%m-%d %H:%M:%S\")}')
print(f'  雲量    : {best_item.properties[\"eo:cloud_cover\"]:.1f}%')
print(f'  平台    : {best_item.properties.get(\"platform\", \"N/A\")}')
"""))

# ───────────────────────────────────────────────────────────────────
# [S3] Load bands + BOA offset fix
# ───────────────────────────────────────────────────────────────────
cells.append(code("""# [S3] 載入 6 波段 + SCL 雲遮罩（AWS Element84 BOA offset 修正版）
# =============================================================================
# AWS Element84 的 STAC asset 聲明 scale=0.0001, offset=-0.1（baseline 04.00 BOA shift）。
# stackstac 預設會自動套用 scale + offset → 我們補回 0.1 還原傳統反射率（0-1 範圍）
BANDS_ASSETS_ALL = ['blue', 'green', 'red', 'nir', 'swir16', 'swir22', 'scl']
BANDS = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']    # Sentinel-2 官方代號（顯示用）
BAND_NAMES = ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2']

stack = stackstac.stack(
    [best_item], assets=BANDS_ASSETS_ALL,
    epsg=32651, resolution=20,
    bounds_latlon=TAROKO_BBOX, dtype='float64',
)
print(f'Lazy 陣列: {stack.shape}  (time, band, y, x)')
print('正在 .compute()，請稍候...')

data = stack.compute()
img_all = data.values[0]                   # (7, H, W)

scl = img_all[-1]                          # SCL 不被 stackstac scale，保持整數
img = img_all[:-1] + 0.1                   # 撤回 BOA offset → 反射率 0-1 範圍

# --- SCL 雲/雲影/雲遮罩 ---
# SCL: 3=Cloud Shadow, 8=Cloud Med, 9=Cloud High, 10=Cirrus
cloud_mask = np.isin(scl, [3, 8, 9, 10])
print(f'雲/雲影像素: {cloud_mask.sum():,} / {cloud_mask.size:,} ({cloud_mask.mean()*100:.1f}%)')

img[:, cloud_mask] = np.nan
img = np.where((img <= 0) | (img > 1), np.nan, img)

n_bands, n_rows, n_cols = img.shape
print(f'\\n影像形狀: {img.shape}  (bands, height, width)')
print(f'像素大小: 20m × 20m')
print(f'影像實體大小: {n_cols * 20 / 1000:.1f} km × {n_rows * 20 / 1000:.1f} km')
print(f'有效像素比例（去雲後）: {np.sum(~np.isnan(img[0])) / img[0].size * 100:.1f}%')

for i, name in enumerate(BAND_NAMES):
    valid = img[i][~np.isnan(img[i])]
    if len(valid) > 0:
        print(f'  {name:6s} ({BANDS[i]}): '
              f'min={valid.min():.4f} max={valid.max():.4f} mean={valid.mean():.4f}')

# UTM transform（後續 ROI 柵格化 + SWCB 比對用）
x_coords = data.x.values
y_coords = data.y.values
x_res = float(x_coords[1] - x_coords[0])
y_res = float(y_coords[1] - y_coords[0])
img_transform = Affine(x_res, 0, float(x_coords[0]) - x_res / 2,
                       0, y_res, float(y_coords[0]) - y_res / 2)
print(f'\\nUTM transform 已建立（EPSG:32651）')
"""))

# ───────────────────────────────────────────────────────────────────
# [S4] RGB visualization
# ───────────────────────────────────────────────────────────────────
cells.append(code("""# [S4] True / False color 視覺化
# =============================================================================
def percentile_stretch(band, low=2, high=98):
    valid = band[~np.isnan(band)]
    if len(valid) == 0:
        return band
    vmin = np.percentile(valid, low)
    vmax = np.percentile(valid, high)
    return np.clip((band - vmin) / (vmax - vmin + 1e-10), 0, 1)


def make_rgb(img_arr, band_indices, low=2, high=98):
    rgb = np.stack(
        [percentile_stretch(img_arr[i], low, high) for i in band_indices],
        axis=-1,
    )
    return np.nan_to_num(rgb, nan=0)


true_color = make_rgb(img, [2, 1, 0])       # R=B04, G=B03, B=B02
false_color = make_rgb(img, [3, 2, 1])      # R=B08, G=B04, B=B03 → 紅色 = 植被

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
axes[0].imshow(true_color)
axes[0].set_title('True Color (B4-B3-B2)\\n真色彩', fontsize=14)
axes[1].imshow(false_color)
axes[1].set_title('False Color (B8-B4-B3)\\n假色彩（紅 = 植被）', fontsize=14)
for ax in axes:
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
plt.suptitle(
    f'Sentinel-2  {best_item.datetime.strftime(\"%Y-%m-%d\")}  秀林 / 太魯閣',
    fontsize=15, y=1.02,
)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'study_area_rgb.png'),
            dpi=130, bbox_inches='tight')
plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════
#  TASK 1: K-means
# ═══════════════════════════════════════════════════════════════════
cells.append(md("""## Task 1 — K-means 非監督分類 (15%)

對 6 波段反射率影像進行 K=5 K-means 分群，分析每個 cluster 的平均光譜，推測對應到的土地覆蓋類型。"""))

cells.append(code("""# [T1-1] 特徵矩陣 + K-means K=5
# =============================================================================
pixels = img.reshape(n_bands, -1).T               # (n_pixels, 6)
valid_pixel_mask = ~np.any(np.isnan(pixels), axis=1)
pixels_valid = pixels[valid_pixel_mask]
print(f'有效像素數: {pixels_valid.shape[0]:,} / {pixels.shape[0]:,}')

K = 5
print(f'\\n正在跑 K-means (K={K})...')
kmeans = KMeans(n_clusters=K, random_state=42, n_init=10, max_iter=300)
labels_km = kmeans.fit_predict(pixels_valid)
print(f'K-means 完成！ Inertia = {kmeans.inertia_:.2f}')

# 重建 2D 分類圖
class_map_km = np.full(pixels.shape[0], np.nan)
class_map_km[valid_pixel_mask] = labels_km
class_map_km = class_map_km.reshape(n_rows, n_cols)

# 各 cluster 平均光譜 + NDVI / NDBI
print('\\n=== 各 Cluster 平均光譜 ===')
print(f'  {\"Cluster\":<9}{\"Size\":>10}{\"Blue\":>8}{\"Green\":>8}{\"Red\":>8}'
      f'{\"NIR\":>8}{\"SWIR1\":>8}{\"SWIR2\":>8}{\"NDVI\":>8}{\"NDBI\":>8}')
cluster_means = kmeans.cluster_centers_
for c in range(K):
    size = int(np.sum(labels_km == c))
    m = cluster_means[c]
    ndvi = (m[3] - m[2]) / (m[3] + m[2] + 1e-10)
    ndbi = (m[4] - m[3]) / (m[4] + m[3] + 1e-10)
    print(f'  C{c:<8}{size:>10,}'
          f'{m[0]:>8.4f}{m[1]:>8.4f}{m[2]:>8.4f}{m[3]:>8.4f}{m[4]:>8.4f}{m[5]:>8.4f}'
          f'{ndvi:>+8.3f}{ndbi:>+8.3f}')
"""))

cells.append(code("""# [T1-2] K-means 視覺化 + 光譜曲線
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# 左：分類圖
cmap_km = plt.cm.get_cmap('Set1', K)
im = axes[0].imshow(class_map_km, cmap=cmap_km, vmin=-0.5, vmax=K - 0.5)
cbar = plt.colorbar(im, ax=axes[0], ticks=range(K), shrink=0.8)
cbar.set_label('Cluster ID')
axes[0].set_title(f'K-means 非監督分類 (K={K})', fontsize=14)
axes[0].set_xlabel('Column')
axes[0].set_ylabel('Row')

# 右：各 cluster 平均光譜
colors_spec = plt.cm.Set1(np.linspace(0, 1, K))
for c in range(K):
    axes[1].plot(range(n_bands), cluster_means[c], 'o-',
                 color=colors_spec[c], linewidth=2, markersize=8,
                 label=f'Cluster {c} ({int(np.sum(labels_km == c)):,} px)')
axes[1].set_xticks(range(n_bands))
axes[1].set_xticklabels([f'{BAND_NAMES[i]}\\n({BANDS[i]})' for i in range(n_bands)])
axes[1].set_ylabel('Mean Reflectance')
axes[1].set_title('各 Cluster 平均光譜曲線', fontsize=14)
axes[1].legend(fontsize=10, loc='best')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'kmeans_classification.png'),
            dpi=130, bbox_inches='tight')
plt.show()
print(f'→ Saved kmeans_classification.png')
"""))

cells.append(md("""### Task 1 — Cluster 識別與討論

下表是依據上方平均光譜 + NDVI/NDBI + 在影像上的空間分布所做的人工判讀（**會在 notebook 跑完後由學生根據實際結果填寫**）。

| Cluster | 像素佔比 | 光譜特徵 | 推測地物 |
|---------|---------|---------|---------|
| C0 | _<填寫>_% | _<填寫>_ | _<填寫>_ |
| C1 | _<填寫>_% | _<填寫>_ | _<填寫>_ |
| C2 | _<填寫>_% | _<填寫>_ | _<填寫>_ |
| C3 | _<填寫>_% | _<填寫>_ | _<填寫>_ |
| C4 | _<填寫>_% | _<填寫>_ | _<填寫>_ |

**討論：哪些 cluster 容易解讀？哪些難？為什麼？**

_<填寫此處 — 重點通常是「水體+陰影混淆」、「裸地+建物混淆」這類非監督分類的典型限制，可參考課堂 Demo 的結論>_"""))

# ═══════════════════════════════════════════════════════════════════
#  TASK 2: Random Forest
# ═══════════════════════════════════════════════════════════════════
cells.append(md("""## Task 2 — Random Forest 監督分類 (25%)

使用 Method B（KMZ 多邊形 ROI）。把 5 個類別的 KMZ 檔放在 notebook 同一資料夾，
程式會自動掃描並透過 Placemark 名稱或檔名推斷類別。

### 5 個類別

| ID | 名稱 | KMZ 命名建議 |
|----|------|------|
| 0 | Water | `水體.kmz` 或 `water.kmz` |
| 1 | Forest | `森林.kmz` |
| 2 | Cropland | `農地.kmz` |
| 3 | Bare/Landslide | `裸露地.kmz` |
| 4 | Built-up | `建物.kmz` |"""))

cells.append(code("""# [T2-1] 載入 KMZ ROI + 解析 + 提取訓練像素
# =============================================================================
import glob

CLASS_NAMES = ['Water', 'Forest', 'Cropland', 'Bare/Landslide', 'Built-up']
CLASS_NAMES_ZH = ['水體', '森林', '農地', '裸地/崩塌', '建物']
N_CLASSES = len(CLASS_NAMES)

# 多邊形名稱／檔名 → 類別 ID（順序很重要：長關鍵字在前）
name_to_class_ordered = [
    ('水體', 0), ('水', 0), ('Water', 0), ('water', 0),
    ('森林', 1), ('植被', 1), ('植', 1), ('林', 1),
    ('Forest', 1), ('forest', 1), ('Vegetation', 1),
    ('農地', 2), ('農田', 2), ('農', 2),
    ('Cropland', 2), ('cropland', 2), ('Agriculture', 2),
    ('裸露地', 3), ('裸地', 3), ('崩塌', 3), ('裸', 3),
    ('Bare', 3), ('bare', 3), ('Landslide', 3),
    ('建物', 4), ('建', 4), ('Built', 4), ('built', 4), ('Built-up', 4),
]


def classify_name(text):
    for kw, cid in name_to_class_ordered:
        if kw in text:
            return cid
    return None


def parse_kmz(filename, fallback_class=None):
    NS = '{http://www.opengis.net/kml/2.2}'
    results = []
    with zipfile.ZipFile(filename, 'r') as z:
        kml_name = [n for n in z.namelist() if n.endswith('.kml')][0]
        with z.open(kml_name) as f:
            tree = ET.parse(f)
    for pm in tree.findall(f'.//{NS}Placemark'):
        name_elem = pm.find(f'{NS}name')
        coords_elem = pm.find(f'.//{NS}coordinates')
        if coords_elem is None or coords_elem.text is None:
            continue
        pm_name = (name_elem.text or '').strip() if name_elem is not None else ''
        cls_id = classify_name(pm_name) if pm_name else None
        src_tag = 'Placemark'
        if cls_id is None and fallback_class is not None:
            cls_id = fallback_class
            src_tag = 'filename'
        if cls_id is None:
            print(f'  ⚠ 無法辨識 \"{pm_name}\"，已跳過')
            continue
        pts = []
        for c in coords_elem.text.strip().split():
            parts = c.split(',')
            if len(parts) >= 2:
                try:
                    pts.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue
        if len(pts) < 3:
            continue
        poly = Polygon(pts)
        if poly.is_valid and poly.area > 0:
            results.append((cls_id, poly, pm_name, src_tag))
    return results


# 掃描資料夾內所有 KMZ（排除 SWCB 的 KML — 用副檔名區分）
kmz_files = sorted(glob.glob(os.path.join(WORK_DIR, '*.kmz')))
if not kmz_files:
    raise FileNotFoundError(
        '找不到 KMZ 訓練 ROI！請把 5 個類別的 .kmz 檔放到本 notebook 同一資料夾，再重新執行。'
    )

print(f'掃到 {len(kmz_files)} 個 KMZ')
for f in kmz_files:
    print(f'  - {os.path.basename(f)}  ({os.path.getsize(f):,} bytes)')

polygons_by_class = {i: [] for i in range(N_CLASSES)}
print('\\n--- 解析 KMZ ---')
for kmz_file in kmz_files:
    stem = os.path.splitext(os.path.basename(kmz_file))[0]
    fallback_cls = classify_name(stem)
    print(f'\\n[{os.path.basename(kmz_file)}]' +
          (f'  (檔名 → {CLASS_NAMES[fallback_cls]})' if fallback_cls is not None else ''))
    for cls_id, poly, pm_name, src in parse_kmz(kmz_file, fallback_class=fallback_cls):
        polygons_by_class[cls_id].append(poly)
        print(f'  ✓ \"{pm_name or stem}\" [{src}] → {CLASS_NAMES[cls_id]}')
"""))

cells.append(code("""# [T2-2] 多邊形 → UTM → 柵格化 → 提取訓練像素
# =============================================================================
transformer = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:32651', always_xy=True)
shapes = []
for cls_id, polys in polygons_by_class.items():
    for poly in polys:
        utm_coords = [transformer.transform(x, y) for x, y in poly.exterior.coords]
        utm_poly = Polygon(utm_coords)
        if utm_poly.is_valid and utm_poly.area > 0:
            shapes.append((utm_poly, cls_id))

roi_raster = rasterize(
    shapes, out_shape=(n_rows, n_cols),
    transform=img_transform, fill=-1, dtype=np.int8, all_touched=True,
)

X_list, y_list = [], []
for cls_id in range(N_CLASSES):
    cls_mask = (roi_raster == cls_id)
    cls_pixels = img[:, cls_mask].T
    valid_rows = ~np.any(np.isnan(cls_pixels), axis=1)
    if valid_rows.sum() > 0:
        X_list.append(cls_pixels[valid_rows])
        y_list.append(np.full(valid_rows.sum(), cls_id))

X_roi = np.vstack(X_list)
y_roi = np.concatenate(y_list)

print('=== 訓練樣本統計 ===')
print(f'總像素: {len(y_roi):,}\\n')
for cls_id in range(N_CLASSES):
    n = int(np.sum(y_roi == cls_id))
    n_poly = len(polygons_by_class[cls_id])
    flag = '✅' if n >= 50 else ('🔶' if n >= 30 else '⚠️ 嚴重不足')
    print(f'  Class {cls_id} {CLASS_NAMES[cls_id]:>16s} ({CLASS_NAMES_ZH[cls_id]:>6s}): '
          f'{n:>5,} px, {n_poly} 多邊形  {flag}')

# 視覺化 ROI 疊加於真色彩
fig, ax = plt.subplots(figsize=(12, 7))
ax.imshow(true_color)
roi_colors = ['#0077BE', '#228B22', '#DAA520', '#CD853F', '#808080']
for cls_id in range(N_CLASSES):
    m = (roi_raster == cls_id)
    if np.any(m):
        overlay = np.zeros((*m.shape, 4))
        overlay[m] = mcolors.to_rgba(roi_colors[cls_id], alpha=0.6)
        ax.imshow(overlay)

legend = [Patch(facecolor=roi_colors[i], alpha=0.7,
                label=f'{CLASS_NAMES[i]} ({CLASS_NAMES_ZH[i]})') for i in range(N_CLASSES)]
ax.legend(handles=legend, loc='upper right', framealpha=0.9)
ax.set_title('訓練樣本 ROI 疊加真色彩', fontsize=14)
plt.tight_layout()
plt.show()
"""))

cells.append(code("""# [T2-3] 訓練 Random Forest + 評估
# =============================================================================
X_tr, X_te, y_tr, y_te = train_test_split(
    X_roi, y_roi, test_size=0.2, random_state=42, stratify=y_roi,
)
print(f'訓練集: {len(y_tr):,} px / 測試集: {len(y_te):,} px')

print('\\n正在訓練 RF (n_estimators=200)...')
rf = RandomForestClassifier(
    n_estimators=200,
    max_features='sqrt',
    random_state=42,
    n_jobs=-1,
    oob_score=True,
)
rf.fit(X_tr, y_tr)
y_pred_test = rf.predict(X_te)

train_acc = rf.score(X_tr, y_tr)
test_acc = accuracy_score(y_te, y_pred_test)
oob_acc = rf.oob_score_
kappa = cohen_kappa_score(y_te, y_pred_test)

print('\\n=== Random Forest 評估 ===')
print(f'  Training Accuracy: {train_acc:.4f} ({train_acc*100:.2f}%)')
print(f'  Test     Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)')
print(f'  OOB      Accuracy: {oob_acc:.4f} ({oob_acc*100:.2f}%)')
print(f'  Cohen Kappa      : {kappa:.4f}')

print('\\n=== Classification Report ===')
# 用 labels=[0..N_CLASSES-1] 避免測試集缺類時的長度錯誤
print(classification_report(
    y_te, y_pred_test,
    labels=list(range(N_CLASSES)),
    target_names=CLASS_NAMES, digits=4, zero_division=0,
))
"""))

cells.append(code("""# [T2-4] 對全影像進行分類 + 視覺化
# =============================================================================
print('正在對全影像 ({:,} 像素) 進行分類預測...'.format(len(pixels_valid)))
rf_labels_all = rf.predict(pixels_valid)
class_map_rf = np.full(pixels.shape[0], np.nan)
class_map_rf[valid_pixel_mask] = rf_labels_all
class_map_rf = class_map_rf.reshape(n_rows, n_cols)
print('完成')

# 配色：藍/綠/金/棕/灰 (per spec)
lc_colors = ['#0077BE', '#228B22', '#DAA520', '#CD853F', '#808080']
lc_cmap = mcolors.ListedColormap(lc_colors)
lc_bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
lc_norm = mcolors.BoundaryNorm(lc_bounds, lc_cmap.N)

fig, axes = plt.subplots(1, 2, figsize=(18, 7))
axes[0].imshow(true_color)
axes[0].set_title('True Color 參考', fontsize=13)
axes[1].imshow(class_map_rf, cmap=lc_cmap, norm=lc_norm)
axes[1].set_title(
    f'Random Forest 分類\\nOA={test_acc:.3f} / Kappa={kappa:.3f}',
    fontsize=13,
)
legend = [Patch(facecolor=lc_colors[i],
                label=f'{CLASS_NAMES[i]} ({CLASS_NAMES_ZH[i]})')
          for i in range(N_CLASSES)]
axes[1].legend(handles=legend, loc='lower right', framealpha=0.9, fontsize=10)
for ax in axes:
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'rf_classification.png'),
            dpi=130, bbox_inches='tight')
plt.show()
print(f'→ Saved rf_classification.png')
"""))

cells.append(code("""# [T2-5] Feature Importance
# =============================================================================
importance = rf.feature_importances_
order = np.argsort(importance)[::-1]

fig, ax = plt.subplots(figsize=(8, 5))
colors_bar = plt.cm.viridis(np.linspace(0.2, 0.8, n_bands))
ax.barh(
    [f'{BAND_NAMES[i]} ({BANDS[i]})' for i in order[::-1]],
    importance[order[::-1]],
    color=[colors_bar[i] for i in order[::-1]],
    edgecolor='black', linewidth=0.5,
)
ax.set_xlabel('Feature Importance')
ax.set_title('Random Forest — Band Importance')
for i, v in enumerate(importance[order[::-1]]):
    ax.text(v + 0.005, i, f'{v:.3f}', va='center', fontsize=10)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'rf_feature_importance.png'),
            dpi=130, bbox_inches='tight')
plt.show()

print('\\n=== Feature Importance 排名 ===')
for rank, idx in enumerate(order, 1):
    print(f'  {rank}. {BAND_NAMES[idx]:6s} ({BANDS[idx]}): {importance[idx]:.4f}')
"""))

cells.append(code("""# [T2-6] K-means vs Random Forest 並列比較
# =============================================================================
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

axes[0].imshow(true_color)
axes[0].set_title('True Color', fontsize=13)
axes[0].set_xlabel('Column'); axes[0].set_ylabel('Row')

axes[1].imshow(class_map_km, cmap=plt.cm.get_cmap('Set1', K),
               vmin=-0.5, vmax=K-0.5)
axes[1].set_title('K-means (Unsupervised, K=5)', fontsize=13)
axes[1].set_xlabel('Column')

axes[2].imshow(class_map_rf, cmap=lc_cmap, norm=lc_norm)
axes[2].set_title(f'Random Forest (Supervised)\\nOA={test_acc:.3f}', fontsize=13)
axes[2].set_xlabel('Column')
axes[2].legend(handles=legend, loc='lower right', framealpha=0.9, fontsize=8)

plt.suptitle('K-means vs Random Forest — 並列比較', fontsize=15, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'kmeans_vs_rf_comparison.png'),
            dpi=130, bbox_inches='tight')
plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════
#  TASK 3: Accuracy + SWCB validation
# ═══════════════════════════════════════════════════════════════════
cells.append(md("""## Task 3 — Accuracy Assessment & SWCB 獨立驗證 (35%)

兩部分：
- **Part A**：用自己的 80/20 split 評估（混淆矩陣 + OOB + Macro/Weighted）
- **Part B**：把「Bare/Landslide」類與 SWCB（農業部水土保持署）官方崩塌判釋圖比對

### Part A — 內部精度"""))

cells.append(code("""# [T3-A1] Confusion Matrix + Classification Report
# =============================================================================
cm = confusion_matrix(y_te, y_pred_test, labels=list(range(N_CLASSES)))

fig, ax = plt.subplots(figsize=(9, 7))
disp = ConfusionMatrixDisplay(cm, display_labels=CLASS_NAMES)
disp.plot(cmap='Blues', values_format='d', ax=ax, colorbar=True)
ax.set_title(f'Confusion Matrix — RF Classification\\nOA={test_acc:.4f}, Kappa={kappa:.4f}',
             fontsize=13)
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'confusion_matrix.png'),
            dpi=130, bbox_inches='tight')
plt.show()

# 計算每類 Producer's Accuracy (Recall) 和 User's Accuracy (Precision)
print('\\n=== 每類精度（手動逐列計算）===')
print(f'  {\"Class\":<16}{\"N test\":>10}{\"User Acc (P)\":>20}{\"Producer Acc (R)\":>22}')
for i in range(N_CLASSES):
    row_sum = cm[i, :].sum()
    col_sum = cm[:, i].sum()
    prod_acc = cm[i, i] / row_sum if row_sum > 0 else 0
    user_acc = cm[i, i] / col_sum if col_sum > 0 else 0
    print(f'  {CLASS_NAMES[i]:<16}{row_sum:>10,}{user_acc:>20.4f}{prod_acc:>22.4f}')
"""))

cells.append(code("""# [T3-A2] OOB vs Test + Macro / Weighted Avg Analysis
# =============================================================================
from sklearn.metrics import f1_score

f1_macro = f1_score(y_te, y_pred_test, average='macro',
                    labels=list(range(N_CLASSES)), zero_division=0)
f1_weighted = f1_score(y_te, y_pred_test, average='weighted',
                       labels=list(range(N_CLASSES)), zero_division=0)
gap = f1_weighted - f1_macro

print('=== OOB vs Test ===')
print(f'  OOB  Accuracy : {oob_acc:.4f}')
print(f'  Test Accuracy : {test_acc:.4f}')
print(f'  Δ (Test-OOB)  : {test_acc - oob_acc:+.4f}')
print('  解釋：兩者接近代表模型在 OOB 與 held-out test 上一致 → 沒有過度配適')

print('\\n=== Macro vs Weighted F1 ===')
print(f'  Macro    F1   : {f1_macro:.4f}  (每類等權平均)')
print(f'  Weighted F1   : {f1_weighted:.4f}  (依測試集樣本數加權)')
print(f'  Gap          : {gap:+.4f}')
if abs(gap) > 0.03:
    print('  ⚠ Gap > 0.03 → 弱勢類別的 F1 被多數類別稀釋（典型於不平衡資料）')
else:
    print('  ✅ Gap ≤ 0.03 → 各類別 F1 大致均衡')

print('\\n=== 每類測試樣本數（Support）===')
for i in range(N_CLASSES):
    n = int(np.sum(y_te == i))
    flag = ' ⚠ <30 信心度低' if n < 30 else ''
    print(f'  {CLASS_NAMES[i]:<16}: {n:>5,}{flag}')
"""))

cells.append(md("""### Part B — SWCB 獨立驗證

把你的「Bare/Landslide」類別（class_id=3）與農業部水土保持署官方判釋的崩塌地圖
（`20240802新生崩塌地.kml`）做空間重疊比對。

> 把 `20240802新生崩塌地.kml` 放在 notebook 同一資料夾。"""))

cells.append(code("""# [T3-B1] 載入 SWCB KML + 裁切到研究區
# =============================================================================
SWCB_FILE = os.path.join(WORK_DIR, '20240802新生崩塌地.kml')

if not os.path.exists(SWCB_FILE):
    raise FileNotFoundError(
        f'找不到 SWCB KML：{SWCB_FILE}\\n'
        '請從 https://drive.google.com/file/d/17ka8y4N3IADSnJ1ymCJuzOfkutRzG-p8/view '
        '下載，並放在 notebook 同一資料夾。'
    )

# 解析 KML（命名空間正確處理）
NS = {'kml': 'http://www.opengis.net/kml/2.2'}
tree = ET.parse(SWCB_FILE)
polygons_swcb = []
for pm in tree.getroot().findall('.//kml:Placemark', NS):
    coords_el = pm.find('.//kml:coordinates', NS)
    if coords_el is None or coords_el.text is None:
        continue
    pts = []
    for s in coords_el.text.strip().split():
        parts = s.split(',')
        if len(parts) >= 2:
            try:
                pts.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    if len(pts) >= 3:
        poly = Polygon(pts)
        if poly.is_valid and poly.area > 0:
            polygons_swcb.append(poly)

gdf_swcb = gpd.GeoDataFrame(geometry=polygons_swcb, crs='EPSG:4326')
print(f'SWCB 全臺崩塌多邊形數: {len(gdf_swcb):,}')

study_box = box(*TAROKO_BBOX)
gdf_clip = gdf_swcb[gdf_swcb.intersects(study_box)].copy()
gdf_clip['geometry'] = gdf_clip.geometry.intersection(study_box)
gdf_clip = gdf_clip[~gdf_clip.is_empty].copy()
print(f'裁切到研究區後: {len(gdf_clip):,}')

# 投影到 UTM 51N 計算面積
gdf_clip_utm = gdf_clip.to_crs('EPSG:32651')
total_swcb_m2 = gdf_clip_utm.area.sum()
print(f'SWCB 總崩塌面積（研究區內）: {total_swcb_m2:,.0f} m² ({total_swcb_m2/1e4:.1f} ha)')
"""))

cells.append(code("""# [T3-B2] SWCB polygons → 像素 mask（同 RF 網格）
# =============================================================================
# 用 RF 影像的 UTM transform 來柵格化，這樣兩個 mask 完全對齊
swcb_utm_shapes = []
for geom in gdf_clip_utm.geometry:
    if geom.geom_type == 'Polygon':
        swcb_utm_shapes.append((geom, 1))
    elif geom.geom_type == 'MultiPolygon':
        for sub in geom.geoms:
            swcb_utm_shapes.append((sub, 1))

swcb_mask = rasterize(
    swcb_utm_shapes,
    out_shape=(n_rows, n_cols),
    transform=img_transform,
    fill=0, dtype='uint8', all_touched=True,
)
print(f'SWCB 崩塌像素（20m grid）: {swcb_mask.sum():,} '
      f'({swcb_mask.sum() * 400 / 1e4:.1f} ha)')

# RF 的 Bare/Landslide 類別（class_id=3）
rf_landslide = (class_map_rf == 3).astype('uint8')
# 排除 NaN（雲遮罩處）— 雲區不算入分母
valid_for_compare = ~np.isnan(class_map_rf)
print(f'RF 偵測 Bare/Landslide 像素: {rf_landslide.sum():,} '
      f'({rf_landslide.sum() * 400 / 1e4:.1f} ha)')
print(f'有效比較像素: {valid_for_compare.sum():,} '
      f'(雲區 {(~valid_for_compare).sum():,} 已排除)')
"""))

cells.append(code("""# [T3-B3] 空間重疊指標 — Recall / Precision / IoU / F1
# =============================================================================
# 只在 valid（非雲）區域內比較
swcb_v = swcb_mask & valid_for_compare
rf_v   = rf_landslide & valid_for_compare

tp = np.sum((rf_v == 1) & (swcb_v == 1))
fp = np.sum((rf_v == 1) & (swcb_v == 0))
fn = np.sum((rf_v == 0) & (swcb_v == 1))
tn = np.sum((rf_v == 0) & (swcb_v == 0))

recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
iou       = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0
f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print('=== 空間重疊指標（vs SWCB 獨立判釋）===')
print(f'  TP (你偵測且 SWCB 確認)        : {tp:>9,} px ({tp*400/1e4:>7.2f} ha)')
print(f'  FP (你偵測但 SWCB 未列)        : {fp:>9,} px ({fp*400/1e4:>7.2f} ha)')
print(f'  FN (SWCB 列但你漏判)           : {fn:>9,} px ({fn*400/1e4:>7.2f} ha)')
print(f'  TN (兩者皆非)                  : {tn:>9,} px')
print()
print(f'  Recall    (= TP / (TP+FN))     : {recall:.4f}  ← 漏判率 = {1-recall:.1%}')
print(f'  Precision (= TP / (TP+FP))     : {precision:.4f}  ← 誤報率 = {1-precision:.1%}')
print(f'  IoU       (= TP / (TP+FP+FN))  : {iou:.4f}')
print(f'  F1                              : {f1:.4f}')

# 存到 dict 供 Task 4 使用
swcb_metrics = {
    'tp_pixels': int(tp), 'fp_pixels': int(fp), 'fn_pixels': int(fn),
    'recall': round(float(recall), 4),
    'precision': round(float(precision), 4),
    'iou': round(float(iou), 4),
    'f1': round(float(f1), 4),
    'swcb_total_pixels': int(swcb_mask.sum()),
    'rf_landslide_pixels': int(rf_landslide.sum()),
}
"""))

cells.append(code("""# [T3-B4] TP / FN / FP overlay 視覺化
# =============================================================================
overlay = np.zeros((n_rows, n_cols, 4), dtype=np.float32)
# 透明灰底 = TN
overlay[(rf_v == 1) & (swcb_v == 1)] = [0.0, 0.78, 0.0, 0.8]   # TP 綠
overlay[(rf_v == 0) & (swcb_v == 1)] = [0.85, 0.0, 0.0, 0.85]  # FN 紅（漏判）
overlay[(rf_v == 1) & (swcb_v == 0)] = [1.0, 0.85, 0.0, 0.75]  # FP 黃（誤報）

fig, axes = plt.subplots(1, 2, figsize=(18, 7))
axes[0].imshow(true_color)
axes[0].set_title('True Color 參考', fontsize=13)
axes[1].imshow(true_color)
axes[1].imshow(overlay)
axes[1].set_title(
    f'RF vs SWCB 比對 (Recall={recall:.3f}, Precision={precision:.3f}, IoU={iou:.3f})',
    fontsize=13,
)
legend_items = [
    Patch(facecolor='#00C800', label=f'TP 兩者皆判崩塌  ({tp:,} px)'),
    Patch(facecolor='#D90000', label=f'FN SWCB 列但你漏 ({fn:,} px)'),
    Patch(facecolor='#FFD800', label=f'FP 你判但 SWCB 無 ({fp:,} px)'),
]
axes[1].legend(handles=legend_items, loc='lower right', framealpha=0.95, fontsize=10)
for ax in axes:
    ax.set_xlabel('Column'); ax.set_ylabel('Row')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'swcb_overlay.png'),
            dpi=130, bbox_inches='tight')
plt.show()
print(f'→ Saved swcb_overlay.png')
"""))

cells.append(md("""### Part B — 必答討論

**Q1：為什麼完美重疊（IoU = 1.0）幾乎不可能？**

_<填寫此處>_

提示重點：
- **時序差異**：你的 Sentinel-2 影像日期 vs SWCB 判釋日期（2024-08-02）有間隔，期間可能有新崩塌或舊崩塌復植
- **空間解析度差異**：Sentinel-2 20m vs SWCB 高解析度衛星/航拍 — 小於 20m 的崩塌被你略過、大於 20m 邊界誤差累積
- **類別定義差異**：你的「Bare/Landslide」包含河床、裸土，但 SWCB 只記錄「新生崩塌」
- **訓練樣本偏差**：你的 ROI 若代表性不足，會系統性誤判

**Q2：FN（漏判崩塌）集中在哪？為什麼？**

_<填寫此處>_

提示：用 swcb_overlay.png 觀察紅色區域分布 — 是否多集中在山陰側（光譜陰影）、雲邊緣、或是窄長型崩塌（線狀通道）？

**Q3：這個外部驗證 vs 你的 internal test accuracy 哪個更值得相信？**

_<填寫此處>_

提示：
- Internal test 用的是**同一張影像同分布**的像素 → 上限是「我訓練好不好」
- External SWCB 是**獨立來源、不同感測器、不同時間** → 才是真正的「對世界正確嗎」
- 但 SWCB 本身也有判釋誤差，所以兩個都不是 ground truth"""))

# ═══════════════════════════════════════════════════════════════════
#  TASK 4: AI Report
# ═══════════════════════════════════════════════════════════════════
cells.append(md("""## Task 4 — AI Classification Report (25%)

統計各類別面積，再用 Gemini 產出指揮官簡報，最後**批判性評估** LLM 的回答。"""))

cells.append(code("""# [T4-1] 計算各類別面積統計
# =============================================================================
PIXEL_AREA_M2 = 20 * 20  # 400 m²

valid_total = int(np.sum(~np.isnan(class_map_rf)))
stats_rows = []
for cls_id in range(N_CLASSES):
    n_px = int(np.sum(class_map_rf == cls_id))
    area_ha = n_px * PIXEL_AREA_M2 / 10000
    area_km2 = n_px * PIXEL_AREA_M2 / 1e6
    pct = n_px / valid_total * 100 if valid_total > 0 else 0
    stats_rows.append({
        'class_id': cls_id,
        'class_en': CLASS_NAMES[cls_id],
        'class_zh': CLASS_NAMES_ZH[cls_id],
        'pixels': n_px,
        'area_ha': round(area_ha, 2),
        'area_km2': round(area_km2, 4),
        'pct_of_valid': round(pct, 2),
    })

stats_df = pd.DataFrame(stats_rows)
print('=== 各類別面積統計 ===')
print(stats_df.to_string(index=False))

stats_csv = os.path.join(OUTPUT_DIR, 'class_area_stats.csv')
stats_df.to_csv(stats_csv, index=False, encoding='utf-8-sig')
print(f'\\n→ Saved {stats_csv}')
"""))

cells.append(code("""# [T4-2] 呼叫 Gemini 產出指揮官簡報（含 fallback chain）
# =============================================================================
# 從環境變數或 .env 讀 API 金鑰；沒有就印備援文字
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(WORK_DIR, '.env'))
except ImportError:
    pass

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
GEMINI_DELAY = float(os.getenv('GEMINI_REQUEST_DELAY_S', '3'))
GEMINI_RETRIES = int(os.getenv('GEMINI_RETRY_ATTEMPTS', '3'))

MODEL_CHAIN = [GEMINI_MODEL, 'gemini-2.5-flash-lite',
               'gemini-flash-latest', 'gemini-flash-lite-latest']
seen = set()
MODEL_CHAIN = [m for m in MODEL_CHAIN if not (m in seen or seen.add(m))]

# 統計摘要（給 LLM 的 evidence）
stats_text = stats_df.to_string(index=False)
metrics_text = (
    f\"OA: {test_acc:.4f}, Kappa: {kappa:.4f}\\n\"
    f\"SWCB IoU: {swcb_metrics['iou']:.4f}\\n\"
    f\"SWCB Recall: {swcb_metrics['recall']:.4f}\\n\"
    f\"SWCB Precision: {swcb_metrics['precision']:.4f}\\n\"
    f\"SWCB FN pixels: {swcb_metrics['fn_pixels']:,}\\n\"
    f\"SWCB FP pixels: {swcb_metrics['fp_pixels']:,}\"
)

prompt = f\"\"\"你是花蓮縣災害應變中心的 GIS 分析師。根據以下災後土地覆蓋分類結果與獨立驗證指標，撰寫一份「災後土地覆蓋分析報告」（繁體中文，300-500 字）。

研究區：秀林鄉 / 太魯閣周邊（含蘇花公路沿線及近海區域）BBOX [121.40, 24.10, 121.80, 24.25]
災害事件：2024 年 4 月 3 日花蓮地震（M7.4）
分類方法：Random Forest（6 波段 Sentinel-2 L2A，5 類別）

【分類精度】
{metrics_text}

【各類別面積】
{stats_text}

【SWCB 獨立驗證】 SWCB 是農業部水土保持署根據高解析度影像判釋的官方崩塌地，作為獨立 ground truth。

報告需包含：
1. 災後土地覆蓋概況（哪些地物主導？哪些稀少？）
2. 崩塌/裸地面積估計 + 空間分布（蘇花公路沿線？立霧溪流域？）
3. 與 SWCB 官方比對：IoU、Recall、Precision 各代表什麼風險？指揮官要先看哪個？
4. 建議：這張分類圖能支援哪些後續分析（避難所評估、路網可達性、土石流潛勢）？
5. 不確定性說明：哪些限制必須與指揮官溝通（雲遮、Sentinel-2 解析度、訓練樣本偏差）

請用條列 + 短段落混合的格式，重點數字加粗，避免空話。\"\"\"

print('=== Prompt to Gemini ===')
print(prompt[:600] + '...\\n[truncated]')
print()
print('=== 呼叫 Gemini ===')

ai_response = None
ai_model_used = None
ai_error = None

if not GEMINI_API_KEY or GEMINI_API_KEY.startswith('your-'):
    ai_error = 'No GEMINI_API_KEY found — using placeholder.'
else:
    try:
        from google import genai as google_genai
        client = google_genai.Client(api_key=GEMINI_API_KEY)
        for model_name in MODEL_CHAIN:
            for attempt in range(GEMINI_RETRIES):
                try:
                    resp = client.models.generate_content(model=model_name, contents=prompt)
                    text = resp.text.strip() if hasattr(resp, 'text') else str(resp)
                    if text:
                        ai_response = text
                        ai_model_used = model_name
                        break
                except Exception as e:
                    msg = str(e)
                    ai_error = f'{model_name} attempt {attempt+1}: {msg[:140]}'
                    print(f'  ... {ai_error}')
                    if '429' in msg or 'quota' in msg.lower():
                        break
                    time.sleep(GEMINI_DELAY * (2 ** attempt))
            if ai_response:
                break
    except ImportError:
        ai_error = 'google.genai SDK not installed (pip install google-genai)'

if ai_response:
    print(f'\\n✅ Gemini response 取得自 {ai_model_used}')
else:
    print(f'\\n⚠ Gemini 全部失敗: {ai_error}')
    ai_response = (
        '[Gemini API 暫時無法呼叫 — 以下為依資料人工撰寫的備援簡報]\\n\\n'
        '*(請設定 GEMINI_API_KEY 後重跑此 cell 取得 LLM 回應)*'
    )
    ai_model_used = '(failed)'

# 存完整 prompt + response
ai_md = os.path.join(OUTPUT_DIR, 'ai_briefing.md')
with open(ai_md, 'w', encoding='utf-8') as f:
    f.write('# AI Classification Briefing — Gemini Response\\n\\n')
    f.write(f'**Model**: {ai_model_used or GEMINI_MODEL}\\n\\n')
    f.write('## Prompt\\n\\n```\\n' + prompt + '\\n```\\n\\n')
    f.write('## Response\\n\\n' + ai_response + '\\n')
print(f'→ Saved {ai_md}')
"""))

cells.append(code("""# [T4-3] 顯示 AI 回應全文
# =============================================================================
from IPython.display import Markdown, display
print('=' * 72)
print(f'Gemini Strategic Briefing — Model: {ai_model_used}')
print('=' * 72)
print()
print(ai_response)
print()
print('=' * 72)
"""))

cells.append(md("""### Task 4 — LLM 批判評估（必填）

_<填寫此處 — 1 段落>_

**評估面向（建議涵蓋）**：

1. **面積數字是否正確？** LLM 是否憑空編造數字、或重組統計表？對照 `class_area_stats.csv` 一個一個檢查。

2. **不確定性說明是否到位？** Gemini 有沒有提到 (a) Sentinel-2 20m 解析度限制 (b) 影像日期 vs SWCB 判釋日期落差 (c) 雲遮造成的盲區？

3. **建議是否實際可用？** 「支援避難所評估」這種口號 vs「在 X 路段優先增設臨時收容點，因為對應到 N 公頃裸地+陡坡」這種具體建議的差距。

4. **LLM 哪些回答是「真知識」哪些是「樣板話」？** 提供的本地專業（蘇花公路、立霧溪、太魯閣）細節是否真實？還是隨機拼貼出來看起來像？

5. **你會增加 / 刪除 / 重寫哪一段？** 用一句話總結你對 AI 簡報的「驗收結論」。"""))

# ───────────────────────────────────────────────────────────────────
# ARIA v8.0 Reflection (最後)
# ───────────────────────────────────────────────────────────────────
cells.append(md("""## ARIA v8.0 — Upgrade Reflection (Markdown report 用)

從 v7.0 的「閾值法」到 v8.0 的「分類器」，**核心觀念變更**：

| 維度 | v7.0 閾值法 | v8.0 分類器 |
|------|------------|------------|
| 輸入 | 單一指標（NDVI / VV-dB / NDWI） | 同時 6 波段反射率 |
| 輸出 | 二元（是/否） | 多類（5 類土地覆蓋） |
| 決策面 | 1D（一個閾值切平面） | 6D（在特徵空間中切分多區） |
| 訓練資料 | 不需要 | 需要 ROI 標籤 |
| 可解讀性 | 高（一行 if） | 中（feature importance 給線索） |
| 對混合像素的處理 | 不能 | 可（機率輸出，雖然這作業用 hard label） |
| 後續可延伸 | 難（多閾值會打架） | 易（換分類器即可） |

**這次作業的關鍵教訓（在跑完所有 cell 後填）**：

_<填寫 — 3-5 個要點，例如：>_
- _<填寫>_
- _<填寫>_
- _<填寫>_"""))

# ───────────────────────────────────────────────────────────────────
# Write notebook
# ───────────────────────────────────────────────────────────────────
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"✓ Wrote {NB_PATH}")
print(f"  Total cells: {len(cells)}")
