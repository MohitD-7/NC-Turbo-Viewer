"""
fix_2676_canvas_color_links.py
Populate the missing Color_Link (Dropbox folder link) for the 4 "Canvas"
colored 2676-DG Club Chair items. These use an older part-number format
(2676-001-9236-01-XX, no "DG-304" segment) that the original ingestion
never parsed a folder hyperlink for, unlike every other 2676-DG item.
The Excel's Color cell has the folder link as a HYPERLINK() formula;
this pulls it out and writes it into the catalogue.
"""

import json
import shutil
import openpyxl
from datetime import datetime

CATALOGUE_PATH = "data/catalogue.json"
FUR_EXCEL = r"C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Furniture - Jul 25, 2026.xlsx"

# catalogue Part Number -> Excel Part Number (Excel omits the "NC" prefix for these 4)
PN_MAP = {
    "NC2676-001-9236-01-CV": "2676-001-9236-01-CV",
    "NC2676-001-9236-01-CW": "2676-001-9236-01-CW",
    "NC2676-001-9236-01-BK": "2676-001-9236-01-BK",
    "NC2676-001-9236-01-CG": "2676-001-9236-01-CG",
}

print("Reading Excel Color hyperlinks...", flush=True)
wb = openpyxl.load_workbook(FUR_EXCEL, data_only=False)
ws = wb["2676 - DG"]
rows = list(ws.iter_rows())
headers = [c.value for c in rows[0]]
pn_idx = headers.index("Part Number")
color_idx = headers.index("Color")

excel_pn_to_link = {}
for row in rows[1:]:
    pn = row[pn_idx].value
    if pn and str(pn).strip() in PN_MAP.values():
        cell = row[color_idx]
        formula = cell.value or ""
        if isinstance(formula, str) and formula.startswith("=HYPERLINK("):
            url = formula.split('"')[1]
            excel_pn_to_link[str(pn).strip()] = url

print(f"Found {len(excel_pn_to_link)} folder links in Excel", flush=True)
for pn, url in excel_pn_to_link.items():
    print(f"  {pn}: {url}")

print("\nLoading catalogue...", flush=True)
with open(CATALOGUE_PATH, encoding="utf-8") as f:
    cat = json.load(f)

fixed = 0
for cat_pn, excel_pn in PN_MAP.items():
    item = next((i for i in cat if i.get("Part Number") == cat_pn), None)
    if not item:
        print(f"  WARNING: {cat_pn} not found in catalogue, skipping")
        continue
    url = excel_pn_to_link.get(excel_pn)
    if not url:
        print(f"  WARNING: no Excel folder link found for {excel_pn}, skipping")
        continue
    item["Color_Link"] = url
    fixed += 1
    print(f"  Fixed {cat_pn} -> {url}")

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{CATALOGUE_PATH}.backup_{ts}"
shutil.copy(CATALOGUE_PATH, backup_path)
print(f"\nBackup: {backup_path}", flush=True)

with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

print(f"\nDone: fixed Color_Link on {fixed}/{len(PN_MAP)} items.")
