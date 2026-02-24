import os
import requests
import folium
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json

# Load environment variables
load_dotenv()

class AQIMonitor:
    def __init__(self):
        self.api_key = os.getenv('API_KEY_MOENV')
        if not self.api_key:
            raise ValueError("API_KEY_MOENV not found in environment variables")
        
        self.base_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
        self.aqi_data = None
        
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
    
    def get_aqi_color(self, aqi_value):
        """Get color based on AQI value"""
        try:
            aqi = int(aqi_value)
        except (ValueError, TypeError):
            return 'gray'
        
        if aqi <= 50:
            return 'green'
        elif aqi <= 100:
            return 'yellow'
        elif aqi <= 150:
            return 'orange'
        elif aqi <= 200:
            return 'red'
        elif aqi <= 300:
            return 'purple'
        else:
            return 'maroon'
    
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
                    top: 10px; right: 10px; width: 150px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>AQI Legend</h4>
        <p><i class="fa fa-circle" style="color:green"></i> 0-50 良好</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> 51-100 普通</p>
        <p><i class="fa fa-circle" style="color:orange"></i> 101-150 對敏感族群不健康</p>
        <p><i class="fa fa-circle" style="color:red"></i> 151-200 對所有族群不健康</p>
        <p><i class="fa fa-circle" style="color:purple"></i> 201-300 非常不健康</p>
        <p><i class="fa fa-circle" style="color:maroon"></i> 300+ 危害</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add markers for each monitoring station
        for station in self.aqi_data:
            try:
                # Extract station information
                site_name = station.get('sitename', 'Unknown')
                aqi = station.get('aqi', 'N/A')
                pm25 = station.get('pm2.5', 'N/A')
                pm10 = station.get('pm10', 'N/A')
                status = station.get('status', 'N/A')
                
                # Get coordinates
                lat = float(station.get('latitude', 0))
                lon = float(station.get('longitude', 0))
                
                if lat == 0 or lon == 0:
                    continue
                
                # Determine color based on AQI
                color = self.get_aqi_color(aqi)
                
                # Create popup content
                popup_content = f'''
                <b>{site_name}</b><br>
                AQI: {aqi}<br>
                狀態: {status}<br>
                PM2.5: {pm25}<br>
                PM10: {pm10}<br>
                更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                '''
                
                # Add marker
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_content, max_width=300),
                    color='black',
                    fillColor=color,
                    fillOpacity=0.7,
                    weight=1
                ).add_to(m)
                
            except (ValueError, KeyError) as e:
                print(f"Error processing station {station.get('sitename', 'Unknown')}: {e}")
                continue
        
        # Save map
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        m.save(save_path)
        print(f"AQI map saved to {save_path}")
        return save_path
    
    def save_data_to_csv(self, save_path='data/aqi_data.csv'):
        """Save AQI data to CSV file"""
        if not self.aqi_data:
            print("No AQI data available. Please fetch data first.")
            return False
        
        try:
            df = pd.DataFrame(self.aqi_data)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"AQI data saved to {save_path}")
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
        
        # Save data to CSV
        print("正在保存數據...")
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
