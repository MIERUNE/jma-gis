import concurrent.futures
import io
import logging
import re
import urllib.parse
import zipfile
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


BASE_URL = "https://www.data.jma.go.jp/developer/"
OUTPUT = Path("output/shapes")


def list_zip_files() -> list[str]:
    res = requests.get("https://www.data.jma.go.jp/developer/gis.html")
    res.raise_for_status()
    return list(
        urllib.parse.urljoin(BASE_URL, match.group(1))
        for match in re.finditer(r'<a href="(.*gis.*[^"]+\.zip)"', res.text)
    )


def download_and_extract(url):
    logging.info(f"Start downloading: {url}")
    res = requests.get(url)
    res.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(res.content)) as zip:
        for info in zip.infolist():
            info.filename = info.filename.encode("cp437").decode("cp932")
            info.filename = info.filename.split("/")[-1]
            zip.extract(info, OUTPUT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    executor = concurrent.futures.ThreadPoolExecutor(16)
    executor.map(download_and_extract, list_zip_files())
