"""Local, explainable job-to-profile recommendation utilities."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from src.preprocessing.skill_extractor import extract_skills


SCORE_MIN = 50.0
SCORE_MAX = 100.0
COMPOSITE_WEIGHTS = {
    "skills": 0.45,
    "role": 0.10,
    "location": 0.225,
    "seniority": 0.135,
    "domain": 0.09,
}

ROLE_TERMS = {
    "fullstack": ("full stack", "fullstack"),
    "backend": ("backend", "back-end", "server side", "server-side"),
    "frontend": ("frontend", "front-end", "front end"),
    "devops": ("devops", "dev ops", "site reliability", " sre "),
    "data": ("data engineer", "data scientist", "data analyst", "analytics"),
    "mobile": ("mobile engineer", "mobile developer", "android", "ios"),
    "product": ("product manager", "product owner", "product analyst"),
    "sales": ("sales", "account executive", "business development"),
    "marketing": ("marketing", "brand manager", "growth"),
    "hr": ("human resources", "hr ", "recruiter", "talent acquisition"),
    "finance": ("finance", "accountant", "accounting", "financial analyst"),
    "operations": ("operations", "supply chain", "logistics"),
    "customer_success": ("customer success", "customer support", "client success"),
    "legal": ("legal", "lawyer", "counsel", "compliance"),
    "systems": ("systems engineer", "infrastructure", "network engineer"),
}

ADJACENT_ROLES = {
    "fullstack": {"backend", "frontend", "mobile"},
    "backend": {"fullstack", "devops", "systems", "data"},
    "frontend": {"fullstack", "mobile", "product"},
    "devops": {"backend", "systems", "data"},
    "data": {"backend", "devops", "finance"},
    "mobile": {"frontend", "fullstack"},
    "product": {"frontend", "marketing", "sales"},
    "sales": {"marketing", "customer_success", "product"},
    "marketing": {"sales", "product"},
    "hr": {"operations"},
    "finance": {"operations", "data"},
    "operations": {"finance", "hr", "customer_success"},
    "customer_success": {"sales", "operations"},
    "legal": {"finance", "operations"},
    "systems": {"devops", "backend"},
}

CITY_ALIASES = {
    "bangalore": "bengaluru",
    "bengaluru": "bengaluru",
    "gurgaon": "gurugram",
    "gurugram": "gurugram",
    "bombay": "mumbai",
    "mumbai": "mumbai",
    "madras": "chennai",
    "chennai": "chennai",
    "calcutta": "kolkata",
    "kolkata": "kolkata",
}

SENIORITY_RANKS = {"junior": 0, "mid": 1, "senior": 2, "staff": 3}
JOB_LEVEL_RANKS = {
    "internship": 0,
    "entry level": 0,
    "associate": 1,
    "mid-senior level": 2,
    "director": 3,
    "executive": 3,
}


@dataclass
class CandidateProfile:
    roles: list[str] = field(default_factory=list)
    skills_primary: list[str] = field(default_factory=list)
    skills_secondary: list[str] = field(default_factory=list)
    experience_years: int | None = None
    seniority: str = "Mid"
    domains: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, record: dict[str, Any]) -> "CandidateProfile":
        preferences = record.get("preferences") or {}
        return cls(
            roles=_string_list(record.get("roles")),
            skills_primary=_string_list(record.get("skills_primary")),
            skills_secondary=_string_list(record.get("skills_secondary")),
            experience_years=_as_optional_int(record.get("experience_years")),
            seniority=str(record.get("seniority") or "Mid"),
            domains=_string_list(record.get("domains")),
            preferences=preferences if isinstance(preferences, dict) else {},
        )


def load_profiles(data_dir: Path) -> list[dict[str, Any]]:
    return _load_json(data_dir / "synthetic_profiles.json")


def load_jobs(data_dir: Path) -> list[dict[str, Any]]:
    processed_path = data_dir / "processed" / "scraped_jobs_with_skills.json"
    jobs_path = processed_path if processed_path.exists() else data_dir / "scraped_jobs.json"
    jobs = _load_json(jobs_path)
    for job in jobs:
        extracted = job.get("extracted_Skills")
        if not isinstance(extracted, list):
            job["extracted_Skills"] = extract_skills(job.get("description", ""))
    return jobs


def recommend_jobs(
    profile: CandidateProfile | dict[str, Any],
    jobs: Iterable[dict[str, Any]],
    limit: int = 20,
    role_family: str | None = None,
    location_query: str | None = None,
) -> list[dict[str, Any]]:
    """Score jobs, sort best-fit first, and attach score explanations."""
    candidate = (
        profile
        if isinstance(profile, CandidateProfile)
        else CandidateProfile.from_mapping(profile)
    )
    if limit < 1:
        raise ValueError("limit must be at least 1")

    results: list[dict[str, Any]] = []
    for job in jobs:
        if role_family and role_family != "All" and _job_role_family(job) != role_family:
            continue
        if location_query and location_query.casefold() not in str(
            job.get("location", "")
        ).casefold():
            continue

        dimensions = {
            "Skills": _skill_score(candidate, job),
            "Role": _role_score(candidate, job),
            "Location": _location_score(candidate, job),
            "Seniority": _seniority_score(candidate, job),
            "Domain": _domain_score(candidate, job),
        }
        weighted_fit = sum(
            dimensions[label.title()] * weight
            for label, weight in COMPOSITE_WEIGHTS.items()
        )
        score = SCORE_MIN + (weighted_fit / 100) * (SCORE_MAX - SCORE_MIN)
        matches, gaps = _skill_matches(candidate, job)
        result = dict(job)
        result["recommendation"] = {
            "score": round(score, 1),
            "dimensions": {key: round(value) for key, value in dimensions.items()},
            "matches": matches,
            "gaps": gaps,
            "role_family": _job_role_family(job),
        }
        results.append(result)

    results.sort(
        key=lambda item: (
            -item["recommendation"]["score"],
            -item["recommendation"]["dimensions"]["Skills"],
            str(item.get("title", "")).casefold(),
            str(item.get("id", "")),
        )
    )
    return results[:limit]


def _skill_score(profile: CandidateProfile, job: dict[str, Any]) -> float:
    primary = _unique_skill_values(profile.skills_primary)
    primary_normalized = {_normalize_skill(skill) for skill in primary}
    secondary = [
        skill
        for skill in _unique_skill_values(profile.skills_secondary)
        if _normalize_skill(skill) not in primary_normalized
    ]
    if not primary and not secondary:
        return 50.0

    job_skills = {_normalize_skill(skill) for skill in job.get("extracted_Skills", [])}
    description = str(job.get("description", ""))
    matched_primary = sum(
        _skill_is_present(skill, job_skills, description) for skill in primary
    )
    matched_secondary = sum(
        _skill_is_present(skill, job_skills, description) for skill in secondary
    )
    total_weight = len(primary) * 2 + len(secondary)
    matched_weight = matched_primary * 2 + matched_secondary
    return 100 * matched_weight / total_weight if total_weight else 50.0


def _skill_matches(profile: CandidateProfile, job: dict[str, Any]) -> tuple[list[str], list[str]]:
    job_skills = {_normalize_skill(skill) for skill in job.get("extracted_Skills", [])}
    description = str(job.get("description", ""))
    matches = [
        skill for skill in profile.skills_primary + profile.skills_secondary
        if _skill_is_present(skill, job_skills, description)
    ]
    matched = {_normalize_skill(skill) for skill in matches}
    gaps = [
        skill for skill in profile.skills_primary + profile.skills_secondary
        if _normalize_skill(skill) not in matched
    ]
    return list(dict.fromkeys(matches)), list(dict.fromkeys(gaps))


def _skill_is_present(skill: str, job_skills: set[str], description: str) -> bool:
    normalized = _normalize_skill(skill)
    if normalized in job_skills:
        return True
    if not skill.strip():
        return False
    pattern = r"(?<!\w)" + re.escape(skill.strip()) + r"(?!\w)"
    return re.search(pattern, description, flags=re.IGNORECASE) is not None


def _role_score(profile: CandidateProfile, job: dict[str, Any]) -> float:
    profile_families = {
        family for role in profile.roles if (family := _infer_role_family(role))
    }
    job_family = _job_role_family(job)
    if not profile_families:
        return 60.0
    if job_family in profile_families:
        return 100.0
    if any(job_family in ADJACENT_ROLES.get(family, set()) for family in profile_families):
        return 78.0
    if job_family:
        return 45.0

    role_text = " ".join(profile.roles).casefold()
    title_words = set(re.findall(r"[a-z0-9]+", str(job.get("title", "")).casefold()))
    role_words = set(re.findall(r"[a-z0-9]+", role_text))
    useful_words = role_words - {"engineer", "developer", "senior", "junior", "mid"}
    return 75.0 if useful_words & title_words else 50.0


def _job_role_family(job: dict[str, Any]) -> str:
    hint = str(job.get("role_family_hint") or "").strip().casefold()
    if hint:
        return hint.replace(" ", "_")
    return _infer_role_family(str(job.get("title", "")))


def _infer_role_family(role: str) -> str:
    normalized = f" {role.casefold()} "
    for family, terms in ROLE_TERMS.items():
        if any(term in normalized for term in terms):
            return family
    return ""


def _seniority_score(profile: CandidateProfile, job: dict[str, Any]) -> float:
    profile_rank = SENIORITY_RANKS.get(profile.seniority.casefold())
    job_level = str(job.get("seniority_level") or "").strip().casefold()
    job_rank = JOB_LEVEL_RANKS.get(job_level)
    if job_rank is None:
        title_rank = _rank_from_title(str(job.get("title", "")))
        job_rank = title_rank
    if job_rank is None:
        return 70.0
    if profile_rank is None:
        profile_rank = _rank_from_experience(profile.experience_years)
        return _rank_match_score(profile_rank, job_rank) if profile_rank is not None else 70.0

    declared_level_score = _rank_match_score(profile_rank, job_rank)
    experience_rank = _rank_from_experience(profile.experience_years)
    if experience_rank is None:
        return declared_level_score
    experience_score = _rank_match_score(experience_rank, job_rank)
    return declared_level_score * 0.75 + experience_score * 0.25


def _rank_match_score(profile_rank: int, job_rank: int) -> float:
    distance = abs(profile_rank - job_rank)
    return {0: 100.0, 1: 75.0, 2: 50.0}.get(distance, 30.0)


def _rank_from_experience(experience_years: int | None) -> int | None:
    if experience_years is None:
        return None
    if experience_years <= 2:
        return 0
    if experience_years <= 6:
        return 1
    if experience_years <= 10:
        return 2
    return 3


def _rank_from_title(title: str) -> int | None:
    title = title.casefold()
    if any(term in title for term in ("intern", "entry", "junior", "jr.")):
        return 0
    if any(term in title for term in ("staff", "principal", "director", "executive")):
        return 3
    if any(term in title for term in ("senior", " sr.", "lead", "manager")):
        return 2
    if any(term in title for term in ("associate", "mid-level", "mid level")):
        return 1
    return None


def _domain_score(profile: CandidateProfile, job: dict[str, Any]) -> float:
    domains = [domain.casefold().strip() for domain in profile.domains if domain.strip()]
    if not domains:
        return 70.0
    description = " ".join(
        str(job.get(field, "")) for field in ("industry", "domain_hint", "description")
    ).casefold()
    if not description.strip():
        return 70.0
    for domain in domains:
        if domain in description:
            return 100.0
        tokens = [token for token in re.findall(r"[a-z0-9]+", domain) if len(token) > 3]
        if tokens and any(re.search(r"\b" + re.escape(token) + r"\b", description) for token in tokens):
            return 80.0
    return 45.0


def _location_score(profile: CandidateProfile, job: dict[str, Any]) -> float:
    preferences = profile.preferences
    locations = _string_list(preferences.get("locations"))
    remote_preference = bool(preferences.get("remote"))
    job_location = str(job.get("location", ""))
    is_remote = _is_remote(job)
    if remote_preference and is_remote:
        return 100.0
    if not locations:
        return 70.0

    job_cities = _normalized_cities(job_location)
    requested_cities = set().union(*(_normalized_cities(location) for location in locations))
    if job_cities & requested_cities:
        return 100.0
    if is_remote:
        return 75.0
    return 35.0


def _normalized_cities(value: str) -> set[str]:
    words = re.findall(r"[a-z]+", value.casefold())
    return {CITY_ALIASES[word] for word in words if word in CITY_ALIASES}


def _is_remote(job: dict[str, Any]) -> bool:
    value = job.get("remote_hint")
    if isinstance(value, bool):
        return value
    if str(value).casefold() == "true":
        return True
    return "remote" in str(job.get("location", "")).casefold()


def _unique_skill_values(skills: list[str]) -> list[str]:
    unique: dict[str, str] = {}
    for skill in skills:
        normalized = _normalize_skill(skill)
        if normalized:
            unique.setdefault(normalized, skill.strip())
    return list(unique.values())


def _normalize_skill(skill: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", skill.casefold())


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _as_optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Required dataset file was not found: {path}")
    with path.open(encoding="utf-8") as file:
        records = json.load(file)
    if not isinstance(records, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return records
