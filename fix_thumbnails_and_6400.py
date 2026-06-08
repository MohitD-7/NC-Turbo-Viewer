"""
fix_thumbnails_and_6400.py
  A) Force-refresh thumbnails for all Foutput.csv products (archive old, download fresh WF-priority)
  B) Update 6400-DG from 6400 DG without table.csv + Jun 08 Furniture Excel
Concurrent downloads — 8 workers.
"""

import json, hashlib, os, shutil, requests, csv, re, openpyxl, threading
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR        = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CATALOGUE_PATH  = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR       = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE_DIR     = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_thumbnails_replaced"
FURNITURE_EXCEL = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Jun 08, 2026.xlsx"
CSV_6400        = r"C:\Users\Lenovo\Desktop\6400 DG without table.csv"
THUMBNAIL_SIZE  = (400, 400)
WORKERS         = 10
DELAY           = 0.3  # seconds between each download to avoid Dropbox rate limiting

WF_COLS  = [f"Wayfair Image {i}"   for i in range(1, 16)]
NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = WF_COLS + NC_COLS + BY_COLS + HD_COLS

os.makedirs(ARCHIVE_DIR, exist_ok=True)

_lock = threading.Lock()

FOUTPUT_PNS = list(dict.fromkeys([
    "CUSH5619B-CFN","CUSH5619B-HE","CUSH5619B-CN","CUSH5619B-RC","CUSH5619B-RG","CUSH5619B-RI","CUSH5619B-RO",
    "CUSH3717B-CFN","CUSH3717B-HE","CUSH3717B-CN","CUSH3717B-RC","CUSH3717B-RG","CUSH3717B-RI","CUSH3717B-RO",
    "CUSH4017B-CFN","CUSH4017B-HE","CUSH4017B-CN","CUSH4017B-RC","CUSH4017B-RG","CUSH4017B-RI","CUSH4017B-RO",
    "CUSH4818B-CFN","CUSH4818B-HE","CUSH4818B-CN","CUSH4818B-RC","CUSH4818B-RG","CUSH4818B-RI","CUSH4818B-RO",
    "CUSH2325DS-CFN","CUSH2325DS-HE","CUSH2325DS-CN","CUSH2325DS-RC","CUSH2325DS-RG","CUSH2325DS-RI","CUSH2325DS-RO",
    "CUSH2424DS-CFN","CUSH2424DS-HE","CUSH2424DS-CN","CUSH2424DS-RC","CUSH2424DS-RG","CUSH2424DS-RI","CUSH2424DS-RO",
    "CUSH2526DS-CFN","CUSH2526DS-HE","CUSH2526DS-CN","CUSH2526DS-RC","CUSH2526DS-RG","CUSH2526DS-RI","CUSH2526DS-RO",
    "CUSH2630DS-CFN","CUSH2630DS-HE","CUSH2630DS-CN","CUSH2630DS-RC","CUSH2630DS-RG","CUSH2630DS-RI","CUSH2630DS-RO",
    "CUSH271SCC-CFN","CUSH271SCC-HE","CUSH271SCC-CN","CUSH271SCC-RC","CUSH271SCC-RG","CUSH271SCC-RI","CUSH271SCC-RO",
    "CUSH2178CL-CFN","CUSH2178CL-HE","CUSH2178CL-CN","CUSH2178CL-RC","CUSH2178CL-RG","CUSH2178CL-RI","CUSH2178CL-RO",
    "CUSH2375CL-CFN","CUSH2375CL-HE","CUSH2375CL-CN","CUSH2375CL-RC","CUSH2375CL-RG","CUSH2375CL-RI","CUSH2375CL-RO",
    "CUSH2473CL-CFN","CUSH2473CL-HE","CUSH2473CL-CN","CUSH2473CL-RC","CUSH2473CL-RG","CUSH2473CL-RI","CUSH2473CL-RO",
    "CUSH2680CL-CFN","CUSH2680CL-HE","CUSH2680CL-CN","CUSH2680CL-RC","CUSH2680CL-RG","CUSH2680CL-RI","CUSH2680CL-RO",
    "CUSH2022O-CFN","CUSH2022O-HE","CUSH2022O-CN","CUSH2022O-RC","CUSH2022O-RG","CUSH2022O-RI","CUSH2022O-RO",
    "CUSH2319O-CFN","CUSH2319O-HE","CUSH2319O-CN","CUSH2319O-RC","CUSH2319O-RG","CUSH2319O-RI","CUSH2319O-RO",
    "CUSH2424O-CFN","CUSH2424O-HE","CUSH2424O-CN","CUSH2424O-RC","CUSH2424O-RG","CUSH2424O-RI","CUSH2424O-RO",
    "CUSH2624O-CFN","CUSH2624O-HE","CUSH2624O-CN","CUSH2624O-RC","CUSH2624O-RG","CUSH2624O-RI","CUSH2624O-RO",
    "CUSH1616DC-CFN","CUSH1616DC-HE","CUSH1616DC-CN","CUSH1616DC-RC","CUSH1616DC-RG","CUSH1616DC-RI","CUSH1616DC-RO",
    "CUSH1818DC-CFN","CUSH1818DC-HE","CUSH1818DC-CN","CUSH1818DC-RC","CUSH1818DC-RG","CUSH1818DC-RI","CUSH1818DC-RO",
    "CUSH2020DC-CFN","CUSH2020DC-HE","CUSH2020DC-CN","CUSH2020DC-RC","CUSH2020DC-RG","CUSH2020DC-RI","CUSH2020DC-RO",
    "CUSH2119DC-CFN","CUSH2119DC-HE","CUSH2119DC-CN","CUSH2119DC-RC","CUSH2119DC-RG","CUSH2119DC-RI","CUSH2119DC-RO",
]))


