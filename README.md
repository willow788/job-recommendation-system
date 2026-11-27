# Role Radar

Role Radar is an **in-progress job discovery prototype**. It compares a
candidate profile with a bundled catalog of job postings, ranks the postings,
and shows the signals behind each result. The application is intended to help
people explore opportunities; its scores are estimates, not hiring decisions
or a guarantee of job fit.

The current app is a local-first Streamlit application with a deterministic,
rule-based recommender. It reads JSON data bundled in this repository and does
not load a trained model or require a network connection at startup.
**Deployment is not configured in this repository.** See the
[pre-deployment checklist](docs/DEPLOYMENT.md) before making the app publicly
available.

## What the app does

- **Sample profile:** select a bundled candidate profile to explore the
  recommendations.
- **Build a profile:** enter target roles, core and additional skills,
  industries/domains, seniority, years of experience, preferred cities, and
  remote-work preference.
- **Upload a resume:** upload a PDF, DOCX, or TXT resume and let the parser
  suggest profile fields. Review and edit the detected values before using
  them.
- **Explore recommendations:** filter by job role family or a text query for
  job location; choose how many results to show; inspect each result's overall
  score, component scores, matching skills, skill gaps, description, and
  posting link when available.

The app's interface is dark-themed. It does not create user accounts, save
profiles to a database, or provide a way to apply for jobs.

## Run locally

Use Python 3.10 or newer. From the repository root, create and activate a
virtual environment, install dependencies, and start Streamlit.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit, usually <http://localhost:8501>. The app
loads jobs and sample profiles from `data/`. No API key, account, model
download, or external service is needed to start it.

## Using the application

### Build a profile

Enter comma-separated values for roles, skills, domains, and preferred cities.
Core skills have greater influence than additional skills. Select a seniority
level and experience range, and indicate whether remote work is acceptable.
Select **Update recommendations** to apply the entered values.

### Upload a resume

The uploader accepts `.pdf`, `.docx`, and `.txt` files up to 10 MB. The parser
looks for contact details, role titles, skills, experience, seniority,
domains, education, certifications, languages, and work history. Detected
profile fields are editable before recommendations are calculated. Extraction
uses text and simple patterns; it can miss or misclassify information, so
review all results.

Scanned/image-only PDFs are not supported because OCR is not implemented.
PDFs over 100 pages are rejected. Invalid, encrypted, empty, unsupported, or
textless uploads produce an error instead of recommendations.

**Privacy:** the app code does not write uploaded resumes to the repository or
to a database. The browser does send the file to the server running Streamlit
for parsing. This does not describe retention or logging by a hosting
provider; review that provider's policies before using real candidate data.

### Read the results

Each recommendation shows an overall fit score out of 100 and rounded scores
for skills, role, location, seniority, and domain. Matching and unmatched
candidate skills are listed separately. A job description can be expanded,
and a posting link is shown only when the record includes a URL.

The role-family selector limits results to the selected family. The location
filter is a case-insensitive substring search against the job's location
field; it is separate from preferred-location scoring in the candidate
profile. The result-count control sets a maximum from 5 to 50 jobs. If filters
exclude all jobs, try a different role family or location query.

## Recommendation method

The current implementation is a heuristic baseline in
`src/recommender.py`; it is not a trained or calibrated ranking model. It
calculates five component scores, each on a 0–100 scale, then combines them
using these weights:

| Component | Weight | Main signals |
| --- | ---: | --- |
| Skills | 45% | Candidate skills found in extracted job skills or job-description text. |
| Location | 22.5% | Preferred city, remote preference, and job location/remote hints. |
| Seniority | 13.5% | Candidate seniority and experience compared with the job level or title. |
| Role | 10% | Candidate role family compared with the job family. |
| Domain | 9% | Candidate domains compared with job industry, domain hint, and description. |

Primary skills have twice the weight of secondary skills in the skills
component. Skill matching is case-insensitive and uses the bundled skill
dictionary plus text matching. A candidate with no listed skills receives a
neutral skills score.

