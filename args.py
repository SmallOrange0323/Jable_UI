import argparse
from bs4 import BeautifulSoup
import random
from urllib.request import Request, urlopen
from config import headers
import re


def get_parser():
    parser = argparse.ArgumentParser(description="Jable TV Downloader")
    parser.add_argument("--random", type=bool, default=False,
                        help="Enter True for download random ")
    parser.add_argument("--url", type=str, default="",
                        help="Jable TV URL to download")
    parser.add_argument("--all-urls", type=str, default="",
                        help="Jable URL contains multiple avs")
    
    return parser


def av_recommand():
    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
    url = 'https://jable.tv/'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        h6_tags = soup.find_all('h6', class_='title')
        # 精準匹配影片連結格式
        av_list = re.findall(r'https://jable\.tv/videos/[^/"]+/', str(h6_tags))
        if not av_list:
            return None
        return random.choice(av_list)
    except Exception:
        return None


# print(av_recommand())
