import sys
import os
import threading
import time

# 載入專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from args import av_recommand
    from movies import movieLinks
    from download import download_task
    print("[OK] 模組載入成功")
except Exception as e:
    print(f"[ERR] 模組載入失敗: {e}")
    sys.exit(1)

def test_random():
    print("\n--- 測試 [隨機一部] ---")
    try:
        url = av_recommand()
        if url:
            print(f"[OK] 成功抓取隨機網址: {url}")
            return url
        else:
            print("[ERR] 抓取隨機網址失敗 (無回傳內容)")
    except Exception as e:
        print(f"[ERR] 隨機功能報錯: {e}")
    return None

def test_actor(url):
    print(f"\n--- 測試 [演員全集]: {url} ---")
    try:
        links = movieLinks(url)
        if links:
            print(f"[OK] 成功抓取演員影片數: {len(links)}")
            print(f"範例連結: {links[0]}")
            return links[0]
        else:
            print("[ERR] 抓取演員影片失敗 (清單為空，請檢查 URL 格式)")
    except Exception as e:
        print(f"[ERR] 演員功能報錯: {e}")
    return None

def test_download(url):
    print(f"\n--- 測試 [核心解析與下載]: {url} ---")
    # 使用一個 Dummy stop_event
    stop_event = threading.Event()
    
    def mock_info(info):
        print(f"[INFO] 抓到影片資訊: {info.get('title')}")
        
    def mock_progress(processed, total, percent, text, status):
        # 只印出關鍵狀態變更
        print(f"[WAIT] 狀態變更: [{status}] {text} ({percent:.1f}%)")
        if status in ["error", "downloading", "merging"]:
            # 如果能到 downloading 代表 Selenium 解析成功了，我們就停止測試 (節省時間)
            if status == "downloading":
                print("[OK] 已成功進入下載階段 (Selenium 解析正常)")
                stop_event.set()


    base_path = os.path.join(os.getcwd(), "test_downloads")
    if not os.path.exists(base_path): os.makedirs(base_path)
    
    try:
        success = download_task(url, base_path, stop_event=stop_event, 
                                progress_callback=mock_progress, 
                                info_callback=mock_info)
        print(f"任務回傳結果: {success}")
    except Exception as e:
        print(f"❌ 下載功能發生異常中斷: {e}")

if __name__ == "__main__":
    # 1. 測試隨機
    rand_url = test_random()
    
    # 2. 測試演員 (使用三上悠亞作為測試範例)
    actor_url = "https://jable.tv/models/yua-mikami/"
    sample_url = test_actor(actor_url)
    
    # 3. 測試主要解析功能 (使用剛才抓到的隨機或樣本網址)
    target_url = rand_url if rand_url else sample_url
    if target_url:
        test_download(target_url)
    else:
        print("\n跳過下載測試，因為前面沒抓到網址")
