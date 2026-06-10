"""
refresh_color.py — Force re-download thumbnails for all products of a given color.
Usage: python refresh_color.py "Canvas Heather Beige" Cushions
"""

import json, os, hashlib, requests, time, shutil, threading, sys
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR   = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH   = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR  = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE    = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_thumbnails_color_refresh"
THUMBNAIL_SIZE = (400, 400)
WORKERS    = 10
DELAY      = 0.5

TARGET_COLOR    = sys.argv[1] if len(sys.argv) > 1 else "Canvas Heather Beige"
TARGET_CATEGORY = sys.argv[2] if len(sys.argv) > 2 else None  # None = all

os.makedirs(ARCHIVE, exist_ok=True)
_lock = threading.Lock()
_stats = {"archived": 0, "downloaded": 0, "failed": 0}

WF_COLS = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS = [f"Northcape Image {i}" for i in range(1, 16)]

def get_priority_urls(p, limit=5):
    urls = []
    for cols in [WF_COLS, BY_COLS, NC_COLS]:
        for col in cols:
            v = (p.get(col) or "").strip()
            if v.startswith("http"): urls.append(v)
        if len(urls) >= limit: break
    return urls[:limit]

def archive_thumb(fname):
    src = os.path.join(THUMB_DIR, fname)
    if os.path.exists(src):
        shutil.move(src, os.path.join(ARCHIVE, fname))
        with _lock: _stats["archived"] += 1

def download_thumb(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    dest  = os.path.join(THUMB_DIR, fname)
    # NOTE: do NOT skip if exists — force fresh download
    time.sleep(DELAY)
    try:
        raw  = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        resp = requests.get(raw, timeout=30)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(dest, "JPEG", quality=85)
            with _lock: _stats["downloaded"] += 1
            return f"thumbnails/{fname}"
    except Exception:
        pass
    with _lock: _stats["failed"] += 1
    return None

def refresh(idx):
    p = data[idx]
    # Archive existing thumbnails
    for path in p.get("Image_List", []):
        archive_thumb(os.path.basename(path))

    urls = get_priority_urls(p)
    new_il = []
    for url in urls:
        result = download_thumb(url)
        if result: new_il.append(result)
    p["Image_List"]      = new_il
    p["Local_Thumbnail"] = new_il[0] if new_il else ""
    return idx

print(f"Loading catalogue...", flush=True)
with open(CAT_PATH, encoding="utf-8") as f:
    data = json.load(f)

# Find matching products
targets = []
for idx, p in enumerate(data):
    if p.get("Color") != TARGET_COLOR: continue
    if TARGET_CATEGORY and p.get("Category") != TARGET_CATEGORY: continue
    targets.append(idx)

print(f"Color: {TARGET_COLOR!r} | Category: {TARGET_CATEGORY or 'ALL'}", flush=True)
print(f"Matching products: {len(targets)}", flush=True)
total = sum(len(get_priority_urls(data[i])) for i in targets)
print(f"Thumbnails to download: {total}", flush=True)
print(f"Workers: {WORKERS} | Delay: {DELAY}s\n", flush=True)

done = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(refresh, i): data[i]["Part Number"] for i in targets}
    for fut in as_completed(futures):
        fut.result()
        done += 1
        if done % 10 == 0:
            print(f"  [{done}/{len(targets)}] archived={_stats['archived']} downloaded={_stats['downloaded']} failed={_stats['failed']}", flush=True)

print(f"\nSaving catalogue...", flush=True)
with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"Saved.", flush=True)
print(f"\nDONE: archived={_stats['archived']} downloaded={_stats['downloaded']} failed={_stats['failed']}", flush=True)
