"""
add_new_2001a.py
Add the 90 new 2001A products from Jun 22 Furniture Excel.
Downloads up to 5 thumbnails each, Wayfair priority.
"""

import json, os, re, hashlib, requests, time, openpyxl
from io import BytesIO
from PIL import Image
from collections import Counter

BASE_DIR  = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH  = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR = os.path.join(BASE_DIR, "static/thumbnails")
FUR_EXCEL = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Jun 22, 2026.xlsx"
THUMBNAIL_SIZE = (400, 400)
DELAY = 0.8

WF_COLS  = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = WF_COLS + BY_COLS + NC_COLS + HD_COLS

stats = {"added": 0, "downloaded": 0, "failed": 0}

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

def download_thumb(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    dest  = os.path.join(THUMB_DIR, fname)
    if os.path.exists(dest):
        return f"thumbnails/{fname}"
    time.sleep(DELAY)
    try:
        raw  = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
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
    data = json.load(f)
cat_pns = {p["Part Number"] for p in data}
print(f"Catalogue: {len(data)} products", flush=True)

print("Reading Jun 22 Furniture Excel (2001A sheet)...", flush=True)
wb = openpyxl.load_workbook(FUR_EXCEL)
excel_2001a = {}
for sheet in wb.sheetnames:
    if "2001A" not in sheet: continue
    ws = wb[sheet]
    headers = [c.value for c in ws[1]]
    if "Part Number" not in headers: continue
    pn_col = headers.index("Part Number") + 1
    for row in ws.iter_rows(min_row=2):
        pn = row[pn_col - 1].value
        if not pn: continue
        excel_2001a[pn.strip()] = {headers[i]: (row[i].value if i < len(row) else None) for i in range(len(headers))}
print(f"  Excel 2001A: {len(excel_2001a)}", flush=True)

missing = sorted(set(excel_2001a.keys()) - cat_pns)
print(f"Missing 2001A in catalogue: {len(missing)}", flush=True)

for n, pn in enumerate(missing, 1):
    exc = excel_2001a[pn]
    cn, cl = parse_color(exc.get("Color"))
    new_p = {
        "Part Number":         pn,
        "Collection":          exc.get("Collection") or "2001A",
        "Collection Type":     exc.get("Collection") or "2001A",
        "Category":            "Furniture",
        "Type":                exc.get("Type") or "Furniture",
        "Color":               cn or "",
        "Color_Link":          cl or "",
        "Product":             exc.get("Product") or "",
        "Arm/Table-Top":       exc.get("Arm/Table-Top") or "",
        "Panel":               exc.get("Panel") or "",
        "Dropbox Folder Path": exc.get("Dropbox Folder Path") or "",
        "Last Modified":       str(exc.get("Last Modified") or ""),
        "NC Image Count":      int(exc.get("NC Image Count") or 0),
        "BY Image Count":      int(exc.get("BY Image Count") or 0),
        "WF Image Count":      int(exc.get("WF Image Count") or 0),
        "HD Image Count":      int(exc.get("HD Image Count") or 0),
        "Image_List":          [],
        "Local_Thumbnail":     "",
    }
    for col in ALL_COLS:
        v = (exc.get(col) or "")
        v = str(v).strip() if v else ""
        new_p[col] = v if v.startswith("http") else ""

    # Derive Color from Dropbox path if missing
    if not new_p["Color"] and new_p["Dropbox Folder Path"]:
        derived = new_p["Dropbox Folder Path"].rstrip("/").split("/")[-1]
        if derived: new_p["Color"] = derived

    urls = get_priority_urls(new_p)
    il = []
    for url in urls:
        r = download_thumb(url)
        if r:
            il.append(r)
            stats["downloaded"] += 1
        else:
            stats["failed"] += 1
    new_p["Image_List"]      = il
    new_p["Local_Thumbnail"] = il[0] if il else ""
    data.append(new_p)
    stats["added"] += 1
    if n % 10 == 0:
        print(f"  [{n}/{len(missing)}] dl={stats['downloaded']} fail={stats['failed']}", flush=True)

# Retry failures sequentially with longer delay
print("\nRetrying failures sequentially (1.5s delay)...", flush=True)
retry_done = 0
retry_ok = 0
for p in data:
    if p.get("Part Number") not in missing: continue
    il = p.get("Image_List", [])
    if len(il) >= 5: continue
    have = set(os.path.basename(x) for x in il)
    urls = get_priority_urls(p)
    needed = [u for u in urls if hashlib.md5(u.encode()).hexdigest()+".jpg" not in have]
    slots = 5 - len(il)
    for url in needed[:slots]:
        time.sleep(1.5)
        # Don't use download_thumb's delay; just call it
        fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
        fpath = os.path.join(THUMB_DIR, fname)
        try:
            raw = url.replace("dl=0","raw=1").replace("dl=1","raw=1")
            r = requests.get(raw, timeout=30)
            ct = r.headers.get("Content-Type", "")
            if r.status_code == 200 and "image" in ct:
                img = Image.open(BytesIO(r.content))
                if img.mode in ("RGBA","P"): img = img.convert("RGB")
                img.thumbnail(THUMBNAIL_SIZE)
                img.save(fpath, "JPEG", quality=85)
                il.append(f"thumbnails/{fname}")
                retry_ok += 1
        except Exception:
            pass
        retry_done += 1
    p["Image_List"] = il[:5]
    p["Local_Thumbnail"] = il[0] if il else ""

if retry_done:
    print(f"  Retried {retry_done}, succeeded {retry_ok}", flush=True)

with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nDone:")
print(f"  Added:       {stats['added']} new 2001A products")
print(f"  Downloaded:  {stats['downloaded']} thumbnails (initial)")
print(f"  Retry ok:    {retry_ok}")
print(f"  Final catalogue size: {len(data)}")
dist = Counter(len(p.get("Image_List", [])) for p in data)
print("Image_List distribution:")
for k in sorted(dist): print(f"  {k} images: {dist[k]}")
