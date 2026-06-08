"""
prefetch_furniture_thumbs.py
Pre-download furniture thumbnails from Jun 08 Furniture Excel (all sheets except 6600/6701).
Does NOT touch catalogue.json — just downloads files to static/thumbnails/.
Run in parallel with the cushion script, then update catalogue after.
"""

import hashlib, os, requests, openpyxl
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

THUMB_DIR       = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer/static/thumbnails"
FURNITURE_EXCEL = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Jun 08, 2026.xlsx"
THUMBNAIL_SIZE  = (400, 400)
WORKERS         = 15
SKIP_SHEETS     = {"6600 - DG", "6701 - DG"}  # already handled

WF_COLS = [f"Wayfair Image {i}"   for i in range(1, 16)]
NC_COLS = [f"Northcape Image {i}" for i in range(1, 16)]
BY_COLS = [f"Overstock Image {i}" for i in range(1, 16)]

_lock = threading.Lock()

def get_priority_urls(row_dict, limit=5):
    urls = []
    for cols in [WF_COLS, NC_COLS, BY_COLS]:
        for col in cols:
            v = (row_dict.get(col) or "").strip()
            if v.startswith("http"):
                urls.append(v)
        if len(urls) >= limit:
            break
    return urls[:limit]

def download_if_missing(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    dest  = os.path.join(THUMB_DIR, fname)
    if os.path.exists(dest):
        return True  # already cached
    try:
        raw  = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        resp = requests.get(raw, timeout=30)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(dest, "JPEG", quality=85)
            return True
    except:
        pass
    return False

print("Reading Furniture Excel...", flush=True)
wb = openpyxl.load_workbook(FURNITURE_EXCEL, read_only=True, data_only=True)

all_urls = []
for sheet in wb.sheetnames:
    if sheet in SKIP_SHEETS:
        print(f"  Skipping: {sheet}", flush=True)
        continue
    ws = wb[sheet]
    headers = [c.value for c in next(ws.iter_rows())]
    if "Part Number" not in headers:
        continue
    sheet_urls = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        row_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        sheet_urls.extend(get_priority_urls(row_dict))
    # Deduplicate within sheet
    sheet_urls = list(dict.fromkeys(sheet_urls))
    all_urls.extend(sheet_urls)
    print(f"  {sheet}: {len(sheet_urls)} URLs", flush=True)

all_urls = list(dict.fromkeys(all_urls))  # global deduplicate
# Filter to only ones not yet on disk
missing_urls = [u for u in all_urls if not os.path.exists(os.path.join(THUMB_DIR, hashlib.md5(u.encode()).hexdigest() + ".jpg"))]
print(f"\nTotal URLs: {len(all_urls)} | Already cached: {len(all_urls)-len(missing_urls)} | To download: {len(missing_urls)}", flush=True)

done = 0; failed = 0

def worker(url):
    ok = download_if_missing(url)
    return ok

print(f"Downloading with {WORKERS} workers...", flush=True)
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker, u): u for u in missing_urls}
    for fut in as_completed(futures):
        if fut.result():
            done += 1
        else:
            failed += 1
        if (done + failed) % 100 == 0:
            print(f"  {done+failed}/{len(missing_urls)} | ok={done} fail={failed}", flush=True)

print(f"\nDone. Downloaded={done} | Failed={failed}", flush=True)
