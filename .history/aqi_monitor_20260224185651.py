import os
import requests
import folium
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import math

# Load environment variables
load_dotenv()

class AQIMonitor:
    def __init__(self):
        self.api_key = os.getenv('API_KEY_MOENV')
        if not self.api_key:
            raise ValueError("API_KEY_MOENV not found in environment variables")
        
        self.base_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
        self.aqi_data = None
        self.taipei_station_coords = (25.0478, 121.5170)  # Taipei Station coordinates
        
    def fetch_aqi_data(self):
        """Fetch real-time AQI data from MOENV API"""
        try:
            params = {
                'api_key': self.api_key,
                'format': 'json'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'records' not in data:
                raise ValueError("Invalid API response format")
                
            self.aqi_data = data['records']
            print(f"Successfully fetched {len(self.aqi_data)} monitoring stations data")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates using Haversine formula (in kilometers)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_aqi_color(self, aqi_value):
        """Get color based on AQI value - simplified 3-color scheme"""
        try:
            aqi = int(aqi_value)
        except (ValueError, TypeError):
            return 'gray'
        
        if aqi <= 50:
            return 'green'
        elif aqi <= 100:
            return 'yellow'
        else:
            return 'red'
    
    def create_aqi_map(self, save_path='outputs/aqi_map.html'):
        """Create folium map with AQI monitoring stations"""
        if not self.aqi_data:
            print("No AQI data available. Please fetch data first.")
            return None
        
        # Create map centered on Taiwan
        taiwan_center = [23.8, 121.0]
        m = folium.Map(location=taiwan_center, zoom_start=7)
        
        # Add AQI legend
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 150px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>AQI 圖例</h4>
        <p><i class="fa fa-circle" style="color:green"></i> 0-50 良好</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> 51-100 普通</p>
        <p><i class="fa fa-circle" style="color:red"></i> 101+ 不健康</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add markers for each monitoring station
        for station in self.aqi_data:
            try:
                # Extract station information
                site_name = station.get('sitename', 'Unknown')
                county = station.get('county', 'Unknown')
                aqi = station.get('aqi', 'N/A')
                
                # Get coordinates
                lat = float(station.get('latitude', 0))
                lon = float(station.get('longitude', 0))
                
                if lat == 0 or lon == 0:
                    continue
                
                # Determine color based on AQI
                color = self.get_aqi_color(aqi)
                
                # Create popup content
                popup_content = f'''
                <div style="font-family: Arial, sans-serif; width: 200px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{site_name}</h4>
                <p style="margin: 5px 0;"><strong>所在地:</strong> {county}</p>
                <p style="margin: 5px 0;"><strong>即時 AQI:</strong> <span style="font-size: 18px; font-weight: bold; color: {color};">{aqi}</span></p>
                <p style="margin: 5px 0; font-size: 12px; color: #666;">更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                '''
                
                # Add marker
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10,
                    popup=folium.Popup(popup_content, max_width=250),
                    color='white',
                    fillColor=color,
                    fillOpacity=0.8,
                    weight=2,
                    tooltip=f"{site_name} - AQI: {aqi}"
                ).add_to(m)
                
            except (ValueError, KeyError) as e:
                print(f"Error processing station {station.get('sitename', 'Unknown')}: {e}")
                continue
        
        # Save map
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        m.save(save_path)
        print(f"AQI map saved to {save_path}")
        return save_path
    
    def save_data_to_csv(self, save_path='outputs/aqi_analysis.csv'):
        """Save AQI data with distance calculation to CSV file"""
        if not self.aqi_data:
            print("No AQI data available. Please fetch data first.")
            return False
        
        try:
            # Process data with distance calculation
            processed_data = []
            for station in self.aqi_data:
                try:
                    lat = float(station.get('latitude', 0))
                    lon = float(station.get('longitude', 0))
                    
                    if lat == 0 or lon == 0:
                        distance = 'N/A'
                    else:
                        distance = self.calculate_distance(
                            self.taipei_station_coords[0], 
                            self.taipei_station_coords[1],
                            lat, 
                            lon
                        )
                    
                    processed_station = station.copy()
                    processed_station['distance_from_taipei_km'] = round(distance, 2) if distance != 'N/A' else 'N/A'
                    processed_data.append(processed_station)
                    
                except (ValueError, KeyError) as e:
                    print(f"Error processing station {station.get('sitename', 'Unknown')}: {e}")
                    continue
            
            # Create DataFrame and save
            df = pd.DataFrame(processed_data)
            
            # Reorder columns to put important info first
            important_cols = ['sitename', 'county', 'aqi', 'distance_from_taipei_km', 'latitude', 'longitude']
            other_cols = [col for col in df.columns if col not in important_cols]
            df = df[important_cols + other_cols]
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"AQI analysis data saved to {save_path}")
            
            # Print summary statistics
            valid_distances = df[df['distance_from_taipei_km'] != 'N/A']['distance_from_taipei_km']
            if not valid_distances.empty:
                print(f"Distance statistics:")
                print(f"  Closest station: {valid_distances.min():.2f} km")
                print(f"  Farthest station: {valid_distances.max():.2f} km")
                print(f"  Average distance: {valid_distances.mean():.2f} km")
            
            return True
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False

def main():
    """Main function to run AQI monitoring"""
    print("=== 台灣空氣品質監測系統 ===")
    
    try:
        # Initialize AQI monitor
        monitor = AQIMonitor()
        
        # Fetch data
        print("正在獲取空氣品質數據...")
        if not monitor.fetch_aqi_data():
            print("獲取數據失敗，請檢查 API Key 或網路連線")
            return
        
        # Save data to CSV with distance analysis
        print("正在保存數據並計算距離...")
        monitor.save_data_to_csv()
        
        # Create map
        print("正在生成地圖...")
        map_path = monitor.create_aqi_map()
        
        if map_path:
            print(f"\n完成！地圖已保存至: {map_path}")
            print("請在瀏覽器中開啟 HTML 檔案查看結果")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")

if __name__ == "__main__":
    main()
