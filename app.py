from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.recommender import CandidateProfile, load_jobs, load_profiles, recommend_jobs
from src.resume_parser import ResumeParseError, parse_resume


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

st.set_page_config(page_title="Role Radar", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #f1eef6;
        --muted: #aaa6b5;
        --paper: #17161d;
        --card: #201e28;
        --line: #373440;
        --violet: #a38ddd;
        --sidebar: #1d1b25;
        --sidebar-input: #302d3a;
        --red: #d2767f;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--paper);
        color: var(--ink);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .main .block-container {
        max-width: 1360px;
        padding: 3rem 3.25rem 5rem;
    }
    [data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #f4f1e8;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #bdc9bf;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: var(--sidebar-input);
        color: #f7f5ef;
        border-color: rgba(255, 255, 255, 0.18);
        border-radius: 9px;
    }
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
        color: #b5c3b9;
    }
    [data-testid="stSidebar"] input[type="radio"] {
        accent-color: var(--red);
    }
    [data-testid="stSidebar"] button[kind="primary"] {
        background: var(--violet);
        color: #211b2b;
        border: 0;
        border-radius: 9px;
        font-weight: 650;
    }
    .brand-mark {
        color: #f5f1fa;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.65rem;
        font-weight: 600;
        letter-spacing: -0.045em;
        margin: 0 0 0.15rem;
    }
    .brand-note,
    .eyebrow {
        color: var(--red);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }
    .brand-note {
        color: #aaa3ba;
        margin: 0 0 2.2rem;
    }
    .hero {
        border-bottom: 1px solid var(--line);
        margin-bottom: 2rem;
        padding: 0.2rem 0 1.8rem;
    }
    .hero .eyebrow {
        margin: 0 0 0.9rem;
    }
    .hero h1 {
        color: var(--ink);
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(2.7rem, 5vw, 4.7rem);
        font-weight: 500;
        letter-spacing: -0.065em;
        line-height: 1.03;
        margin: 0;
    }
    .hero h1 em {
        color: var(--violet);
        font-weight: 400;
    }
    .hero-copy {
        color: var(--muted);
        font-size: 1.05rem;
        margin: 0.9rem 0 0;
    }
    [data-testid="stMetric"] {
        background: #211f2a;
        border: 1px solid var(--line);
        border-radius: 13px;
        padding: 0.9rem 1rem;
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: 0.66rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    [data-testid="stMetricValue"] {
        color: var(--ink);
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.55rem;
    }
    .score-badge {
        background: #282531;
        border: 1px solid var(--line);
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
        min-width: 5.2rem;
        padding: 0.7rem 0.8rem;
    }
    .score-badge span,
    .score-badge small {
        color: var(--muted);
        font-size: 0.62rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .score-badge strong {
        color: var(--ink);
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.45rem;
        font-weight: 500;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 16px;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.14);
        margin: 0.25rem 0 1rem;
        padding: 0.6rem 0.9rem;
    }
    [data-testid="stProgressBar"] > div > div {
        background: var(--violet);
    }
    .match-rank {
        color: var(--red);
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }
    h2, h3 {
        color: var(--ink);
        font-family: Georgia, "Times New Roman", serif;
        letter-spacing: -0.025em;
    }
    [data-testid="stCaptionContainer"] {
        color: var(--muted);
    }
    @media (max-width: 800px) {
        .main .block-container {
            padding: 2rem 1.15rem 3rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading the job and candidate datasets...")
def get_catalog() -> tuple[list[dict], list[dict]]:
    return load_jobs(DATA_DIR), load_profiles(DATA_DIR)


st.sidebar.markdown(
    '<div class="brand-mark">Role Radar</div>'
    '<div class="brand-note">Thoughtful career matching</div>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <header class="hero">
        <p class="eyebrow">A more considered way to search</p>
        <h1>Find work that <em>fits.</em></h1>
        <p class="hero-copy">Explore opportunities shaped around your experience and ambitions.</p>
    </header>
    """,
    unsafe_allow_html=True,
)

try:
    jobs, profiles = get_catalog()
except (FileNotFoundError, ValueError) as error:
    st.error(f"Could not load the bundled datasets: {error}")
    st.stop()

profile_mode = st.sidebar.radio(
    "Candidate profile",
    ["Choose a sample profile", "Build my profile", "Upload a resume"],
)
resume_details = None
if profile_mode == "Choose a sample profile":
    profile_index = st.sidebar.selectbox(
        "Sample profile",
        range(len(profiles)),
        format_func=lambda index: (
            f"Profile {profiles[index]['profile_id']} — "
            f"{', '.join(profiles[index].get('roles', [])[:2]) or 'Candidate'}"
        ),
    )
    candidate = CandidateProfile.from_mapping(profiles[profile_index])
    st.sidebar.caption(
        f"{candidate.seniority} · "
        f"{candidate.experience_years if candidate.experience_years is not None else 'Experience unknown'} "
        f"{'years' if candidate.experience_years is not None else ''} · "
        f"{len(candidate.skills_primary) + len(candidate.skills_secondary)} listed skills"
    )
elif profile_mode == "Build my profile":
    with st.sidebar.form("candidate_profile"):
        roles = st.text_input("Target roles", "Software Engineer")
        primary_skills = st.text_input("Core skills", "Python, SQL")
        secondary_skills = st.text_input("Additional skills", "")
        domains = st.text_input("Industries or domains", "")
        seniority = st.selectbox("Seniority", ["Junior", "Mid", "Senior", "Staff"])
        experience = st.slider("Years of experience", 0, 40, 3)
        locations = st.text_input("Preferred cities", "Bengaluru")
        remote = st.checkbox("Open to remote work")
        st.form_submit_button("Update recommendations")

    candidate = CandidateProfile.from_mapping(
        {
            "roles": roles,
            "skills_primary": primary_skills,
            "skills_secondary": secondary_skills,
            "domains": domains,
            "seniority": seniority,
            "experience_years": experience,
            "preferences": {"locations": locations, "remote": remote},
        }
    )
else:
    st.sidebar.caption("PDF, DOCX or TXT. Parsed in this session and not saved.")
    resume_file = st.sidebar.file_uploader(
        "Upload resume",
        type=["pdf", "docx", "txt"],
        max_upload_size=10,
    )
    if resume_file is None:
        st.info("Upload a resume to extract your profile and find matching jobs.")
        st.stop()
    try:
        resume_details = parse_resume(resume_file.name, resume_file.getvalue())
    except ResumeParseError as error:
        st.sidebar.error(str(error))
        st.stop()
    extracted_profile = CandidateProfile.from_mapping(resume_details["candidate"])
    seniority_options = ["Junior", "Mid", "Senior", "Staff"]
    with st.sidebar.form("uploaded_resume_profile"):
        roles = st.text_input("Target roles", ", ".join(extracted_profile.roles))
        primary_skills = st.text_input(
            "Core skills", ", ".join(extracted_profile.skills_primary)
        )
        secondary_skills = st.text_input(
            "Additional skills", ", ".join(extracted_profile.skills_secondary)
        )
        domains = st.text_input("Industries or domains", ", ".join(extracted_profile.domains))
        seniority = st.selectbox(
            "Seniority",
            seniority_options,
            index=seniority_options.index(extracted_profile.seniority),
        )
        experience = st.slider(
            "Years of experience",
            0,
            40,
            min(40, extracted_profile.experience_years or 0),
        )
        locations = st.text_input(
            "Preferred cities",
            ", ".join(extracted_profile.preferences.get("locations", [])),
        )
        remote = st.checkbox(
            "Open to remote work",
            value=bool(extracted_profile.preferences.get("remote")),
        )
        st.form_submit_button("Update recommendations")

    candidate = CandidateProfile.from_mapping(
        {
            "roles": roles,
            "skills_primary": primary_skills,
            "skills_secondary": secondary_skills,
            "domains": domains,
            "seniority": seniority,
            "experience_years": experience,
            "preferences": {"locations": locations, "remote": remote},
        }
    )

if resume_details:
    with st.sidebar.expander("Review extracted resume details", expanded=False):
        contact = resume_details["contact"]
        st.text(
            "\n".join(
                [
                    *(
                        f"{label}: {contact.get(key) or 'Not detected'}"
                        for label, key in (
                            ("Name", "name"),
                            ("Email", "email"),
                            ("Phone", "phone"),
                            ("Location", "location"),
                            ("LinkedIn", "linkedin"),
                            ("GitHub", "github"),
                        )
                    ),
                    f"Target roles: {', '.join(candidate.roles) or 'Not detected'}",
                    f"Seniority: {candidate.seniority}",
                    f"Experience: {candidate.experience_years if candidate.experience_years is not None else 'Not detected'} years",
                    f"Skills: {', '.join(candidate.skills_primary + candidate.skills_secondary) or 'Not detected'}",
                    f"Domains: {', '.join(candidate.domains) or 'Not detected'}",
                    f"Education: {', '.join(resume_details['education']) or 'Not detected'}",
                    f"Certifications: {', '.join(resume_details['certifications']) or 'Not detected'}",
                    f"Languages: {', '.join(resume_details['languages']) or 'Not detected'}",
                ]
            )
        )
        if resume_details["summary"]:
            st.text("Summary: " + resume_details["summary"])
        if resume_details["work_history"]:
            st.text("Experience:\n" + "\n".join(resume_details["work_history"]))
        if resume_details["missing_fields"]:
            st.caption(
                "Could not confidently detect: "
                + ", ".join(resume_details["missing_fields"])
                + ". Review your resume details before relying on the matches."
            )

role_families = sorted(
    {str(job.get("role_family_hint")) for job in jobs if job.get("role_family_hint")}
)
with st.sidebar:
    st.subheader("Job filters")
    selected_family = st.selectbox("Role family", ["All", *role_families])
    location_query = st.text_input("Filter job location", placeholder="e.g. Bengaluru")
    result_count = st.slider("Number of recommendations", 5, 50, 20)

recommendations = recommend_jobs(
    candidate,
    jobs,
    limit=result_count,
    role_family=selected_family,
    location_query=location_query.strip() or None,
)

if not recommendations:
    st.info("No jobs match these filters. Try another location or role family.")
    st.stop()

top_score = recommendations[0]["recommendation"]["score"]
col1, col2, col3 = st.columns(3)
col1.metric("Jobs", f"{len(jobs):,}")
col2.metric("Shown", len(recommendations))
col3.metric("Top fit", f"{top_score:.1f}", help="Scored out of 100")
st.caption(
    "Scores are explainable estimates based on skills, role, location, seniority, and domain. "
    "They are not hiring decisions or a guarantee of job fit."
)

for rank, job in enumerate(recommendations, start=1):
    match = job["recommendation"]
    with st.container(border=True):
        heading, score_col = st.columns([4, 1.5])
        heading.markdown(
            f'<div class="match-rank">Recommended role {rank:02}</div>',
            unsafe_allow_html=True,
        )
        heading.subheader(job.get("title") or "Untitled job")
        score_col.markdown(
            '<div class="score-badge">'
            f'<span>Match</span><strong>{match["score"]:.1f}</strong><small>of 100</small>'
            "</div>",
            unsafe_allow_html=True,
        )
        details = " · ".join(
            str(value)
            for value in (job.get("company"), job.get("location"), job.get("seniority_level"))
            if value
        )
        st.write(details or "Job details unavailable")
        dimensions = match["dimensions"]
        st.progress(int(match["score"]), text="Weighted overall match")
        st.caption(
            "Skills {Skills}% · Role {Role}% · Location {Location}% · Seniority {Seniority}% · "
            "Domain {Domain}%".format(**dimensions)
        )
        if match["matches"]:
            st.write("**Matching skills:** " + ", ".join(match["matches"]))
        if match["gaps"]:
            st.write("**Skills not found in posting:** " + ", ".join(match["gaps"]))
        description = str(job.get("description") or "").strip()
        if description:
            with st.expander("Job description"):
                st.write(description)
        if job.get("url"):
            st.link_button("Open job posting", str(job["url"]))
