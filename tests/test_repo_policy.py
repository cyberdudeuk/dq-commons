"""Repository policies that must hold on every commit.

1. No decks or films unless explicitly allowed (D-REPO-01): slide decks and video files are never
   committed unless their path is listed in .media-allowlist.
2. No email addresses in anything people read (D-REPO-02): the contact form is the only route, so no
   page, document or data file may contain an email address, apart from GitHub's no-reply addresses
   used by automation.
3. No credentials, private links or protective marking banners (D-REPO-03, adapted from the GitHub Repos
   Asset Catalogue's scan_sensitive.py): tokens and keys, links to private claude.ai chats, projects or
   artifacts, and documents bannered OFFICIAL-SENSITIVE, SECRET or TOP SECRET never belong in a public
   repository. A self-test plants one example of each and fails if any is missed.
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK_FILM = re.compile(r"\.(ppt|pptx|pps|ppsx|key|odp|mp4|m4v|mov|webm|avi|mkv|wmv|mpg|mpeg)$", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
ALLOWED_EMAIL = re.compile(r"(noreply|no-reply)@|@users\.noreply\.github\.com|@example\.|@v\d")
SENSITIVE = [
    ("GitHub token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY")),
    ("Slack webhook", re.compile(r"hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+")),
    ("private claude.ai link", re.compile(r"claude\.ai/(artifact|design|chat|project)/", re.I)),
    ("protective marking banner", re.compile(r"^[ \t>#*]*(OFFICIAL[- ]SENSITIVE|TOP SECRET|SECRET)[ \t*]*$", re.M)),
]
TEXT = re.compile(r"\.(md|html|yaml|yml|json|jsonld|csv|py|js|txt|ttl|toml)$", re.I)


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:  # not a git checkout (for example a source zip): check the folder instead
        return [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]
    return out.stdout.splitlines()


class RepoPolicy(unittest.TestCase):
    def test_no_decks_or_films(self):
        allow = {l.strip() for l in (ROOT / ".media-allowlist").read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("#")}
        bad = [f for f in tracked() if DECK_FILM.search(f) and f not in allow]
        self.assertEqual(bad, [], "Decks and films aren't kept in this repository unless listed in .media-allowlist")

    def test_no_email_addresses(self):
        bad = []
        for f in tracked():
            if not TEXT.search(f) or f.startswith("tests/"):
                continue
            try:
                text = (ROOT / f).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            for m in EMAIL.finditer(text):
                if not ALLOWED_EMAIL.search(m.group(0)):
                    bad.append(f"{f}: {m.group(0)}")
        self.assertEqual(bad, [], "Use the contact form; never publish an email address")


    def test_no_credentials_private_links_or_markings(self):
        bad = []
        for f in tracked():
            if not TEXT.search(f) or f.startswith("tests/"):
                continue
            try:
                text = (ROOT / f).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            bad += [f"{f}: {name}" for name, rx in SENSITIVE if rx.search(text)]
        self.assertEqual(bad, [], "Remove credentials, private links and protective marking banners from the repository")

    def test_sensitive_scan_catches_every_rule(self):
        """The vaccination: one planted example per rule (built at run time, so the file itself stays clean)."""
        planted = {"GitHub token": "ghp_" + "a1" * 18, "Slack token": "xoxb-" + "1234567890-abc",
                   "AWS access key": "AKIA" + "ABCDEFGHIJ123456", "Google API key": "AIza" + "x" * 35,
                   "private key": "-----BEGIN " + "RSA PRIVATE KEY-----", "Slack webhook": "hooks.slack.com/services/T0AB/B0CD/" + "x" * 20,
                   "private claude.ai link": "https://claude.ai/" + "chat/123", "protective marking banner": "\nOFFICIAL" + "-SENSITIVE\n"}
        for name, rx in SENSITIVE:
            self.assertRegex(planted[name], rx, f"the {name} rule missed its planted example")
        self.assertNotRegex("Never post anything marked OFFICIAL-SENSITIVE.", SENSITIVE[-1][1])


if __name__ == "__main__":
    unittest.main()
