import csv

input_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv'
output_file = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9_cleaned.csv'
log_file = r'D:\YongZhi\2026_RS\data\dropped_outliers_log.csv'

outliers = []
valid_rows = []

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    
    for row in reader:
        try:
            lon = float(row.get('經度', 0))
            lat = float(row.get('緯度', 0))
        except ValueError:
            lon, lat = 0, 0
            
        # condition for outliers:
        # 1. 0,0 coordinate
        # 2. Outside Taiwan (rough bounding box 118-124E, 21-27N)
        # Note: None were > 180 or > 90 so EPSG:3826 is clear.
        is_outlier = False
        reason = ""
        
        if lon == 0 and lat == 0:
            is_outlier = True
            reason = "Zero coordinate"
        elif not (118 <= lon <= 124 and 21 <= lat <= 27):
            is_outlier = True
            reason = "Out of Taiwan bounds"
            
        if is_outlier:
            # We add the reason to the log but not the original row data
            row_copy = dict(row)
            row_copy['DROP_REASON'] = reason
            outliers.append(row_copy)
        else:
            valid_rows.append(row)

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
print(f"Dropped {len(outliers)} rows. Log saved to: {log_file}")
