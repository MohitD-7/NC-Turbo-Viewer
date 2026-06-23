"""
apply_jun22.py
Three refresh operations:
  A. Accent Pillow CUSHTH14/16/18/20/24 — sync URLs from Jun 22 AP Excel,
     archive current thumbnails, re-download (Wayfair priority, max 5).
  B. Furniture 2001A (all 48 products) — sync URLs from Jun 22 Furniture
     Excel, archive thumbnails, re-download.
  C. Furniture 2676 - DG — for each filename in the user-provided list,
     locate the corresponding URL in the catalogue, archive that
     specific cached thumbnail, re-download from the same URL.
"""

import json, os, re, hashlib, shutil, requests, threading, time, openpyxl
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

BASE_DIR  = "c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer"
CAT_PATH  = os.path.join(BASE_DIR, "data/catalogue.json")
THUMB_DIR = os.path.join(BASE_DIR, "static/thumbnails")
ARCHIVE   = r"C:\Users\Lenovo\Downloads\NC - Library Naming\archived_thumbnails_jun22"
AP_EXCEL  = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Accent Pillow - Jun 22, 2026.xlsx"
FUR_EXCEL = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Jun 22, 2026.xlsx"

WORKERS = 10
DELAY   = 0.5
THUMBNAIL_SIZE = (400, 400)

os.makedirs(ARCHIVE, exist_ok=True)
_lock = threading.Lock()
_stats = {"archived": 0, "downloaded": 0, "failed": 0, "urls_synced": 0}

