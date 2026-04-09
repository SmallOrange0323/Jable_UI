import requests
import os
from bs4 import BeautifulSoup


from config import headers

def getCover(html_file, folder_path):
  # get cover
  soup = BeautifulSoup(html_file, "html.parser")
  cover_name = f"{os.path.basename(folder_path)}.jpg"
  cover_path = os.path.join(folder_path, cover_name)
  for meta in soup.find_all("meta"):
      meta_content = meta.get("content")
      if not meta_content:
          continue
      if "preview.jpg" not in meta_content:
          continue
      try:
          r = requests.get(meta_content, headers=headers, timeout=15)
          with open(cover_path, "wb") as cover_fh:
              cover_fh.write(r.content)
      except Exception as e:
          print(f"unable to download cover: {e}")

  print(f"cover downloaded as {cover_name}")
