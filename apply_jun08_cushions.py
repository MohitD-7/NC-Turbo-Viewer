import json, hashlib, os, re, requests, shutil, openpyxl
from io import BytesIO
from PIL import Image

catalogue_path = 'c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer/data/catalogue.json'
thumb_dir = 'c:/Users/Lenovo/Downloads/NC - Library Naming/Viewer/NC_Turbo_Viewer/static/thumbnails'
excel_path = r'C:\Users\Lenovo\Master Image Library Dropbox\Master Image Library\NorthCape Library - Master Excel - Cushions - Jun 08, 2026.xlsx'
THUMBNAIL_SIZE = (400, 400)

IMG_COLS = (
    [f'Wayfair Image {i}' for i in range(1, 16)] +
    [f'Overstock Image {i}' for i in range(1, 16)] +
    [f'Home Depot Image {i}' for i in range(1, 16)] +
    [f'Northcape Image {i}' for i in range(1, 16)]
)

def get_first5(d):
    urls = []
    for col in IMG_COLS:
        v = (d.get(col) or '').strip()
        if v.startswith('http'):
            urls.append(v)
        if len(urls) == 5:
            break
    return urls

def parse_color(val):
    if not isinstance(val, str):
        return None, None
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', val)
    if m:
        return m.group(2), m.group(1)
    return (val, None) if not val.startswith('http') else (None, val)

def download_thumb(url):
    fname = hashlib.md5(url.encode()).hexdigest() + '.jpg'
    fpath = os.path.join(thumb_dir, fname)
    if os.path.exists(fpath):
        return f'thumbnails/{fname}'
    try:
        raw = url.replace('dl=0', 'raw=1').replace('dl=1', 'raw=1')
        r = requests.get(raw, timeout=25)
        if r.status_code == 200:
            img = Image.open(BytesIO(r.content))
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(fpath, 'JPEG', quality=85)
            return f'thumbnails/{fname}'
    except Exception:
        pass
    return None

# Load catalogue
with open(catalogue_path, encoding='utf-8') as f:
    data = json.load(f)
cat_map = {p['Part Number']: i for i, p in enumerate(data)}

# Read Excel with raw formulas for HYPERLINK parsing
wb = openpyxl.load_workbook(excel_path)
excel_products = {}
for sheet in wb.sheetnames:
    ws = wb[sheet]
    headers = [c.value for c in ws[1]]
    if 'Part Number' not in headers:
        continue
    pn_col = headers.index('Part Number') + 1
    for row in ws.iter_rows(min_row=2):
        pn = row[pn_col - 1].value
        if not pn:
            continue
        excel_products[pn] = {
            headers[i]: (row[i].value if i < len(row) else None)
            for i in range(len(headers))
        }

print(f'Excel: {len(excel_products)} products')
print(f'Catalogue: {len(data)} products')

stats = {
    'url_updated': 0, 'field_updated': 0, 'color_updated': 0,
    'new_added': 0, 'removed': 0, 'deleted': 0, 'downloaded': 0, 'failed': 0
}

thumbs_to_delete = set()

for pn, excel_row in excel_products.items():
    idx = cat_map.get(pn)

    if idx is None:
        # New record
        color_name, color_link = parse_color(excel_row.get('Color'))
        new_prod = {
            'Part Number': pn,
            'Collection': (excel_row.get('Collection') or ''),
            'Category': 'Cushion',
            'Type': 'Cushions',
            'Color': color_name or '',
            'Color_Link': color_link or '',
            'Dropbox Folder Path': excel_row.get('Dropbox Folder Path') or '',
            'Last Modified': str(excel_row.get('Last Modified') or ''),
            'Image_List': [],
            'Local_Thumbnail': '',
        }
        for col in IMG_COLS:
            v = (excel_row.get(col) or '').strip()
            new_prod[col] = v if v.startswith('http') else ''
        urls = get_first5(new_prod)
        il = []
        for url in urls:
            result = download_thumb(url)
            if result:
                il.append(result)
                stats['downloaded'] += 1
            else:
                stats['failed'] += 1
        new_prod['Image_List'] = il
        new_prod['Local_Thumbnail'] = il[0] if il else ''
        data.append(new_prod)
        cat_map[pn] = len(data) - 1
        stats['new_added'] += 1
        print(f'  New: {pn} ({len(il)} images downloaded)')
        continue

    p = data[idx]
    changed = False

    # Color / Color_Link
    color_name, color_link = parse_color(excel_row.get('Color'))
    if color_name and p.get('Color') != color_name:
        p['Color'] = color_name
        changed = True
        stats['color_updated'] += 1
    if color_link and p.get('Color_Link') != color_link:
        p['Color_Link'] = color_link
        changed = True

    # All image columns
    for col in IMG_COLS:
        excel_v = (excel_row.get(col) or '').strip()
        excel_v = excel_v if excel_v.startswith('http') else ''
        cat_v = (p.get(col) or '').strip()
        if excel_v != cat_v:
            p[col] = excel_v
            changed = True

    # Rebuild Image_List from new first-5
    new_first5 = get_first5(p)
    old_il = list(p.get('Image_List') or [])
    old_il_fnames = set(os.path.basename(path) for path in old_il)
    new_il_fnames = set(hashlib.md5(u.encode()).hexdigest() + '.jpg' for u in new_first5)

    for fname in old_il_fnames - new_il_fnames:
        thumbs_to_delete.add(fname)

    new_il = []
    for url in new_first5:
        fname = hashlib.md5(url.encode()).hexdigest() + '.jpg'
        if fname in old_il_fnames:
            new_il.append(f'thumbnails/{fname}')
        else:
            result = download_thumb(url)
            if result:
                new_il.append(result)
                stats['downloaded'] += 1
            else:
                stats['failed'] += 1

    if new_il != old_il:
        p['Image_List'] = new_il
        p['Local_Thumbnail'] = new_il[0] if new_il else ''
        stats['url_updated'] += 1
        changed = True

    if changed:
        stats['field_updated'] += 1

# Remove bad PN without CUSH prefix
bad_pn = '1616DC-CF'
if bad_pn in cat_map:
    idx = cat_map[bad_pn]
    old_p = data[idx]
    for path in (old_p.get('Image_List') or []):
        thumbs_to_delete.add(os.path.basename(path))
    data.pop(idx)
    stats['removed'] += 1
    print(f'Removed bad PN: {bad_pn}')

# Delete orphaned thumbnails
all_referenced = set()
for p in data:
    for path in (p.get('Image_List') or []):
        all_referenced.add(os.path.basename(path))

for fname in thumbs_to_delete:
    if fname not in all_referenced:
        fpath = os.path.join(thumb_dir, fname)
        if os.path.exists(fpath):
            os.remove(fpath)
            stats['deleted'] += 1

# Save
with open(catalogue_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print()
print('=== DONE ===')
print(f'Products updated (Image_List):    {stats["url_updated"]}')
print(f'Products updated (any field):     {stats["field_updated"]}')
print(f'Color/Color_Link updated:         {stats["color_updated"]}')
print(f'New records added:                {stats["new_added"]}')
print(f'Records removed:                  {stats["removed"]}')
print(f'Thumbnails deleted:               {stats["deleted"]}')
print(f'Thumbnails downloaded:            {stats["downloaded"]}')
print(f'Download failures:                {stats["failed"]}')
