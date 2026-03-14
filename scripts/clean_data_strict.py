import csv
import shutil

input_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9_backup_before_audit_20260303_153212.csv'
output_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv'
log_file = r'D:\YongZhi\2026_RS\data\dropped_outliers_log.csv'

outdoor_keywords = ['公園', '廣場', '綠地', '操場', '停車場', '空地', '營區', '風景區', '庭院', '林場', '農場']

outliers = []
valid_rows = []

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    
    if 'is_indoor' in fieldnames:
        fieldnames.remove('is_indoor')
    fieldnames.append('is_indoor')
    
    for row in reader:
        try:
            lon = float(row.get('經度', 0))
            lat = float(row.get('緯度', 0))
        except ValueError:
            lon, lat = 0, 0
            
        is_outlier = False
        reason = ""
        
        # Stricter Taiwan boundaries (excluding remote islands like Matsu/Kinmen for this AQI map as it breaks the zoom)
        # Even if we include them, we must exclude outliers.
        # Let's say: Lon 118-122.5, Lat 21.5-26.5
        if lon == 0 and lat == 0:
            is_outlier = True
            reason = "Zero coordinate"
        elif 118 <= lat <= 126 and 21 <= lon <= 27:
            # Lat/Lon transposed case
            is_outlier = True
            reason = "Transposed coordinates / Invalid"
        elif lon < 118 or lon > 122.5 or lat < 21.5 or lat > 26.5:
            is_outlier = True
            reason = f"Out of bounds: ({lon}, {lat})"
            
        name = row.get('避難收容處所名稱', '')
        district = row.get('縣市及鄉鎮市區', '')
        
        # Indoor verification logic (including '營區' fix)
        is_indoor = True
        for kw in outdoor_keywords:
            if kw in name:
                if kw == '營區':
                    if '活動中心' in name or '國小' in name or '國中' in name or '公所' in name:
                        continue
                is_indoor = False
                break
                
        row_copy = dict(row)
        # Remove any stray is_indoor if reading from a previously augmented file
        if 'is_indoor' in row_copy:
            del row_copy['is_indoor']
        row_copy['is_indoor'] = str(is_indoor)
            
        if is_outlier:
            row_copy['DROP_REASON'] = reason
            outliers.append(row_copy)
        else:
            valid_rows.append(row_copy)

# Write cleaned data
with open(output_file, 'w', encoding='utf-8-sig', newline='') as out_f:
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(valid_rows)

# Write separated dropped rows log
if outliers:
    log_fieldnames = fieldnames + ['DROP_REASON']
    with open(log_file, 'w', encoding='utf-8-sig', newline='') as log_f:
        writer = csv.DictWriter(log_f, fieldnames=log_fieldnames)
        writer.writeheader()
        writer.writerows(outliers)

print(f"Cleaned data saved to: {output_file}")
print(f"Dropped {len(outliers)} anomalous rows. Log saved to: {log_file}")
