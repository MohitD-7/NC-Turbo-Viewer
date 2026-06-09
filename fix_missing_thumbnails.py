"""
fix_missing_thumbnails.py
Download missing/incomplete thumbnails for all products.
Priority: Wayfair → Beyond (Overstock) → Northcape
Concurrent downloads with 10 workers + 0.5s delay per worker.
"""

import json, os, hashlib, requests, time, threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

cat_path   = "data/catalogue.json"
thumb_dir  = "static/thumbnails"
THUMBNAIL_SIZE = (400, 400)
WORKERS    = 10
DELAY      = 0.5

# Priority: Wayfair first, then Beyond (Overstock), then Northcape
WF_COLS = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS = [f"Northcape Image {i}" for i in range(1, 16)]

_lock     = threading.Lock()
_counter  = {"ok": 0, "fail": 0, "total": 0}

def get_priority_urls(p, limit=5):
    urls = []
    for cols in [WF_COLS, BY_COLS, NC_COLS]:
        for col in cols:
            v = (p.get(col) or "").strip()
            if v.startswith("http"):
                urls.append(v)
        if len(urls) >= limit:
            break
    return urls[:limit]

def download(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    fpath = os.path.join(thumb_dir, fname)
    if os.path.exists(fpath):
        return f"thumbnails/{fname}"
    time.sleep(DELAY)
    try:
        raw  = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        r    = requests.get(raw, timeout=30)
        if r.status_code == 200:
            img = Image.open(BytesIO(r.content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(fpath, "JPEG", quality=85)
            return f"thumbnails/{fname}"
    except Exception:
        pass
    return None

def worker_task(args):
    idx, valid_il, needed_urls = args
    new_il   = list(valid_il)
    dl_ok    = 0
    dl_fail  = 0
    for url in needed_urls:
        result = download(url)
        if result:
            new_il.append(result)
            dl_ok += 1
        else:
            dl_fail += 1
        with _lock:
            _counter["ok"]    += (1 if result else 0)
            _counter["fail"]  += (0 if result else 1)
    return idx, new_il[:5], dl_ok, dl_fail

print("Loading catalogue...", flush=True)
with open(cat_path, encoding="utf-8") as f:
    data = json.load(f)
print(f"Total products: {len(data)}", flush=True)

# Build work list
to_fix = []
for idx, p in enumerate(data):
    il       = p.get("Image_List", [])
    valid_il = [path for path in il
                if os.path.exists(os.path.join(thumb_dir, os.path.basename(path)))]
    urls     = get_priority_urls(p)
    have     = set(os.path.basename(x) for x in valid_il)
    needed   = [u for u in urls
                if hashlib.md5(u.encode()).hexdigest() + ".jpg" not in have]
    slots    = 5 - len(valid_il)
    if (len(valid_il) != len(il)) or (slots > 0 and needed):
        to_fix.append((idx, valid_il, needed[:max(slots, 0)]))

total_urls = sum(len(t[2]) for t in to_fix)
_counter["total"] = total_urls
print(f"Products to fix: {len(to_fix)} | URLs to download: {total_urls}", flush=True)
print(f"Starting with {WORKERS} workers, {DELAY}s delay...", flush=True)

completed = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(worker_task, t): t[0] for t in to_fix}
    for fut in as_completed(futures):
        idx, new_il, dl_ok, dl_fail = fut.result()
        data[idx]["Image_List"]      = new_il
        data[idx]["Local_Thumbnail"] = new_il[0] if new_il else ""
        completed += 1
        if completed % 10 == 0:
            with _lock:
                ok, fail = _counter["ok"], _counter["fail"]
            print(f"  Products: {completed}/{len(to_fix)} | DL ok={ok} fail={fail}", flush=True)

print(f"\nSaving catalogue...", flush=True)
with open(cat_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Done: {_counter['ok']} downloaded | {_counter['fail']} failed", flush=True)
dist = Counter(len(p.get("Image_List", [])) for p in data)
print("Final image distribution:")
for k in sorted(dist):
    print(f"  {k} images: {dist[k]} products")
