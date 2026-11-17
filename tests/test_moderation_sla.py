"""Moderation service levels reach every issue form that waits for a person.

Defect D-MOD-01 (17 November 2026, issue #42): a "[Join]" request waited past its 5-working-day first
reply unseen. The Triage workflow only scanned `contact` and `contribution`, the join form's `community`
label did not exist (GitHub silently skips unknown labels), and the form promised 10 working days while
docs/MODERATION.md and the welcome reply promise 5. These checks stop each of those recurring.
"""
import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FORMS = ROOT / ".github" / "ISSUE_TEMPLATE"
TRIAGE = (ROOT / ".github" / "workflows" / "triage.yml").read_text(encoding="utf-8")
BASELINE = json.loads((ROOT / ".github" / "settings-baseline.json").read_text(encoding="utf-8"))
REQUIRED = set(BASELINE["labels"]["required"][0])
# First-reply promises allowed by docs/MODERATION.md section 2.
ALLOWED_REPLY_DAYS = {"1", "2", "5"}


def forms():
    for f in sorted(FORMS.glob("*.yml")):
        if f.name == "config.yml":
            continue
        yield f, yaml.safe_load(f.read_text(encoding="utf-8"))


def scanned_labels():
    m = re.search(r"for \(const label of \[([^\]]*)\]\)", TRIAGE)
    return set(re.findall(r"'([^']+)'", m.group(1))) if m else set()


class ModerationSla(unittest.TestCase):
    def test_every_form_label_exists_in_the_baseline(self):
        for f, form in forms():
            for label in form.get("labels", []):
                self.assertIn(label, REQUIRED, f"{f.name}: label '{label}' is not in settings-baseline.json")

    def test_triage_scans_every_form_that_waits_for_a_moderator(self):
        scanned = scanned_labels()
        self.assertTrue(scanned, "could not read the labels the Triage workflow scans")
        for f, form in forms():
            labels = set(form.get("labels", []))
            if "triage" in labels or "contact" in labels or "contribution" in labels:
                self.assertTrue(labels & scanned, f"{f.name}: none of {sorted(labels)} is scanned by triage.yml")

    def test_reply_promises_match_the_service_levels(self):
        for f in FORMS.glob("*.yml"):
            for days in re.findall(r"reply[^.\"]*?within (\d+) working day", f.read_text(encoding="utf-8")):
                self.assertIn(days, ALLOWED_REPLY_DAYS, f"{f.name} promises a first reply in {days} working days")


if __name__ == "__main__":
    unittest.main()
