import json
import pandas as pd

with open('data/catalogue.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data)
print(f"Total records: {len(df)}")
print(f"Types found: {df['Type'].unique()}")

cushions = df[df['Type'] == 'Cushions']
print(f"Cushion records: {len(cushions)}")

if not cushions.empty:
    print("\nSample Cushion Data (first 2):")
    sample = cushions.head(2).to_dict('records')
    for item in sample:
        print(f"Part Number: {item.get('Part Number')}")
        print(f"NC Image Count: {repr(item.get('NC Image Count'))}")
        print(f"Local_Thumbnail: {repr(item.get('Local_Thumbnail'))}")
        print("-" * 20)

    # Check why they are filtered
    selected_market = "Northcape"
    channel_to_count = {
        "Northcape": "NC Image Count",
        "Overstock": "OS Image Count",
        "Wayfair": "WF Image Count",
        "Home Depot": "HD Image Count"
    }
    count_col = channel_to_count.get(selected_market)
    print(f"\nFiltering by {count_col} > 0...")
    
    # Simulate filtering logic
    # Replicate the logic from catalogue_turbo_app.py:
    # df = df[df[count_col] > 0]
    
    try:
        filtered_cushions = cushions[cushions[count_col] > 0]
        print(f"Filtered cushions count: {len(filtered_cushions)}")
    except Exception as e:
        print(f"Filtering error: {e}")
        # Let's check dtypes
        print(f"Dtype of {count_col}: {cushions[count_col].dtype}")
        print(f"Unique values in {count_col}: {cushions[count_col].unique()}")
