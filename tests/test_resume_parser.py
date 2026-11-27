from io import BytesIO
import unittest

from docx import Document
from pypdf import PdfWriter

from src.resume_parser import ResumeParseError, parse_resume


RESUME_TEXT = """\
Jordan Lee
jordan.lee@example.com | +91 98765 43210 | Bengaluru
linkedin.com/in/jordan-lee

Professional Summary
Senior backend engineer with 7+ years of experience in fintech.

Work Experience
Senior Backend Engineer | Fintech Labs | 2021 - Present
Backend Engineer | Commerce Co | 2018 - 2021

Technical Skills
Python, Django, PostgreSQL, Docker, AWS, Redis

Education
Bachelor of Technology, Computer Science

Certifications
AWS Certified Developer
"""


class ResumeParserTests(unittest.TestCase):
    def test_extracts_contact_profile_and_resume_sections_from_text(self):
        result = parse_resume("candidate.txt", RESUME_TEXT.encode("utf-8"))
        candidate = result["candidate"]

        self.assertEqual(result["contact"]["name"], "Jordan Lee")
        self.assertEqual(result["contact"]["email"], "jordan.lee@example.com")
        self.assertEqual(result["contact"]["location"], "Bengaluru")
        self.assertEqual(candidate["roles"][0], "Senior Backend Engineer")
        self.assertEqual(candidate["experience_years"], 7)
        self.assertEqual(candidate["seniority"], "Senior")
        self.assertIn("Python", candidate["skills_primary"])
        self.assertEqual(candidate["domains"], ["Fintech"])
        self.assertIn("Bachelor of Technology, Computer Science", result["education"])
        self.assertIn("AWS Certified Developer", result["certifications"])

    def test_extracts_text_from_docx_tables_and_paragraphs(self):
        document = Document()
        document.add_paragraph("Morgan Chen")
        document.add_paragraph("morgan@example.com")
        document.add_paragraph("Skills")
        table = document.add_table(rows=1, cols=1)
        table.cell(0, 0).text = "Python, PostgreSQL, Docker"
        output = BytesIO()
        document.save(output)

        result = parse_resume("candidate.docx", output.getvalue())
        self.assertEqual(result["contact"]["name"], "Morgan Chen")
        self.assertIn("Python", result["candidate"]["skills_primary"])
        self.assertIn("PostgreSQL", result["candidate"]["skills_primary"])

    def test_rejects_empty_or_unsupported_uploads(self):
        with self.assertRaises(ResumeParseError):
            parse_resume("candidate.pdf", b"")
        with self.assertRaises(ResumeParseError):
            parse_resume("candidate.rtf", b"some text")
        with self.assertRaisesRegex(ResumeParseError, "PDF could not be read"):
            parse_resume("broken.pdf", b"not a pdf")

    def test_explains_scanned_or_textless_pdfs(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        output = BytesIO()
        writer.write(output)

        with self.assertRaisesRegex(ResumeParseError, "No selectable text"):
            parse_resume("candidate.pdf", output.getvalue())


if __name__ == "__main__":
    unittest.main()
