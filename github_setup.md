# GitHub 設定說明

由於系統中未安裝 GitHub CLI，請手動完成以下步驟：

## 方法一：使用 GitHub 網頁介面

1. 前往 [GitHub](https://github.com) 並登入
2. 點擊右上角的 "+" 選擇 "New repository"
3. 設定倉庫：
   - Repository name: `aqi-analysis`
   - Description: `台灣空氣品質監測系統 - 即時 AQI 數據分析與視覺化`
   - 選擇 Public
4. 點擊 "Create repository"
5. 在新建立的倉庫頁面，選擇 "push an existing repository from the command line"
6. 複製並執行顯示的命令（類似以下）：

```bash
git remote add origin https://github.com/YOUR_USERNAME/aqi-analysis.git
git branch -M main
git push -u origin main
```

## 方法二：安裝 GitHub CLI

如果您想使用 GitHub CLI，請先安裝：

**Windows (Chocolatey):**
```bash
choco install gh
```

**Windows (Scoop):**
```bash
scoop install gh
```

安裝後執行：
```bash
gh auth login
gh repo create aqi-analysis --public --source=. --push
```

## 目前狀態

✅ Git 倉庫已初始化  
✅ 所有檔案已提交  
⏳ 等待推送到 GitHub

程式功能已完成：
- ✅ 空間計算：計算各測站到台北車站距離
- ✅ 資料輸出：CSV 檔案保存至 /outputs
- ✅ 地圖視覺化：優化的三色 AQI 顯示
