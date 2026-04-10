import os
import subprocess
import threading
import sys

def get_ffmpeg_path():
    """取得 ffmpeg 可執行檔路徑，優先順序：打包環境 > 同目錄 > 系統 PATH"""
    if hasattr(sys, '_MEIPASS'):
        meipass_ffmpeg = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        if os.path.exists(meipass_ffmpeg):
            return meipass_ffmpeg
    if os.path.exists('ffmpeg.exe'):
        return 'ffmpeg.exe'
    return 'ffmpeg'  # 依賴系統 PATH

def get_segment_count(folder_path):
    try:
        with open(os.path.join(folder_path, 'concat_list.txt'), 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.startswith('file'))
    except Exception:
        return None

def ffmpegEncode(folder_path, file_name, action=1, stop_event=None, progress_callback=None):
    if action == 0:
        return

    concat_list_path = os.path.join(folder_path, 'concat_list.txt')
    dst = os.path.join(folder_path, f'{file_name}.mp4')

    if not os.path.exists(concat_list_path):
        if progress_callback: progress_callback(0, 100, 0, "❌ 找不到合成清單", status="error")
        return

    # 使用統一的路徑偵測邏輯
    ffmpeg_bin = get_ffmpeg_path()

    total_segments = get_segment_count(folder_path) or 1

    # 隱藏 CMD 視窗標記
    creationflags = 0
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NO_WINDOW

    cmd = [ffmpeg_bin, '-y',
           '-f', 'concat',
           '-safe', '0',
           '-i', concat_list_path,
           '-c', 'copy',
           '-bsf:a', 'aac_adtstoasc',
           '-movflags', '+faststart',
           '-progress', 'pipe:1',
           '-nostats',
           '-loglevel', 'info',
           dst]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                bufsize=1, encoding='utf-8', creationflags=creationflags)

    processed_segments = 0
    if progress_callback: progress_callback(0, total_segments, 0, "準備合成...", status="merging")
    
    for line in process.stdout:
        if stop_event and stop_event.is_set():
            try:
                process.terminate()
            except Exception:
                pass
            if progress_callback: progress_callback(processed_segments, total_segments, (processed_segments/total_segments)*100, "任務已暫停", status="paused")
            return
            
        if 'Opening' in line and 'for reading' in line:
            processed_segments += 1
            if processed_segments <= total_segments:
                if progress_callback:
                    pct = (processed_segments / total_segments) * 100
                    progress_callback(processed_segments, total_segments, pct, f"正在合成 {processed_segments}/{total_segments}", status="merging")
                    
        if line.startswith('progress=end'):
            processed_segments = total_segments
            if progress_callback:
                 progress_callback(total_segments, total_segments, 100, "合成準備完成", status="merging")

    process.wait()

    if process.returncode == 0:
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        if progress_callback:
            progress_callback(total_segments, total_segments, 100, "✅ 下載完成!", status="done")
    elif not (stop_event and stop_event.is_set()):
        if progress_callback: progress_callback(processed_segments, total_segments, 0, f"❌ 轉檔發生錯誤 (Code: {process.returncode})", status="error")
