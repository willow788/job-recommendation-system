#we will perform the eda
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

Data_dir = Path("data")

files = [
    "scraped_jobs.json",
    "synthetic_profiles.json",
    "phase2_pairs.json",
    "phase2_labels.json",
    "phase3_pairs.json",
    "phase3_labels.json",
    "gold_labels.json",
    "benchmarks.json"
]

for file in files:
    file_path = Data_dir / file

    print("---------------------------------")
    print(f"File: {file_path}")
    print(f"Size: {file_path.stat().st_size / 1024:.2f} KB")

    #open the file
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"type of data: {type(data)}")

    #length of data
    print(f"Number of items in data: {len(data)}")

    if isinstance(data, list):
        print(f"First 5 items in data: {data[:5]}")

        if data:
            print(f"Keys of the first item in data: {list(data[0].keys())}")
            print(json.dumps(data[0], indent=4, ensure_ascii=False))

    elif isinstance(data, dict):
        print(f"Top level keys of the dictionary: {list(data.keys())}")

        if data:
            sample_key = next(iter(data))
            sample = json.dumps(data[sample_key], indent=4, ensure_ascii=False)
            print(f"Sample record for '{sample_key}': {sample}")
        

