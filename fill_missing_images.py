"""
fill_missing_images.py
======================
Step 2: Fill products that have fewer than 5 images.

Does two things in one pass:
  A) Stale check — for each product, verify existing Image_List entries match
     current source URLs. If an entry is stale (URL changed), flag for re-download.
  B) Fill up — for products with <5 valid images, download enough new thumbnails
     from source columns to reach 5 (or as many as available).

Saves catalogue.json after completion. Run from the NC_Turbo_Viewer directory.
"""

import json, hashlib, os, shutil, requests, csv, time
from io import BytesIO
from PIL import Image

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
CATALOGUE_PATH = os.path.join(BASE_DIR, "data", "catalogue.json")
THUMB_DIR      = os.path.join(BASE_DIR, "static", "thumbnails")
LOG_PATH       = os.path.join(BASE_DIR, "fill_missing_images_log.csv")

THUMBNAIL_SIZE = (400, 400)
MAX_IMAGES     = 5

IMG_COLS = (
    [f"Wayfair Image {i}"      for i in range(1, 16)] +
    [f"Overstock Image {i}"    for i in range(1, 16)] +
    [f"Home Depot Image {i}"   for i in range(1, 16)] +
    [f"Northcape Image {i}"    for i in range(1, 16)] +
    [f"Bed Bath Beyond Image {i}" for i in range(1, 16)]
)


def thumb_path_for(url):
    fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    return os.path.join(THUMB_DIR, fname), f"thumbnails/{fname}"


def download_thumbnail(url):
    """Download, resize and save thumbnail. Returns relative path or None."""
    full_path, rel_path = thumb_path_for(url)
    if os.path.exists(full_path):
        return rel_path  # already cached
    try:
        raw_url = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        resp = requests.get(raw_url, timeout=25)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(full_path, "JPEG", quality=85)
            return rel_path
    except Exception:
        pass
    return None


def get_current_url_hashes(product):
    hashes = {}
    for col in IMG_COLS:
        url = (product.get(col) or "").strip()
        if url.startswith("http"):
            fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
            hashes[fname] = (url, col)
    return hashes


def main():
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    downloaded = 0
    failed = 0
    stale_fixed = 0
    filled = 0
    log_rows = []

    print(f"Loaded {total} products.")
    print(f"Processing...\n")

    for idx, product in enumerate(data):
        pn     = product.get("Part Number", "")
        color  = product.get("Color", "")
        il     = product.get("Image_List", [])

        current_url_hashes = get_current_url_hashes(product)

        # --- A) Stale check: remove Image_List entries whose hash is not in current URLs ---
        valid_il = []
        for path in il:
            fname = os.path.basename(path)
            if fname in current_url_hashes:
                valid_il.append(path)
            else:
                # Stale — the URL this was downloaded from is no longer in the catalogue
                stale_fixed += 1
                log_rows.append({
                    "Part Number": pn, "Color": color,
                    "Action": "stale_removed", "Column": "",
                    "URL": "", "Filename": fname, "Result": "removed_from_image_list"
                })

        # --- B) Fill up to MAX_IMAGES ---
        valid_fnames = set(os.path.basename(p) for p in valid_il)
        slots_needed = MAX_IMAGES - len(valid_il)

        if slots_needed > 0:
            for col in IMG_COLS:
                if slots_needed <= 0:
                    break
                url = (product.get(col) or "").strip()
                if not url.startswith("http"):
                    continue
                fname = hashlib.md5(url.encode()).hexdigest() + ".jpg"
                if fname in valid_fnames:
                    continue  # already in valid list

                result = download_thumbnail(url)
                if result:
                    valid_il.append(result)
                    valid_fnames.add(fname)
                    slots_needed -= 1
                    downloaded += 1
                    filled += 1
                    log_rows.append({
                        "Part Number": pn, "Color": color,
                        "Action": "downloaded", "Column": col,
                        "URL": url, "Filename": fname, "Result": "ok"
                    })
                    if downloaded % 25 == 0:
                        print(f"  [{idx+1}/{total}] Downloaded {downloaded} | Failed {failed} | Stale removed {stale_fixed}", flush=True)
                else:
                    failed += 1
                    log_rows.append({
                        "Part Number": pn, "Color": color,
                        "Action": "download_failed", "Column": col,
                        "URL": url, "Filename": fname, "Result": "failed"
                    })

        # Update Image_List
        product["Image_List"] = valid_il
        # Update Local_Thumbnail to first image
        if valid_il:
            product["Local_Thumbnail"] = valid_il[0]

    # Save catalogue
    with open(CATALOGUE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nCatalogue saved.")

    # Save log
    with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Part Number","Color","Action","Column","URL","Filename","Result"])
        writer.writeheader()
        writer.writerows(log_rows)

    # Final stats
    print("\n" + "="*50)
    print(f"DONE")
    print(f"  Stale entries removed:    {stale_fixed}")
    print(f"  New images downloaded:    {downloaded}")
    print(f"  Download failures:        {failed}")
    print(f"  Log saved to:             {LOG_PATH}")

    # Image_List distribution after
    from collections import Counter
    dist = Counter(len(p.get("Image_List", [])) for p in data)
    print("\nImage_List distribution after run:")
    for k in sorted(dist):
        print(f"  {k} images: {dist[k]} products")


if __name__ == "__main__":
    main()