def thumb_fname(url):
    return hashlib.md5(url.encode()).hexdigest() + ".jpg"


def archive_thumb(fname):
    src = os.path.join(THUMB_DIR, fname)
    if os.path.exists(src):
        shutil.move(src, os.path.join(ARCHIVE_DIR, fname))
        return True
    return False


def download_fresh(url):
    """Download fresh (ignores cache). Returns 'thumbnails/<hash>.jpg' or None."""
    import time
    fname = thumb_fname(url)
    dest  = os.path.join(THUMB_DIR, fname)
    time.sleep(DELAY)
    try:
        raw  = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        resp = requests.get(raw, timeout=30)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(dest, "JPEG", quality=85)
            return f"thumbnails/{fname}"
    except Exception as e:
        with _lock:
            print(f"  FAIL {url.split('/')[-1].split('?')[0]}: {e}", flush=True)
    return None


def get_priority_urls(p, limit=5):
    urls = []
    for cols in [WF_COLS, NC_COLS, BY_COLS, HD_COLS]:
        for col in cols:
            v = (p.get(col) or "").strip()
            if v.startswith("http"):
                urls.append(v)
        if len(urls) >= limit:
            break
    return urls[:limit]


def parse_hyperlink(val):
    if not isinstance(val, str): return None, None
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', val)
    if m: return m.group(2), m.group(1)
    return (val, None) if not val.startswith("http") else (None, val)


def process_product_concurrent(args):
    """Used by ThreadPoolExecutor — archives old thumbs, downloads fresh ones."""
    pn, target_urls, old_il_fnames = args
    archived = 0
    for fname in old_il_fnames:
        if archive_thumb(fname):
            archived += 1
    new_il = []
    for url in target_urls:
        result = download_fresh(url)
        if result:
            new_il.append(result)
    return pn, new_il, archived, len(target_urls) - len(new_il)  # (pn, il, archived, failed)


# ─────────────────────────────────────────────────────────────────────────────
print("Loading catalogue...", flush=True)
with open(CATALOGUE_PATH, encoding="utf-8") as f:
    data = json.load(f)
cat_map = {p["Part Number"]: i for i, p in enumerate(data)}
print(f"Catalogue: {len(data)} products", flush=True)


# ══════════════════════════════════════════════════════════════════════════════
# PART A: Foutput.csv products — concurrent
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Part A: Foutput.csv products (8 concurrent workers) ===", flush=True)

tasks = []
for pn in FOUTPUT_PNS:
    idx = cat_map.get(pn)
    if idx is None:
        print(f"  NOT IN CATALOGUE: {pn}", flush=True)
        continue
    p = data[idx]
    target_urls    = get_priority_urls(p)
    old_il_fnames  = [os.path.basename(path) for path in p.get("Image_List", [])]
    tasks.append((pn, target_urls, old_il_fnames))

print(f"  {len(tasks)} products queued, {sum(len(t[1]) for t in tasks)} images to download", flush=True)

a_fixed = 0; a_archived = 0; a_dl = 0; a_failed = 0

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(process_product_concurrent, t): t[0] for t in tasks}
    for fut in as_completed(futures):
        pn, new_il, archived, failed = fut.result()
        idx = cat_map[pn]
        data[idx]["Image_List"]     = new_il
        data[idx]["Local_Thumbnail"] = new_il[0] if new_il else ""
        a_fixed   += 1
        a_archived += archived
        a_dl       += len(new_il)
        a_failed   += failed
        if a_fixed % 25 == 0:
            print(f"  [{a_fixed}/{len(tasks)}] {a_dl} downloaded, {a_failed} failed", flush=True)

print(f"Part A done: {a_fixed} products | {a_archived} archived | {a_dl} downloaded | {a_failed} failed", flush=True)


# ══════════════════════════════════════════════════════════════════════════════
# PART B: 6400-DG from CSV + Jun 08 Furniture Excel — concurrent
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== Part B: 6400-DG update ===", flush=True)

