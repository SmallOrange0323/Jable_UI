import threading
import time
from download import download_task

class DownloadJob:
    def __init__(self, job_id, url, base_path, max_threads, on_info, on_progress, on_done):
        self.job_id = job_id
        self.url = url
        self.base_path = base_path
        self.max_threads = max_threads
        self.on_info = on_info
        self.on_progress = on_progress
        self.on_done = on_done
        self.stop_event = threading.Event()
        self.status = "queued"
        self.thread = None

    def start(self):
        self.status = "running"
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def pause(self):
        if self.status == "running":
            self.status = "paused"
            self.stop_event.set()

    def cancel(self):
        self.status = "cancelled"
        self.stop_event.set()

    def _run(self):
        try:
            success = download_task(
                url=self.url,
                base_path=self.base_path,
                stop_event=self.stop_event,
                progress_callback=self.on_progress,
                info_callback=self.on_info,
                max_threads=self.max_threads
            )
            if not self.stop_event.is_set():
                self.status = "done" if success else "error"
                if self.on_done:
                    self.on_done(self.job_id, success)
            else:
                 # 若因事件中斷，維持暫停狀態，除非被明確 cancel
                 if self.status != "cancelled":
                      self.status = "paused"
                 if self.on_done:
                      self.on_done(self.job_id, False) # 通知 GUI 任務中斷

        except Exception as e:
            print(f"Job Critical Error: {e}")
            self.status = "error"
            if self.on_done:
                 self.on_done(self.job_id, False)

class TaskQueueManager:
    """管理全域並列下載數量，避免網路或資源耗盡"""
    def __init__(self):
        self.jobs = {} # job_id -> DownloadJob
        self.max_concurrent = 2
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
    def set_max_concurrent(self, value):
        self.max_concurrent = int(value)
        
    def add_job(self, job_id, url, base_path, max_threads, on_info, on_progress, on_done):
        with self.lock:
            job = DownloadJob(job_id, url, base_path, max_threads, on_info, on_progress, on_done)
            self.jobs[job_id] = job
            return job
            
    def pause_job(self, job_id):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].pause()
                
    def resume_job(self, job_id):
        with self.lock:
            if job_id in self.jobs and self.jobs[job_id].status in ["paused", "queued", "error"]:
                 self.jobs[job_id].status = "queued"

    def remove_job(self, job_id):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].cancel()
                del self.jobs[job_id]

    def shutdown(self):
        """停止監控執行緒，關閉應用程式時呼叫"""
        self._stop_event.set()

    def _monitor_loop(self):
        """定時監控隊列，若有空位則啟動新任務"""
        while not self._stop_event.is_set():
            with self.lock:
                running_count = sum(1 for j in self.jobs.values() if j.status == "running")
                
                # 從 queue 狀態取出可以執行的任務
                for job in self.jobs.values():
                    if running_count >= self.max_concurrent:
                        break
                    if job.status == "queued":
                        job.start()
                        running_count += 1
            time.sleep(1)
