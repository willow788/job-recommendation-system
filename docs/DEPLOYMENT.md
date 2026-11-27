# Deployment checklist

Role Radar is still in development. This repository does not select or
configure a hosting provider, set up a production domain, or provide
authentication, a database, or persistent user accounts. Complete the checks
below with the intended hosting provider before sharing a public URL.

## 1. Choose and configure the host

- Decide whether the app should be public or access-restricted. The app itself
  has no login or access-control layer.
- Configure a supported Python runtime (3.10 or newer) and install
  `requirements.txt` from the repository root.
- Start the app with Streamlit bound to the host interface:

  ```bash
  streamlit run app.py --server.address 0.0.0.0
  ```

- Configure the port and health/readiness behavior using the hosting
  provider's supported settings. No provider-specific deployment files are
  included in this repository.
- Set resource limits appropriate for the bundled datasets and simultaneous
  sessions. The app loads the job and profile catalog into Streamlit's data
  cache; it does not need the ONNX artifacts in `data/models/`.

## 2. Review data and privacy

- Review the dataset provenance, redistribution permissions, licenses, and
  appropriateness of the bundled job postings and profiles. See
  [`../data/README.md`](../data/README.md).
- The app does not save uploaded resumes to the repository or a database.
  Resume contents are uploaded to the server and parsed in the app process;
  hosting providers may have their own request, crash, or diagnostic logs and
  retention behavior. Confirm those policies before accepting real resumes.
- The resume uploader accepts PDF, DOCX, and TXT files up to 10 MB. PDF text
  extraction is limited to 100 pages and does not perform OCR.
- Avoid exposing personal contact details or resume contents in screenshots,
  logs, or support requests. Do not promise users data deletion or retention
  behavior beyond what the selected host actually provides.
- Explain in the user-facing experience that recommendations are
  heuristic estimates, can be inaccurate, and must not be used as hiring
  decisions.

## 3. Verify the release

Run the unit tests before deployment:

```bash
python -m unittest discover -s tests -v
```

Then verify the deployed instance in a browser:

- The app starts without errors and loads the bundled jobs and sample
  profiles.
- Sample profile and manually entered profile modes produce recommendations.
- Role-family and location filters work, and empty results are handled.
- A text-based PDF, DOCX, and TXT resume can be uploaded and reviewed; an
  unsupported or invalid file produces a useful error.
- The interface is usable on the screen sizes and browsers you intend to
  support.
- The deployed revision includes `data/scraped_jobs.json`,
  `data/synthetic_profiles.json`, and, if used, the processed jobs file.

## 4. Operations and updates

- Keep deployment dependencies and the deployed Git revision identifiable;
  `requirements.txt` currently uses minimum-version ranges rather than a
  fully locked environment.
- Decide how dataset refreshes will be reviewed and released. The optional
  `download_data.py` script fetches data from Hugging Face and is not required
  to start the app.
- Confirm how the host handles availability, logs, restarts, and rollback.
  This repository does not configure monitoring, backups, or a release
  pipeline.
- Re-run the browser checks and unit tests after changing the recommender,
  resume parser, data files, or dependencies.
