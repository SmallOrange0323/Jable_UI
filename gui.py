import customtkinter as ctk
from PIL import Image
import threading
import time
import uuid
import sys
import os
import subprocess
import tkinter.messagebox as messagebox
from settings_manager import load_settings, save_settings
from queue_manager import TaskQueueManager

def set_window_icon(window):
    """通用的視窗圖示設置函式"""
    try:
        from PIL import Image, ImageTk
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        ico_path = os.path.join(base_path, "app_icon.ico")
        png_path = os.path.join(base_path, "kyarugasm.png")
        
        if os.name == 'nt' and os.path.exists(ico_path):
            window.iconbitmap(ico_path)
        
        if os.path.exists(png_path):
            img = Image.open(png_path)
            # 將 PhotoImage 存入 window 物件防止 GC
            window._icon_img = ImageTk.PhotoImage(img)
            window.wm_iconphoto(True, window._icon_img)
    except Exception as e:
        print(f"無法載入視窗圖示: {e}")

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, settings, on_save_callback):
        super().__init__(master)
        self.title("設定 (Settings)")
        self.geometry("450x500")
        # 使用延遲機制確保圖示成功加載
        self.after(200, lambda: set_window_icon(self))
        self.settings = settings
        self.on_save_callback = on_save_callback
        
        # 儲存路徑
        ctk.CTkLabel(self, text="下載儲存路徑:", font=("Microsoft JhengHei", 14, "bold")).pack(pady=(15, 5), padx=20, anchor="w")
        self.path_entry = ctk.CTkEntry(self, width=350, font=("Microsoft JhengHei", 12))
        self.path_entry.insert(0, self.settings.get("download_path", ""))
        self.path_entry.pack(pady=5, padx=20, side="top", anchor="w")
        
        # 同時下載任務數
        ctk.CTkLabel(self, text="全域同時下載影片數:", font=("Microsoft JhengHei", 14, "bold")).pack(pady=(15, 5), padx=20, anchor="w")
        self.concurrent_combobox = ctk.CTkComboBox(self, values=["1", "2", "3", "5"], font=("Microsoft JhengHei", 12))
        self.concurrent_combobox.set(str(self.settings.get("max_concurrent_tasks", 2)))
        self.concurrent_combobox.pack(pady=5, padx=20, anchor="w")
        
        # 單一影片最高並行連線數
        ctk.CTkLabel(self, text="單一影片最高連線數 (TS碎塊):", font=("Microsoft JhengHei", 14, "bold")).pack(pady=(15, 5), padx=20, anchor="w")
        self.threads_combobox = ctk.CTkComboBox(self, values=["自動", "8", "16", "32"], font=("Microsoft JhengHei", 12))
        self.threads_combobox.set(str(self.settings.get("max_threads_per_task", "自動")))
        self.threads_combobox.pack(pady=5, padx=20, anchor="w")
 
        # 佈景主題
        ctk.CTkLabel(self, text="佈景主題:", font=("Microsoft JhengHei", 14, "bold")).pack(pady=(15, 5), padx=20, anchor="w")
        self.theme_combobox = ctk.CTkComboBox(self, values=["dark", "light", "system"], font=("Microsoft JhengHei", 12))
        self.theme_combobox.set(self.settings.get("theme", "dark"))
        self.theme_combobox.pack(pady=5, padx=20, anchor="w")

        # 下載完成後開啟資料夾
        self.open_folder_var = ctk.BooleanVar(value=bool(self.settings.get("open_folder_on_complete", True)))
        self.open_folder_checkbox = ctk.CTkCheckBox(self, text="下載完成後自動開啟資料夾", variable=self.open_folder_var, 
                                                    fg_color="#FF4D8C", font=("Microsoft JhengHei", 12))
        self.open_folder_checkbox.pack(pady=(20, 10), padx=20, anchor="w")

        # 保存按鈕
        self.save_btn = ctk.CTkButton(self, text="儲存設定", fg_color="#FF4D8C", hover_color="#E03A76", 
                                      font=("Microsoft JhengHei", 16, "bold"), command=self.save_settings)
        self.save_btn.pack(pady=20)

    def save_settings(self):
        self.settings["download_path"] = self.path_entry.get()
        self.settings["max_concurrent_tasks"] = int(self.concurrent_combobox.get())
        self.settings["max_threads_per_task"] = self.threads_combobox.get()
        self.settings["theme"] = self.theme_combobox.get()
        self.settings["open_folder_on_complete"] = self.open_folder_var.get()
        
        save_settings(self.settings)
        ctk.set_appearance_mode(self.settings["theme"])
        if self.on_save_callback:
            self.on_save_callback(self.settings)
        self.destroy()

