# 台灣空氣品質監測系統

使用 Python 串接環境部 API 獲取全台即時 AQI 數據，並在地圖上視覺化顯示。

## 功能特色

- 🌍 串接環境部 API (aqx_p_432) 獲取全台即時 AQI 數據
- 🔑 從 `.env` 檔案安全讀取 API Key
- 📍 使用 Folium 在地圖上標示所有測站位置
- 🎨 根據 AQI 數值顯示不同顏色（綠色到深紅色）
- 📊 將數據保存為 CSV 檔案
- 🚀 自動環境安裝腳本

## 快速開始

### 1. 環境設定

執行自動安裝腳本：

```bash
python setup.py
```

或手動安裝：

```bash
pip install -r requirements.txt
```

### 2. 設定 API Key

確保 `.env` 檔案包含您的環境部 API Key：

```
API_KEY_MOENV=your_api_key_here
```

### 3. 執行程式

```bash
python aqi_monitor.py
```

## 輸出檔案

- `outputs/aqi_map.html` - 互動式 AQI 地圖
- `data/aqi_data.csv` - 原始 AQI 數據

## AQI 顏色對應

| AQI 範圍 | 顏色 | 狀態 |
|---------|------|------|
| 0-50 | 綠色 | 良好 |
| 51-100 | 黃色 | 普通 |
| 101-150 | 橙色 | 對敏感族群不健康 |
| 151-200 | 紅色 | 對所有族群不健康 |
| 201-300 | 紫色 | 非常不健康 |
| 300+ | 深紅色 | 危害 |

## 專案結構

```
.
├── aqi_monitor.py      # 主程式
├── setup.py           # 環境安裝腳本
├── requirements.txt   # 依賴套件列表
├── .env              # 環境變數設定
├── .gitignore        # Git 忽略檔案
├── data/             # 數據存放目錄
├── outputs/          # 輸出檔案目錄
└── README.md         # 說明文件
```

## 依賴套件

- `requests` - HTTP 請求
- `python-dotenv` - 環境變數管理
- `folium` - 互動式地圖
- `pandas` - 數據處理

## 注意事項

- 請確保網路連線正常
- API Key 需要有效且未過期
- 地圖檔案需要在瀏覽器中開啟查看
