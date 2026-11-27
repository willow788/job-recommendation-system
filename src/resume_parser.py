"""Local extraction of candidate details from common resume file formats."""

from __future__ import annotations

import re
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.preprocessing.skill_extractor import extract_skills


MAX_RESUME_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 100

SECTION_NAMES = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "about",
        "career objective",
        "objective",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "career history",
        "work history",
    },
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "competencies",
        "areas of expertise",
    },
    "education": {"education", "academic background", "qualifications"},
    "certifications": {"certifications", "certificates", "licenses"},
    "languages": {"languages", "language skills"},
}

ROLE_CUES = (
    "engineer",
    "developer",
    "analyst",
    "manager",
    "consultant",
    "designer",
    "scientist",
    "architect",
    "specialist",
    "director",
    "lead",
    "intern",
    "administrator",
    "executive",
    "associate",
    "recruiter",
    "accountant",
    "lawyer",
    "researcher",
    "marketing",
    "sales",
    "product owner",
    "customer success",
)

DOMAINS = (
    "Enterprise SaaS",
    "E-commerce",
    "Developer Tools",
    "Consumer Goods",
    "Social Media",
    "Manufacturing",
    "Healthcare",
    "Education",
    "EdTech",
    "Fintech",
    "Banking",
    "Analytics",
    "Logistics",
    "HR Tech",
    "Automotive",
    "Gaming",
    "Payments",
    "Consulting",
    "Biotech",
    "Travel",
    "Retail",
)

CITY_NAMES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "madras": "Chennai",
    "chennai": "Chennai",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur",
    "kochi": "Kochi",
    "noida": "Noida",
    "delhi": "Delhi",
}


class ResumeParseError(ValueError):
    """Raised when a resume is invalid, unsupported, or has no readable text."""


def parse_resume(filename: str, content: bytes) -> dict[str, Any]:
    """Extract contact and job-matching details from an uploaded resume."""
    if not content:
        raise ResumeParseError("The uploaded file is empty.")
    if len(content) > MAX_RESUME_BYTES:
        raise ResumeParseError("Resume files must be 10 MB or smaller.")

    suffix = Path(filename).suffix.casefold()
    if suffix == ".pdf":
        text = _read_pdf(content)
    elif suffix == ".docx":
        text = _read_docx(content)
    elif suffix == ".txt":
        text = _read_text(content)
    else:
        raise ResumeParseError("Use a PDF, DOCX, or TXT resume.")

    lines = [line.strip(" \t•*-") for line in text.replace("\r", "\n").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise ResumeParseError("No readable text was found in the resume.")

    sections = _split_sections(lines)
    full_text = "\n".join(lines)
    header = "\n".join(lines[:12])
    experience_years = _extract_experience_years(full_text)
    experience_lines = sections.get("experience", [])
    roles = _extract_roles(experience_lines)
    if not roles:
        roles = _extract_roles(lines[:20])

    listed_skills = extract_skills("\n".join(sections.get("skills", [])))
    all_skills = extract_skills(full_text)
    skills = list(dict.fromkeys(listed_skills + all_skills))
    domain_context = "\n".join(
        line
        for section in ("header", "summary", "experience", "skills")
        for line in sections.get(section, [])
    )
    domains = _extract_domains(domain_context)
    location = _extract_location(header)
    remote = bool(re.search(r"\bremote\b", header, flags=re.IGNORECASE))

    candidate = {
        "roles": roles,
        "skills_primary": skills[:6],
        "skills_secondary": skills[6:9],
        "experience_years": experience_years,
        "seniority": _infer_seniority(roles, experience_years),
        "domains": domains,
        "preferences": {
            "locations": [location] if location else [],
            "remote": remote,
            "min_salary": None,
            "company_sizes": [],
        },
    }

    contact = {
        "name": _extract_name(lines[:12]),
        "email": _first_match(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", header),
        "phone": _extract_phone(header),
        "location": location,
        "linkedin": _first_match(
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Z0-9._%/-]+",
            header,
        ),
        "github": _first_match(
            r"(?:https?://)?(?:www\.)?github\.com/[A-Z0-9-]+",
            header,
        ),
    }

    return {
        "candidate": candidate,
        "contact": contact,
        "summary": " ".join(sections.get("summary", []))[:1200],
        "education": sections.get("education", [])[:12],
        "certifications": sections.get("certifications", [])[:12],
        "languages": sections.get("languages", [])[:8],
        "work_history": experience_lines[:20],
        "missing_fields": [
            label
            for label, value in (
                ("name", contact["name"]),
                ("email", contact["email"]),
                ("phone", contact["phone"]),
                ("target role", roles),
                ("skills", skills),
                ("experience", experience_years),
                ("location", location),
            )
            if not value
        ],
    }


def _read_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted and not reader.decrypt(""):
            raise ResumeParseError("This PDF is password-protected. Upload an unlocked copy.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ResumeParseError("Resume PDFs must have 100 pages or fewer.")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as error:
        raise ResumeParseError("The PDF could not be read. Try exporting it again.") from error
    if not text.strip():
        raise ResumeParseError(
            "No selectable text was found. Scanned-image PDFs need OCR before upload."
        )
    return text


def _read_docx(content: bytes) -> str:
    try:
        document = Document(BytesIO(content))
    except (PackageNotFoundError, zipfile.BadZipFile) as error:
        raise ResumeParseError("The DOCX file is invalid or damaged.") from error

    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells if cell.text.strip()))
    text = "\n".join(parts)
    if not text.strip():
        raise ResumeParseError("No readable text was found in the DOCX resume.")
    return text