class JobItemFrame(ctk.CTkFrame):
    def __init__(self, master, job_id, url, manager, on_click_callback, get_path_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.job_id = job_id
        self.url = url
        self.manager = manager
        self.on_click_callback = on_click_callback
        self.get_path_callback = get_path_callback
        self.dir_name = "(擷取資訊中...)"
        
        self.info_dict = {"title": "正在分析網址...", "cover": None}
        
        # UI Elements
        self.grid_columnconfigure(1, weight=1)
        
        self.title_lbl = ctk.CTkLabel(self, text=self.info_dict["title"], font=("Microsoft JhengHei", 12, "bold"), anchor="w")
        self.title_lbl.grid(row=0, column=0, columnspan=3, padx=10, pady=(5,0), sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self, progress_color="#FF4D8C", height=10)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=(5,5), sticky="ew")
        
        self.status_lbl = ctk.CTkLabel(self, text="狀態: 排隊中 | 0%", font=("Microsoft JhengHei", 10), text_color="gray", anchor="w")
        self.status_lbl.grid(row=2, column=0, columnspan=2, padx=10, pady=(0,5), sticky="ew")
        
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=1, column=2, rowspan=2, padx=5, pady=5)
        
        self.pause_btn = ctk.CTkButton(self.btn_frame, text="暫停", width=40, height=30, 
                                       font=("Microsoft JhengHei", 12), command=self.toggle_pause)
        self.pause_btn.pack(side="left", padx=2)
        
        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="移除", width=40, height=30, 
                                        fg_color="#333", hover_color="#555", 
                                        font=("Microsoft JhengHei", 12), command=self.cancel_job)
        self.cancel_btn.pack(side="left", padx=2)

        # 使用者互動
        self.bind("<Button-1>", self._on_click)
        self.status_lbl.bind("<Button-1>", self._on_click)
        self.title_lbl.bind("<Button-1>", self._on_click)
        
        # 雙擊開啟資料夾
        self.bind("<Double-Button-1>", self._on_double_click)
        self.status_lbl.bind("<Double-Button-1>", self._on_double_click)
        self.title_lbl.bind("<Double-Button-1>", self._on_double_click)

    def _on_click(self, event):
        if self.on_click_callback:
            self.on_click_callback(self.job_id, self)

    def _on_double_click(self, event):
        if self.dir_name and self.dir_name != "(擷取資訊中...)":
            base_path = self.get_path_callback()
            path = os.path.join(base_path, self.dir_name)
            if os.path.exists(path) and os.name == 'nt':
                os.startfile(path)

    def highlight(self):
        self.configure(fg_color="#3d3d3d", border_color="#FF4D8C", border_width=2)
        
    def unhighlight(self):
        self.configure(fg_color="transparent", border_width=0)

    def set_info(self, info_dict):
        self.info_dict = info_dict
        self.dir_name = info_dict.get("dirName", self.dir_name)
        title = info_dict.get("title", "未知影片")
        self.title_lbl.configure(text=f"{title[:40]}..." if len(title)>40 else title)
        
        # 取得標題後自動觸發點擊，讓右邊預覽區跟著動
        self._on_click(None)
        
    def set_progress(self, processed, total, percent, text, status):
        self.progress_bar.set(percent / 100.0)
        stat_text = f"[{status.upper()}] {text} ({percent:.1f}%)"
        self.status_lbl.configure(text=stat_text)
        
        if status == "error":
            self.progress_bar.configure(progress_color="red")
        elif status == "paused":
            self.progress_bar.configure(progress_color="orange")
        elif status == "done":
            self.progress_bar.configure(progress_color="#00cc66")
        else:
            self.progress_bar.configure(progress_color="#FF4D8C")

    def toggle_pause(self):
        job = self.manager.jobs.get(self.job_id)
        if not job: return
        
        if job.status == "running":
            self.manager.pause_job(self.job_id)
            self.pause_btn.configure(text="繼續")
        elif job.status in ["paused", "queued", "error"]:
            self.manager.resume_job(self.job_id)
            self.pause_btn.configure(text="暫停")

    def cancel_job(self):
        self.manager.remove_job(self.job_id)
        self.destroy()

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.settings = load_settings()
        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        ctk.set_default_color_theme("blue")
        
        self.title("JableTV Downloader Pro")
        self.geometry("1050x700")
        self.minsize(900, 500)
        
        self.queue_manager = TaskQueueManager()
        self.queue_manager.set_max_concurrent(self.settings.get("max_concurrent_tasks", 2))
        
        self.job_frames = {}
        self.selected_item = None
        self._cover_cache = {}       # path -> CTkImage，避免重複讀檔
        self._preview_req_id = 0     # 防止快速點擊時舊請求覆蓋新結果
        
        self._build_ui()
        set_window_icon(self)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """視窗關閉時優雅地停止背景執行緒"""
        self.queue_manager.shutdown()
        self.destroy()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # === 頂部區域 Header ===
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        self.url_entry = ctk.CTkEntry(header_frame, placeholder_text="請貼上影片網址，或貼出演員專頁網址然後點擊 [演員全集]", 
                                      height=40, font=("Microsoft JhengHei", 12))
        self.url_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # 綁定右鍵直接貼上功能
        self.url_entry.bind("<Button-3>", self._quick_paste)
        
        analyze_btn = ctk.CTkButton(header_frame, text="添加下載", fg_color="#FF4D8C", hover_color="#E03A76", 
                                    height=40, font=("Microsoft JhengHei", 16, "bold"), command=self.add_url_to_queue)
        analyze_btn.grid(row=0, column=1)

        random_btn = ctk.CTkButton(header_frame, text="隨機一部", fg_color="#2b2b2b", hover_color="#444", 
                                    height=40, font=("Microsoft JhengHei", 16, "bold"), command=self.add_random_queue)
        random_btn.grid(row=0, column=2, padx=(10, 0))
        
        actor_btn = ctk.CTkButton(header_frame, text="演員全集", fg_color="#2b2b2b", hover_color="#444", 
                                    height=40, font=("Microsoft JhengHei", 16, "bold"), command=self.add_actor_queue)
        actor_btn.grid(row=0, column=3, padx=(5, 0))

        # === 中央區塊 ===
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=6) # Queue 佔 6
        main_frame.grid_columnconfigure(1, weight=4) # Preview 佔 4
        main_frame.grid_rowconfigure(0, weight=1)
        
        # 左側: 隊列 ScrollableFrame
        queue_container = ctk.CTkFrame(main_frame)
        queue_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        queue_container.grid_rowconfigure(1, weight=1)
        queue_container.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(queue_container, text="📥 下載隊列 (Download Queue)", font=("Microsoft JhengHei", 14, "bold"), anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.queue_frame = ctk.CTkScrollableFrame(queue_container, fg_color="transparent")
        self.queue_frame.grid(row=1, column=0, sticky="nsew")

        # 右側: 預覽與全域控制
        right_container = ctk.CTkFrame(main_frame)
        right_container.grid(row=0, column=1, sticky="nsew")
        right_container.grid_rowconfigure(0, weight=1)
        right_container.grid_columnconfigure(0, weight=1)
        
        # 右上: 預覽區 (固定佈局防止晃動)
        self.preview_frame = ctk.CTkFrame(right_container, fg_color="#1a1a1a" if self.settings.get("theme")=="dark" else"#e6e6e6")
        self.preview_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        # 標題容器: 固定高度 100 像素，防止上下擠壓
        self.title_container = ctk.CTkFrame(self.preview_frame, fg_color="transparent", height=100)
        self.title_container.grid(row=0, column=0, pady=(10,0), padx=10, sticky="ew")
        self.title_container.grid_propagate(False) # 強制固定高度
        self.title_container.grid_columnconfigure(0, weight=1)
        self.title_container.grid_rowconfigure(0, weight=1)
        
        self.preview_title = ctk.CTkLabel(self.title_container, text="等待選擇...", font=("Microsoft JhengHei", 16, "bold"), wraplength=350)
        self.preview_title.grid(row=0, column=0, sticky="nsew")
        
        self.preview_image_lbl = ctk.CTkLabel(self.preview_frame, text="(無封面圖)", font=("Microsoft JhengHei", 14))
        self.preview_image_lbl.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # 右下: 全域控制按鈕
        control_frame = ctk.CTkFrame(right_container, fg_color="transparent")
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        for i in range(2): control_frame.grid_columnconfigure(i, weight=1)
        for i in range(2): control_frame.grid_rowconfigure(i, weight=1)
        
        ctk.CTkButton(control_frame, text="全部開始", fg_color="#0066cc", height=40, 
                      font=("Microsoft JhengHei", 16, "bold"), command=self.start_all).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(control_frame, text="全部暫停", fg_color="#cc7a00", height=40, 
                      font=("Microsoft JhengHei", 16, "bold"), command=self.pause_all).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(control_frame, text="清理已完成", fg_color="#2b2b2b", height=40, 
                      font=("Microsoft JhengHei", 16, "bold"), command=self.clear_done).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(control_frame, text="全部移除", fg_color="#cc0000", height=40, 
                      font=("Microsoft JhengHei", 16, "bold"), command=self.remove_all).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # === 底部區域 Footer ===
        footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        footer_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        footer_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(footer_frame, text="設定", width=80, fg_color="#333", 
                      font=("Microsoft JhengHei", 14), command=self.open_settings).grid(row=0, column=0, sticky="w")
        self.global_status_lbl = ctk.CTkLabel(footer_frame, text=f"路徑: {self.settings['download_path']} | 系統就緒", 
                                              text_color="gray", font=("Microsoft JhengHei", 14))
        self.global_status_lbl.grid(row=0, column=1, sticky="e")

    def _quick_paste(self, event):
        """滑鼠右鍵點擊後自動清空並貼上剪貼簿內容"""
        try:
            clipboard_content = self.clipboard_get()
            if clipboard_content:
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, clipboard_content.strip())
        except Exception:
            pass

    def open_settings(self):
        SettingsWindow(self, self.settings, self._on_settings_saved)
        
    def _on_settings_saved(self, new_settings):
        self.settings = new_settings
        self.queue_manager.set_max_concurrent(self.settings.get("max_concurrent_tasks", 2))
        self.global_status_lbl.configure(text=f"路徑: {self.settings['download_path']} | 設定已更新")

    def add_random_queue(self):
        def _fetch():
            self.global_status_lbl.configure(text="正在隨機挑選熱門影片...", text_color="#0066cc")
            from args import av_recommand
            try:
                url = av_recommand()
                if url:
                    self.after(0, lambda: self.global_status_lbl.configure(text=f"路徑: {self.settings['download_path']} | 系統就緒", text_color="gray"))
                self.after(0, lambda: self._trigger_add(url))
            except Exception as e:
                self.after(0, lambda: self.global_status_lbl.configure(text="❌ 取得隨機影片失敗", text_color="red"))
        threading.Thread(target=_fetch, daemon=True).start()
        
    def add_actor_queue(self):
        url = self.url_entry.get().strip()
        if not url: return
        self.url_entry.delete(0, 'end')
        
        def _fetch(actor_url):
            self.global_status_lbl.configure(text="正在分析演員全集，請不要操作介面...", text_color="#0066cc")
            from movies import movieLinks
            try:
                urls = movieLinks(actor_url)
                if not urls:
                    self.after(0, lambda: self.global_status_lbl.configure(text="❌ 未找到任何影片", text_color="red"))
                    return
                for u in urls:
                    self.after(0, lambda link=u: self._trigger_add(link))
                self.after(0, lambda: self.global_status_lbl.configure(text=f"✅ 成功將 {len(urls)} 部影片加入隊列!", text_color="#00cc66"))
            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"演員全集報錯: {error_msg}")
                self.after(0, lambda: messagebox.showerror("演員全集錯誤", f"無法獲取清單，錯誤訊息：\n{str(e)}"))
                self.after(0, lambda: self.global_status_lbl.configure(text="❌ 獲取演員全集發生錯誤", text_color="red"))
                
        threading.Thread(target=_fetch, args=(url,), daemon=True).start()

    def _trigger_add(self, url):
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, url)
        self.add_url_to_queue()

    def add_url_to_queue(self):
        url = self.url_entry.get().strip()
        if not url: return
        self.url_entry.delete(0, 'end')
        
        job_id = str(uuid.uuid4())
        
        def on_click(j_id, item_frame):
            if self.selected_item:
                self.selected_item.unhighlight()
            self.selected_item = item_frame
            self.selected_item.highlight()
            self.update_preview(self.job_frames[j_id].info_dict)
            
        item = JobItemFrame(
            self.queue_frame, job_id, url, self.queue_manager, on_click,
            get_path_callback=lambda: self.settings["download_path"]
        )
        item.pack(fill="x", pady=5)
        self.job_frames[job_id] = item
        
        def on_info(info_dict):
            self.after(0, lambda: item.set_info(info_dict))
            
        def on_progress(processed, total, percent, text, status):
            self.after(0, lambda: item.set_progress(processed, total, percent, text, status))
            
        def on_done(j_id, success):
            def handle_done():
                job = self.queue_manager.jobs.get(j_id)
                if not job: return
                
                # 優先檢查是否為人為暫停
                is_paused = job.stop_event.is_set()
                status = "done" if success else ("paused" if is_paused else "error")
                
                current_text = item.status_lbl.cget("text")
                if success:
                    final_text = "完成"
                elif is_paused:
                    final_text = "已暫停"
                else:
                    final_text = "錯誤"
                
                if not success and not is_paused:
                    # 如果失敗且不是人為暫停，處理報錯訊息
                    if "❌" in current_text:
                        final_text = current_text.split("]")[-1].strip() if "]" in current_text else current_text
                    
                    # 只有在分析階段 (0%) 報錯時才彈出提示
                    if item.progress_bar.get() == 0:
                         messagebox.showerror("下載任務錯誤", f"網址：{url}\n錯誤原因：{final_text}")
                
                item.set_progress(100 if success else (item.progress_bar.get()*100), 100, 
                                  100 if success else (item.progress_bar.get()*100), 
                                  final_text, status)

                if success and self.settings.get("open_folder_on_complete") and item.dir_name and item.dir_name != "(擷取資訊中...)":
                    path = os.path.join(self.settings["download_path"], item.dir_name)
                    if os.path.exists(path) and os.name == 'nt':
                        os.startfile(path)
            self.after(0, handle_done)

        self.queue_manager.add_job(
            job_id, url, self.settings["download_path"], self.settings.get("max_threads_per_task", "自動"),
            on_info, on_progress, on_done
        )

    def update_preview(self, info_dict):
        self.preview_title.configure(text=info_dict.get("title", "無標題"))
        cover_path = info_dict.get("cover")

        if not cover_path or not os.path.exists(cover_path):
            self.preview_image_lbl.configure(image="", text="分析中或無封面圖")
            return

        # 快取命中：直接顯示，不開背景執行緒
        if cover_path in self._cover_cache:
            self.preview_image_lbl.configure(image=self._cover_cache[cover_path], text="")
            return

        # 遞增請求 ID，讓舊請求在回來時知道自己已過時
        self._preview_req_id += 1
        req_id = self._preview_req_id
        self.preview_image_lbl.configure(image="", text="載入中...")

        def _load_image():
            try:
                img = Image.open(cover_path)
                img.thumbnail((350, 450))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                def _update():
                    if req_id == self._preview_req_id:  # 只更新最新的請求
                        self._cover_cache[cover_path] = ctk_img
                        self.preview_image_lbl.configure(image=ctk_img, text="")
                self.after(0, _update)
            except Exception:
                def _error():
                    if req_id == self._preview_req_id:
                        self.preview_image_lbl.configure(image="", text="無法載入封面")
                self.after(0, _error)

        threading.Thread(target=_load_image, daemon=True).start()

    def start_all(self):
        for jid in self.queue_manager.jobs.keys():
            self.queue_manager.resume_job(jid)
            if jid in self.job_frames:
                 self.job_frames[jid].pause_btn.configure(text="暫停")
                 
    def pause_all(self):
        for jid in list(self.queue_manager.jobs.keys()):
            self.queue_manager.pause_job(jid)
            if jid in self.job_frames:
                 self.job_frames[jid].pause_btn.configure(text="繼續")

    def clear_done(self):
        to_del = []
        for jid, job in self.queue_manager.jobs.items():
            if job.status == "done": to_del.append(jid)
        for jid in to_del:
            self.queue_manager.remove_job(jid)
            if jid in self.job_frames:
                self.job_frames[jid].destroy()
                del self.job_frames[jid]
                
    def remove_all(self):
        for jid in list(self.queue_manager.jobs.keys()):
            self.queue_manager.remove_job(jid)
        for j_frame in self.job_frames.values():
            j_frame.destroy()
        self.job_frames.clear()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
