"""
apply_jun11_pillows.py
Apply Jun 11 Accent Pillow Excel changes:
  1. Remove 4 products no longer in Excel
  2. Update 77 products with URL changes (force-refresh thumbnails)
  3. Refresh 16 in-place replacements (same URL, newer Last Modified)
  4. Add 72 new products with thumbnails
Priority: Wayfair → Overstock → Northcape | 10 workers, 0.5s delay
"""

import json, os, hashlib, requests, re, time, shutil, openpyxl, threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

BASE_DIR  = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH  = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE   = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_thumbnails_jun11"
EXCEL     = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Accent Pillow - Jun 11, 2026.xlsx"
THUMBNAIL_SIZE = (400, 400)
WORKERS = 10
DELAY   = 0.5

os.makedirs(ARCHIVE, exist_ok=True)
_lock = threading.Lock()
_stats = {"archived": 0, "downloaded": 0, "failed": 0}

WF_COLS  = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = WF_COLS + BY_COLS + NC_COLS + HD_COLS

def parse_color(val):
    if not isinstance(val, str): return None, None
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', val)
    if m: return m.group(2), m.group(1)
    return (val.strip() or None, None)

def get_priority_urls(p, limit=5):
    urls = []
    for cols in [WF_COLS, BY_COLS, NC_COLS]:
        for col in cols:
            v = (p.get(col) or "")
            v = str(v).strip() if v else ""
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

print("Loading catalogue...", flush=True)
with open(CAT_PATH, encoding="utf-8") as f:
    data = json.load(f)
cat_map = {p["Part Number"]: i for i, p in enumerate(data)}
print(f"Catalogue: {len(data)} products", flush=True)

# Read Excel (raw — for HYPERLINK formulas)
print("Reading Excel...", flush=True)
wb = openpyxl.load_workbook(EXCEL)
excel_rows = {}
for sheet in wb.sheetnames:
    ws = wb[sheet]
    headers = [c.value for c in ws[1]]
    if "Part Number" not in headers: continue
    pn_col = headers.index("Part Number") + 1
    for row in ws.iter_rows(min_row=2):
        pn = row[pn_col - 1].value
        if not pn: continue
        excel_rows[pn] = {headers[i]: (row[i].value if i < len(row) else None) for i in range(len(headers))}
print(f"Excel: {len(excel_rows)} products", flush=True)

# Categorize
new_pns = []
url_changed = []  # (idx, pn, exc)
inplace = []     # (idx, pn, exc)
remove_pns = []

for pn, exc in excel_rows.items():
    if pn not in cat_map:
        new_pns.append((pn, exc))
        continue
    idx = cat_map[pn]
    cat = data[idx]
    exc_lm = str(exc.get("Last Modified") or "")
    cat_lm = str(cat.get("Last Modified") or "")
    if exc_lm == cat_lm: continue  # truly unchanged

    exc_urls = set()
    cat_urls = set()
    for col in ALL_COLS:
        ev = (exc.get(col) or "")
        ev = str(ev).strip() if ev else ""
        if ev.startswith("http"): exc_urls.add(ev)
        cv = (cat.get(col) or "").strip()
        if cv.startswith("http"): cat_urls.add(cv)
    if exc_urls != cat_urls:
        url_changed.append((idx, pn, exc))
    elif exc_urls:
        inplace.append((idx, pn, exc))

# Removed
for pn, p in [(p["Part Number"], p) for p in data]:
    if p.get("Category") in ("Accent Pillows", "Accent Pillow") and pn not in excel_rows:
        remove_pns.append(pn)

print(f"\nNew products: {len(new_pns)}")
print(f"URL changed: {len(url_changed)}")
print(f"In-place replacements: {len(inplace)}")
print(f"To remove: {len(remove_pns)}", flush=True)

# ═══════════════════════════════════════════════════════════════════════════
# Step 1: Remove
# ═══════════════════════════════════════════════════════════════════════════
print(f"\n=== Step 1: Remove {len(remove_pns)} products ===", flush=True)
for pn in remove_pns:
    idx = cat_map.get(pn)
    if idx is None: continue
    for path in data[idx].get("Image_List", []):
        archive_thumb(os.path.basename(path))
    print(f"  Removed: {pn}", flush=True)
data = [p for p in data if p["Part Number"] not in set(remove_pns)]
cat_map = {p["Part Number"]: i for i, p in enumerate(data)}

