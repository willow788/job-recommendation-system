# Role Radar

Role Radar is a local job recommendation app built around the bundled India-focused
job and candidate-profile datasets. It ranks jobs using an explainable baseline
for skills, role, location, seniority, and domain fit. The score is a guide for exploring
postings, not a hiring decision.

## Run locally

Use Python 3.10 or newer. From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local URL (normally `http://localhost:8501`). The data is
bundled in `data/`, so the app does not download anything or require model
weights at startup.

Use either one of the sample candidate profiles or enter your target roles,
skills, experience, domains, and preferred cities in the sidebar. Filter results
by role family or job location. Each recommendation shows its component scores,
matched skills, and job description.

The interface is dark-only, using charcoal and violet with restrained red accents.

Choose **Upload a resume** to extract contact details, skills, target roles,
experience, seniority, domains, education, certifications, languages, and work
history from a PDF, DOCX, or TXT file. Review and edit the candidate fields
before recommendations. The file is parsed in the app session and is not written
to the project. Check the extracted details before using the
recommendations. Image-only scanned PDFs are not supported because they need OCR.

## Tests and preprocessing

Run the focused test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

To regenerate the preprocessed jobs file:

```powershell
python -m src.preprocessing.extract_job_skills
```

The recommender reads `data/processed/scraped_jobs_with_skills.json` when it is
present, and falls back to `data/scraped_jobs.json` otherwise. The optional
`download_data.py` script fetches the source dataset from Hugging Face.