WF_COLS  = [f"Wayfair Image {i}"   for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = WF_COLS + BY_COLS + NC_COLS + HD_COLS

# --- The 2676-DG image filenames the user said were replaced -----------------
REPLACED_2676 = """
NC2676-DG-304-13S1LS-CAL_2.jpg NC2676-DG-304-13S1LS-BK_2.jpg
NC2676-DG-304-13S1LS-CFN_1.jpg NC2676-DG-304-13S1LS-CFN_2.jpg NC2676-DG-304-13S1LS-CFN_3.jpg
NC2676-DG-304-13S1LS-CFN_4.jpg NC2676-DG-304-13S1LS-CFN_5.jpg NC2676-DG-304-13S1LS-CFN_6.jpg
NC2676-DG-304-13S1LS-CFN_7.jpg NC2676-DG-304-13S1LS-CG_2.jpg
NC2676-DG-304-13S1LS-HE_1.jpg NC2676-DG-304-13S1LS-HE_2.jpg NC2676-DG-304-13S1LS-HE_3.jpg
NC2676-DG-304-13S1LS-HE_4.jpg NC2676-DG-304-13S1LS-HE_5.jpg NC2676-DG-304-13S1LS-HE_6.jpg
NC2676-DG-304-13S1LS-HE_7.jpg
NC2676-DG-304-13S1LS-CN_1.jpg NC2676-DG-304-13S1LS-CN_2.jpg NC2676-DG-304-13S1LS-CN_3.jpg
NC2676-DG-304-13S1LS-CN_4.jpg NC2676-DG-304-13S1LS-CN_5.jpg NC2676-DG-304-13S1LS-CN_6.jpg
NC2676-DG-304-13S1LS-CN_7.jpg
NC2676-DG-304-13S1LS-CV_2.jpg NC2676-DG-304-13S1LS-SV_2.jpg
NC2676-DG-304-13S1LS-CLC_2.jpg NC2676-DG-304-13S1LS-RHA_2.jpg NC2676-DG-304-13S1LS-SR_2.jpg
NC2676-DG-304-2C13S-CAL_2.jpg NC2676-DG-304-2C13S-BK_2.jpg
NC2676-DG-304-2C13S-CFN_1.jpg NC2676-DG-304-2C13S-CFN_2.jpg NC2676-DG-304-2C13S-CFN_3.jpg
NC2676-DG-304-2C13S-CFN_4.jpg NC2676-DG-304-2C13S-CFN_5.jpg NC2676-DG-304-2C13S-CFN_6.jpg
NC2676-DG-304-2C13S-CFN_7.jpg NC2676-DG-304-2C13S-CFN_8.jpg NC2676-DG-304-2C13S-CG_2.jpg
NC2676-DG-304-2C13S-HE_1.jpg NC2676-DG-304-2C13S-HE_2.jpg NC2676-DG-304-2C13S-HE_3.jpg
NC2676-DG-304-2C13S-HE_4.jpg NC2676-DG-304-2C13S-HE_5.jpg NC2676-DG-304-2C13S-HE_6.jpg
NC2676-DG-304-2C13S-HE_7.jpg
NC2676-DG-304-2C13S-CN_1.jpg NC2676-DG-304-2C13S-CN_2.jpg NC2676-DG-304-2C13S-CN_3.jpg
NC2676-DG-304-2C13S-CN_4.jpg NC2676-DG-304-2C13S-CN_5.jpg NC2676-DG-304-2C13S-CN_6.jpg
NC2676-DG-304-2C13S-CN_7.jpg
NC2676-DG-304-2C13S-CV_2.jpg NC2676-DG-304-2C13S-SV_2.jpg NC2676-DG-304-2C13S-CLC_2.jpg
NC2676-DG-304-2C13S-RHA_2.jpg NC2676-DG-304-2C13S-SR_2.jpg
NC2676-DG-304-2C13S1LS-CAL_2.jpg NC2676-DG-304-2C13S1LS-BK_2.jpg
NC2676-DG-304-2C13S1LS-CFN_1.jpg NC2676-DG-304-2C13S1LS-CFN_2.jpg NC2676-DG-304-2C13S1LS-CFN_3.jpg
NC2676-DG-304-2C13S1LS-CFN_4.jpg NC2676-DG-304-2C13S1LS-CFN_5.jpg NC2676-DG-304-2C13S1LS-CFN_6.jpg
NC2676-DG-304-2C13S1LS-CFN_7.jpg NC2676-DG-304-2C13S1LS-CFN_8.jpg NC2676-DG-304-2C13S1LS-CG_2.jpg
NC2676-DG-304-2C13S1LS-HE_1.jpg NC2676-DG-304-2C13S1LS-HE_2.jpg NC2676-DG-304-2C13S1LS-HE_3.jpg
NC2676-DG-304-2C13S1LS-HE_4.jpg NC2676-DG-304-2C13S1LS-HE_5.jpg NC2676-DG-304-2C13S1LS-HE_6.jpg
NC2676-DG-304-2C13S1LS-HE_7.jpg NC2676-DG-304-2C13S1LS-HE_8.jpg
NC2676-DG-304-2C13S1LS-CN_1.jpg NC2676-DG-304-2C13S1LS-CN_2.jpg NC2676-DG-304-2C13S1LS-CN_3.jpg
NC2676-DG-304-2C13S1LS-CN_4.jpg NC2676-DG-304-2C13S1LS-CN_5.jpg NC2676-DG-304-2C13S1LS-CN_6.jpg
NC2676-DG-304-2C13S1LS-CN_7.jpg NC2676-DG-304-2C13S1LS-CN_8.jpg
NC2676-DG-304-2C13S1LS-CV_2.jpg NC2676-DG-304-2C13S1LS-SV_2.jpg
NC2676-DG-304-2C13S1LS-CLC_2.jpg NC2676-DG-304-2C13S1LS-RHA_2.jpg NC2676-DG-304-2C13S1LS-SR_2.jpg
NC2676-DG-304-2C1LS-CAL_2.jpg NC2676-DG-304-2C1LS-BK_2.jpg
NC2676-DG-304-2C1LS-CFN_1.jpg NC2676-DG-304-2C1LS-CFN_2.jpg NC2676-DG-304-2C1LS-CFN_3.jpg
NC2676-DG-304-2C1LS-CFN_4.jpg NC2676-DG-304-2C1LS-CFN_5.jpg NC2676-DG-304-2C1LS-CFN_6.jpg
NC2676-DG-304-2C1LS-CFN_7.jpg NC2676-DG-304-2C1LS-CG_2.jpg
NC2676-DG-304-2C1LS-HE_1.jpg NC2676-DG-304-2C1LS-HE_2.jpg NC2676-DG-304-2C1LS-HE_3.jpg
NC2676-DG-304-2C1LS-HE_4.jpg NC2676-DG-304-2C1LS-HE_5.jpg NC2676-DG-304-2C1LS-HE_6.jpg
NC2676-DG-304-2C1LS-HE_7.jpg
NC2676-DG-304-2C1LS-CN_1.jpg NC2676-DG-304-2C1LS-CN_2.jpg NC2676-DG-304-2C1LS-CN_3.jpg
NC2676-DG-304-2C1LS-CN_4.jpg NC2676-DG-304-2C1LS-CN_5.jpg NC2676-DG-304-2C1LS-CN_6.jpg
NC2676-DG-304-2C1LS-CN_7.jpg
NC2676-DG-304-2C1LS-CV_2.jpg NC2676-DG-304-2C1LS-SV_2.jpg NC2676-DG-304-2C1LS-CLC_2.jpg
NC2676-DG-304-2C1LS-RHA_2.jpg NC2676-DG-304-2C1LS-SR_2.jpg
NC2676-DG-304-2SR13S-CAL_2.jpg NC2676-DG-304-2SR13S-BK_2.jpg
NC2676-DG-304-2SR13S-CFN_1.jpg NC2676-DG-304-2SR13S-CFN_2.jpg NC2676-DG-304-2SR13S-CFN_3.jpg
NC2676-DG-304-2SR13S-CFN_4.jpg NC2676-DG-304-2SR13S-CFN_5.jpg NC2676-DG-304-2SR13S-CFN_6.jpg
NC2676-DG-304-2SR13S-CFN_7.jpg NC2676-DG-304-2SR13S-CG_2.jpg
NC2676-DG-304-2SR13S-HE_1.jpg NC2676-DG-304-2SR13S-HE_2.jpg NC2676-DG-304-2SR13S-HE_3.jpg
NC2676-DG-304-2SR13S-HE_4.jpg NC2676-DG-304-2SR13S-HE_5.jpg NC2676-DG-304-2SR13S-HE_6.jpg
NC2676-DG-304-2SR13S-HE_7.jpg
NC2676-DG-304-2SR13S-CN_1.jpg NC2676-DG-304-2SR13S-CN_2.jpg NC2676-DG-304-2SR13S-CN_3.jpg
NC2676-DG-304-2SR13S-CN_4.jpg NC2676-DG-304-2SR13S-CN_5.jpg NC2676-DG-304-2SR13S-CN_6.jpg
NC2676-DG-304-2SR13S-CN_7.jpg
NC2676-DG-304-2SR13S-CV_2.jpg NC2676-DG-304-2SR13S-SV_2.jpg
NC2676-DG-304-2SR13S-CLC_2.jpg NC2676-DG-304-2SR13S-RHA_2.jpg NC2676-DG-304-2SR13S-SR_2.jpg
NC2676-DG-304-2SR1LS-CAL_2.jpg NC2676-DG-304-2SR1LS-BK_2.jpg
NC2676-DG-304-2SR1LS-CFN_1.jpg NC2676-DG-304-2SR1LS-CFN_2.jpg NC2676-DG-304-2SR1LS-CFN_3.jpg
NC2676-DG-304-2SR1LS-CFN_4.jpg NC2676-DG-304-2SR1LS-CFN_5.jpg NC2676-DG-304-2SR1LS-CFN_6.jpg
NC2676-DG-304-2SR1LS-CFN_7.jpg NC2676-DG-304-2SR1LS-CG_2.jpg
NC2676-DG-304-2SR1LS-HE_1.jpg NC2676-DG-304-2SR1LS-HE_2.jpg NC2676-DG-304-2SR1LS-HE_3.jpg
NC2676-DG-304-2SR1LS-HE_4.jpg NC2676-DG-304-2SR1LS-HE_5.jpg NC2676-DG-304-2SR1LS-HE_6.jpg
NC2676-DG-304-2SR1LS-HE_7.jpg
NC2676-DG-304-2SR1LS-CN_1.jpg NC2676-DG-304-2SR1LS-CN_2.jpg NC2676-DG-304-2SR1LS-CN_3.jpg
NC2676-DG-304-2SR1LS-CN_4.jpg NC2676-DG-304-2SR1LS-CN_5.jpg NC2676-DG-304-2SR1LS-CN_6.jpg
NC2676-DG-304-2SR1LS-CN_7.jpg
NC2676-DG-304-2SR1LS-CV_2.jpg NC2676-DG-304-2SR1LS-SV_2.jpg
NC2676-DG-304-2SR1LS-CLC_2.jpg NC2676-DG-304-2SR1LS-RHA_2.jpg NC2676-DG-304-2SR1LS-SR_2.jpg
NC2676-DG-304-4C2LS-CAL_2.jpg NC2676-DG-304-4C2LS-BK_2.jpg
NC2676-DG-304-4C2LS-CFN_1.jpg NC2676-DG-304-4C2LS-CFN_2.jpg NC2676-DG-304-4C2LS-CFN_3.jpg
NC2676-DG-304-4C2LS-CFN_4.jpg NC2676-DG-304-4C2LS-CFN_5.jpg NC2676-DG-304-4C2LS-CFN_6.jpg
NC2676-DG-304-4C2LS-CFN_7.jpg NC2676-DG-304-4C2LS-CG_2.jpg
NC2676-DG-304-4C2LS-HE_1.jpg NC2676-DG-304-4C2LS-HE_2.jpg NC2676-DG-304-4C2LS-HE_3.jpg
NC2676-DG-304-4C2LS-HE_4.jpg NC2676-DG-304-4C2LS-HE_5.jpg NC2676-DG-304-4C2LS-HE_6.jpg
NC2676-DG-304-4C2LS-HE_7.jpg
NC2676-DG-304-4C2LS-CN_1.jpg NC2676-DG-304-4C2LS-CN_2.jpg NC2676-DG-304-4C2LS-CN_3.jpg
NC2676-DG-304-4C2LS-CN_4.jpg NC2676-DG-304-4C2LS-CN_5.jpg NC2676-DG-304-4C2LS-CN_6.jpg
NC2676-DG-304-4C2LS-CN_7.jpg
NC2676-DG-304-4C2LS-CV_2.jpg NC2676-DG-304-4C2LS-SV_2.jpg
NC2676-DG-304-4C2LS-CLC_2.jpg NC2676-DG-304-4C2LS-RHA_2.jpg NC2676-DG-304-4C2LS-SR_2.jpg
NC2676-DG-304-4SR2LS-CAL_2.jpg NC2676-DG-304-4SR2LS-BK_2.jpg
NC2676-DG-304-4SR2LS-CFN_1.jpg NC2676-DG-304-4SR2LS-CFN_2.jpg NC2676-DG-304-4SR2LS-CFN_3.jpg
NC2676-DG-304-4SR2LS-CFN_4.jpg NC2676-DG-304-4SR2LS-CFN_5.jpg NC2676-DG-304-4SR2LS-CFN_6.jpg
NC2676-DG-304-4SR2LS-CFN_7.jpg NC2676-DG-304-4SR2LS-CG_2.jpg
NC2676-DG-304-4SR2LS-HE_1.jpg NC2676-DG-304-4SR2LS-HE_2.jpg NC2676-DG-304-4SR2LS-HE_3.jpg
NC2676-DG-304-4SR2LS-HE_4.jpg NC2676-DG-304-4SR2LS-HE_5.jpg NC2676-DG-304-4SR2LS-HE_6.jpg
NC2676-DG-304-4SR2LS-HE_7.jpg
NC2676-DG-304-4SR2LS-CN_1.jpg NC2676-DG-304-4SR2LS-CN_2.jpg NC2676-DG-304-4SR2LS-CN_3.jpg
NC2676-DG-304-4SR2LS-CN_4.jpg NC2676-DG-304-4SR2LS-CN_5.jpg NC2676-DG-304-4SR2LS-CN_6.jpg
NC2676-DG-304-4SR2LS-CN_7.jpg
NC2676-DG-304-4SR2LS-CV_2.jpg NC2676-DG-304-4SR2LS-SV_2.jpg
NC2676-DG-304-4SR2LS-CLC_2.jpg NC2676-DG-304-4SR2LS-RHA_2.jpg NC2676-DG-304-4SR2LS-SR_2.jpg
""".split()

# Parse into (PN, image_number) tuples
REPLACED_2676_PARSED = []
for fname in REPLACED_2676:
    m = re.match(r'(NC2676-DG-\S+?)_(\d+)\.jpg', fname)
    if m:
        REPLACED_2676_PARSED.append((m.group(1), int(m.group(2))))


# ─── Helpers ──────────────────────────────────────────────────────────────────
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
        r = requests.get(raw, timeout=30)
        ct = r.headers.get("Content-Type", "")
        if r.status_code == 200 and "image" in ct:
            img = Image.open(BytesIO(r.content))
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


# ─── Read Excel files ─────────────────────────────────────────────────────────
def read_excel(path, sheet_filter=None):
    """Returns {pn: row_dict}"""
    wb = openpyxl.load_workbook(path)
    out = {}
    for sheet in wb.sheetnames:
        if sheet_filter and not sheet_filter(sheet): continue
        ws = wb[sheet]
        headers = [c.value for c in ws[1]]
        if "Part Number" not in headers: continue
        pn_col = headers.index("Part Number") + 1
        for row in ws.iter_rows(min_row=2):
            pn = row[pn_col - 1].value
            if not pn: continue
            out[pn.strip()] = {headers[i]: (row[i].value if i < len(row) else None) for i in range(len(headers))}
    return out

print("Reading Jun 22 Accent Pillow Excel...", flush=True)
ap_excel = read_excel(AP_EXCEL)
print(f"  AP Excel: {len(ap_excel)} products", flush=True)

print("Reading Jun 22 Furniture Excel...", flush=True)
fur_excel = read_excel(FUR_EXCEL)
print(f"  Furniture Excel: {len(fur_excel)} products", flush=True)


# ─── Build a refresh-product function ─────────────────────────────────────────
def sync_and_refresh(args):
    """Sync URL fields from Excel, archive all thumbnails, re-download top 5."""
    idx, pn, exc = args
    p = data[idx]

    # Sync URL columns from Excel (if Excel row provided)
    if exc:
        for col in ALL_COLS:
            v = (exc.get(col) or "")
            v = str(v).strip() if v else ""
            new_val = v if v.startswith("http") else ""
            if (p.get(col) or "") != new_val:
                p[col] = new_val
                with _lock: _stats["urls_synced"] += 1
        # Sync Color / Color_Link
        color_field = next((k for k in ("Color", "Cushion Color") if k in exc), None)
        if color_field:
            cn, cl = parse_color(exc.get(color_field))
            if cn: p["Color"] = cn
            if cl: p["Color_Link"] = cl
        if exc.get("Last Modified"):
            p["Last Modified"] = str(exc["Last Modified"])
        for f in ("NC Image Count", "BY Image Count", "WF Image Count", "HD Image Count"):
            if f in exc and exc[f] is not None:
                try: p[f] = int(exc[f])
                except (ValueError, TypeError): pass

    # Archive all current thumbnails
    for path in p.get("Image_List", []):
        archive_thumb(os.path.basename(path))

    # Re-download
    urls = get_priority_urls(p)
    new_il = []
    for url in urls:
        r = download_thumb(url)
        if r: new_il.append(r)
    p["Image_List"] = new_il
    p["Local_Thumbnail"] = new_il[0] if new_il else ""
    return idx


# ─── Task A: Accent Pillow CUSHTH14/16/18/20/24 ──────────────────────────────
print("\n=== Task A: Accent Pillow CUSHTH14/16/18/20/24 ===", flush=True)
ap_prefixes = ("CUSHTH14", "CUSHTH16", "CUSHTH18", "CUSHTH20", "CUSHTH24")
ap_targets = []
for idx, p in enumerate(data):
    pn = p.get("Part Number", "")
    if pn.startswith(ap_prefixes):
        ap_targets.append((idx, pn, ap_excel.get(pn)))
print(f"Accent Pillow targets: {len(ap_targets)} products", flush=True)

done_a = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(sync_and_refresh, t): t[1] for t in ap_targets}
    for fut in as_completed(futs):
        fut.result()
        done_a += 1
        if done_a % 20 == 0:
            print(f"  [A {done_a}/{len(ap_targets)}] archived={_stats['archived']} dl={_stats['downloaded']} fail={_stats['failed']}", flush=True)
