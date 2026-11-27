---
language: en
license: apache-2.0
task_categories:
  - text-classification
tags:
  - job-matching
  - india
  - resume-scoring
size_categories:
  - 10K<n<100K
---

# Role Radar dataset

This directory contains bundled data for the Role Radar prototype, including
India-focused job postings, sample candidate profiles, and artifacts for
training and evaluating job-profile fit scoring. The application currently
uses the job postings, sample profiles, and preprocessed job file; it does not
load the model or label artifacts.

## Files

| File | Contents |
| --- | --- |
| `scraped_jobs.json` | 2,500 job postings. Records include an ID, title, company, location, description, seniority, industry, URL, and matching hints. |
| `processed/scraped_jobs_with_skills.json` | Job postings with skills extracted from descriptions. The app prefers this file when present. |
| `synthetic_profiles.json` | 640 sample candidate profiles with role, skill, experience, seniority, domain, and preference fields. |
| `phase2_pairs.json`, `phase3_pairs.json` | Profile/job pair records for dataset experiments. |
| `phase2_labels.json`, `phase3_labels.json` | Dimension and composite labels associated with pair IDs. |
| `gold_labels.json` | 108 human-reviewed evaluation records. |
| `benchmarks.json` | Benchmark and evaluation metadata. |
| `models/` | ONNX model/tokenizer artifacts; not used by the current Streamlit app. |

The raw jobs file has 15 distinct `role_family_hint` values, including
`non-tech`. The profiles file contains 640 records. Pair and label file counts
are not interchangeable: for example, `phase3_pairs.json` and
`phase3_labels.json` contain different numbers of records. Consult the files
themselves when designing a training or evaluation pipeline.

## Common record fields

Job records include `id`, `title`, `company`, `location`, `description`,
`seniority_level`, `industry`, `url`, `role_family_hint`, and other hints.
Profile records include `profile_id`, `roles`, `skills_primary`,
`skills_secondary`, `experience_years`, `seniority`, `domains`, and
`preferences`.

Label records use `pair_id` to associate dimension scores such as `skills`,
`seniority`, `domain`, `location`, and `composite` with a profile/job pair.
Some label files also include fields such as `matches`, `gaps`,
`label_source`, or `confidence`; fields vary by dataset phase.

## Use in this application

The app loads data from the repository-relative `data/` directory:

```python
from pathlib import Path

from src.recommender import load_jobs, load_profiles

data_dir = Path("data")
jobs = load_jobs(data_dir)
profiles = load_profiles(data_dir)
```

For the full local setup and test instructions, see the root
[README](../README.md).

## Data review before deployment

This repository describes the profiles as synthetic and public-resume-derived.
Before redistributing the dataset or deploying it for public use, verify the
provenance, permissions, and applicable licenses for every bundled dataset
and model artifact. Check that the included job descriptions, links, and
profile records are appropriate to expose. Do not treat dataset labels or
recommendation scores as objective measures of a person's qualifications.
