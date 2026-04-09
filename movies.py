import requests
from config import headers
from bs4 import BeautifulSoup
import os

def movieLinks(url):
    # 網址標準化處理: 將 /model/ 替換為 /models/ (JableTV 網址規範變更)
    if "jable.tv/model/" in url:
        url = url.replace("jable.tv/model/", "jable.tv/models/")
    
    links = []

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return links
            
        bs = BeautifulSoup(response.text, "html.parser")
        # 尋找所有影片連結
        a_tags = bs.select('div.img-box>a')
        for a_tag in a_tags:
            links.append(a_tag['href'])
            
    except Exception as e:
        print(f"解析演員頁面失敗: {e}")
        
    return links