print(f"Task A done: {done_a} products", flush=True)


# ─── Task B: Furniture 2001A ──────────────────────────────────────────────────
print("\n=== Task B: Furniture 2001A ===", flush=True)
b_targets = []
for idx, p in enumerate(data):
    if p.get("Collection", "") == "2001A" or p.get("Part Number", "").startswith("NC2001A"):
        b_targets.append((idx, p["Part Number"], fur_excel.get(p["Part Number"])))
print(f"2001A targets: {len(b_targets)} products", flush=True)

done_b = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(sync_and_refresh, t): t[1] for t in b_targets}
    for fut in as_completed(futs):
        fut.result()
        done_b += 1
        if done_b % 10 == 0:
            print(f"  [B {done_b}/{len(b_targets)}] archived={_stats['archived']} dl={_stats['downloaded']} fail={_stats['failed']}", flush=True)
print(f"Task B done: {done_b} products", flush=True)


# ─── Task C: Furniture 2676 - DG specific filenames ───────────────────────────
print("\n=== Task C: Furniture 2676-DG (specific filenames) ===", flush=True)
print(f"Filenames specified: {len(REPLACED_2676)} | parsed: {len(REPLACED_2676_PARSED)}", flush=True)

# First sync URL columns for affected products from Excel (in case Excel has updates too)
affected_pns_2676 = sorted({pn for pn, _ in REPLACED_2676_PARSED})
print(f"Distinct PNs in 2676 list: {len(affected_pns_2676)}", flush=True)

