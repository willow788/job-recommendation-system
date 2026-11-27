import json
import pandas as pd
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from .skill_extractor import extract_skills
except ImportError:
    from skill_extractor import extract_skills


def main():
    root = Path(__file__).resolve().parents[2]
    with (root / "data" / "scraped_jobs.json").open("r", encoding="utf-8") as f:
        scraped_jobs = json.load(f)

    df = pd.DataFrame(scraped_jobs)
    df["extracted_Skills"] = df["description"].apply(extract_skills)

    for _, row in df.head(10).iterrows():
        print("\nJob Title:", row["title"])
        print("Extracted Skills:", row["extracted_Skills"])
        print("Job Description:", row["description"])

    op_dir = root / "data" / "processed"
    op_dir.mkdir(parents=True, exist_ok=True)

    df.to_json(
        op_dir / "scraped_jobs_with_skills.json",
        orient="records",
        indent=4,
        force_ascii=False,
    )


if __name__ == "__main__":
    main()