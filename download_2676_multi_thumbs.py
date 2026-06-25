import json, os, hashlib, shutil, urllib.request
from datetime import datetime

CATALOGUE_PATH = 'data/catalogue.json'
THUMB_DIR = 'static/thumbnails'
MAX_IMAGES = 5

with open(CATALOGUE_PATH) as f:
    cat = json.load(f)

items_2676 = [i for i in cat if i.get('Collection') == '2676 - DG']
print(f'Total 2676-DG items: {len(items_2676)}')

downloaded = 0
skipped = 0
failed = []

for item in items_2676:
    nc_urls = [item.get(f'Northcape Image {n}') for n in range(1, 18) if item.get(f'Northcape Image {n}')]
    by_urls = [item.get(f'Overstock Image {n}') for n in range(1, 16) if item.get(f'Overstock Image {n}')]
    urls_to_use = (nc_urls or by_urls)[:MAX_IMAGES]

    if not urls_to_use:
        skipped += 1
        continue

    local_paths = []
    for url in urls_to_use:
        fname = hashlib.md5(url.encode()).hexdigest() + '.jpg'
        dest = os.path.join(THUMB_DIR, fname)

        if not os.path.exists(dest):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as resp, open(dest, 'wb') as f:
                    shutil.copyfileobj(resp, f)
                downloaded += 1
            except Exception as e:
                failed.append((item.get('Part Number'), url, str(e)))
                continue

        local_paths.append(f'thumbnails/{fname}')

    if local_paths:
        item['Image_List'] = local_paths
        item['Local_Thumbnail'] = local_paths[0]
        item['_thumbnail_path'] = local_paths[0]

    if (downloaded + skipped) % 50 == 0 and downloaded > 0:
        print(f'  Downloaded {downloaded} images so far...')

print(f'\nNew images downloaded: {downloaded}')
print(f'Items skipped (no URLs): {skipped}')
print(f'Failed: {len(failed)}')
for pn, url, err in failed[:10]:
    print(f'  {pn}: {err}')

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy(CATALOGUE_PATH, f'data/catalogue.backup_{ts}')
with open(CATALOGUE_PATH, 'w') as f:
    json.dump(cat, f, indent=2)
print(f'\ncatalogue.json updated.')
