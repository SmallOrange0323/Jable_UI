> **我是完全不會寫程式的麻瓜，謝謝浣熊大大的心血，以下都是靠 Antigravity 跟 Gemini 3 flash 模型製作完成，如果有問題，我也只能繼續問 AI。**

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

## 🛠️ 快速開始

### 1. 準備環境
- **系統需求**：Windows 10/11。
- **硬體建議**：穩定的網路連線與足夠的磁碟空間（用於暫存 TS 片段）。

### 2. 下載與安裝 (麻瓜友善)
1. **下載本專案**：點擊右上方 `Code` -> `Download ZIP` 並解壓縮。
2. **準備環境**：確認電腦已安裝 **Python 3.10+**。
   - **重要**：安裝時請務必勾選底部 **[ ] Add Python to PATH**，否則後續腳本將無法執行。
3. **建置程式 (EXE)**：
   - 雙擊執行 `build_gui.bat`。
   - 系統會自動為您：**安裝必要套件**、**下載 FFmpeg**、**產生圖示**並**完成打包**。
4. **啟動 JableTV Downloader**：
   - 打包完成後，進入 `dist/` 資料夾，連點兩下 `JableTVPro.exe` 即可使用。

---

## ⚖️ 法律聲明與致謝

### 致謝
- 核心下載邏輯參考自 [hcjohn463/JableTVDownload](https://github.com/hcjohn463/JableTVDownload)。
- 介面與現代化重構由 **Antigravity (AI)** 協助指導完成。

### 免責聲明
本工具僅供技術交流與學術研究使用，請勿用於非法下載或任何侵犯版權之行為。作品標權均屬原作者或公司所有。使用者需自行承擔使用本工具所產生之所有法律責任，開發者與貢獻者不對任何誤用行為負責。

---

## 🤝 參與貢獻

這是一個開放的開源專案，如果您有任何想法、發現 Bug 或想要加入新功能，歡迎隨時進行 Fork 並提交 Pull Request。我們相信透過技術的分享與進步，大家可以一起讓這個工具變得更好、更穩定。

**「開心看片，World Peace！」**

---

> 如果您喜歡這個專案，歡迎點個 ⭐ **Star** 支持開發！
