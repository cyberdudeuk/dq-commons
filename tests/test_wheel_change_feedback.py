"""Checks for v2.9.0: the data management wheel, change and delivery roles, and the feedback routes.

Plain English: every wheel area maps only to maturity themes, DMA topics, lifecycle stages and pages that exist,
and speaks to every audience; every RACI activity has exactly one accountable role; every added change role is
in the role picker; the blueprint is complete; and the Microsoft Form never asks for names or emails.
"""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
K = ROOT / "knowledge"
load = lambda n: yaml.safe_load((K / f"{n}.yaml").read_text(encoding="utf-8"))
W, CH, FB, ST, MAT = load("dama-wheel"), load("change-delivery"), load("feedback"), load("stakeholders"), load("maturity")
PAGES = {f.stem for f in (ROOT / "portal" / "src" / "pages").glob("*.html")}


class Wheel(unittest.TestCase):
    def test_eleven_knowledge_areas_with_governance_at_the_centre(self):
        ids = [a["id"] for a in W["areas"]]
        self.assertEqual(len(ids), 11)
        self.assertEqual(len(set(ids)), 11)
        self.assertEqual([a["id"] for a in W["areas"] if a["group"] == "centre"], ["governance"])

    def test_mappings_point_to_things_that_exist(self):
        themes = {t["id"] for t in MAT["themes"]}
        groups = {g["id"] for g in W["groups"]} | {"centre"}
        stages = {s["id"] for s in W["lifecycle"]}
        audiences = {a["id"] for a in W["audiences"]}
        for a in W["areas"]:
            self.assertIn(a["group"], groups, a["id"])
            self.assertTrue(set(a["themes"]) <= themes, a["id"])
            self.assertTrue(a["dma"] and set(a["dma"]) <= set(W["dma"]["topics"]), a["id"])
            self.assertTrue(a["lifecycle"] and set(a["lifecycle"]) <= stages, a["id"])
            self.assertTrue(set(a["pages"]) <= PAGES, f"{a['id']}: {set(a['pages']) - PAGES}")
            self.assertEqual(set(a["views"]), audiences, f"{a['id']} must speak to every audience")
            self.assertTrue(a["dam"] and a["irm"], a["id"])

    def test_every_dma_topic_and_lifecycle_stage_is_used(self):
        used = {t for a in W["areas"] for t in a["dma"]}
        self.assertEqual(len(W["dma"]["topics"]), 10)
        missing = set(W["dma"]["topics"]) - used
        self.assertLessEqual(missing, {"skills"}, "only skills may run through every area without its own mapping")
        area_ids = {a["id"] for a in W["areas"]}
        for s in W["lifecycle"]:
            self.assertTrue(set(s["areas"]) <= area_ids, s["id"])

    def test_join_up_actions_are_concrete(self):
        self.assertEqual(len(W["joinup"]), 10)
        for j in W["joinup"]:
            for k in ("action", "who", "detail", "outcome", "first_step", "measure"):
                self.assertTrue(j.get(k), f"{j['id']} missing {k}")

    def test_frameworks_cover_both_sides(self):
        sides = {f["side"] for f in W["frameworks"]}
        self.assertTrue({"data", "records"} <= sides)


class ChangeRoles(unittest.TestCase):
    def test_one_accountable_role_per_activity(self):
        for a in CH["raci_activities"]:
            accountable = [r for r, v in CH["raci"].items() if v.get(a["id"]) == "A"]
            self.assertEqual(len(accountable), 1, f"{a['id']} has {accountable}")
            for r, v in CH["raci"].items():
                self.assertIn(v.get(a["id"]), {"R", "A", "C", "I"}, f"{r} {a['id']}")

    def test_raci_roles_and_added_roles_are_in_the_picker(self):
        roles = {r["id"]: r for r in ST["roles"]}
        for r in CH["raci"]:
            self.assertIn(r, roles)
        for a in CH["assessment"]:
            if a["verdict"] == "add":
                self.assertEqual(roles[a["id"]].get("group"), "change", a["id"])
        change_ids = {r["id"] for r in ST["roles"] if r.get("group") == "change"}
        self.assertEqual(change_ids, {a["id"] for a in CH["assessment"] if a["verdict"] == "add"})

    def test_role_ids_do_not_clash_with_page_sections(self):
        html = (ROOT / "portal" / "src" / "pages" / "roles.html").read_text(encoding="utf-8")
        sections = set(re.findall(r'<section id="([^"]+)"', html))
        self.assertFalse(sections & {r["id"] for r in ST["roles"]}, "a role id equal to a section id breaks deep links")

    def test_phases_and_blueprint_are_complete(self):
        phases = {p["id"] for p in CH["phases"]}
        for a in CH["raci_activities"]:
            self.assertIn(a["phase"], phases)
        lanes = {l["id"] for l in CH["blueprint"]["lanes"]}
        for p in phases:
            self.assertEqual(set(CH["blueprint"]["cells"][p]), lanes, p)

    def test_change_role_routes_go_to_real_pages(self):
        for r in ST["roles"]:
            if r.get("group") == "change":
                for x in r.get("routes", []):
                    self.assertIn(x["link"].split(".html")[0], PAGES, f"{r['id']}: {x['link']}")


class Feedback(unittest.TestCase):
    def test_form_never_asks_for_names_or_contact_details(self):
        for q in FB["questions"]:
            self.assertIsNone(re.search(r"\b(your name|e-?mail address|phone)\b", q["text"], re.I), q["text"])
        self.assertTrue(any("Record name" in s for s in FB["microsoft_form"]["settings"]))

    def test_form_link_is_empty_or_a_microsoft_forms_address(self):
        for k in ("url", "prefill_url"):
            u = FB["microsoft_form"].get(k) or ""
            self.assertTrue(u == "" or re.match(r"^https://(forms\.office\.com|forms\.microsoft\.com|forms\.cloud\.microsoft)/", u), u)
        if FB["microsoft_form"].get("prefill_url"):
            self.assertIn("PAGE", FB["microsoft_form"]["prefill_url"])

    def test_questions_are_numbered_in_order(self):
        self.assertEqual([q["n"] for q in FB["questions"]], list(range(1, len(FB["questions"]) + 1)))

    def test_routes_link_to_real_pages(self):
        for r in FB["routes"]:
            if r.get("link"):
                self.assertIn(r["link"].split(".html")[0], PAGES, r["id"])


if __name__ == "__main__":
    unittest.main()
