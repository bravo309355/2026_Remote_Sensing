import csv

input_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9_backup_before_audit_20260303_153212.csv'
output_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv'
log_file = r'D:\YongZhi\2026_RS\data\dropped_outliers_log.csv'

outdoor_keywords = ['公園', '廣場', '綠地', '操場', '停車場', '空地', '營區', '風景區', '庭院', '林場', '農場']

patches = {
    '空軍第737戰術戰鬥機聯隊': (121.182415, 22.796350),
}

# Bounding box per county: (min_lon, max_lon, min_lat, max_lat)
# Based on real Taiwan geography plus a small buffer
county_bbox = {
    # Northern Taiwan
    '基隆市': (121.40, 121.85, 25.00, 25.20),
    '臺北市': (121.43, 121.67, 24.95, 25.22),
    '新北市': (121.28, 122.01, 24.60, 25.30),   # Wulai/Pinglin go down to ~24.65
    '桃園市': (121.05, 121.45, 24.50, 25.15),   # Fuxing district extends south to ~24.5
    '新竹市': (120.88, 121.05, 24.72, 24.86),
    '新竹縣': (120.85, 121.42, 24.28, 24.95),   # Jianshi/Wufeng mountains extend south
    # Central Taiwan
    '苗栗縣': (120.60, 121.10, 24.28, 24.72),
    '臺中市': (120.45, 121.10, 24.00, 24.50),
    '彰化縣': (120.25, 120.70, 23.75, 24.20),
    '南投縣': (120.40, 121.35, 23.50, 24.10),
    '雲林縣': (120.10, 120.75, 23.48, 23.85),
    # Southern Taiwan
    '嘉義市': (120.38, 120.52, 23.43, 23.52),
    '嘉義縣': (120.10, 120.85, 23.20, 23.68),   # Mountain townships extend east
    '臺南市': (120.05, 120.65, 22.88, 23.42),
    '高雄市': (120.15, 121.05, 22.45, 23.20),
    '屏東縣': (120.25, 120.90, 21.88, 22.90),
    # Eastern Taiwan
    '宜蘭縣': (121.15, 121.95, 24.20, 25.00),   # Datong/Nanao extend west & south
    '花蓮縣': (121.10, 121.75, 23.05, 24.35),
    '臺東縣': (120.70, 121.60, 22.00, 23.45),
    # Outer islands
    '澎湖縣': (119.30, 119.75, 23.10, 23.70),
    '金門縣': (118.10, 118.55, 24.22, 24.55),   # Lieyu (小金門) at ~24.27
    '連江縣': (119.85, 120.55, 25.88, 26.45),
}

def match_county(district):
    """Match district string to county name."""
    for county in county_bbox:
        if district.startswith(county):
            return county
    return None

def is_round_placeholder(lon, lat):
    """Check if coordinates are suspiciously round (integer values = placeholder)."""
    return lon == int(lon) and lat == int(lat) and lon > 0

outliers = []
valid_rows = []

print("Running final comprehensive coordinate cleanup...")

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames)
    if 'is_indoor' in fieldnames:
        fieldnames.remove('is_indoor')
    fieldnames.append('is_indoor')
    
    for row in reader:
        name = row.get('避難收容處所名稱', '')
        district = row.get('縣市及鄉鎮市區', '')
        try:
            lon = float(row.get('經度', 0))
            lat = float(row.get('緯度', 0))
        except ValueError:
            lon, lat = 0, 0

        is_outlier = False
        reason = ""

        # 1. Apply manual patches
        if name in patches:
            lon, lat = patches[name]
            row['經度'] = str(lon)
            row['緯度'] = str(lat)

        # 2. Zero coordinates
        elif lon == 0 or lat == 0:
            is_outlier = True
            reason = "Zero coordinate"

        # 3. Round placeholder coordinates
        elif is_round_placeholder(lon, lat):
            is_outlier = True
            reason = f"Round placeholder ({lon}, {lat})"

        # 4. Transposed lat/lon
        elif 118 <= lat <= 126 and 21 <= lon <= 27:
            is_outlier = True
            reason = "Transposed coordinates"

        # 5. County bounding box validation
        else:
            county = match_county(district)
            if county:
                bbox = county_bbox[county]
                min_lon, max_lon, min_lat, max_lat = bbox
                if lon < min_lon or lon > max_lon or lat < min_lat or lat > max_lat:
                    is_outlier = True
                    reason = f"{county} bbox violation: ({lon},{lat}) outside [{min_lon}-{max_lon},{min_lat}-{max_lat}]"
            else:
                # Unknown county — just do basic Taiwan bounds check
                if not (118.0 <= lon <= 122.2 and 21.5 <= lat <= 26.5):
                    is_outlier = True
                    reason = f"Outside Taiwan bounds ({lon}, {lat})"

        # Calculate indoor status
        is_indoor = True
        for kw in outdoor_keywords:
            if kw in name:
                if kw == '營區':
                    if '活動中心' in name or '國小' in name or '國中' in name or '公所' in name:
                        continue
                is_indoor = False
                break

        row_copy = dict(row)
        if 'is_indoor' in row_copy:
            del row_copy['is_indoor']
        row_copy['is_indoor'] = str(is_indoor)

        if is_outlier:
            row_copy['DROP_REASON'] = reason
            outliers.append(row_copy)
        else:
            valid_rows.append(row_copy)

with open(output_file, 'w', encoding='utf-8-sig', newline='') as out_f:
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(valid_rows)

if outliers:
    log_fieldnames = fieldnames + ['DROP_REASON']
    with open(log_file, 'w', encoding='utf-8-sig', newline='') as log_f:
        writer = csv.DictWriter(log_f, fieldnames=log_fieldnames)
        writer.writeheader()
        writer.writerows(outliers)

print(f"Cleaned data: {len(valid_rows)} valid records saved.")
print(f"Dropped {len(outliers)} anomalous rows, logged to dropped_outliers_log.csv.")

# Print summary by type
print("\nDropped summary:")
reasons_summary = {}
for o in outliers:
    r = o.get('DROP_REASON', '')
    if 'bbox' in r:
        county = r.split(' bbox')[0]
        reasons_summary[f"bbox: {county}"] = reasons_summary.get(f"bbox: {county}", 0) + 1
    else:
        key = r.split('(')[0].strip() if '(' in r else r
        reasons_summary[key] = reasons_summary.get(key, 0) + 1

for k, v in sorted(reasons_summary.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