The weighted component result is mapped to the displayed 50–100 range:

```text
overall_score = 50 + (weighted_component_score / 100) * 50
```

Role-family matches and city aliases use fixed rules; seniority and domain
scores also use fixed levels and fallback values when information is missing.
These choices are implementation details, not evidence that the scores
predict hiring outcomes. Review the scoring helpers in `src/recommender.py`
before interpreting or changing the method.

## Data

The repository bundles 2,500 job postings, 640 sample candidate profiles,
preprocessed job records, pair/label files, evaluation artifacts, and ONNX
model/tokenizer files. The app uses the jobs, profiles, and preprocessed
skills; the current recommendation path does **not** load the label or ONNX
artifacts.

For file descriptions, common record fields, and data-review cautions, see
[`data/README.md`](data/README.md). In particular, verify source provenance,
redistribution rights, and suitability of all bundled material before
deployment. Do not treat dataset labels or recommendation scores as objective
measures of a person's qualifications.

The app prefers `data/processed/scraped_jobs_with_skills.json` when it exists
and falls back to `data/scraped_jobs.json`. It loads
`data/synthetic_profiles.json` for the sample-profile selector. Missing or
malformed required JSON data prevents the app from loading the catalog and is
reported in the interface.

### Refresh or preprocess data

`download_data.py` is an optional script that downloads the
`oksomu/role-radar-dataset` dataset from Hugging Face into `data/`. It is not
run at application startup. Review downloaded changes and their provenance
before using or committing them.

To regenerate the preprocessed jobs file from the bundled raw jobs, install
the script's extra dependency (`pandas` is not listed in the app's
`requirements.txt`) and run:

```bash
python -m pip install pandas
python -m src.preprocessing.extract_job_skills
```

The skill extractor uses a manually maintained alias dictionary in
`src/preprocessing/skills_dictionary.py`. Update that dictionary if new skills
need to be recognized, then regenerate the processed file and verify the
results.

## Development and tests

Install the app dependencies as described in [Run locally](#run-locally), then
run the unit tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

The tests cover skill extraction, recommendation ordering and filtering,
score behavior, TXT and DOCX resume parsing, and PDF validation/error handling.
When changing the
recommender, parser, preprocessing, or data schema, add or update focused
tests for the affected behavior.

## Project structure

```text
app.py                              Streamlit UI and user workflow
src/recommender.py                  Data loading, profile normalization, scoring
src/resume_parser.py                PDF, DOCX, and TXT resume text extraction
src/preprocessing/
  skill_extractor.py                Extract skills using the skill dictionary
  skills_dictionary.py              Canonical skills and aliases
  extract_job_skills.py             Generate processed job data
data/
  scraped_jobs.json                 Raw job postings
  processed/                        Job postings with extracted skills
  synthetic_profiles.json           Sample profiles
  *_pairs.json, *_labels.json       Training and evaluation artifacts
tests/                              Unit tests
docs/DEPLOYMENT.md                  Pre-deployment checklist
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| App reports it cannot load datasets | Run Streamlit from the repository root and confirm `data/synthetic_profiles.json` and at least one of the raw or processed jobs files exists and contains a JSON array. |
| Resume fields are missing or inaccurate | Review and edit the extracted profile; use a text-based PDF, DOCX, or TXT file. Scanned PDFs require OCR before upload. |
| No recommendations appear | Clear or broaden the role-family and location filters. The location filter searches the job location text rather than using candidate preferences. |
| Recommendations look unexpected | Check candidate roles, skills, domains, locations, and seniority. Scores are rule-based estimates; see [Recommendation method](#recommendation-method). |
| Preprocessing fails to import pandas | Install its optional dependency with `python -m pip install pandas`. |

## Deployment

There is no production deployment configuration in the repository yet.
Before sharing the site, choose a host, decide whether it will be public or
restricted, check dataset rights and resume privacy, and verify the deployed
instance. Follow the [deployment checklist](docs/DEPLOYMENT.md).
