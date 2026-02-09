import openpyxl
import json
import re
import os
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import hashlib

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THUMBNAIL_SIZE = (400, 400)
MAX_THREADS = 40  # Faster with more threads
PUBLIC_THUMBS_DIR = os.path.join(BASE_DIR, "static", "thumbnails")
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCEL_FILE = os.path.join(BASE_DIR, "catalogue.xlsx")
JSON_OUTPUT = os.path.join(DATA_DIR, "catalogue.json")

def extract_link(formula):
    if not isinstance(formula, str) or not formula.startswith("="):
        return None
    match = re.search(r'HYPERLINK\("(.*?)",\s*"(.*?)"\)', formula)
    if match:
        return match.group(1)
    return None

def get_value_from_formula(formula):
    if not isinstance(formula, str) or not formula.startswith("="):
        return str(formula) if formula is not None else ""
    match = re.search(r'HYPERLINK\("(.*?)",\s*"(.*?)"\)', formula)
    if match:
        return match.group(2)
    return str(formula)

def download_and_resize(url, part_number):
    if not url or "dropbox.com" not in url:
        return None
    
    url_hash = hashlib.md5(url.encode()).hexdigest()
    thumb_name = f"{url_hash}.jpg"
    thumb_path = os.path.join(PUBLIC_THUMBS_DIR, thumb_name)
    
    # Skip if already exists (avoids duplicate work)
    if os.path.exists(thumb_path):
        return f"thumbnails/{thumb_name}"

    try:
        raw_url = url.replace("dl=0", "raw=1").replace("dl=1", "raw=1")
        response = requests.get(raw_url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(thumb_path, "JPEG", quality=85)
            # Return relative path for the app
            return f"thumbnails/{thumb_name}"
    except Exception as e:
        pass
    return None

def update_catalogue():
    print("--- NorthCape Turbo Upkeep Script ---")
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: {EXCEL_FILE} not found in this folder!")
        return

    os.makedirs(PUBLIC_THUMBS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print(f"Loading Excel: {EXCEL_FILE}...")
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=False)
    
    catalogue_data = []

    for sheet_name in wb.sheetnames:
        if sheet_name in ["Status", "Empty", "Sheet1"]: continue
        
        print(f"Processing Sheet: {sheet_name}")
        ws = wb[sheet_name]
        headers = [cell.value for cell in ws[1]]
        
        for row_idx in range(2, ws.max_row + 1):
            row_data = {"Collection Type": sheet_name}
            has_data = False
            first_img_url = None
            
            for col_idx, header in enumerate(headers):
                if not header: continue
                cell = ws.cell(row=row_idx, column=col_idx + 1)
                val = cell.value
                
                if header in ["Color", "Part Number"]:
                    row_data[header] = get_value_from_formula(val)
                    link = extract_link(val)
                    if link: row_data[f"{header}_Link"] = link
                else:
                    row_data[header] = val if val is not None else ""
            
            # Collect ALL potential Dropbox links for this item
            potential_urls = []
            # Check all columns for dropbox links (prioritize those with 'Image' in header)
            # We sort headers to prioritize 'Image 1' over 'Image 10' if possible
            img_cols = sorted([h for h in headers if h and "Image" in h and h != "Dropbox Folder Path"], 
                             key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
            
            for h in img_cols:
                val = row_data.get(h)
                if val and "dropbox.com" in str(val):
                    potential_urls.append(str(val))
            
            if has_data:
                row_data["_potential_urls"] = potential_urls
                catalogue_data.append(row_data)

    print(f"Optimizing data and thumbnails for {len(catalogue_data)} items...")
    
    def process_item(item):
        urls = item.get("_potential_urls", [])
        item["Local_Thumbnail"] = None
        
        # Try each URL until one succeeds
        for url in urls:
            thumb_path = download_and_resize(url, item.get("Part Number"))
            if thumb_path:
                item["Local_Thumbnail"] = thumb_path
                break
                
        if "_potential_urls" in item:
            del item["_potential_urls"]
        return item

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        final_data = list(executor.map(process_item, catalogue_data))

    with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"Success! {len(final_data)} records updated. App is ready.")

if __name__ == "__main__":
    update_catalogue()
