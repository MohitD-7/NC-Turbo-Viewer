"""
revert_bad_dl_fix.py
Undo the incorrect fix_dropbox_dl_params.py run, which appended a spurious
"?dl=1" to every Dropbox URL -- even ones that already had a valid "&dl=1"
inside their existing query string (e.g. "...?rlkey=xxx&dl=1"). That produced
invalid double-query-string URLs like "...&dl=1?dl=1", which Dropbox rejects.

Verified: every affected URL has exactly one erroneous "?dl=1" segment
appended after its original, valid query string. This strips that tail.
"""

import json
import shutil
from datetime import datetime

CATALOGUE_PATH = "data/catalogue.json"
NC_COLS  = [f"Northcape Image {i}" for i in range(1, 16)]
BY_COLS  = [f"Overstock Image {i}" for i in range(1, 16)]
WF_COLS  = [f"Wayfair Image {i}" for i in range(1, 16)]
HD_COLS  = [f"Home Depot Image {i}" for i in range(1, 16)]
ALL_COLS = NC_COLS + BY_COLS + WF_COLS + HD_COLS

print("Loading catalogue...", flush=True)
with open(CATALOGUE_PATH, encoding="utf-8") as f:
    cat = json.load(f)
print(f"Catalogue: {len(cat)} items", flush=True)

fixed_count = 0
unexpected = []

for item in cat:
    for col in ALL_COLS + ["Color_Link"]:
        url = item.get(col, "")
        if url and isinstance(url, str) and url.count("?") > 1:
            parts = url.split("?")
            tail = parts[2:]
            if tail != ["dl=1"] * len(tail):
                unexpected.append((item.get("Part Number"), col, url))
                continue
            item[col] = parts[0] + "?" + parts[1]
            fixed_count += 1

if unexpected:
    print(f"ABORTING: {len(unexpected)} URLs had an unexpected pattern, refusing to guess:")
    for pn, col, url in unexpected[:10]:
        print(f"  {pn} / {col}: {url}")
    raise SystemExit(1)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{CATALOGUE_PATH}.backup_{ts}"
shutil.copy(CATALOGUE_PATH, backup_path)
print(f"Backup: {backup_path}", flush=True)

with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

print(f"\nDone: reverted {fixed_count} corrupted URLs back to their valid form.")
