"""
fix_dg_wt_urls.py
For 6400-DG products with Product='13S1LS': remove URLs containing 'NC6400-WT-',
archive cached thumbnails for those URLs, re-download Image_List from remaining
valid DG URLs (Wayfair priority, max 5), and update image count fields.
"""

import json, os, hashlib, requests, time, shutil, threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR   = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH   = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR  = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE    = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_dg_wt_wrong"
THUMBNAIL_SIZE = (400, 400)
WORKERS = 10
DELAY   = 0.5

os.makedirs(ARCHIVE, exist_ok=True)
_lock = threading.Lock()
_stats = {"archived": 0, "downloaded": 0, "failed": 0, "urls_removed": 0}

WF_COLS = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS = [f"Northcape Image {i}" for i in range(1, 16)]
HD_COLS = [f"Home Depot Image {i}" for i in range(1, 16)]

def archive_thumb(fname):
    src = os.path.join(THUMB_DIR, fname)
    if os.path.exists(src):
        shutil.move(src, os.path.join(ARCHIVE, fname))
        with _lock: _stats["archived"] += 1

def download_thumb(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    dest  = os.path.join(THUMB_DIR, fname)
    if os.path.exists(dest):
        return f"thumbnails/{fname}"
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

def get_priority_urls(p, limit=5):
    urls = []
    for cols in [WF_COLS, BY_COLS, NC_COLS]:
        for col in cols:
            v = (p.get(col) or "").strip()
            if v.startswith("http"): urls.append(v)
        if len(urls) >= limit: break
    return urls[:limit]

print("Loading catalogue...", flush=True)
with open(CAT_PATH, encoding="utf-8") as f:
    data = json.load(f)

# Find 6400-DG products where Product == '13S1LS' exactly
targets = []
for idx, p in enumerate(data):
    coll = (p.get("Collection") or "").strip()
    if "6400" not in coll or "DG" not in coll: continue
    if (p.get("Product") or "").strip() != "13S1LS": continue
    targets.append(idx)

print(f"6400-DG with Product='13S1LS': {len(targets)} products", flush=True)

# Process each
def process(idx):
    p = data[idx]
    # Remove URLs containing NC6400-WT- from all image columns
    cols_modified = 0
    wf_count = 0; by_count = 0; nc_count = 0; hd_count = 0
    for col_group, counter_name in [(WF_COLS, "wf"), (BY_COLS, "by"), (NC_COLS, "nc"), (HD_COLS, "hd")]:
        for col in col_group:
            v = (p.get(col) or "").strip()
            if not v.startswith("http"): continue
            if "NC6400-WT-" in v or "nc6400-wt-" in v.lower():
                # Archive its thumbnail
                fname = hashlib.md5(v.encode()).hexdigest() + ".jpg"
                archive_thumb(fname)
                p[col] = ""
                cols_modified += 1
                with _lock: _stats["urls_removed"] += 1
            else:
                if counter_name == "wf": wf_count += 1
                elif counter_name == "by": by_count += 1
                elif counter_name == "nc": nc_count += 1
                elif counter_name == "hd": hd_count += 1
    # Update image count fields
    p["WF Image Count"] = wf_count
    p["BY Image Count"] = by_count
    p["NC Image Count"] = nc_count
    p["HD Image Count"] = hd_count

    # Archive current Image_List thumbnails (force fresh)
    for path in p.get("Image_List", []):
        archive_thumb(os.path.basename(path))

    # Re-download Image_List from remaining valid URLs
    urls = get_priority_urls(p)
    new_il = []
    for url in urls:
        result = download_thumb(url)
        if result: new_il.append(result)
    p["Image_List"]      = new_il
    p["Local_Thumbnail"] = new_il[0] if new_il else ""
    return idx, cols_modified

done = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(process, i): data[i]["Part Number"] for i in targets}
    for fut in as_completed(futures):
        idx, removed = fut.result()
        done += 1
        if done % 5 == 0:
            print(f"  [{done}/{len(targets)}] urls_removed={_stats['urls_removed']} archived={_stats['archived']} downloaded={_stats['downloaded']} failed={_stats['failed']}", flush=True)

print(f"\nSaving catalogue...", flush=True)
with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"Saved.", flush=True)
print(f"\nDONE: urls_removed={_stats['urls_removed']} archived={_stats['archived']} downloaded={_stats['downloaded']} failed={_stats['failed']}", flush=True)
