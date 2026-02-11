import json
import os
import pandas as pd

def analyze_catalogue():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "data", "catalogue.json")
    
    if not os.path.exists(json_path):
        print("Catalogue JSON not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_items = len(data)
    multi_image_items = 0
    nc_image_counts = {}
    
    for item in data:
        count = item.get("NC Image Count", 0)
        if count > 1:
            multi_image_items += 1
        
        nc_image_counts[count] = nc_image_counts.get(count, 0) + 1
    
    print(f"Total Items: {total_items}")
    print(f"Items with >1 Image: {multi_image_items} ({multi_image_items/total_items:.1%})")
    print("\nNC Image Count Distribution:")
    for count in sorted(nc_image_counts.keys()):
        print(f"  {count} image(s): {nc_image_counts[count]} items")

    # Sample some with multiple images to see URLs
    print("\nSamples of multi-image items:")
    samples = [i for i in data if i.get("NC Image Count", 0) > 1][:5]
    for s in samples:
        print(f"  Part: {s.get('Part Number')} | Images: {s.get('NC Image Count')}")
        for j in range(1, min(4, s.get("NC Image Count") + 1)):
            print(f"    Img {j}: {s.get(f'Northcape Image {j}')}")

if __name__ == "__main__":
    analyze_catalogue()
