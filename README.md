# 🚀 JableTV Downloader Pro

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

**JableTV Downloader Pro** 是一款基於 Python 開發的現代化影片下載工具，專為 JableTV 量身設計。本專案從原本的命令列工具進化為具備 **現代化 GUI 介面**、**分層排隊系統** 與 **自動化轉檔流程** 的專業級應用。

---

## ✨ 核心特色

### 🖥️ 現代化圖形介面 (GUI)
- **CustomTkinter 框架**：打造具備現代質感的深色/淺色模式介面。
- **即時預覽**：內建影片標題擷取與封面圖預覽功能。
- **下載隊列管理**：全視窗化的隊列系統，支援個別任務的 **暫停、恢復與移除**。

### ⚡ 強大的下載引擎
- **多執行緒加速**：支援單一影片多連線並行下載 TS 碎塊，速度極快。
- **全域任務排隊**：可自定義同時下載的影片數量，避免頻寬被單一任務佔滿。
- **自動化流程**：從爬蟲分析網址、下載資料、FFmpeg 合併片段到產生 MP4，一氣呵成。

### 🔍 智慧探索功能
- **演員全集下載**：只需輸入演員專頁，自動抓取該演員所有影片並加入隊列。
- **隨機探索**：點擊按鈕，自動從熱門影片中隨機挑選一部並準備下載。

---

## 🛠️ 環境需求與依賴

### 1. 核心需求
- **OS**: Windows (目前 GUI 主要針對 Windows 優化)
- **Python**: 3.10 或更高版本
- **瀏覽器**: 需安裝 Google Chrome (供 Selenium 爬蟲抓取動態內容)

### 2. 關鍵依賴：FFmpeg (必備)
> [!IMPORTANT]
> **本專案「未內建」FFmpeg 執行檔。**
> FFmpeg 是將下載的 TS 片段合併並編碼為 MP4 的核心組件。
> 
> **安裝步驟：**
> 1. 下載預編譯版本：[Gyan.dev (推薦)](https://www.gyan.dev/ffmpeg/builds/) 或 [FFmpeg 官網](https://www.ffmpeg.org/download.html)。
> 2. 下載後解壓縮，將其中的 `ffmpeg.exe` 放置於本專案的 **根目錄** 下。
> 3. 或者將 FFmpeg 的路徑加入系統環境變數 (PATH) 亦可。

---

## 🚀 快速開始

### 對於一般使用者 (Windows)
1. **下載原始碼**。
2. **安裝 FFmpeg**：將 `ffmpeg.exe` 放入專案資料夾。
3. **初始化環境**：執行 `INIT.bat` 自動建立虛擬環境與安裝依賴。
4. **啟動程式**：執行 `RUN.bat` 即可進入 GUI 介面。

### 對於 Docker 愛用者
不需要手動安裝環境，直接使用容器化部署：
```bash
# 建立 Image
docker build -t jable-pro .

# 執行（掛載下載目錄）
docker run -it -v D:\downloads:/downloads jable-pro
```

---

## 📦 開發者與打包指南

如果你想要修改程式碼並自行產生 `.exe` 執行檔，請使用內建的自動化打包工具。

### 打包 EXE 流程
1. 執行 `build_gui.bat`。
2. 該腳本會執行以下自動化流程：
   - 偵測 Python 環境並安裝所有必要的庫。
   - **自動偵測 FFmpeg**：若目錄下缺失 `ffmpeg.exe`，將自動從官方源下載並解壓。
   - 自動生成應用程式圖示。
   - 執行 PyInstaller 打包。
3. 打包完成後，最終的執行檔位於 `dist/` 資料夾內。

---

## 📐 技術架構

本專案採用模組化設計，各司其職：
- **`gui.py`**: 主介面層，處理使用者互動與狀態顯示。
- **`queue_manager.py`**: 管理並行任務與執行緒調度。
- **`crawler.py`**: 核心爬蟲，負責解析 Jable 網站與獲取 m3u8。
- **`download.py`**: TS 段落下載器。
- **`merge.py` / `encode.py`**: 調用 FFmpeg 進行後期處理。

---

## 📜 聲明與致謝

### 原始專案
本專案的 UI 版本是基於 [hcjohn463/JableTVDownload](https://github.com/hcjohn463/JableTVDownload) 的核心下載邏輯進行重構與介面開發。

### 免責聲明
本工具僅供技術交流與學術研究使用，請勿用於非法下載或侵犯版權之行為。使用者需自行承擔使用本工具所產生之所有法律責任。

---

> 如果你覺得這個版本好用，歡迎給個 ⭐ Star 支持！
