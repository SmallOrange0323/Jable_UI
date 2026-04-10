import os
import requests
from config import headers
from functools import partial
import concurrent.futures
import time
import copy
import threading
from tqdm import tqdm
from Crypto.Cipher import AES

def scrape(ci_params, folderPath, lock, session, urls, stop_event, progress_callback):
    """
    下載片段的核心函數。
    """
    if stop_event and stop_event.is_set():
        return False
        
    fileName = urls.split('/')[-1][0:-3]
    saveName = os.path.join(folderPath, fileName + ".mp4")

    # 若檔案存在就不抓了
    if os.path.exists(saveName):
        return True

    try:
        response = session.get(urls, headers=headers, timeout=30)
        if response.status_code == 200:
            content_ts = response.content
            if ci_params:
                ci = AES.new(ci_params['key'], AES.MODE_CBC, ci_params['iv'])
                content_ts = ci.decrypt(content_ts)
            with open(saveName, 'wb') as f:
                f.write(content_ts)
            
            with lock:
                if progress_callback:
                    pass  # 進度集中由 _progress_hook 處理
            return True
    except Exception:
        pass
    
    return False

def measureSpeed(tsList, sample_count=3):
    sample = tsList[:sample_count]
    times = []
    sizes = []

    def _fetch(url):
        t0 = time.time()
        try:
            with requests.Session() as s:
                response = s.get(url, headers=headers, timeout=15)
            size_kb = len(response.content) / 1024
            return time.time() - t0, size_kb
        except Exception:
            return 2.0, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=sample_count) as ex:
        results = list(ex.map(_fetch, sample))
    times = [r[0] for r in results]
    sizes = [r[1] for r in results]
    avg_sec = sum(times) / len(times) if times else 2.0
    avg_speed_kb = sum(sizes) / sum(times) if sum(times) > 0 else 0
    return avg_sec, avg_speed_kb

def prepareCrawl(ci_params, folderPath, tsList, stop_event=None, progress_callback=None, max_threads="自動"):
    downloadList = copy.deepcopy(tsList)
    total = len(downloadList)

    avg_sec_per_ts, avg_speed_kb = measureSpeed(tsList)
    
    # 決定 workers 數量
    if str(max_threads).isdigit():
        workers = int(max_threads)
    else:
        workers = min(32, max(8, int(avg_speed_kb / 200)))
        
    startCrawl(ci_params, folderPath, downloadList, total, workers, stop_event, progress_callback)

def startCrawl(ci_params, folderPath, downloadList, total, workers, stop_event, progress_callback):
    lock = threading.Lock()
    with requests.Session() as session:
        _run_crawl(ci_params, folderPath, downloadList, total, workers, lock, session, stop_event, progress_callback)

def _run_crawl(ci_params, folderPath, downloadList, total, workers, lock, session, stop_event, progress_callback):
    # 預檢：只找出還沒存在的檔案，將初始 I/O 降到最低
    pending_list = []
    processed = 0
    for url in downloadList:
        file_ts = url.split('/')[-1][0:-3] + '.mp4'
        if os.path.exists(os.path.join(folderPath, file_ts)):
            processed += 1
        else:
            pending_list.append(url)
            
    lock_processed = threading.Lock()
    retry_list = []
    lock_retry = threading.Lock()

    def _progress_hook(future, url):
        nonlocal processed
        if stop_event and stop_event.is_set():
            return
        
        try:
            result = future.result()
            if result:
                with lock_processed:
                    processed += 1
                    if progress_callback:
                        percent = (processed / total) * 100
                        progress_callback(processed, total, percent, f"{processed}/{total}", status="downloading")
            else:
                with lock_retry:
                    retry_list.append(url)
        except Exception:
            with lock_retry:
                retry_list.append(url)

    # 效能關鍵點：保持 Executor 在外層，工人們不用反覆解散重建
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        while pending_list:
            if stop_event and stop_event.is_set():
                if progress_callback: progress_callback(processed, total, (processed/total)*100, "任務已暫停", status="paused")
                break

            with lock_retry:
                retry_list.clear() # 清空失敗名單，準備新一輪

            futures = []
            for url in pending_list:
                f = executor.submit(scrape, ci_params, folderPath, lock, session, url, stop_event, None)
                # 使用閉包綁定 URL
                f.add_done_callback(lambda fut, u=url: _progress_hook(fut, u))
                futures.append(f)
            
            # 等待當下所有的任務都跑完
            concurrent.futures.wait(futures)

            if stop_event and stop_event.is_set():
                break

            # 從 retry_list 拿回失敗的 URL 進行下一次迴圈 (完全不需要再執行 os.path.exists 掃碟)
            with lock_retry:
                pending_list = list(retry_list)

            if pending_list:
                time.sleep(1) # 重試前給伺服器稍做喘息
