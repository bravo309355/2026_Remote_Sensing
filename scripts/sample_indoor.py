import csv

file_path = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv'

true_samples = []
false_samples = []
camp_samples = []

with open(file_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get('避難收容處所名稱', '')
        district = row.get('縣市及鄉鎮市區', '')
        is_indoor = row.get('is_indoor', '')
        
        # Grab some examples that have 營區 to show the fix worked
        if '營區' in district and is_indoor == 'True' and len(camp_samples) < 5:
            camp_samples.append(name)
            
        if is_indoor == 'True' and len(true_samples) < 10 and '營區' not in district:
            true_samples.append(name)
        elif is_indoor == 'False' and len(false_samples) < 10:
            false_samples.append(name)
            
        if len(true_samples) == 10 and len(false_samples) == 10 and len(camp_samples) == 5:
            break

with open(r'D:\YongZhi\2026_RS\data\sample_result2.txt', 'w', encoding='utf-8-sig') as res:
    res.write("=== 室內設施 (包含容易誤判的「營區」行政區) ===\n")
    for s in camp_samples:
        res.write(f"- {s}\n")
        
    res.write("\n=== 一般室內設施 (is_indoor = True) ===\n")
    for s in true_samples:
        res.write(f"- {s}\n")
        
    res.write("\n=== 戶外設施 (is_indoor = False) ===\n")
    for s in false_samples:
        res.write(f"- {s}\n")

print("Sample complete.")
