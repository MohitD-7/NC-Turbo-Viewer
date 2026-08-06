"""
fix_6400dg_wayfair_aug06.py
Sync 6400-DG with the Aug 06, 2026 Furniture Excel:

1. Add 12 brand-new "Canvas Natural" (-CN) items -- 100% Wayfair-sourced,
   never existed in the catalogue before.
2. For 51 existing items whose WF Image Count changed (50 that went from
   0 -> N and were relying on Overstock (BY-) thumbnails as filler, plus
   1 that already had pure-Wayfair thumbnails but gained an image):
   - Sync all image URL columns + counts to the new Excel
   - Delete their current local thumbnail files (unless shared with
     another catalogue item)
   - Clear Image_List / Local_Thumbnail
   - Re-download up to 5 thumbnails sourced ONLY from Wayfair Image
     columns
"""

import json, os, re, hashlib, requests, time, shutil, openpyxl
from io import BytesIO
from PIL import Image
from datetime import datetime
from collections import Counter

BASE_DIR  = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH  = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR = os.path.join(BASE_DIR, "static/thumbnails")
FUR_EXCEL = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Aug 06, 2026.xlsx"
THUMBNAIL_SIZE = (400, 400)
DELAY = 0.8

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
    time.sleep(DELAY)
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


print("Loading catalogue...", flush=True)
with open(CAT_PATH, encoding="utf-8") as f:
    cat = json.load(f)
print(f"Catalogue: {len(cat)} items", flush=True)

print("Reading Aug 06 Furniture Excel (6400 sheet, values)...", flush=True)
wb_vals = openpyxl.load_workbook(FUR_EXCEL, read_only=True, data_only=True)
ws_vals = wb_vals["6400"]
rows_vals = list(ws_vals.iter_rows(values_only=True))
headers = rows_vals[0]
excel_items = [dict(zip(headers, r)) for r in rows_vals[1:]]
excel_dg = {e["Part Number"].strip(): e for e in excel_items
            if e.get("Collection") == "6400 - DG" and e.get("Part Number")}
print(f"  6400-DG rows: {len(excel_dg)}", flush=True)

print("Reading Color hyperlinks (formulas)...", flush=True)
wb_form = openpyxl.load_workbook(FUR_EXCEL, data_only=False)
ws_form = wb_form["6400"]
rows_form = list(ws_form.iter_rows())
f_headers = [c.value for c in rows_form[0]]
pn_idx = f_headers.index("Part Number")
color_idx = f_headers.index("Color")
color_formula_by_pn = {}
for row in rows_form[1:]:
    pn = row[pn_idx].value
    if pn and str(pn).strip() in excel_dg:
        color_formula_by_pn[str(pn).strip()] = row[color_idx].value

cat_by_pn = {i["Part Number"]: i for i in cat}
cat_dg_pns = {i["Part Number"] for i in cat if i.get("Collection") == "6400 - DG"}

new_pns = sorted(pn for pn in excel_dg if pn not in cat_by_pn)
refresh_pns = sorted(
    pn for pn in excel_dg
    if pn in cat_by_pn
    and int(excel_dg[pn].get("WF Image Count") or 0) != int(cat_by_pn[pn].get("WF Image Count") or 0)
)
print(f"\nNew items to add: {len(new_pns)}", flush=True)
print(f"Existing items to refresh: {len(refresh_pns)}", flush=True)

# --- Safety: build a map of thumbnail filename -> how many catalogue items reference it ---
thumb_ref_count = Counter()
for item in cat:
    for t in item.get("Image_List", []):
        thumb_ref_count[t] += 1

# --- Part 1: refresh existing items -----------------------------------
stats = {"deleted_files": 0, "kept_shared": 0, "downloaded": 0, "failed": 0, "added": 0}

for n, pn in enumerate(refresh_pns, 1):
    item = cat_by_pn[pn]
    exc = excel_dg[pn]

    # Delete old thumbnail files if not shared with another item
    old_thumbs = item.get("Image_List", [])
    for t in old_thumbs:
        thumb_ref_count[t] -= 1
        if thumb_ref_count[t] <= 0:
            fpath = os.path.join(THUMB_DIR, t.replace("thumbnails/", ""))
            if os.path.exists(fpath):
                os.remove(fpath)
                stats["deleted_files"] += 1
        else:
            stats["kept_shared"] += 1

    # Sync all image columns from new Excel
    for col in ALL_COLS:
        v = (exc.get(col) or "")
        v = str(v).strip() if v else ""
        item[col] = v if v.startswith("http") else ""
    # Derive counts from actual populated cells, not the (sometimes stale) count fields
    item["NC Image Count"] = len([c for c in NC_COLS if item.get(c)])
    item["BY Image Count"] = len([c for c in BY_COLS if item.get(c)])
    item["WF Image Count"] = len([c for c in WF_COLS if item.get(c)])
    item["HD Image Count"] = len([c for c in HD_COLS if item.get(c)])
    item["Last Modified"] = str(exc.get("Last Modified") or item.get("Last Modified") or "")

    # Re-download up to 5 thumbnails, Wayfair only
    wf_urls = [item[c] for c in WF_COLS if item.get(c)]
    il = []
    for url in wf_urls[:5]:
        r = download_thumb(url)
        if r:
            il.append(r)
            thumb_ref_count[r] += 1
            stats["downloaded"] += 1
        else:
            stats["failed"] += 1
    item["Image_List"] = il
    item["Local_Thumbnail"] = il[0] if il else ""

    if n % 10 == 0:
        print(f"  refresh [{n}/{len(refresh_pns)}] dl={stats['downloaded']} fail={stats['failed']}", flush=True)

