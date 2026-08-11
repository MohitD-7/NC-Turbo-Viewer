"""
add_2001_dining_chair_aug11.py
Add the 16 re-uploaded "Dining Chair" color items for the 2001
collection from the Aug 11, 2026 Furniture Excel. Some colors existed
before (deleted in the prior cleanup step), some are brand new -- all
100% Wayfair-sourced (NC=BY=HD=0, WF=8 each). Thumbnails are
downloaded concurrently across all items.
"""

import json, os, re, hashlib, requests, shutil, openpyxl
from io import BytesIO
from PIL import Image
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR  = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH  = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR = os.path.join(BASE_DIR, "static/thumbnails")
FUR_EXCEL = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Aug 11, 2026.xlsx"
THUMBNAIL_SIZE = (400, 400)
MAX_WORKERS = 8

NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
WF_COLS  = [f"Wayfair Image {i}"   for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = NC_COLS + BY_COLS + WF_COLS + HD_COLS


def parse_hyperlink(value):
    if not value:
        return "", ""
    value = str(value).strip()
    m = re.match(r'=HYPERLINK\("([^"]+)"\s*,\s*"([^"]*)"\)', value, re.I)
    if m:
        return m.group(2), m.group(1)
    if value.startswith("http"):
        return value, value
    return value, ""


def download_thumb(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    dest  = os.path.join(THUMB_DIR, fname)
    if os.path.exists(dest):
        return f"thumbnails/{fname}"
    try:
        raw = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        r = requests.get(raw, timeout=30)
        ct = r.headers.get("Content-Type", "")
        if r.status_code == 200 and "image" in ct:
            img = Image.open(BytesIO(r.content))
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(dest, "JPEG", quality=85)
            return f"thumbnails/{fname}"
    except Exception:
        pass
    return None


def download_many(url_tasks):
    """url_tasks: list of (pn, url). Returns dict pn -> list of thumb paths (in url order)."""
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_to_task = {pool.submit(download_thumb, url): (pn, url) for pn, url in url_tasks}
        for future in as_completed(future_to_task):
            pn, url = future_to_task[future]
            thumb = future.result()
            results.setdefault(pn, {})[url] = thumb
    return results


print("Loading catalogue...", flush=True)
with open(CAT_PATH, encoding="utf-8") as f:
    cat = json.load(f)
cat_pns = {p["Part Number"] for p in cat}
print(f"Catalogue: {len(cat)} products", flush=True)

print("Reading Aug 11 Furniture Excel (2001 sheet, values)...", flush=True)
wb_vals = openpyxl.load_workbook(FUR_EXCEL, read_only=True, data_only=True)
ws_vals = wb_vals["2001"]
rows_vals = list(ws_vals.iter_rows(values_only=True))
headers = rows_vals[0]
excel_items = [dict(zip(headers, r)) for r in rows_vals[1:]]
dc_rows = [e for e in excel_items if e.get("Product") == "Dining Chair" and e.get("Part Number")]
print(f"  Dining Chair rows: {len(dc_rows)}", flush=True)

print("Reading Color hyperlinks (formulas)...", flush=True)
wb_form = openpyxl.load_workbook(FUR_EXCEL, data_only=False)
ws_form = wb_form["2001"]
rows_form = list(ws_form.iter_rows())
f_headers = [c.value for c in rows_form[0]]
pn_idx = f_headers.index("Part Number")
color_idx = f_headers.index("Color")
color_formula_by_pn = {}
for row in rows_form[1:]:
    pn = row[pn_idx].value
    if pn:
        color_formula_by_pn[str(pn).strip()] = row[color_idx].value

new_pns = [e["Part Number"].strip() for e in dc_rows if e["Part Number"].strip() not in cat_pns]
print(f"New Dining Chair items to add: {len(new_pns)}", flush=True)
if len(new_pns) != len(dc_rows):
    already = [e["Part Number"].strip() for e in dc_rows if e["Part Number"].strip() in cat_pns]
    print(f"  WARNING: {len(already)} already in catalogue, skipping: {already}", flush=True)

# --- Build all new item dicts first (no downloads yet) ---
new_items = {}
for exc in dc_rows:
    pn = exc["Part Number"].strip()
    if pn not in new_pns:
        continue
    color_value, folder_link = parse_hyperlink(color_formula_by_pn.get(pn) or "")

    item = {
        "Collection Type":     "2001",
        "Thumbnail":           "",
        "Dropbox Folder Path": exc.get("Dropbox Folder Path") or "",
        "Part Number":         pn,
        "Category":            "Furniture",
        "Type":                exc.get("Type") or "Furniture",
        "Collection":          exc.get("Collection") or "2001",
        "Product":             exc.get("Product") or "",
        "Color":               color_value or "",
        "Color_Link":          folder_link,
        "Last Modified":       str(exc.get("Last Modified") or ""),
        "Image_List":          [],
        "Local_Thumbnail":     "",
    }
    for col in ALL_COLS:
        v = (exc.get(col) or "")
        v = str(v).strip() if v else ""
        item[col] = v if v.startswith("http") else ""
    item["NC Image Count"] = len([c for c in NC_COLS if item.get(c)])
    item["BY Image Count"] = len([c for c in BY_COLS if item.get(c)])
    item["WF Image Count"] = len([c for c in WF_COLS if item.get(c)])
    item["HD Image Count"] = len([c for c in HD_COLS if item.get(c)])
    new_items[pn] = item

# --- Download all thumbnails for all items concurrently ---
url_tasks = []
for pn, item in new_items.items():
    wf_urls = [item[c] for c in WF_COLS if item.get(c)][:5]
    for url in wf_urls:
        url_tasks.append((pn, url))

print(f"\nDownloading {len(url_tasks)} thumbnails concurrently ({MAX_WORKERS} workers)...", flush=True)
results = download_many(url_tasks)

stats = {"added": 0, "downloaded": 0, "failed": 0}
failed_tasks = []
for pn, item in new_items.items():
    wf_urls = [item[c] for c in WF_COLS if item.get(c)][:5]
    il = []
    for url in wf_urls:
        thumb = results.get(pn, {}).get(url)
        if thumb:
            il.append(thumb)
            stats["downloaded"] += 1
        else:
            stats["failed"] += 1
            failed_tasks.append((pn, url))
    item["Image_List"] = il
    item["Local_Thumbnail"] = il[0] if il else ""
    cat.append(item)
    stats["added"] += 1
    print(f"  {pn} ({item['Color']}) -> {len(il)} images", flush=True)

# --- Retry failures concurrently ---
if failed_tasks:
    print(f"\nRetrying {len(failed_tasks)} failed downloads concurrently...", flush=True)
    retry_results = download_many(failed_tasks)
    retry_ok = 0
    for pn, url in failed_tasks:
        thumb = retry_results.get(pn, {}).get(url)
        if thumb:
            new_items[pn]["Image_List"].append(thumb)
            new_items[pn]["Local_Thumbnail"] = new_items[pn]["Image_List"][0]
            retry_ok += 1
    print(f"  Retried, succeeded {retry_ok}/{len(failed_tasks)}", flush=True)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{CAT_PATH}.backup_{ts}"
shutil.copy(CAT_PATH, backup_path)
print(f"\nBackup: {backup_path}", flush=True)

with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

print(f"\nDone:")
print(f"  Added:       {stats['added']} new Dining Chair products")
print(f"  Downloaded:  {stats['downloaded']} thumbnails (initial)")
print(f"  Failed (before retry): {stats['failed']}")
print(f"  Final catalogue size: {len(cat)}")
dist = Counter(len(p.get("Image_List", [])) for p in cat if p.get("Part Number") in new_pns)
print("New items Image_List distribution:")
for k in sorted(dist): print(f"  {k} images: {dist[k]}")
