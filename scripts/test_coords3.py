import csv
from pyproj import Transformer

input_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9_backup_before_audit_20260303_153212.csv'
transformer = Transformer.from_crs("epsg:3826", "epsg:4326")

def is_twd97(x, y):
    # Rough bounded box for TWD97 (Taiwan)
    return 150000 <= x <= 350000 and 2400000 <= y <= 2800000

print("Verifying if the shifted points are just unprojected TWD97 (EPSG:3826)...")
twd97_count = 0
with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            x_val = float(row.get('經度', 0))
            y_val = float(row.get('緯度', 0))
        except ValueError:
            continue
            
        # The data might be in EPSG:3826 already, but just treated as Lat/Lon!
        # Let's see if there are numbers like 172000...
        if is_twd97(x_val, y_val):
            twd97_count += 1
            if twd97_count <= 5:
                lat, lon = transformer.transform(x_val, y_val)
                print(f"[{row.get('縣市及鄉鎮市區')}] {row.get('避難收容處所名稱')}: {x_val}, {y_val} -> WGS84: ({lon}, {lat})")

print(f"Total pure TWD97 found: {twd97_count}")

# What if they are encoded differently e.g. TWD97 but divided by 1000? 
# TWD97 / 10000 : 17.2, 250.0  -> No, Lat Lon is around 120, 23.
print("\nChecking for TWD97 divided by a factor...")
with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            x_val = float(row.get('經度', 0))
            y_val = float(row.get('緯度', 0))
        except ValueError:
            continue
            
        # If it's something like x=119.7, y=27 -- this is actually WGS84 for MATSU island!
        if '連江' in row.get('縣市及鄉鎮市區', '') or '金門' in row.get('縣市及鄉鎮市區', '') or '澎湖' in row.get('縣市及鄉鎮市區', '') or '臺東' in row.get('縣市及鄉鎮市區', ''):
            if '737' in row.get('避難收容處所名稱', ''):
                print(f"[TARGET 737] {row.get('縣市及鄉鎮市區')} {row.get('避難收容處所名稱')}: {x_val}, {y_val}")
                
        # What if X and Y are swapped?
        if 21 <= x_val <= 27 and 118 <= y_val <= 126:
            print(f"Swapped Lat/Lon: {row.get('避難收容處所名稱')} X:{x_val} Y:{y_val}")