# Read CSV
csv_pns = set()
try:
    with open(CSV_6400, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows   = list(reader)
    print(f"  CSV: {len(rows)} rows, columns: {list(rows[0].keys()) if rows else []}", flush=True)
    for row in rows:
        for col, val in row.items():
            val = str(val or "").strip()
            m = re.match(r"((?:N[CI]+)?6[45]\d+[^_\s]*?)_\d+", val)
            if m: csv_pns.add(m.group(1))
            if ("part" in col.lower() or col.lower() == "pn") and val:
                csv_pns.add(val)
    print(f"  Extracted {len(csv_pns)} PNs from CSV. Sample: {list(csv_pns)[:5]}", flush=True)
except Exception as e:
    print(f"  CSV read error: {e}", flush=True)

# Read Excel 6400 sheet
print("  Reading Furniture Excel (6400 sheet)...", flush=True)
wb = openpyxl.load_workbook(FURNITURE_EXCEL)
excel_6400 = {}
for sheet in wb.sheetnames:
    if "6400" not in sheet: continue
    ws = wb[sheet]
    headers = [c.value for c in ws[1]]
    if "Part Number" not in headers: continue
    pn_col = headers.index("Part Number") + 1
    for row in ws.iter_rows(min_row=2):
        pn = row[pn_col - 1].value
        if not pn: continue
        excel_6400[pn] = {headers[i]: (row[i].value if i < len(row) else None) for i in range(len(headers))}
    print(f"  Sheet '{sheet}': {len(excel_6400)} products", flush=True)

# Determine which to update
if csv_pns:
    pns_to_update = set()
    for csv_pn in csv_pns:
        if csv_pn in excel_6400:
            pns_to_update.add(csv_pn)
        else:
            for epn in excel_6400:
                if csv_pn in epn:
                    pns_to_update.add(epn)
    print(f"  Matched {len(pns_to_update)} products from CSV", flush=True)
else:
    pns_to_update = set(excel_6400.keys()) & set(cat_map.keys())
    print(f"  No CSV matches — updating all {len(pns_to_update)} 6400 catalogue products", flush=True)

# Build tasks for Part B
b_tasks = []
b_new_products = []

for pn in pns_to_update:
    excel_row  = excel_6400.get(pn, {})
    color_name, color_link = parse_hyperlink(excel_row.get("Color"))
    idx = cat_map.get(pn)

    if idx is None:
        # New product
        new_prod = {
            "Part Number": pn, "Collection": excel_row.get("Collection") or "6400 - DG",
            "Category": "Furniture", "Type": "Furniture",
            "Color": color_name or "", "Color_Link": color_link or "",
            "Dropbox Folder Path": excel_row.get("Dropbox Folder Path") or "",
            "Last Modified": str(excel_row.get("Last Modified") or ""),
            "Image_List": [], "Local_Thumbnail": "",
        }
        for col in ALL_COLS:
            v = (excel_row.get(col) or "").strip()
            new_prod[col] = v if v.startswith("http") else ""
        b_new_products.append(new_prod)
        continue

    p = data[idx]
    # Update URL fields from Excel
    for col in ALL_COLS:
        v = (excel_row.get(col) or "").strip()
        p[col] = v if v.startswith("http") else ""
    if color_name: p["Color"]      = color_name
    if color_link: p["Color_Link"] = color_link

    target_urls   = get_priority_urls(p)
    old_il_fnames = [os.path.basename(path) for path in p.get("Image_List", [])]
    b_tasks.append((pn, target_urls, old_il_fnames))

print(f"  {len(b_tasks)} to update, {len(b_new_products)} new products", flush=True)

b_fixed = 0; b_archived = 0; b_dl = 0; b_failed = 0; b_new = 0

# Download for updates
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(process_product_concurrent, t): t[0] for t in b_tasks}
    for fut in as_completed(futures):
        pn, new_il, archived, failed = fut.result()
        idx = cat_map[pn]
        data[idx]["Image_List"]      = new_il
        data[idx]["Local_Thumbnail"] = new_il[0] if new_il else ""
        b_fixed   += 1
        b_archived += archived
        b_dl       += len(new_il)
        b_failed   += failed
        if b_fixed % 100 == 0:
            print(f"  [{b_fixed}/{len(b_tasks)}] {b_dl} downloaded", flush=True)

# Download for new products
def download_new(prod):
    urls  = get_priority_urls(prod)
    il    = []
    fails = 0
    for url in urls:
        r = download_fresh(url)
        if r: il.append(r)
        else: fails += 1
    prod["Image_List"]      = il
    prod["Local_Thumbnail"] = il[0] if il else ""
    return prod, fails

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {ex.submit(download_new, prod): prod["Part Number"] for prod in b_new_products}
    for fut in as_completed(futures):
        prod, fails = fut.result()
        data.append(prod)
        cat_map[prod["Part Number"]] = len(data) - 1
        b_new    += 1
        b_dl     += len(prod["Image_List"])
        b_failed += fails

print(f"Part B done: {b_fixed} updated | {b_new} new | {b_archived} archived | {b_dl} downloaded | {b_failed} failed", flush=True)

# Save
print("\nSaving catalogue.json...", flush=True)
with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Saved.", flush=True)

print("\n" + "=" * 60, flush=True)
print("SUMMARY", flush=True)
print(f"Part A: {a_fixed} products | {a_archived} archived | {a_dl} downloaded | {a_failed} failed", flush=True)
print(f"Part B: {b_fixed} updated | {b_new} new | {b_archived} archived | {b_dl} downloaded | {b_failed} failed", flush=True)
print(f"Archive: {ARCHIVE_DIR}", flush=True)
