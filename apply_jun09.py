"""
apply_jun09.py
Apply Jun 09 Excel changes to catalogue:
  1. Remove 4 old/renamed products (archive thumbnails)
  2. Update 86 changed products (archive old thumbs, update URLs, re-download)
  3. Add 311 new products (download thumbnails)
  4. Fix priority source for 53 CUSHSACL products (OS→WF swap)
5 workers, 1s delay per worker.
"""

import json, os, hashlib, requests, re, time, shutil, openpyxl, threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

BASE_DIR   = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH   = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR  = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE    = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_thumbnails_jun09"
THUMBNAIL_SIZE = (400, 400)
WORKERS    = 10
DELAY      = 0.5

EXCELS = [
    r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Accent Pillow - Jun 09, 2026.xlsx",
    r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Cushions - Jun 09, 2026.xlsx",
    r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Jun 09, 2026.xlsx",
]

WF_COLS  = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = WF_COLS + BY_COLS + NC_COLS + HD_COLS

# Products to remove from catalogue
REMOVE_PNS = {"1616DC-CFN", "CUSHBOL207-MLY", "CUSHTH20-MLY", "CUSHTHK2013-MLY"}

os.makedirs(ARCHIVE, exist_ok=True)
_lock = threading.Lock()
_stats = {"archived": 0, "downloaded": 0, "failed": 0}

def parse_color(val):
    if not isinstance(val, str): return None, None
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', val)
    if m: return m.group(2), m.group(1)
    return (val.strip() or None, None)

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
        return True
    return False

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

# ─── Load catalogue ───────────────────────────────────────────────────────────
print("Loading catalogue...", flush=True)
with open(CAT_PATH, encoding="utf-8") as f:
    data = json.load(f)
cat_map = {p["Part Number"]: i for i, p in enumerate(data)}
print(f"Catalogue: {len(data)} products", flush=True)

# ─── Read all Excel files ─────────────────────────────────────────────────────
print("\nReading Excel files...", flush=True)
excel_rows = {}
for path in EXCELS:
    wb = openpyxl.load_workbook(path)
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        headers = [c.value for c in ws[1]]
        if "Part Number" not in headers: continue
        pn_col = headers.index("Part Number") + 1
        count = 0
        for row in ws.iter_rows(min_row=2):
            pn = row[pn_col - 1].value
            if not pn: continue
            excel_rows[pn] = {
                "sheet": sheet,
                "file": os.path.basename(path),
                **{headers[i]: (row[i].value if i < len(row) else None)
                   for i in range(len(headers))}
            }
            count += 1
        print(f"  {os.path.basename(path)} / {sheet}: {count} rows", flush=True)
