#!/usr/bin/env python3
"""
自動環境安裝腳本
"""

import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_command(command, description):
    """執行命令並處理錯誤"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} 失敗: {e}")
        print(f"錯誤輸出: {e.stderr}")
        return False

def check_python_version():
    """檢查 Python 版本"""
    print(f"Python 版本: {sys.version}")
    if sys.version_info < (3, 7):
        print("錯誤: 需要 Python 3.7 或更高版本")
        return False
    return True

def install_dependencies():
    """安裝依賴套件"""
    return run_command(
        f"{sys.executable} -m pip install -r \"{PROJECT_ROOT / 'requirements.txt'}\"",
        "安裝依賴套件"
    )

def check_env_file():
    """檢查 .env 檔案"""
    env_path = PROJECT_ROOT / ".env"
    if not os.path.exists(env_path):
        print("✗ .env 檔案不存在")
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'API_KEY_MOENV' not in content:
            print("✗ .env 檔案中缺少 API_KEY_MOENV")
            return False
    
    print("✓ .env 檔案檢查通過")
    return True

def create_directories():
    """建立必要的目錄"""
    directories = [PROJECT_ROOT / 'data', PROJECT_ROOT / 'outputs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 建立目錄: {directory}")
    return True

def main():
    """主安裝程序"""
    print("=== 空氣品質監測系統環境安裝 ===\n")
    
    # 檢查 Python 版本
    if not check_python_version():
        return False
    
    # 建立目錄
    if not create_directories():
        return False
    
    # 檢查 .env 檔案
    if not check_env_file():
        print("\n請確保 .env 檔案存在且包含有效的 API_KEY_MOENV")
        return False
    
    # 安裝依賴
    if not install_dependencies():
        return False
    
    print("\n=== 安裝完成 ===")
    print("現在可以執行: python aqi_monitor.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
