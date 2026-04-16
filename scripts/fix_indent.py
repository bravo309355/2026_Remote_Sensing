with open("D:/YongZhi/2026_RS/aqi_monitor.py", "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

# Lines 473-480 currently have the bad indent
replacement = [
    "        ensure_parent_dir(save_path)",
    "        aqi_map.save(save_path)",
    "        self.last_map_stats = {",
    "            \"map_markers_added\": markers_added,",
    "            \"map_markers_skipped\": markers_skipped,",
    "        }",
    "        print(f\"AQI map saved to {save_path}\")",
    "        return save_path"
]

new_lines = lines[:472] + replacement + lines[480:]

with open("D:/YongZhi/2026_RS/aqi_monitor.py", "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")
print("File written.")
