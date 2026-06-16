"""
fix_specific_products.py
For specific products:
  1. Pull fresh Color_Link from the Jun 09 Cushions Excel HYPERLINK formula
  2. Force-archive current thumbnails
  3. Re-download Image_List from Wayfair URLs (priority order, max 5)
"""

import json, os, hashlib, requests, time, shutil, openpyxl, re

BASE_DIR  = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH  = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE   = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_thumbnails_specific"
EXCEL     = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Cushions - Jun 09, 2026.xlsx"
THUMBNAIL_SIZE = (400, 400)

os.makedirs(ARCHIVE, exist_ok=True)

TARGETS = [
    'CUSH23253S-CN','CUSH25263S-CN','CUSH2613S-CN','CUSH300C-CN',
    'CUSH2325LS-CN','CUSH2526LS-CN','CUSH261LS-CN','CUSH270LS-CN',
    'CUSH271OR-RC','CUSH2119DC-CFN',
]

WF_COLS = [f"Wayfair Image {i}" for i in range(1, 16)]
BY_COLS = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS = [f"Northcape Image {i}" for i in range(1, 16)]

from PIL import Image
from io import BytesIO

def parse_hyperlink(val):
    if not isinstance(val, str): return None, None
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', val)
    if m: return m.group(2), m.group(1)  # (text, url)
    return (val.strip() or None, None)

def archive(fname):
    src = os.path.join(THUMB_DIR, fname)
    if os.path.exists(src):
        shutil.move(src, os.path.join(ARCHIVE, fname))
        return True
    return False

def download(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    dest  = os.path.join(THUMB_DIR, fname)
    if os.path.exists(dest):
        # Already cached but we want fresh — delete it
        archive(fname)
    try:
        raw  = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        r = requests.get(raw, timeout=30)
        if r.status_code == 200 and 'image' in r.headers.get('Content-Type',''):
            img = Image.open(BytesIO(r.content))
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(dest, "JPEG", quality=85)
            return f"thumbnails/{fname}"
        else:
            return None
    except Exception as e:
        print(f"    FAIL: {e}")
        return None

def priority_urls(p, limit=5):
    urls = []
    for cols in [WF_COLS, BY_COLS, NC_COLS]:
        for col in cols:
            v = (p.get(col) or "").strip()
            if v.startswith("http"): urls.append(v)
        if len(urls) >= limit: break
    return urls[:limit]

# 1. Read Excel and build PN -> (color_name, color_link)
print("Reading Excel for HYPERLINK formulas...")
wb = openpyxl.load_workbook(EXCEL)
excel_data = {}
for sheet in wb.sheetnames:
    ws = wb[sheet]
    headers = [c.value for c in ws[1]]
    if 'Part Number' not in headers: continue
    pn_col = headers.index('Part Number') + 1
    color_col = headers.index('Color') + 1 if 'Color' in headers else None
    for row in ws.iter_rows(min_row=2):
        pn = row[pn_col-1].value
        if not pn or pn.strip() not in TARGETS: continue
        cn, cl = parse_hyperlink(row[color_col-1].value if color_col else None)
        excel_data[pn.strip()] = {'color': cn, 'link': cl}

print(f"Found {len(excel_data)} in Excel")
for pn, d in excel_data.items():
    print(f"  {pn}: Color={d['color']}, Link={'YES' if d['link'] else 'NO'}")

# 2. Update catalogue
print("\nUpdating catalogue...")
with open(CAT_PATH, encoding='utf-8') as f:
    data = json.load(f)

# Apply user-provided override for CUSH2119DC-CFN Wayfair Image 1
USER_PROVIDED = {
    'CUSH2119DC-CFN': {
        'Wayfair Image 1': 'https://www.dropbox.com/scl/fi/1ymsao8yhyoholl76rwr8/CUSH2119DC-CFN_1.jpg?rlkey=eum8kea6xpus3hq1zfjvbwt92&st=id1cniic&dl=1',
    }
}

archived_count = 0
downloaded_count = 0
failed_count = 0

for pn in TARGETS:
    idx = None
    for i, p in enumerate(data):
        if p.get('Part Number') == pn:
            idx = i
            break
    if idx is None:
        print(f"  {pn}: NOT IN CATALOGUE")
        continue
    p = data[idx]

    # Update Color_Link from Excel if available
    exc = excel_data.get(pn)
    if exc and exc.get('link'):
        if p.get('Color_Link') != exc['link']:
            p['Color_Link'] = exc['link']
            print(f"  {pn}: Color_Link updated")
    if exc and exc.get('color'):
        if p.get('Color') != exc['color']:
            p['Color'] = exc['color']

    # Apply user-provided URL overrides
    if pn in USER_PROVIDED:
        for col, url in USER_PROVIDED[pn].items():
            p[col] = url
            print(f"  {pn}: {col} set to user-provided URL")

    # Archive existing thumbnails
    for path in p.get('Image_List', []):
        if archive(os.path.basename(path)):
            archived_count += 1

    # Re-download
    urls = priority_urls(p)
    new_il = []
    for url in urls:
        result = download(url)
        if result:
            new_il.append(result)
            downloaded_count += 1
        else:
            failed_count += 1

    p['Image_List']      = new_il
    p['Local_Thumbnail'] = new_il[0] if new_il else ""
    print(f"  {pn}: {len(new_il)}/{len(urls)} images downloaded")

with open(CAT_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nDone: {archived_count} archived | {downloaded_count} downloaded | {failed_count} failed")
