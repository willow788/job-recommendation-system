import unittest

from src.preprocessing.skill_extractor import extract_skills
from src.recommender import CandidateProfile, recommend_jobs


class SkillExtractorTests(unittest.TestCase):
    def test_extracts_punctuated_skills_without_partial_word_matches(self):
        skills = extract_skills("Build with Node.js, C++, and SQL. Avoid using NoSQL.")
        self.assertEqual(skills, ["C++", "Node.js", "SQL"])


class RecommenderTests(unittest.TestCase):
    def setUp(self):
        self.profile = CandidateProfile(
            roles=["Backend Engineer"],
            skills_primary=["Python", "Node.js"],
            skills_secondary=["Docker"],
            experience_years=4,
            seniority="Mid",
            domains=["E-commerce"],
            preferences={"locations": ["Bangalore"], "remote": False},
        )
        self.jobs = [
            {
                "id": "match",
                "title": "Backend Engineer",
                "description": "Python Node.js Docker E-commerce Bengaluru",
                "extracted_Skills": ["Python", "Node.js", "Docker"],
                "role_family_hint": "backend",
                "seniority_level": "Associate",
                "industry": "E-commerce",
                "location": "Bengaluru, Karnataka, India",
                "remote_hint": False,
            },
            {
                "id": "other",
                "title": "Marketing Director",
                "description": "Campaign strategy for consumer brands",
                "extracted_Skills": [],
                "role_family_hint": "marketing",
                "seniority_level": "Director",
                "industry": "Retail",
                "location": "Mumbai, Maharashtra, India",
                "remote_hint": False,
            },
        ]

    def test_ranks_relevant_job_first_and_explains_skill_fit(self):
        recommendations = recommend_jobs(self.profile, self.jobs, limit=2)
        self.assertEqual([job["id"] for job in recommendations], ["match", "other"])
        self.assertEqual(
            recommendations[0]["recommendation"]["matches"],
            ["Python", "Node.js", "Docker"],
        )
        self.assertGreater(
            recommendations[0]["recommendation"]["score"],
            recommendations[1]["recommendation"]["score"],
        )

    def test_role_filter_and_invalid_limit(self):
        recommendations = recommend_jobs(
            self.profile, self.jobs, limit=5, role_family="backend"
        )
        self.assertEqual([job["id"] for job in recommendations], ["match"])
        with self.assertRaises(ValueError):
            recommend_jobs(self.profile, self.jobs, limit=0)

    def test_profile_without_skills_uses_neutral_skill_score(self):
        profile = CandidateProfile(roles=["Backend Engineer"])
        recommendations = recommend_jobs(profile, self.jobs, limit=1)
        self.assertEqual(recommendations[0]["recommendation"]["dimensions"]["Skills"], 50)

    def test_experience_refines_declared_seniority(self):
        experienced_profile = CandidateProfile(
            roles=["Backend Engineer"],
            seniority="Mid",
            experience_years=8,
        )
        recommendations = recommend_jobs(experienced_profile, self.jobs, limit=2)
        self.assertEqual(
            recommendations[0]["recommendation"]["dimensions"]["Seniority"],
            94,
        )


if __name__ == "__main__":
    unittest.main()
