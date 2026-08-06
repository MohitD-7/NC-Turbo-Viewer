"""
remove_duplicate_4c2ls_clc.py
Remove the stale duplicate catalogue entry for "NC6400-DG-713-4C2LS-CLC "
(trailing space in Part Number) -- a leftover pre-fix row with the old
8-image data (including the erroneous duplicate "_1" image) that the
Aug 06 sync never touched because it keyed on the exact, unpadded Part
Number. The correct entry (no trailing space, WF=7, fresh Wayfair
thumbnails) already exists elsewhere in the catalogue.
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

STALE_PN = "NC6400-DG-713-4C2LS-CLC "
CORRECT_PN = "NC6400-DG-713-4C2LS-CLC"

stale_idx = next((idx for idx, i in enumerate(cat) if i.get("Part Number") == STALE_PN), None)
correct_item = next((i for i in cat if i.get("Part Number") == CORRECT_PN), None)

if stale_idx is None:
    raise SystemExit("Stale entry not found -- aborting, nothing to do.")
if correct_item is None:
    raise SystemExit("Correct entry not found -- aborting, refusing to delete the only copy.")

stale_item = cat[stale_idx]
stale_thumbs = set(stale_item.get("Image_List", []))
correct_thumbs = set(correct_item.get("Image_List", []))

# Only delete thumbnail files not referenced by ANY other catalogue entry
other_referenced = set()
for i in cat:
    if i is stale_item:
        continue
    other_referenced.update(i.get("Image_List", []))

to_delete_files = stale_thumbs - other_referenced
kept_shared = stale_thumbs & other_referenced

print(f"Stale entry Image_List: {sorted(stale_thumbs)}")
print(f"Correct entry Image_List: {sorted(correct_thumbs)}")
print(f"Thumbnail files safe to delete (not referenced elsewhere): {sorted(to_delete_files)}")
print(f"Thumbnail files kept (referenced by other entries): {sorted(kept_shared)}")

deleted = 0
for t in to_delete_files:
    fpath = os.path.join(THUMB_DIR, t.replace("thumbnails/", ""))
    if os.path.exists(fpath):
        os.remove(fpath)
        deleted += 1

del cat[stale_idx]

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{CATALOGUE_PATH}.backup_{ts}"
shutil.copy(CATALOGUE_PATH, backup_path)
print(f"\nBackup: {backup_path}", flush=True)

with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

print(f"\nDone: removed stale duplicate entry, deleted {deleted} orphaned thumbnail file(s).")
print(f"Final catalogue size: {len(cat)}")
