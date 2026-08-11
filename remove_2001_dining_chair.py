"""
remove_2001_dining_chair.py
Remove all "Dining Chair" items from the 2001 collection -- the user
deleted and is re-uploading all color folders under
/Master Image Library/Furniture/2001/Dining Chair/ with a new set of
colors (some old, some brand new). This clears out the stale entries
and their thumbnails so the new data can be added cleanly afterward.
"""

import json
import os
import shutil
from datetime import datetime

CATALOGUE_PATH = "data/catalogue.json"
THUMB_DIR = "static/thumbnails"

print("Loading catalogue...", flush=True)
with open(CATALOGUE_PATH, encoding="utf-8") as f:
    cat = json.load(f)
print(f"Catalogue: {len(cat)} items", flush=True)

dc_items = [i for i in cat if i.get("Collection") == "2001" and i.get("Product") == "Dining Chair"]
dc_thumbs = set()
for i in dc_items:
    dc_thumbs.update(i.get("Image_List", []))

other_referenced = set()
for i in cat:
    if i in dc_items:
        continue
    other_referenced.update(i.get("Image_List", []))

to_delete_files = dc_thumbs - other_referenced
kept_shared = dc_thumbs & other_referenced

print(f"Dining Chair items to remove: {len(dc_items)}")
for i in dc_items:
    print(f"  {i.get('Part Number')} ({i.get('Color')})")
print(f"Thumbnail files to delete: {len(to_delete_files)}")
print(f"Thumbnail files kept (shared elsewhere): {len(kept_shared)}")

deleted = 0
for t in to_delete_files:
    fpath = os.path.join(THUMB_DIR, t.replace("thumbnails/", ""))
    if os.path.exists(fpath):
        os.remove(fpath)
        deleted += 1

new_cat = [i for i in cat if not (i.get("Collection") == "2001" and i.get("Product") == "Dining Chair")]

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{CATALOGUE_PATH}.backup_{ts}"
shutil.copy(CATALOGUE_PATH, backup_path)
print(f"\nBackup: {backup_path}", flush=True)

with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
    json.dump(new_cat, f, indent=2, ensure_ascii=False)

print(f"\nDone: removed {len(dc_items)} Dining Chair entries, deleted {deleted} thumbnail file(s).")
print(f"Final catalogue size: {len(new_cat)}")
