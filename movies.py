import requests
from config import headers
from bs4 import BeautifulSoup
import os

def movieLinks(url):
    # 網址標準化處理: 將 /model/ 替換為 /models/ (JableTV 網址規範變更)
    if "jable.tv/model/" in url:
        url = url.replace("jable.tv/model/", "jable.tv/models/")

    # 確保 URL 末尾有斜線（方便接上 ?page=N）
    if not url.endswith('/'):
        url += '/'

    links = []
    page = 1

    while True:
        try:
            page_url = f"{url}?page={page}" if page > 1 else url
            response = requests.get(page_url, headers=headers, timeout=15)
            if response.status_code != 200:
                break

            bs = BeautifulSoup(response.text, "html.parser")
            # 尋找所有影片連結
            a_tags = bs.select('div.img-box>a')
            if not a_tags:
                break  # 本頁已無影片，代表已翻到最後一頁

            for a_tag in a_tags:
                links.append(a_tag['href'])

            page += 1

        except Exception as e:
            print(f"解析演員頁面第 {page} 頁失敗: {e}")
            break

    return links
