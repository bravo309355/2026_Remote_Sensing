import csv

report_file = r'D:\YongZhi\2026_RS\data\dropped_records_audit_report.csv'

with open(report_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    borderlines = []
    for row in reader:
        try:
            dist = float(row.get('偏移距離_km', 999))
        except ValueError:
            continue
        if dist < 50 and dist > 0:
            borderlines.append(row)
    
    print(f"Borderline records (< 50km offset): {len(borderlines)}\n")
    for r in borderlines:
        print(f"[{r['縣市及鄉鎮市區']}] {r['避難收容處所名稱']}")
        print(f"  ({r['原始經度']}, {r['原始緯度']}) dist={r['偏移距離_km']}km reason={r['剔除原因']}")
        print()
