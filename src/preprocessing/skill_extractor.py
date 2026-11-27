import re

try:
    from .skills_dictionary import SKILL_DICTIONARY
except ImportError:
    from skills_dictionary import SKILL_DICTIONARY

__all__ = ["SKILL_DICTIONARY"]


def extract_skills(text: str) -> list[str]:

    if not isinstance(text, str):
        return []

    extracted_skills = set()

    for canonical_skill, aliases in SKILL_DICTIONARY.items():
        for alias in aliases:
            pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
            if re.search(pattern, text, flags=re.IGNORECASE):
                extracted_skills.add(canonical_skill)
                break

    return sorted(extracted_skills)