# --- Part 2: add brand-new items ---------------------------------------
for n, pn in enumerate(new_pns, 1):
    exc = excel_dg[pn]
    color_value, folder_link = parse_hyperlink(color_formula_by_pn.get(pn) or "")

    new_item = {
        "Collection Type":     "6400",
        "Thumbnail":           "",
        "Dropbox Folder Path": exc.get("Dropbox Folder Path") or "",
        "Part Number":         pn,
        "Category":            "Furniture",
        "Type":                exc.get("Type") or "Furniture",
        "Collection":          exc.get("Collection") or "6400 - DG",
        "Arm/Table-Top":       exc.get("Arm/Table-Top") or "",
        "Product":             exc.get("Product") or "",
        "Panel":               exc.get("Panel") or "",
        "Color":               color_value or exc.get("Color") or "",
        "Color_Link":          folder_link,
        "Last Modified":       str(exc.get("Last Modified") or ""),
        "Image_List":          [],
        "Local_Thumbnail":     "",
    }
    for col in ALL_COLS:
        v = (exc.get(col) or "")
        v = str(v).strip() if v else ""
        new_item[col] = v if v.startswith("http") else ""
    # Derive counts from actual populated cells, not the (sometimes stale) count fields
    new_item["NC Image Count"] = len([c for c in NC_COLS if new_item.get(c)])
    new_item["BY Image Count"] = len([c for c in BY_COLS if new_item.get(c)])
    new_item["WF Image Count"] = len([c for c in WF_COLS if new_item.get(c)])
    new_item["HD Image Count"] = len([c for c in HD_COLS if new_item.get(c)])

    wf_urls = [new_item[c] for c in WF_COLS if new_item.get(c)]
    il = []
    for url in wf_urls[:5]:
        r = download_thumb(url)
        if r:
            il.append(r)
            thumb_ref_count[r] += 1
            stats["downloaded"] += 1
        else:
            stats["failed"] += 1
    new_item["Image_List"] = il
    new_item["Local_Thumbnail"] = il[0] if il else ""

    cat.append(new_item)
    stats["added"] += 1
    print(f"  new [{n}/{len(new_pns)}] {pn} -> {len(il)} images", flush=True)

# --- Retry failures ------------------------------------------------------
if stats["failed"]:
    print("\nRetrying failures sequentially (1.5s delay)...", flush=True)
    retry_ok = 0
    touched_pns = set(refresh_pns) | set(new_pns)
    for item in cat:
        if item.get("Part Number") not in touched_pns:
            continue
        if len(item.get("Image_List", [])) >= 5:
            continue
        wf_urls = [item[c] for c in WF_COLS if item.get(c)]
        have = set(os.path.basename(x) for x in item.get("Image_List", []))
        needed = [u for u in wf_urls if hashlib.md5(u.encode()).hexdigest() + ".jpg" not in have]
        slots = 5 - len(item.get("Image_List", []))
        il = item.get("Image_List", [])
        for url in needed[:slots]:
            time.sleep(1.5)
            fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
            fpath = os.path.join(THUMB_DIR, fname)
            try:
                raw = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
                r = requests.get(raw, timeout=30)
                ct = r.headers.get("Content-Type", "")
                if r.status_code == 200 and "image" in ct:
                    img = Image.open(BytesIO(r.content))
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    img.thumbnail(THUMBNAIL_SIZE)
                    img.save(fpath, "JPEG", quality=85)
                    il.append(f"thumbnails/{fname}")
                    retry_ok += 1
            except Exception:
                pass
        item["Image_List"] = il
        item["Local_Thumbnail"] = il[0] if il else ""
    print(f"  Retried, succeeded {retry_ok}", flush=True)

# --- Backup + write -------------------------------------------------------
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{CAT_PATH}.backup_{ts}"
shutil.copy(CAT_PATH, backup_path)
print(f"\nBackup: {backup_path}", flush=True)

with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

print(f"\nDone:")
print(f"  New items added:      {stats['added']}")
print(f"  Existing items refreshed: {len(refresh_pns)}")
print(f"  Thumbnail files deleted:  {stats['deleted_files']}")
print(f"  Thumbnail files kept (shared): {stats['kept_shared']}")
print(f"  Thumbnails downloaded:    {stats['downloaded']}")
print(f"  Downloads failed:         {stats['failed']}")
print(f"  Final catalogue size:     {len(cat)}")

touched_pns = set(refresh_pns) | set(new_pns)
dist = Counter(len(item.get("Image_List", [])) for item in cat if item.get("Part Number") in touched_pns)
print("Touched items Image_List distribution:")
for k in sorted(dist): print(f"  {k} images: {dist[k]}")
