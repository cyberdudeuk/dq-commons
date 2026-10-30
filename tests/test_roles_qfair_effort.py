"""Q-FAIR ratings, the effort model, the CDA return columns and the stakeholder and gap register."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import cdareturn, effort, mcp_server, qfair  # noqa: E402


def res(asset=None, met=8, total=8, issues=(), dims=4, checks=()):
    return {"asset": {"id": "a", **(asset or {})}, "as_of": "2026-10-30", "rules_met": met, "rules_total": total,
            "issues": [{"priority": p} for p in issues], "dimensions": {f"d{i}": {"mean_performance": 100} for i in range(dims)},
            "results": [{"check": c} for c in checks]}


class QFair(unittest.TestCase):
    def test_quality_levels(self):
        self.assertEqual(qfair.quality(res())["rating"], "Good")
        self.assertEqual(qfair.quality(res(met=7))["rating"], "Improving")
        self.assertEqual(qfair.quality(res(issues=["High"]))["rating"], "Attention required")
        self.assertEqual(qfair.quality(res(met=5))["rating"], "Attention required")
        self.assertEqual(qfair.quality(res(total=0, met=0))["rating"], "Attention required")

    def test_fair_from_record_never_guessed(self):
        bare = qfair.rate(res())
        self.assertEqual(bare["reusable"]["rating"], "Attention required")
        self.assertIn("licence", bare["reusable"]["missing"])
        full = qfair.rate(res({"iri": "https://x", "title": "t", "description": "d", "owner": "o", "access_route": "open",
                               "classification": "OFFICIAL", "conforms_to": ["CSV"], "identifiers": ["UPRN"], "licence": "OGL-UK-3.0",
                               "provenance": "Administrative records"}))
        self.assertTrue(all(full[p]["rating"] == "Good" for p in qfair.PILLARS))
        self.assertEqual(full["overall"], {**full["overall"], "points": 10, "rating": "Good"})
        # identifier checks in the rules count as shared identifiers
        self.assertEqual(qfair.rate(res({"conforms_to": ["CSV"]}, checks=["identifier"]))["interoperable"]["rating"], "Good")

    def test_return_columns(self):
        for c in ["gds_accessroute", "gds_licence", "gds_qfair_overall", "gds_baselineconfidence"] + [f"gds_qfair_{p}" for p in qfair.PILLARS]:
            self.assertIn(c, cdareturn.COLUMNS)
        row = cdareturn.row({**res({"licence": "OGL-UK-3.0"}), "results": []})
        self.assertEqual(row["gds_licence"], "OGL-UK-3.0")
        self.assertEqual(row["gds_qfair_reusable"], "Improving")


class Effort(unittest.TestCase):
    def test_scenarios_order_and_sense(self):
        s = effort.scenarios(56)
        self.assertEqual(len(s), 4)
        pd = [x["person_days"] for x in s]
        self.assertTrue(pd[0] > pd[1] > pd[3] and pd[0] > pd[2] > pd[3], pd)
        self.assertEqual(s[3]["share_achievable"], 100)
        self.assertLess(s[0]["share_achievable"], 60)
        # per-CDA tier totals: unmeasured assets take far longer than measured ones
        a, b, c = s[0]["per_cda_by_tier"]
        self.assertTrue(a < b < c)

    def test_known_value_matches_portal(self):
        # Same inputs as the portal's defaults on a 56-day window (checked in the browser: 7,465 person-days)
        self.assertEqual(effort.estimate(56)["person_days"], 7465)

    def test_working_days_skip_holidays(self):
        from datetime import date
        self.assertEqual(effort.working_days(date(2026, 12, 21), date(2027, 1, 1)), 7)  # 25, 28 Dec and 1 Jan are holidays

    def test_mcp(self):
        self.assertEqual(len(mcp_server.call_tool("estimate_effort", {"days": 56})["scenarios"]), 4)
        self.assertIn("person_days", mcp_server.call_tool("estimate_effort", {"days": 56, "proportionate": True}))


class Stakeholders(unittest.TestCase):
    def test_register(self):
        d = yaml.safe_load((ROOT / "knowledge" / "stakeholders.yaml").read_text(encoding="utf-8"))
        roles = {r["id"] for r in d["roles"]}
        self.assertTrue({"council", "cdo", "owner", "steward", "dqlead"} <= roles)
        pages = {p.stem for p in (ROOT / "portal" / "src" / "pages").glob("*.html")}
        for r in d["roles"]:
            for k in ("needs", "decide", "watch", "measures"):
                self.assertTrue(all(isinstance(x, str) for x in r.get(k, [])), f"{r['id']}.{k}")
            for link in r.get("routes", []):
                self.assertIn(link["link"].split("#")[0].split(".")[0], pages, link)
        ids = [g["id"] for g in d["gaps"]]
        self.assertEqual(len(ids), len(set(ids)))
        for g in d["gaps"]:
            self.assertIn(g["status"], ("addressed", "partly", "open"), g["id"])
            self.assertIn(g["severity"], ("High", "Medium", "Low"), g["id"])
            self.assertTrue(set(g["affects"]) <= roles, g["id"])
            if g["status"] == "addressed":
                self.assertTrue(g.get("where"), f"{g['id']}: say where it is addressed")
            if g.get("where"):
                self.assertIn(g["where"].split("#")[0].split(".")[0], pages, g["id"])
        for dt in d["dates"]:
            self.assertIn("confirmed", dt)


if __name__ == "__main__":
    unittest.main()
