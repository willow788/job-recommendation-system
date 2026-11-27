from pathlib import Path

data_dir = Path("data")

for file in data_dir.rglob("*"):
    if file.is_file():
        print(file, f"{file.stat().st_size / 1024:.2f} KB")