# ═══════════════════════════════════════════════════════════════════════════
# Step 2 & 3: Update URL-changed + in-place refresh
# ═══════════════════════════════════════════════════════════════════════════
def refresh_existing(args):
    idx, pn, exc = args
    p = data[idx]

    # Update all image URL fields
    for col in ALL_COLS:
        v = (exc.get(col) or "")
        v = str(v).strip() if v else ""
        p[col] = v if v.startswith("http") else ""

    # Update Color/Color_Link/LM
    cn, cl = parse_color(exc.get("Color"))
    if cn: p["Color"] = cn
    if cl: p["Color_Link"] = cl
    p["Last Modified"] = str(exc.get("Last Modified") or "")
    for f in ("NC Image Count","BY Image Count","WF Image Count","HD Image Count"):
        v = exc.get(f)
        if v is not None: p[f] = int(v or 0)

    # Archive all current thumbnails
    for path in p.get("Image_List", []):
        archive_thumb(os.path.basename(path))

    # Download fresh with priority
    urls = get_priority_urls(p)
    new_il = []
    for url in urls:
        r = download_thumb(url)
        if r: new_il.append(r)
    p["Image_List"]      = new_il
    p["Local_Thumbnail"] = new_il[0] if new_il else ""
    return idx

all_existing = url_changed + inplace
print(f"\n=== Step 2: Refresh {len(all_existing)} existing products (URL changes + in-place) ===", flush=True)

# Need to rebuild cat_map after removals
cat_map = {p["Part Number"]: i for i, p in enumerate(data)}
all_existing = [(cat_map[pn], pn, exc) for _, pn, exc in all_existing if pn in cat_map]

done2 = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(refresh_existing, t): t[1] for t in all_existing}
    for fut in as_completed(futures):
        fut.result()
        done2 += 1
        if done2 % 10 == 0:
            print(f"  [{done2}/{len(all_existing)}] archived={_stats['archived']} dl={_stats['downloaded']} fail={_stats['failed']}", flush=True)
print(f"Step 2 done: {done2} refreshed", flush=True)

# ═══════════════════════════════════════════════════════════════════════════
# Step 4: Add new products
# ═══════════════════════════════════════════════════════════════════════════
def add_product(args):
    pn, exc = args
    cn, cl = parse_color(exc.get("Color"))
    new_prod = {
        "Part Number": pn,
        "Collection": exc.get("Collection") or "",
        "Category": "Accent Pillows",
        "Type": "Accent Pillows",
        "Color": cn or "",
        "Color_Link": cl or "",
        "Dropbox Folder Path": exc.get("Dropbox Folder Path") or "",
        "Last Modified": str(exc.get("Last Modified") or ""),
        "NC Image Count": int(exc.get("NC Image Count") or 0),
        "BY Image Count": int(exc.get("BY Image Count") or 0),
        "WF Image Count": int(exc.get("WF Image Count") or 0),
        "HD Image Count": int(exc.get("HD Image Count") or 0),
        "Image_List": [],
        "Local_Thumbnail": "",
    }
    for col in ALL_COLS:
        v = (exc.get(col) or "")
        v = str(v).strip() if v else ""
        new_prod[col] = v if v.startswith("http") else ""

    urls = get_priority_urls(new_prod)
    il = []
    for url in urls:
        r = download_thumb(url)
        if r: il.append(r)
    new_prod["Image_List"]      = il
    new_prod["Local_Thumbnail"] = il[0] if il else ""
    return new_prod

print(f"\n=== Step 3: Add {len(new_pns)} new products ===", flush=True)
done3 = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(add_product, t): t[0] for t in new_pns}
    for fut in as_completed(futures):
        new_p = fut.result()
        data.append(new_p)
        done3 += 1
        if done3 % 15 == 0:
            print(f"  [{done3}/{len(new_pns)}] dl={_stats['downloaded']} fail={_stats['failed']}", flush=True)
print(f"Step 3 done: {done3} added", flush=True)

# Save
print("\nSaving catalogue...", flush=True)
with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Saved.", flush=True)

print(f"\n{'='*60}")
print("SUMMARY")
print(f"  Removed:     {len(remove_pns)}")
print(f"  Refreshed:   {done2}")
print(f"  Added new:   {done3}")
print(f"  Archived:    {_stats['archived']}")
print(f"  Downloaded:  {_stats['downloaded']}")
print(f"  Failed:      {_stats['failed']}")
print(f"  Catalogue:   {len(data)}")