for pn in affected_pns_2676:
    idx = cat_map.get(pn)
    if idx is None: continue
    exc = fur_excel.get(pn)
    if not exc: continue
    p = data[idx]
    # Sync URL columns
    for col in ALL_COLS:
        v = (exc.get(col) or "")
        v = str(v).strip() if v else ""
        new_val = v if v.startswith("http") else ""
        if (p.get(col) or "") != new_val:
            p[col] = new_val
            _stats["urls_synced"] += 1
    if exc.get("Last Modified"):
        p["Last Modified"] = str(exc["Last Modified"])

# Build refresh jobs: for each (PN, image_number), find the URL ending with PN_N.jpg
# in any of the product's image columns and archive + re-download that thumbnail.
def refresh_one_image(args):
    pn, img_num = args
    idx = cat_map.get(pn)
    if idx is None:
        return ("no_pn", pn, img_num)
    p = data[idx]
    needle = f"{pn}_{img_num}.jpg"
    found_url = None
    found_col = None
    for col in ALL_COLS:
        v = (p.get(col) or "").strip()
        if not v.startswith("http"): continue
        url_filename = v.split("/")[-1].split("?")[0]
        if url_filename == needle:
            found_url = v
            found_col = col
            break
    if not found_url:
        return ("no_url", pn, img_num)

    # Archive and re-download
    fname = hashlib.md5(found_url.encode()).hexdigest() + ".jpg"
    archive_thumb(fname)
    # Force fresh download (the archive above removed it from disk)
    r = download_thumb(found_url)
    return ("ok", pn, img_num) if r else ("dl_fail", pn, img_num)

