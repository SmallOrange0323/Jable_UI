import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def get_default_download_path():
    """取得預設的 Windows 下載資料夾，並加上 JableTV 子目錄"""
    if os.name == 'nt':
        try:
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
            return os.path.join(location, 'JableTV')
        except Exception:
            return os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Downloads', 'JableTV')
    return os.path.join(os.path.expanduser('~'), 'Downloads', 'JableTV')

DEFAULT_SETTINGS = {
    "download_path": get_default_download_path(),
    "max_concurrent_tasks": 2,
    "max_threads_per_task": "自動",  # 自動, 限制 8, 限制 32
    "open_folder_on_complete": True,
    "theme": "dark" # dark or light
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # 確保新版本的 key 如果沒在舊檔裡會被補上
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            return settings
    except Exception as e:
        print(f"載入設定失敗: {e}")
        return DEFAULT_SETTINGS

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"儲存設定失敗: {e}")
