import csv
import math

input_file = r'D:\YongZhi\2026_RS\data\dropped_outliers_log.csv'
output_file = r'D:\YongZhi\2026_RS\data\dropped_records_audit_report.csv'

# County centroids (approximate geographic center) for distance calculation
county_centroids = {
    '基隆市': (121.74, 25.13),
    '臺北市': (121.56, 25.04),
    '新北市': (121.47, 25.01),
    '桃園市': (121.30, 24.99),
    '新竹市': (120.97, 24.80),
    '新竹縣': (121.16, 24.69),
    '苗栗縣': (120.82, 24.56),
    '臺中市': (120.68, 24.15),
    '彰化縣': (120.54, 24.05),
    '南投縣': (120.68, 23.90),
    '雲林縣': (120.39, 23.70),
    '嘉義市': (120.45, 23.48),
    '嘉義縣': (120.43, 23.48),
    '臺南市': (120.33, 23.16),
    '高雄市': (120.67, 22.63),
    '屏東縣': (120.55, 22.55),
    '宜蘭縣': (121.74, 24.75),
    '花蓮縣': (121.60, 23.99),
    '臺東縣': (121.15, 22.75),
    '澎湖縣': (119.56, 23.57),
    '金門縣': (118.32, 24.44),
    '連江縣': (119.95, 26.16),
}

def haversine_km(lon1, lat1, lon2, lat2):
    """Calculate distance in km between two WGS84 points."""
    R = 6371.0
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def match_county(district):
    for county in county_centroids:
        if district.startswith(county):
            return county
    return None

# Read and verify
rows = []
with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    in_fieldnames = reader.fieldnames
    for row in reader:
        rows.append(row)

print(f"Total dropped records to verify: {len(rows)}")

# Build output
out_fieldnames = [
    '縣市及鄉鎮市區', '避難收容處所名稱', '原始經度', '原始緯度',
    '剔除原因', '縣市中心經度', '縣市中心緯度', '偏移距離_km',
    '地址', 'is_indoor'
]

out_rows = []
for row in rows:
    district = row.get('縣市及鄉鎮市區', '')
    name = row.get('避難收容處所名稱', '')
    try:
        lon = float(row.get('經度', 0))
        lat = float(row.get('緯度', 0))
    except ValueError:
        lon, lat = 0, 0
    
    reason = row.get('DROP_REASON', '')
    addr = row.get('地址', '')
    is_indoor = row.get('is_indoor', '')
    
    county = match_county(district)
    if county and lon != 0 and lat != 0:
        cx, cy = county_centroids[county]
        dist_km = round(haversine_km(lon, lat, cx, cy), 2)
    else:
        cx, cy = '', ''
        dist_km = ''
    
    out_rows.append({
        '縣市及鄉鎮市區': district,
        '避難收容處所名稱': name,
        '原始經度': lon,
        '原始緯度': lat,
        '剔除原因': reason,
        '縣市中心經度': cx,
        '縣市中心緯度': cy,
        '偏移距離_km': dist_km,
        '地址': addr,
        'is_indoor': is_indoor,
    })

with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=out_fieldnames)
    writer.writeheader()
    writer.writerows(out_rows)

print(f"Audit report saved to: {output_file}")
print(f"\nSample records:")
for r in out_rows[:10]:
    print(f"  [{r['縣市及鄉鎮市區']}] {r['避難收容處所名稱']}")
    print(f"    座標: ({r['原始經度']}, {r['原始緯度']})")
    print(f"    原因: {r['剔除原因']}")
    print(f"    偏移: {r['偏移距離_km']} km")
    print()