results_c = Counter()
done_c = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(refresh_one_image, t): t for t in REPLACED_2676_PARSED}
    for fut in as_completed(futs):
        status, pn, img_num = fut.result()
        results_c[status] += 1
        done_c += 1
        if done_c % 50 == 0:
            print(f"  [C {done_c}/{len(REPLACED_2676_PARSED)}] {dict(results_c)} | archived={_stats['archived']} dl={_stats['downloaded']}", flush=True)

print(f"Task C done: ok={results_c['ok']} no_pn={results_c['no_pn']} no_url={results_c['no_url']} dl_fail={results_c['dl_fail']}", flush=True)

# Show samples of products not found / URLs not matched
def show_samples():
    no_pn_list, no_url_list = [], []
    for pn, n in REPLACED_2676_PARSED:
        if pn not in cat_map:
            no_pn_list.append((pn, n))
            continue
        p = data[cat_map[pn]]
        needle = f"{pn}_{n}.jpg"
        found = False
        for col in ALL_COLS:
            v = (p.get(col) or "").strip()
            if v.startswith("http") and v.split("/")[-1].split("?")[0] == needle:
                found = True; break
        if not found:
            no_url_list.append((pn, n))
    if no_pn_list:
        print(f"\nProducts not in catalogue (sample): {no_pn_list[:5]}", flush=True)
    if no_url_list:
        print(f"URLs not found for these (sample): {no_url_list[:5]}", flush=True)

