import requests
import os
import re
import m3u8
import threading
import traceback
import sys
from urllib.parse import urlparse
from config import headers
from crawler import prepareCrawl
from merge import mergeMp4
from encode import ffmpegEncode, get_ffmpeg_path
from delete import deleteM3u8, deleteMp4
from cover import getCover

def sanitize_filename(name):
    """移除 Windows 不允許的檔案名稱字元"""
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

def check_ffmpeg():
    """檢查環境中是否有 ffmpeg"""
    ffmpeg_bin = get_ffmpeg_path()
    if ffmpeg_bin != 'ffmpeg':  # 找到明確路徑（非 PATH fallback）
        return True
    # 驗證系統 PATH 中是否真的存在 ffmpeg
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run([ffmpeg_bin, '-version'], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, creationflags=creationflags)
        return True
    except Exception:
        return False

def download_task(url, base_path, stop_event=None, progress_callback=None, info_callback=None, max_threads="自動"):
    """
     GUI 專用的下載任務進入點。
    :param url: 影片網址
    :param base_path: 使用者設定的總下載儲存路徑
    :param stop_event: threading.Event 用於接收中斷訊號
    :param progress_callback: (processed, total, percent, text, status)
    :param info_callback: (info_dict) 用於提早回傳封面與標題
    """
    try:
        if progress_callback: progress_callback(0, 100, 0, "正在初始化下載環境...", status="analyzing")
        
        # 預檢 FFmpeg
        if not check_ffmpeg():
            if progress_callback: progress_callback(0, 100, 0, "❌ 找不到 FFmpeg！請將 ffmpeg.exe 放在專案目錄下", status="error")
            return False
        
        # 只取網址的路徑部分，忽略 ? 之後的參數
        clean_path = urlparse(url).path
        urlSplit = [u for u in clean_path.split('/') if u.strip()]
        
        if len(urlSplit) < 1: # 只要路徑有內容即可
            if progress_callback: progress_callback(0, 100, 0, "❌ 網址格式錯誤", status="error")
            return False
            
        dirName = sanitize_filename(urlSplit[-1])
        folderPath = os.path.join(base_path, dirName)
        
        if os.path.exists(os.path.join(folderPath, f'{dirName}.mp4')):
            cover_path = os.path.join(folderPath, f"{dirName}.jpg")
            if info_callback:
                 info_callback({
                     "title": dirName, 
                     "cover": cover_path if os.path.exists(cover_path) else None, 
                     "dirName": dirName
                 })
            if progress_callback: progress_callback(100, 100, 100, "✅ 影片已存在", status="done")
            return True
            
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

        if stop_event and stop_event.is_set(): return False
        
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                 if progress_callback: progress_callback(0, 100, 0, f"❌ 網頁拒絕連線 (HTTP {resp.status_code})", status="error")
                 return False
            page_text = resp.text
        except Exception as e:
             if progress_callback: progress_callback(0, 100, 0, f"❌ 載入網頁異常或超時", status="error")
             return False
        
        if stop_event and stop_event.is_set():
            return False

        # 透過 Regex 提取標題
        title_match = re.search(r'<title>(.*?)</title>', page_text)
        page_title = title_match.group(1).replace(" - Jable.tv", "").strip() if title_match else dirName
        page_title = sanitize_filename(page_title)
        
        try:
            getCover(html_file=page_text, folder_path=folderPath)
        except Exception:
            pass
            
        cover_path = os.path.join(folderPath, f"{dirName}.jpg")
        
        if info_callback:
            info_callback({
                "title": page_title,
                "cover": cover_path if os.path.exists(cover_path) else None,
                "dirName": dirName
            })

        result = re.search(r"https://.+?\.m3u8", page_text)
        if not result:
            if progress_callback: progress_callback(0, 100, 0, "❌ 找不到影片串流 (可能遭阻擋或網址錯誤)", status="error")
            return False
            
        m3u8url = result.group(0)

        if progress_callback: progress_callback(0, 100, 0, "分析完成，準備下載碎塊", status="downloading")

        # 取得 m3u8
        try:
            m3u8_resp = requests.get(m3u8url, headers=headers, timeout=15)
            if m3u8_resp.status_code != 200:
                raise Exception(f"HTTP {m3u8_resp.status_code}")
                
            m3u8file = os.path.join(folderPath, f'{dirName}.m3u8')
            with open(m3u8file, 'wb') as f:
                f.write(m3u8_resp.content)
            
            # 使用 loads 避免路徑解析錯誤
            m3u8obj = m3u8.loads(m3u8_resp.text, uri=m3u8url)
            
            # 計算碎塊下載的基礎 URL
            m3u8urlList = m3u8url.split('/')
            m3u8urlList.pop(-1)
            downloadurl = '/'.join(m3u8urlList)
        except Exception as e:
            if progress_callback: progress_callback(0, 100, 0, f"❌ 取得 m3u8 失敗: {str(e)}", status="error")
            return False

            
        m3u8uri = ''
        m3u8iv = ''
        for key in m3u8obj.keys:
            if key:
                m3u8uri = key.uri
                m3u8iv = key.iv

        tsList = []
        for seg in m3u8obj.segments:
            tsUrl = f"{downloadurl}/{seg.uri}"
            tsList.append(tsUrl)

        if m3u8uri:
            m3u8keyurl = f"{downloadurl}/{m3u8uri}"
            try:
                key_resp = requests.get(m3u8keyurl, headers=headers, timeout=10)
                if key_resp.status_code != 200:
                    raise Exception(f"HTTP {key_resp.status_code}")
                contentKey = key_resp.content
            except Exception as e:
                if progress_callback: progress_callback(0, 100, 0, f"❌ 取得解密金鑰失敗: {str(e)}", status="error")
                return False
            vt = bytes.fromhex(m3u8iv.replace("0x", "").zfill(32))
            ci_params = {'key': contentKey, 'iv': vt}
        else:
            ci_params = None

        if os.path.exists(m3u8file):
            deleteM3u8(folderPath)

        if stop_event and stop_event.is_set(): return False

        # 開始多執行緒下載
        prepareCrawl(ci_params, folderPath, tsList, stop_event=stop_event, progress_callback=progress_callback, max_threads=max_threads)
        
        if stop_event and stop_event.is_set():
             return False

        if progress_callback: progress_callback(0, 100, 0, "準備 FFmpeg 合成...", status="merging")
        mergeMp4(folderPath, tsList)
        
        if stop_event and stop_event.is_set(): return False
        
        ffmpegEncode(folderPath, dirName, 1, stop_event=stop_event, progress_callback=progress_callback)
        
        if stop_event and stop_event.is_set(): return False
        deleteMp4(folderPath)

        return True
    except Exception as e:
        if stop_event and stop_event.is_set(): return False
        
        # 擷取詳細的錯誤行號
        tb = traceback.extract_tb(e.__traceback__)
        last_call = tb[-1]
        line_info = f" (在 {os.path.basename(last_call.filename)} 第 {last_call.lineno} 行)"
        
        error_msg = f"❌ 異常錯誤: {str(e)}{line_info}"
        print(f"Download Task Failed: {error_msg}")
        traceback.print_exc()
        
        if progress_callback: progress_callback(0, 100, 0, error_msg, status="error")
        return False