def _read_text(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return content.decode("cp1252")
        except UnicodeDecodeError as error:
            raise ResumeParseError("The TXT file encoding is not supported.") from error


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    heading_lookup = {
        re.sub(r"[^a-z ]", "", heading.casefold()).strip(): name
        for name, headings in SECTION_NAMES.items()
        for heading in headings
    }
    for line in lines:
        normalized = re.sub(r"[^a-z ]", "", line.casefold()).strip()
        section = heading_lookup.get(normalized)
        if section:
            current = section
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def _extract_name(lines: list[str]) -> str | None:
    ignored = {"resume", "curriculum vitae", "cv"}
    for line in lines:
        candidate = re.split(r"\s+[|•]\s+", line, maxsplit=1)[0].strip()
        if (
            candidate.casefold() not in ignored
            and len(candidate) <= 60
            and re.search(r"[A-Za-z]", candidate)
            and not re.search(r"\d|@", candidate)
            and not re.search(r"\b(?:linkedin|github|www\.)\b", candidate, re.I)
        ):
            return candidate
    return None


def _extract_phone(text: str) -> str | None:
    for match in re.finditer(r"(?<!\w)\+?[\d][\d(). \-]{7,}\d(?!\w)", text):
        digits = re.sub(r"\D", "", match.group())
        if 10 <= len(digits) <= 15:
            return match.group().strip()
    return None


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group().rstrip(".,;") if match else None


def _extract_location(text: str) -> str | None:
    for city, canonical in CITY_NAMES.items():
        if re.search(r"\b" + re.escape(city) + r"\b", text, flags=re.IGNORECASE):
            return canonical
    return "Remote" if re.search(r"\bremote\b", text, flags=re.IGNORECASE) else None


def _extract_roles(lines: list[str]) -> list[str]:
    roles: list[str] = []
    for line in lines:
        if len(line) > 120 or not any(cue in line.casefold() for cue in ROLE_CUES):
            continue
        title = re.split(r"\s+[|•]\s+", line, maxsplit=1)[0].strip(" ,:-")
        title = re.sub(
            r"\b(?:19|20)\d{2}\b.*$",
            "",
            title,
        ).strip(" ,:-")
        if title and title.casefold() not in {role.casefold() for role in roles}:
            roles.append(title)
        if len(roles) == 5:
            break
    return roles


def _extract_experience_years(text: str) -> int | None:
    explicit = re.search(
        r"\b(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s+)?"
        r"(?:professional\s+)?experience\b",
        text,
        flags=re.IGNORECASE,
    )
    if explicit:
        return int(explicit.group(1))

    current_year = datetime.now().year
    ranges: list[tuple[int, int]] = []
    for match in re.finditer(
        r"\b((?:19|20)\d{2})\s*(?:-|–|—|to)\s*"
        r"(present|current|(?:19|20)\d{2})\b",
        text,
        flags=re.IGNORECASE,
    ):
        start = int(match.group(1))
        end = current_year if match.group(2).casefold() in {"present", "current"} else int(match.group(2))
        if start <= end <= current_year and end - start <= 40:
            ranges.append((start, end))
    if not ranges:
        return None

    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    total_years = sum(end - start for start, end in merged)
    return max(1, total_years) if total_years else None


def _infer_seniority(roles: list[str], experience_years: int | None) -> str:
    role_text = roles[0].casefold() if roles else ""
    if re.search(r"\b(staff|principal|director|executive|head)\b", role_text):
        return "Staff"
    if re.search(r"\b(senior|sr\.?|lead)\b", role_text):
        return "Senior"
    if re.search(r"\b(junior|jr\.?|intern|entry-level|graduate)\b", role_text):
        return "Junior"
    if experience_years is None:
        return "Mid"
    if experience_years <= 2:
        return "Junior"
    if experience_years <= 6:
        return "Mid"
    if experience_years <= 10:
        return "Senior"
    return "Staff"


def _extract_domains(text: str) -> list[str]:
    domains = []
    for domain in DOMAINS:
        if re.search(r"\b" + re.escape(domain) + r"\b", text, flags=re.IGNORECASE):
            domains.append(domain)
    return domains[:5]