show_samples()


# ─── Rebuild Image_List for 2676-DG affected products to ensure correct order ─
# (URLs may have shifted positions if Excel changed; rebuild from priority order.)
print("\n=== Rebuilding Image_List for 2676-DG products ===", flush=True)
rebuilt = 0
for pn in affected_pns_2676:
    idx = cat_map.get(pn)
    if idx is None: continue
    p = data[idx]
    urls = get_priority_urls(p)
    new_il = []
    for url in urls:
        fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
        if os.path.exists(os.path.join(THUMB_DIR, fname)):
            new_il.append(f"thumbnails/{fname}")
        else:
            r = download_thumb(url)
            if r: new_il.append(r)
    if new_il != p.get("Image_List"):
        p["Image_List"] = new_il
        p["Local_Thumbnail"] = new_il[0] if new_il else ""
        rebuilt += 1
print(f"  Image_List rebuilt for: {rebuilt} products", flush=True)


# ─── Save catalogue ──────────────────────────────────────────────────────────
print("\nSaving catalogue.json...", flush=True)
with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# ─── Final report ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print(f"  URLs synced from Excel:      {_stats['urls_synced']}")
print(f"  Thumbnails archived:         {_stats['archived']}")
print(f"  Thumbnails downloaded:       {_stats['downloaded']}")
print(f"  Download failures:           {_stats['failed']}")
print()
print(f"  Task A — Accent Pillow products:    {done_a}")
print(f"  Task B — 2001A products:            {done_b}")
print(f"  Task C — 2676-DG image positions:")
print(f"      successful refreshes:           {results_c['ok']}")
print(f"      no matching PN:                 {results_c['no_pn']}")
print(f"      no matching URL:                {results_c['no_url']}")
print(f"      download failed:                {results_c['dl_fail']}")
print(f"  2676-DG products rebuilt:           {rebuilt}")

print(f"\nArchive: {ARCHIVE}")
