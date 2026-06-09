"""
fix_color_and_stale.py
Task A: Fill missing Color + Color_Link from Excel HYPERLINK formulas (931 products)
Task B: Re-download thumbnails for 644 products where Last Modified is newer in Excel
         Priority: Wayfair → Beyond (Overstock) → Northcape, max 5 images
"""

import json, os, hashlib, requests, re, time, shutil, openpyxl, threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

BASE_DIR   = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH   = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR  = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE    = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_thumbnails_stale"
THUMBNAIL_SIZE = (400, 400)
WORKERS    = 5
DELAY      = 1.0

EXCELS = [
    r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Cushions - Jun 08, 2026.xlsx",
    r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Jun 08, 2026.xlsx",
    r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Accent Pillow - Jun 05, 2026.xlsx",
]

WF_COLS = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS = [f"Northcape Image {i}" for i in range(1, 16)]
ALL_IMG = WF_COLS + BY_COLS + NC_COLS + [f"Home Depot Image {i}" for i in range(1, 16)]

os.makedirs(ARCHIVE, exist_ok=True)
_lock = threading.Lock()

def parse_color(val):
    """Extract (color_name, color_link) from =HYPERLINK formula or plain string."""
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

def download_fresh(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    dest  = os.path.join(THUMB_DIR, fname)
    time.sleep(DELAY)
    try:
        raw  = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        resp = requests.get(raw, timeout=30)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(dest, "JPEG", quality=85)
            return f"thumbnails/{fname}"
    except Exception:
        pass
    return None

# ─── Load data ───────────────────────────────────────────────────────────────
print("Loading catalogue...", flush=True)
with open(CAT_PATH, encoding="utf-8") as f:
    data = json.load(f)
cat_map = {p["Part Number"]: i for i, p in enumerate(data)}
print(f"Catalogue: {len(data)} products", flush=True)

# ─── Read all Excel files ─────────────────────────────────────────────────────
print("\nReading Excel files...", flush=True)
excel_rows = {}  # pn -> {col: val}
for path in EXCELS:
    try:
        wb = openpyxl.load_workbook(path)  # no data_only — need HYPERLINK formulas
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            headers = [c.value for c in ws[1]]
            if "Part Number" not in headers: continue
            pn_col = headers.index("Part Number") + 1
            for row in ws.iter_rows(min_row=2):
                pn = row[pn_col - 1].value
                if not pn: continue
                excel_rows[pn] = {headers[i]: (row[i].value if i < len(row) else None)
                                  for i in range(len(headers))}
        print(f"  {os.path.basename(path)}: done", flush=True)
    except Exception as e:
        print(f"  ERROR {os.path.basename(path)}: {e}", flush=True)

print(f"Total Excel rows: {len(excel_rows)}", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# TASK A: Fill missing Color / Color_Link
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Task A: Fill missing Color / Color_Link ===", flush=True)
a_updated = 0

for pn, idx in cat_map.items():
    p = data[idx]
    has_color = bool((p.get("Color") or "").strip())
    has_link  = bool((p.get("Color_Link") or "").strip())
    if has_color and has_link: continue

    # Try Excel first
    exc = excel_rows.get(pn)
    if exc:
        color_name, color_link = parse_color(exc.get("Color"))
        if not has_color and color_name:
            p["Color"] = color_name
        if not has_link and color_link:
            p["Color_Link"] = color_link
        if color_name or color_link:
            a_updated += 1
            continue

    # Fallback: derive Color from Dropbox Folder Path
    if not has_color:
        path_str = (p.get("Dropbox Folder Path") or "").strip()
        if path_str:
            derived = path_str.rstrip("/").split("/")[-1]
            if derived and derived not in ("thumbnails", ""):
                p["Color"] = derived
                a_updated += 1

print(f"Task A done: {a_updated} products updated with Color/Color_Link", flush=True)

# Recount
still_no_color = sum(1 for p in data if not (p.get("Color") or "").strip())
still_no_link  = sum(1 for p in data if not (p.get("Color_Link") or "").strip())
print(f"Remaining without Color: {still_no_color} | without Color_Link: {still_no_link}", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
# TASK B: Re-download stale thumbnails (Last Modified changed)
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Task B: Refresh stale thumbnails ===", flush=True)

stale = []
for pn, exc in excel_rows.items():
    idx = cat_map.get(pn)
    if idx is None: continue
    p = data[idx]
    cat_lm  = str(p.get("Last Modified") or "")
    exc_lm  = str(exc.get("Last Modified") or "")
    if exc_lm and exc_lm != cat_lm:
        stale.append((idx, pn, exc))

print(f"Stale products (Last Modified differs): {len(stale)}", flush=True)

def refresh_product(args):
    idx, pn, exc = args
    p = data[idx]

    # Update image URL fields from Excel
    for col in ALL_IMG:
        v = (exc.get(col) or "").strip()
        p[col] = v if v.startswith("http") else ""

    # Update Last Modified
    p["Last Modified"] = str(exc.get("Last Modified") or "")

    # Archive old thumbnails
    archived = 0
    for path in p.get("Image_List", []):
        fname = os.path.basename(path)
        src = os.path.join(THUMB_DIR, fname)
        if os.path.exists(src):
            shutil.move(src, os.path.join(ARCHIVE, fname))
            archived += 1

    # Download fresh
    target_urls = get_priority_urls(p)
    new_il = []
    dl_ok = 0; dl_fail = 0
    for url in target_urls:
        result = download_fresh(url)
        if result:
            new_il.append(result); dl_ok += 1
        else:
            dl_fail += 1

    p["Image_List"]      = new_il
    p["Local_Thumbnail"] = new_il[0] if new_il else ""
    return idx, archived, dl_ok, dl_fail

total_archived = 0; total_ok = 0; total_fail = 0; done = 0

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(refresh_product, t): t[1] for t in stale}
    for fut in as_completed(futures):
        idx, archived, dl_ok, dl_fail = fut.result()
        total_archived += archived
        total_ok       += dl_ok
        total_fail     += dl_fail
        done           += 1
        if done % 20 == 0:
            print(f"  [{done}/{len(stale)}] archived={total_archived} downloaded={total_ok} failed={total_fail}", flush=True)

print(f"Task B done: {done} products refreshed | {total_archived} archived | {total_ok} downloaded | {total_fail} failed", flush=True)

# ─── Save ─────────────────────────────────────────────────────────────────────
print("\nSaving catalogue...", flush=True)
with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Saved.", flush=True)

dist = Counter(len(p.get("Image_List", [])) for p in data)
print("\nFinal image distribution:")
for k in sorted(dist): print(f"  {k} images: {dist[k]} products")
