import requests
import zipfile
import shutil
import os
import sys
from tqdm import tqdm

def download_ffmpeg(url, target_path):
    print(f"正在從 {url} 下載 FFmpeg...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    block_size = 1024 # 1 Kibibyte
    t = tqdm(total=total_size, unit='iB', unit_scale=True, desc="下載進度")
    
    with open(target_path, 'wb') as f:
        for data in response.iter_content(block_size):
            t.update(len(data))
            f.write(data)
    t.close()
    
    if total_size != 0 and t.n != total_size:
        print("錯誤：下載過程中發生中斷")
        return False
    return True

def extract_ffmpeg(zip_path):
    print("正在解壓縮...")
    temp_dir = "ffmpeg_temp_extract"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # 在解壓縮後的目錄中尋找 ffmpeg.exe
    ffmpeg_exe_path = None
    for root, dirs, files in os.walk(temp_dir):
        if 'ffmpeg.exe' in files:
            ffmpeg_exe_path = os.path.join(root, 'ffmpeg.exe')
            break
            
    if ffmpeg_exe_path:
        print(f"找到 {ffmpeg_exe_path}，正在移至根目錄...")
        shutil.move(ffmpeg_exe_path, "ffmpeg.exe")
        return True
    else:
        print("錯誤：在壓縮包中找不到 ffmpeg.exe")
        return False

def main():
    if os.path.exists("ffmpeg.exe"):
        print("✅ 檢測到 ffmpeg.exe 已存在，跳過下載。")
        return

    # 使用 Gyan.dev 的 Essentials 版本，體積較小且功能足夠
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg_release.zip"
    
    try:
        if download_ffmpeg(url, zip_path):
            if extract_ffmpeg(zip_path):
                print("✅ FFmpeg 下載並安裝完成！")
            
            # 清理暫存
            if os.path.exists("ffmpeg_temp_extract"):
                shutil.rmtree("ffmpeg_temp_extract")
            if os.path.exists(zip_path):
                os.remove(zip_path)
        else:
            print("❌ 無法完成下載。")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 發生異常錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
