import re

with open("D:/YongZhi/2026_RS/aqi_monitor.py", "r", encoding="utf-8") as f:
    text = f.read()

# Find the create_aqi_map function
method_start = text.find('    def create_aqi_map(')
next_method = text.find('    def save_data_to_csv(', method_start)

new_method = """    def create_aqi_map(
        self,
        save_path="outputs/aqi_map.html",
        df=None,
        map_center=None,
        zoom_start=DEFAULT_MAP_ZOOM,
    ):
        \"\"\"Create Folium map with AQI markers, clustering, and layer control.\"\"\"
        if not self.aqi_data:
            print("No AQI data available. Please fetch data first.")
            return None

        if df is None:
            df = self.build_processed_dataframe()
        if df.empty:
            print("No valid AQI data rows available for map generation.")
            return None

        center = list(map_center or self.default_map_center)
        aqi_map = folium.Map(location=center, zoom_start=zoom_start)

        # 1) Re-style the legend to match Folium's actual fa icons exactly
        legend_html = '''
    <div style="
        position: fixed;
        top: 10px;
        right: 10px;
        width: 220px;
        background: white;
        border: 2px solid #666;
        z-index: 9999;
        font-size: 13px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        border-radius: 5px;
    ">
      <b>AQI Legend (測站狀態)</b><br>
      <span style="color:green; font-size: 16px;">&#9679;</span> 0-50 (Good 良好)<br>
      <span style="color:#c9a000; font-size: 16px;">&#9679;</span> 51-100 (Moderate 普通)<br>
      <span style="color:red; font-size: 16px;">&#9679;</span> 101+ (Unhealthy 不良)<br>
      <span style="color:gray; font-size: 16px;">&#9679;</span> Unknown (未知)<br>
      <hr style="margin:6px 0; border: 0; border-top: 1px solid #ccc;">
      <b>Shelters (避難收容處所)</b><br>
      <div style="margin: 4px 0;">
        <i class="fa fa-home" style="color: white; background-color: #38AADD; padding: 4px; border-radius: 50%; width: 22px; height: 22px; text-align: center; line-height: 14px; box-shadow: 0 0 2px rgba(0,0,0,0.5);"></i>
        Indoor (室內)
      </div>
      <div style="margin: 4px 0;">
        <i class="fa fa-tree" style="color: white; background-color: #F69730; padding: 4px; border-radius: 50%; width: 22px; height: 22px; text-align: center; line-height: 14px; box-shadow: 0 0 2px rgba(0,0,0,0.5);"></i>
        Outdoor (室外)
      </div>
    </div>
    '''
        aqi_map.get_root().html.add_child(folium.Element(legend_html))
        
        # 2) Layer Groups setup
        layer_groups = {}
        clusters = {}
        for bucket in AQI_BUCKET_ORDER:
            group = folium.FeatureGroup(name=AQI_BUCKET_LABELS[bucket], show=True)
            layer_groups[bucket] = group
            clusters[bucket] = MarkerCluster().add_to(group)

        markers_added = 0
        markers_skipped = 0

        for record in df.to_dict("records"):
            lat = safe_float(record.get("latitude"))
            lon = safe_float(record.get("longitude"))
            if lat in (None, 0.0) or lon in (None, 0.0):
                markers_skipped += 1
                continue

            bucket = aqi_bucket_key(record.get("aqi"))
            color = self.get_aqi_color(record.get("aqi"))

            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(self._build_popup_html(record), max_width=320),
                color="white",
                weight=1.5,
                fill=True,
                fillColor=color,
                fillOpacity=0.85,
                tooltip=f"{format_value(record.get('sitename'))} - AQI: {format_value(record.get('aqi'))}",
            )
            marker.add_to(clusters[bucket])
            markers_added += 1

        # Load and add shelter data
        import csv
        import os
        from html import escape
        shelter_file = r'D:\\YongZhi\\2026_RS\\data\\避難收容處所點位檔案v9.csv'
        shelter_group_indoor = folium.FeatureGroup(name="Shelters (Indoor)", show=True)
        shelter_group_outdoor = folium.FeatureGroup(name="Shelters (Outdoor)", show=True)
        cluster_indoor = MarkerCluster().add_to(shelter_group_indoor)
        cluster_outdoor = MarkerCluster().add_to(shelter_group_outdoor)
        
        shelters_added = 0
        if os.path.exists(shelter_file):
            with open(shelter_file, 'r', encoding='utf-8-sig') as sf:
                s_reader = csv.DictReader(sf)
                for s_row in s_reader:
                    try:
                        s_lat = float(s_row.get("緯度", 0))
                        s_lon = float(s_row.get("經度", 0))
                    except ValueError:
                        continue
                    
                    if s_lat == 0 or s_lon == 0:
                        continue
                        
                    is_indoor = s_row.get("is_indoor", "") == "True"
                    name = s_row.get("避難收容處所名稱", "Unknown")
                    
                    s_color = "cadetblue" if is_indoor else "orange"
                    s_icon = "home" if is_indoor else "tree"
                    target_cluster = cluster_indoor if is_indoor else cluster_outdoor
                    
                    folium.Marker(
                        location=[s_lat, s_lon],
                        popup=folium.Popup(f"<b>{escape(name)}</b><br>{'Indoor' if is_indoor else 'Outdoor'}", max_width=300),
                        icon=folium.Icon(color=s_color, icon=s_icon, prefix='fa'),
                        tooltip=name
                    ).add_to(target_cluster)
                    shelters_added += 1

        # 3) Add groups to map
        shelter_group_indoor.add_to(aqi_map)
        shelter_group_outdoor.add_to(aqi_map)
        for bucket in AQI_BUCKET_ORDER:
            layer_groups[bucket].add_to(aqi_map)

        # 4) Use GroupedLayerControl instead of default LayerControl
        from folium.plugins import GroupedLayerControl
        GroupedLayerControl(
            groups={
                '空氣品質觀測站 (AQI)': [layer_groups[b] for b in AQI_BUCKET_ORDER],
                '避難收容處所 (Shelters)': [shelter_group_indoor, shelter_group_outdoor]
            },
            exclusive_groups=False,
            collapsed=False,
        ).add_to(aqi_map)

        ensure_parent_dir(save_path)
        aqi_map.save(save_path)
        self.last_map_stats = {
            "map_markers_added": markers_added,
            "map_markers_skipped": markers_skipped,
        }
        print(f"AQI map saved to {save_path}")
        return save_path

"""

new_text = text[:method_start] + new_method + text[next_method:]

with open("D:/YongZhi/2026_RS/aqi_monitor.py", "w", encoding="utf-8") as f:
    f.write(new_text)

print("Done resetting create_aqi_map")
