"""Checks for v2.16.0: the questions answered on the community page.

Plain English: every answered question says where it was asked, what was asked and the answer; links are https;
no email address appears; and the community page has the placeholder that shows them. The negative tests prove
each rule catches a bad entry.
"""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COM = yaml.safe_load((ROOT / "knowledge" / "communities.yaml").read_text(encoding="utf-8"))
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def problems(questions):
    out = []
    for i, q in enumerate(questions):
        for k in ("asked", "question", "answer"):
            if not str(q.get(k, "")).strip():
                out.append(f"{i}: no {k}")
        for u in q.get("links", []):
            if not u.startswith("https://"):
                out.append(f"{i}: link not https: {u}")
        if EMAIL.search(repr(q)):
            out.append(f"{i}: email address")
    return out


class CommunityQuestions(unittest.TestCase):
    def test_questions_are_complete_and_safe(self):
        qs = COM.get("questions", [])
        self.assertGreaterEqual(len(qs), 4)
        self.assertEqual(problems(qs), [])

    def test_negative_cases_are_caught(self):
        bad = [{"asked": "x", "question": "", "answer": "y", "links": ["http://insecure.example"]},
               {"asked": "x", "question": "q", "answer": "write to someone@example.gov.uk"}]
        found = problems(bad)
        self.assertTrue(any("no question" in p for p in found))
        self.assertTrue(any("not https" in p for p in found))
        self.assertTrue(any("email" in p for p in found))

    def test_community_page_shows_them(self):
        src = (ROOT / "portal" / "src" / "pages" / "community.html").read_text(encoding="utf-8")
        self.assertIn("__K_COMMUNITY_QUESTIONS__", src)
        self.assertIn('id="questions"', src)


if __name__ == "__main__":
    unittest.main()