print(f"Total Excel rows: {len(excel_rows)}", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: Remove old/renamed products
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n=== Step 1: Remove {len(REMOVE_PNS)} old products ===", flush=True)
removed_indices = set()
for pn in REMOVE_PNS:
    idx = cat_map.get(pn)
    if idx is None:
        print(f"  NOT FOUND: {pn}", flush=True)
        continue
    p = data[idx]
    for path in p.get("Image_List", []):
        archive_thumb(os.path.basename(path))
    removed_indices.add(idx)
    print(f"  Removed: {pn}", flush=True)

data = [p for i, p in enumerate(data) if i not in removed_indices]
cat_map = {p["Part Number"]: i for i, p in enumerate(data)}
print(f"Step 1 done. Catalogue now: {len(data)} products | Archived: {_stats['archived']}", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: Update changed products
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Step 2: Update changed products ===", flush=True)

def update_product(args):
    idx, pn, exc = args
    p = data[idx]

    # Archive current thumbnails that will be replaced
    old_urls_set = set()
    for col in ALL_COLS:
        v = (p.get(col) or "").strip()
        if v.startswith("http"): old_urls_set.add(v)

    # Update all image URL fields from Excel
    for col in ALL_COLS:
        v = (exc.get(col) or "").strip()
        p[col] = v if v.startswith("http") else ""

    # Update Color/Color_Link/Last Modified
    color_name, color_link = parse_color(exc.get("Color"))
    if color_name: p["Color"] = color_name
    if color_link: p["Color_Link"] = color_link
    if exc.get("Last Modified"): p["Last Modified"] = str(exc["Last Modified"])

    # New URLs set
    new_urls_set = set()
    for col in ALL_COLS:
        v = (p.get(col) or "").strip()
        if v.startswith("http"): new_urls_set.add(v)

    # Archive thumbnails for URLs that are gone
    for url in old_urls_set - new_urls_set:
        fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
        archive_thumb(fname)

    # Also archive current Image_List thumbnails to force fresh download
    for path in p.get("Image_List", []):
        fname = os.path.basename(path)
        fpath = os.path.join(THUMB_DIR, fname)
        if os.path.exists(fpath):
            shutil.move(fpath, os.path.join(ARCHIVE, fname))
            with _lock: _stats["archived"] += 1

    # Download fresh thumbnails
    target_urls = get_priority_urls(p)
    new_il = []
    for url in target_urls:
        result = download_thumb(url)
        if result: new_il.append(result)

    p["Image_List"]      = new_il
    p["Local_Thumbnail"] = new_il[0] if new_il else ""
    return idx

# Find changed products (in both Excel and catalogue, URLs differ)
changed = []
for pn, exc in excel_rows.items():
    idx = cat_map.get(pn)
    if idx is None: continue
    p = data[idx]
    diff = False
    for col in ALL_COLS:
        cat_v = (p.get(col) or "").strip()
        exc_v = (exc.get(col) or "").strip()
        exc_v = exc_v if exc_v.startswith("http") else ""
        if cat_v != exc_v:
            diff = True
            break
    if diff:
        changed.append((idx, pn, exc))

print(f"Changed products: {len(changed)}", flush=True)
done2 = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(update_product, t): t[1] for t in changed}
    for fut in as_completed(futures):
        fut.result()
        done2 += 1
        if done2 % 10 == 0:
            print(f"  [{done2}/{len(changed)}] archived={_stats['archived']} downloaded={_stats['downloaded']} failed={_stats['failed']}", flush=True)

print(f"Step 2 done: {done2} products updated", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Add new products
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Step 3: Add new products ===", flush=True)

def add_product(exc):
    pn = exc.get("Part Number") or exc.get("sheet", "")
    color_name, color_link = parse_color(exc.get("Color"))

    new_prod = {
        "Part Number":        pn,
        "Collection":         exc.get("Collection") or "",
        "Collection Type":    exc.get("Collection") or "",
        "Category":           exc.get("Type") or "Furniture",
        "Type":               exc.get("Type") or "",
        "Color":              color_name or "",
        "Color_Link":         color_link or "",
        "Dropbox Folder Path": exc.get("Dropbox Folder Path") or "",
        "Last Modified":      str(exc.get("Last Modified") or ""),
        "NC Image Count":     int(exc.get("NC Image Count") or 0),
        "BY Image Count":     int(exc.get("BY Image Count") or 0),
        "WF Image Count":     int(exc.get("WF Image Count") or 0),
        "HD Image Count":     int(exc.get("HD Image Count") or 0),
        "Image_List":         [],
        "Local_Thumbnail":    "",
    }
    for col in ALL_COLS:
        v = (exc.get(col) or "").strip()
        new_prod[col] = v if v.startswith("http") else ""

    # Derive color from path if missing
    if not new_prod["Color"] and new_prod["Dropbox Folder Path"]:
        new_prod["Color"] = new_prod["Dropbox Folder Path"].rstrip("/").split("/")[-1]

    target_urls = get_priority_urls(new_prod)
    il = []
    for url in target_urls:
        result = download_thumb(url)
        if result: il.append(result)

    new_prod["Image_List"]      = il
    new_prod["Local_Thumbnail"] = il[0] if il else ""
    return new_prod

new_prods_data = [(pn, exc) for pn, exc in excel_rows.items() if pn not in cat_map]
print(f"New products: {len(new_prods_data)}", flush=True)

done3 = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(add_product, exc): pn for pn, exc in new_prods_data}
    for fut in as_completed(futures):
        new_p = fut.result()
        data.append(new_p)
        cat_map[new_p["Part Number"]] = len(data) - 1
        done3 += 1
        if done3 % 25 == 0:
            print(f"  [{done3}/{len(new_prods_data)}] downloaded={_stats['downloaded']} failed={_stats['failed']}", flush=True)

print(f"Step 3 done: {done3} new products added", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Fix priority source — products where Image_List uses wrong source
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Step 4: Fix Image_List priority source ===", flush=True)

fixed4 = 0
needs_fix = []
for p in data:
    il = p.get("Image_List", [])
    target_urls = get_priority_urls(p)
    if not target_urls: continue
    target_fnames = {hashlib.md5(u.encode()).hexdigest() + ".jpg" for u in target_urls}
    il_fnames = {os.path.basename(x) for x in il}
    if il_fnames != target_fnames:
        needs_fix.append(p)

print(f"Products needing priority fix: {len(needs_fix)}", flush=True)

def fix_priority(p):
    il = p.get("Image_List", [])
    target_urls = get_priority_urls(p)
    target_fnames = {hashlib.md5(u.encode()).hexdigest() + ".jpg" for u in target_urls}
    il_fnames = {os.path.basename(x) for x in il}
    for fname in il_fnames - target_fnames:
        archive_thumb(fname)
    new_il = []
    for url in target_urls:
        fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
        if os.path.exists(os.path.join(THUMB_DIR, fname)):
            new_il.append(f"thumbnails/{fname}")
        else:
            result = download_thumb(url)
            if result: new_il.append(result)
    p["Image_List"]      = new_il
    p["Local_Thumbnail"] = new_il[0] if new_il else ""
    return p

done4 = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(fix_priority, p): p["Part Number"] for p in needs_fix}
    for fut in as_completed(futures):
        fut.result()
        done4 += 1
        fixed4 += 1
        if done4 % 10 == 0:
            print(f"  [{done4}/{len(needs_fix)}] archived={_stats['archived']} downloaded={_stats['downloaded']} failed={_stats['failed']}", flush=True)

print(f"Step 4 done: {fixed4} products priority-fixed", flush=True)

# ─── Save ─────────────────────────────────────────────────────────────────────
print("\nSaving catalogue...", flush=True)
with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"Saved. Total products: {len(data)}", flush=True)

print("\n" + "=" * 60)
print("SUMMARY")
print(f"  Products removed:          4")
print(f"  Products updated:          {done2}")
print(f"  New products added:        {done3}")
print(f"  Priority fixes:            {fixed4}")
print(f"  Thumbnails archived:       {_stats['archived']}")
print(f"  Thumbnails downloaded:     {_stats['downloaded']}")
print(f"  Download failures:         {_stats['failed']}")
print(f"  Final catalogue size:      {len(data)}")

dist = Counter(len(p.get("Image_List", [])) for p in data)
print("\nImage distribution:")
for k in sorted(dist): print(f"  {k} images: {dist[k]} products")
