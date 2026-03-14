import os
import shutil

cleaned = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9_cleaned.csv'
original = r'D:\YongZhi\2026_RS\data\避難收容處所點位檔案v9.csv'

# Since mv command in PowerShell previously hit encoding/escape weirdness, 
# python shutil is safer.
shutil.move(cleaned, original)
print(f"Successfully replaced {original}")
