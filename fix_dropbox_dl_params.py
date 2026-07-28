"""
fix_dropbox_dl_params.py
Fix Dropbox URLs missing a dl= query parameter.
Appends "?dl=1" only to URLs with no query string at all, and "&dl=1" to
URLs that already have a query string (e.g. "...?rlkey=xxx") but no dl
param. Uses proper query-param parsing so URLs that already have dl=
embedded (as "&dl=1" after other params) are correctly left alone.
"""

import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs

CATALOGUE_PATH = "data/catalogue.json"
NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
WF_COLS  = [f"Wayfair Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = NC_COLS + BY_COLS + WF_COLS + HD_COLS


def add_dl_param(url):
    if "dl" in parse_qs(urlparse(url).query):
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}dl=1"

print("Loading catalogue...", flush=True)
with open(CATALOGUE_PATH, encoding="utf-8") as f:
    cat = json.load(f)
print(f"Catalogue: {len(cat)} items", flush=True)

fixed_count = 0
stats = {"image_cols": 0, "color_links": 0}

for item in cat:
    # Fix image columns
    for col in ALL_COLS:
        url = item.get(col, "")
        if url and isinstance(url, str):
            url = url.strip()
            if url.startswith("https://www.dropbox.com/"):
                fixed = add_dl_param(url)
                if fixed != url:
                    item[col] = fixed
                    fixed_count += 1
                    stats["image_cols"] += 1

    # Fix Color_Link
    cl = item.get("Color_Link", "")
    if cl and isinstance(cl, str):
        cl = cl.strip()
        if cl.startswith("https://www.dropbox.com/"):
            fixed = add_dl_param(cl)
            if fixed != cl:
                item["Color_Link"] = fixed
                fixed_count += 1
                stats["color_links"] += 1

# Backup
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{CATALOGUE_PATH}.backup_{ts}"
import shutil
shutil.copy(CATALOGUE_PATH, backup_path)
print(f"Backup: {backup_path}", flush=True)

# Write fixed catalogue
with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

print(f"\nDone:")
print(f"  Fixed URLs: {fixed_count}")
print(f"    - Image columns: {stats['image_cols']}")
print(f"    - Color_Link: {stats['color_links']}")
