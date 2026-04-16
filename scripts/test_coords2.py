import csv
from pyproj import Proj, transform

# Check the exact data of anomalous points 
input_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9_backup_before_audit_20260303_153212.csv'

# It seems Matsu (Lienchiang County - 連江縣) and Kinmen (金門縣) are valid!
# Lon 119.7, Lat 27 => Matsu area.
# Lon 118.3, Lat 24.4 => Kinmen area.

# The prompt requirement: 
# 圖層 A: AQI 測站（依嚴重程度分色）
# 圖層 B: 避難收容處所（區分室內與室外圖標）
# "若避難所出現在海中，代表你的審計邏輯有誤"  -> This might mean I should NOT have filtered out valid offshore islands, or they are actually in the sea?
# Let's see: 
# 空軍第737戰術戰鬥機聯隊 is in Taitung (Taiwan Main Island). 
# If its coordinate is Lon: 119.752, Lat: 27.0 => This is MATSU's coordinate bounds! Wait, Taitung is 121E, 22N. 
# Why would a Taitung base be in Matsu coordinate?

print("Checking the exact row for 737:")
with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get('避難收容處所名稱', '')
        if '737' in name:
            print(f"Name: {name}")
            print(f"District: {row.get('縣市及鄉鎮市區')}")
            print(f"Address: {row.get('地址')}")
            print(f"Lon: {row.get('經度')}, Lat: {row.get('緯度')}")
            print("-" * 50)
            
        district = row.get('縣市及鄉鎮市區', '')
        if '連江' in district or '金門' in district or '澎湖' in district:
            lon = float(row.get('經度', 0))
            lat = float(row.get('緯度', 0))
            if lon == 0 or lat == 0:
                pass
            # Just wanted to know if they belong to outer islands.  
