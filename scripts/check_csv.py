import csv

file_path = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv'
encodings = ['utf-8-sig', 'utf-8', 'big5', 'cp950']

for enc in encodings:
    try:
        with open(file_path, 'r', encoding=enc) as f:
            reader = csv.reader(f)
            header = next(reader)
            row1 = next(reader)
            row2 = next(reader)
            print(f"Successfully loaded with {enc}")
            print("Columns:", header)
            print("Row 1:", row1)
            print("Row 2:", row2)
            break
    except Exception as e:
        continue
