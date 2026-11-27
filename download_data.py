from pathlib import Path
from huggingface_hub import snapshot_download

dataset_dir = snapshot_download(
    repo_id="oksomu/role-radar-dataset",
    repo_type="dataset",
    local_dir=Path("data")
)

print("Dataset location:", dataset_dir)
print("Download complete!")
