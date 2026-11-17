"""Backlog items marked done stay done.

Defect D-BL-01 (17 November 2026): eight backlog items (BL-26 to BL-30, BL-32 to BL-34) were marked done in
knowledge/build.yaml on 5 November but their GitHub issues stayed open, and three of them (BL-28, BL-32, BL-33)
had no test, so the feature could be removed without anything failing. Each done item now names the evidence
that must exist; the check fails if an item is marked done without evidence here, or if the evidence goes.
"""
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUILD = yaml.safe_load((ROOT / "knowledge" / "build.yaml").read_text(encoding="utf-8"))

# Backlog id -> (file, text that must appear in it). One marker per delivered feature.
EVIDENCE = {
    "BL-03": ("docs/transparency/ATRS-AI-ASSISTANT.md", "Algorithmic Transparency"),
    "BL-04": ("scripts/self_check.py", "sources read in full"),
    "BL-05": ("rules/library/geography.yaml", "G06"),
    "BL-07": ("dqkit/rules.py", "iqr"),
    "BL-08": ("dqkit/linkage.py", "recall"),
    "BL-10": (".github/workflows/triage.yml", "needs-reply"),
    "BL-11": ("dqkit/weaver.py", "GeoDCAT"),
    "BL-13": ("dqkit/weaver.py", "SHACL"),
    "BL-14": ("dqkit/weaver.py", "Frictionless"),
    "BL-16": ("packs/un-nqaf.yaml", "NQAF"),
    "BL-18": (".github/workflows/accessibility.yml", "axe"),
    "BL-19": (".github/workflows/content-health.yml", "stale"),
    "BL-20": ("scripts/check_links.py", "archive.org"),
    "BL-21": ("scripts/build_dq_portal.py", "Page last changed"),
    "BL-24": ("scripts/build_dq_portal.py", "dq-commons-offline.zip"),
    "BL-26": ("portal/src/shell.html", "kind of source"),
    "BL-27": ("portal/src/shell.html", "Display options"),
    "BL-28": ("portal/src/pages/learn.html", "progressbar"),
    "BL-29": ("scripts/import_code_evidence.py", "code-evidence.yaml"),
    "BL-30": ("knowledge/feedback.yaml", "sister_routes:"),
    "BL-32": ("portal/src/pages/research.html", 'id="sus"'),
    "BL-33": ("scripts/build_dq_portal.py", "dam_requirements"),
    "BL-34": ("portal/src/shell.html", "journey"),
}


def backlog():
    for value in BUILD.values():
        if isinstance(value, list) and value and isinstance(value[0], dict) and str(value[0].get("id", "")).startswith("BL-"):
            return value
    return []


def problems(items, evidence, root):
    out = []
    for item in items:
        if item.get("status") != "done":
            continue
        if item["id"] not in evidence:
            out.append(f"{item['id']} is marked done but has no evidence in this test")
            continue
        path, marker = evidence[item["id"]]
        f = root / path
        if not f.exists() or marker.lower() not in f.read_text(encoding="utf-8").lower():
            out.append(f"{item['id']}: '{marker}' not found in {path}")
    return out


class BacklogDone(unittest.TestCase):
    def test_every_done_item_has_its_evidence(self):
        items = backlog()
        self.assertTrue(items, "could not read the backlog from knowledge/build.yaml")
        self.assertEqual(problems(items, EVIDENCE, ROOT), [])

    def test_negative_missing_evidence_fails(self):
        # A done item with no evidence entry, and one whose marker is gone, must both be caught.
        fake = [{"id": "BL-99", "status": "done"}, {"id": "BL-26", "status": "done"}]
        found = problems(fake, {"BL-26": ("portal/src/shell.html", "no such marker text 0x7f")}, ROOT)
        self.assertEqual(len(found), 2, found)


class SyncClosesDone(unittest.TestCase):
    """D-BL-01: the backlog sync closes done items' open issues and never reopens or closes anything else."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("b2i", ROOT / "scripts" / "backlog_to_issues.py")
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_closes_only_open_done_issues(self):
        sc = self.m.should_close
        self.assertTrue(sc({"status": "done"}, {"state": "open"}))
        self.assertFalse(sc({"status": "in-progress"}, {"state": "open"}))
        self.assertFalse(sc({"status": "done"}, {"state": "closed"}))
        self.assertFalse(sc({"status": "done"}, {"state": "open", "pull_request": {}}))

    def test_close_comment_quotes_the_delivery_note_and_has_no_email(self):
        text = self.m.close_comment({"id": "BL-26", "done": "5 November 2026 (v2.12.0): source labels."})
        self.assertIn("source labels", text)
        self.assertIn("BL-26", text)
        self.assertNotIn("@", text)


if __name__ == "__main__":
    unittest.main()
