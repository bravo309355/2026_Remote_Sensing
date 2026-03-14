import csv

file_path = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9_backup_before_audit_20260303_153212.csv'
out_path = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv'

epsg3826_count = 0
epsg4326_count = 0
outliers_count = 0
zero_zeros = 0
indoor_true = 0
indoor_false = 0
total = 0
outliers = []

outdoor_keywords = ['公園', '廣場', '綠地', '操場', '停車場', '空地', '營區', '風景區', '庭院', '林場', '農場']

with open(file_path, 'r', encoding='utf-8-sig') as f, open(out_path, 'w', encoding='utf-8-sig', newline='') as out_f:
    reader = csv.DictReader(f)
    # Ensure is_indoor is in fieldnames if not already there, but we are reading from backup so it shouldn't be
    fieldnames = reader.fieldnames
    if 'is_indoor' in fieldnames:
        fieldnames.remove('is_indoor')
    fieldnames.append('is_indoor')
    
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        total += 1
        try:
            lon = float(row.get('經度', 0))
            lat = float(row.get('緯度', 0))
        except ValueError:
            lon, lat = 0, 0
            
        if lon > 180 or lat > 90:
            epsg3826_count += 1
            outliers.append((row.get('序號', '?'), row.get('避難收容處所名稱', ''), lon, lat, 'Suspected EPSG:3826'))
        else:
            epsg4326_count += 1
            if lon == 0 and lat == 0:
                zero_zeros += 1
                outliers.append((row.get('序號', '?'), row.get('避難收容處所名稱', ''), lon, lat, 'Zero coordinate'))
            elif not (118 <= lon <= 124 and 21 <= lat <= 27):
                outliers_count += 1
                outliers.append((row.get('序號', '?'), row.get('避難收容處所名稱', ''), lon, lat, 'Out of Taiwan bounds'))

        # Add is_indoor based on keywords
        name = row.get('避難收容處所名稱', '')
        district = row.get('縣市及鄉鎮市區', '')
        
        is_indoor = True
        
        # Rule out outdoor keywords
        for kw in outdoor_keywords:
            if kw in name:
                # Special cases:
                # 1. 營區: '下營區', '柳營區', '左營區', '新營區' are districts, not military camps (營區)
                if kw == '營區' and '營區' in district and name.endswith('活動中心'):
                    continue # It's just a community center in a district that ends with 營區
                # Even safer: if it's an activity center or school in those districts
                if kw == '營區':
                    # If '營區' is part of the name but it clearly says 活動中心 or 國小/中, it's indoor
                    if '活動中心' in name or '國小' in name or '國中' in name or '公所' in name:
                        continue
                is_indoor = False
                break
        
        if is_indoor:
            indoor_true += 1
        else:
            indoor_false += 1
            
        # Write to new row dictionary ensuring we don't have dupes
        new_row = {k: row[k] for k in row if k != 'is_indoor'}
        new_row['is_indoor'] = str(is_indoor)
        writer.writerow(new_row)

with open(r'D:\YongZhi\2026_RS\data\audit_result.txt', 'w', encoding='utf-8') as res:
    res.write("=== Audit Report ===\n")
    res.write(f"Total records audited: {total}\n")
    res.write(f"Coordinate systems detected: EPSG:4326: {epsg4326_count}, EPSG:3826: {epsg3826_count}\n")
    res.write(f"Zero coordinates (0,0): {zero_zeros}\n")
    res.write(f"Outliers (outside Taiwan): {outliers_count}\n")
    res.write(f"Added feature 'is_indoor': True = {indoor_true}, False = {indoor_false}\n")
    if len(outliers) > 0:
        res.write("\nSample Outliers/Issues:\n")
        for o in outliers:
            res.write(f"{o}\n")

print("Audit complete, results written to data/audit_result.txt")
