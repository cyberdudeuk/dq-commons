"""Tests for the automated pipeline: portfolio runner, rule suggestion and the GitHub Actions workflows.

Run with `python -m unittest discover -s tests -v`.
"""
import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from dqkit import cli, portfolio, profile, rules, workbook

ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO = ROOT / "portfolio.ndl.yaml"
CHART_DIR = ROOT / "assessments" / "ndl" / "chart-data"
AIR = "ndl-environment-air-quality-chart"
CHARTS = {  # same mapping as scripts/run_ndl_assessment.py
    "births.yaml": "people__births.csv",
    "childhood-vaccinations.yaml": "early-years__childhood-vaccinations.csv",
    "road-traffic.yaml": "transport__road-traffic.csv",
    "air-quality.yaml": "environment__air-quality.csv",
    "election-results.yaml": "government-and-parliament__election-results.csv",
    "mot-results.yaml": "transport__mot-results.csv",
    "council-tax.yaml": "government-and-parliament__council-tax-statistics.csv",
    "social-mobility.yaml": "people__social-mobility.csv",
}


def _run(out, as_of, **kw):
    return portfolio.run(PORTFOLIO, date.fromisoformat(as_of), out, log=lambda *a: None, **kw)


def _rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _keys(lst):
    return {(x["asset_id"], x["rule_id"]) for x in lst}


class PortfolioRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.result = _run(cls.out, "2026-10-14")
        cls.doc = json.loads((cls.out / "portfolio.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_output_file_is_written(self):
        for f in ("portfolio.json", "catalogue.dqv.jsonld", "escalations.json", "run-summary.md", "metadata-assessment.json"):
            self.assertTrue((self.out / f).exists(), f)
        for a in self.doc["assets"]:
            for rel in a["files"].values():
                self.assertTrue((self.out / rel).exists(), rel)
            self.assertTrue((self.out / "history" / f"{a['id']}.history.csv").exists())

    def test_cda_return_rows(self):
        from dqkit import cdareturn
        rows = _rows(self.out / "cda-return.csv")
        self.assertEqual(len(rows), len(self.doc["assets"]))
        self.assertEqual(list(rows[0].keys()), cdareturn.COLUMNS)
        by_id = {a["id"]: a for a in self.doc["assets"]}
        for r in rows:
            total = sum(int(r[f"gds_dqissues_{p}"]) for p in ("critical", "high", "medium", "low"))
            match = [a for a in by_id.values() if r["cda_title"] == a.get("title")]
            if match:
                self.assertEqual(total, len(match[0]["issues"]))
            self.assertIn(r["gds_dqtrustlevel"], ("Untrustworthy", "Requires improvement", "Useable", "Trustworthy"))

    def test_portfolio_json_shape(self):
        d = self.doc
        self.assertEqual(d["as_of"], "2026-10-14")
        self.assertEqual(len(d["assets"]), 8)
        for k in ("portfolio", "run_at", "fingerprint", "totals", "assets", "metadata", "changes", "files"):
            self.assertIn(k, d)
        for a in d["assets"]:
            for k in ("id", "title", "owner", "rules_met", "rules_total", "issues", "trust", "route", "operations",
                      "overdue", "dimensions", "measured"):
                self.assertIn(k, a)
            for i in a["issues"]:
                self.assertIn(i["priority"], ("Critical", "High", "Medium", "Low"))
                self.assertTrue(i["resolution"])
        self.assertEqual(d["totals"]["rules_total"], 49)
        self.assertEqual(d["metadata"]["records"], 84)
        self.assertEqual(len(d["metadata"]["checks"]), 20)
        self.assertEqual(set(d["changes"]), {"compared_with", "new", "resolved", "still_open"})

    def test_matches_run_ndl_assessment(self):
        """Same rules_met and trust per asset as scripts/run_ndl_assessment.py, which runs without history."""
        from dqkit import trust
        got = {a["id"]: a for a in self.doc["assets"]}
        for rf, cf in CHARTS.items():
            spec = rules.load_rules(ROOT / "rules" / "ndl" / rf)
            df = pd.read_csv(CHART_DIR / cf, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
            res = rules.run(df, spec, date(2026, 10, 14))
            a = got[spec["asset"]["id"]]
            self.assertEqual((a["rules_met"], a["rules_total"]), (res["rules_met"], res["rules_total"]), rf)
            self.assertEqual(a["trust"]["level"], trust.classify(res)["level"], rf)

    def test_catalogue_is_one_graph(self):
        cat = json.loads((self.out / "catalogue.dqv.jsonld").read_text())
        self.assertIn("@context", cat)
        ids = [n["@id"] for n in cat["@graph"]]
        self.assertEqual(len(ids), len(set(ids)))
        datasets = [n for n in cat["@graph"] if n.get("@type") == "dcat:Dataset"]
        # The 8 chart files share their IRI with their NDL catalogue page, so they merge into those 84 nodes.
        self.assertEqual(len(datasets), 84)
        air = next(n for n in datasets if n["@id"] == "https://www.data.gov.uk/collections/environment/air-quality")
        measured = {m["@id"].split("#m-")[1] for m in air["dqv:hasQualityMeasurement"]}
        self.assertTrue({"R4", "DAM-1"} <= measured)  # a chart rule and a page check

    def test_deterministic_given_as_of(self):
        with tempfile.TemporaryDirectory() as d:
            again = json.loads((_run(Path(d), "2026-10-14")["out"] / "portfolio.json").read_text())
        self.assertEqual(again["fingerprint"], self.doc["fingerprint"])
        self.assertEqual(again["assets"], self.doc["assets"])


class ChangesAndEscalations(unittest.TestCase):
    def test_new_then_resolved(self):
        """Air quality freshness (R4) passes on 2026-04-14 and fails on 2026-10-14 (see examples/illustrative-escalation)."""
        with tempfile.TemporaryDirectory() as d:
            first = _run(d, "2026-04-14", history=False)["portfolio"]
            self.assertIsNone(first["changes"]["compared_with"])
            self.assertNotIn((AIR, "R4"), _keys(first["changes"]["new"]))
            later = _run(d, "2026-10-14", history=False)["portfolio"]
            self.assertEqual(later["changes"]["compared_with"], "2026-04-14")
            self.assertEqual(_keys(later["changes"]["new"]), {(AIR, "R4")})
            self.assertEqual(later["changes"]["resolved"], [])
            self.assertTrue(later["changes"]["still_open"])
            back = _run(d, "2026-04-14", history=False)["portfolio"]
            self.assertEqual(_keys(back["changes"]["resolved"]), {(AIR, "R4")})
            self.assertEqual(back["changes"]["new"], [])

    def test_overdue_escalations_after_three_cycles(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(_run(d, "2026-04-14")["escalations"], [])
            _run(d, "2026-07-14")
            out = _run(d, "2026-10-14")
            esc = json.loads((Path(d) / "escalations.json").read_text())
            self.assertEqual(esc, out["escalations"])
            self.assertTrue(esc)
            for e in esc:
                self.assertIn(e["priority"], ("Critical", "High"))
                self.assertGreater(e["cycles_open"], 1)
                self.assertTrue(e["title"].startswith(f"[DQ] {e['asset_id']} {e['rule_id']}"))
                for k in ("asset_id", "rule_id", "priority", "cycles_open", "escalate_to", "title", "body_markdown"):
                    self.assertIn(k, e)
            air = next(e for e in esc if (e["asset_id"], e["rule_id"]) == (AIR, "R4"))
            self.assertEqual(air["cycles_open"], 2)
            self.assertIn("overdue", air["body_markdown"])
            self.assertIn("supplier", air["escalate_to"])
            # The Medium MOT issue is open too, but Medium is not escalated by this portfolio.
            self.assertNotIn("Medium", {e["priority"] for e in esc})
            doc = out["portfolio"]
            self.assertEqual(doc["totals"]["escalations"], len(esc))
            self.assertEqual(sum(1 for a in doc["assets"] for _ in a["overdue"]), doc["totals"]["overdue_issues"])

    def test_exit_code_with_fail_on_escalation(self):
        with tempfile.TemporaryDirectory() as d:
            for day in ("2026-04-14", "2026-07-14"):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.main(["run", str(PORTFOLIO), "--out", d, "--as-of", day]), 0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["run", str(PORTFOLIO), "--out", d, "--as-of", "2026-10-14", "--fail-on-escalation"]), 2)

    def test_not_due_assets_are_carried_forward(self):
        with tempfile.TemporaryDirectory() as d:
            _run(d, "2026-10-14")
            later = _run(d, "2026-10-21")["portfolio"]
            self.assertEqual(later["totals"]["assets_measured"], 0)
            self.assertTrue(all(a["measured_on"] == "2026-10-14" for a in later["assets"]))
            rows = _rows(Path(d) / "history" / f"{AIR}.history.csv")
            self.assertEqual({r["date"] for r in rows}, {"2026-10-14"})
            forced = _run(d, "2026-10-21", ignore_schedule=True)["portfolio"]
            self.assertEqual(forced["totals"]["assets_measured"], 8)


class HistoryDedup(unittest.TestCase):
    def test_same_date_twice_replaces_rows(self):
        spec = rules.load_rules(ROOT / "rules" / "ndl" / "air-quality.yaml")
        df = pd.read_csv(CHART_DIR / "environment__air-quality.csv", dtype=str, keep_default_na=False, na_values=[""])
        with tempfile.TemporaryDirectory() as d:
            for day in ("2026-04-14", "2026-10-14", "2026-10-14", "2026-07-14"):
                p = workbook.append_history(rules.run(df, spec, date.fromisoformat(day)), d)
            rows = _rows(p)
            self.assertEqual(len(rows), 3 * len(spec["rules"]))
            self.assertEqual([r["date"] for r in rows], sorted(r["date"] for r in rows))
            self.assertEqual(len(workbook.load_history(d, spec["asset"]["id"])["R1"]), 3)

    def test_portfolio_rerun_same_date(self):
        with tempfile.TemporaryDirectory() as d:
            _run(d, "2026-10-14")
            _run(d, "2026-10-14")
            rows = _rows(Path(d) / "history" / f"{AIR}.history.csv")
            self.assertEqual(len(rows), 6)


class Suggest(unittest.TestCase):
    def test_suggested_rules_load_and_mostly_pass_on_every_chart(self):
        for cf in CHARTS.values():
            df = pd.read_csv(CHART_DIR / cf, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
            spec = profile.suggest(df, {"id": "draft", "title": cf})
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "rules.yaml"
                p.write_text(profile.to_yaml(spec, cf))
                loaded = rules.load_rules(p)
            self.assertEqual(loaded, profile.clean(spec), cf)
            self.assertEqual(list(loaded["rules"][0])[:2], ["id", "check"])  # key order kept
            res = rules.run(df, loaded, date(2026, 10, 14))
            self.assertGreaterEqual(res["rules_met"] / res["rules_total"], 0.8, cf)
            for r in loaded["rules"]:
                self.assertEqual(r["purpose"], profile.TBC)
                self.assertTrue(r["description"])
            checks = {r["check"] for r in loaded["rules"]}
            self.assertTrue({"required_columns", "not_null", "type"} <= checks, cf)

    def test_profile_detects_kinds(self):
        df = pd.DataFrame({
            "area_code": ["E06000001", "E06000002", "W06000001", "S12000033"] * 3,
            "period": ["2021-22", "2022-23", "2023-24"] * 4,
            "sex": ["Male", "Female", "Not stated"] * 4,
            "count": [str(i * 10) for i in range(12)],
            "rate": ["1.5", "", "2.5", "3.0"] * 3,
        })
        p = profile.profile(df)
        c = p["columns"]
        self.assertTrue(c["area_code"]["geography"])
        self.assertEqual(c["period"]["kind"], "year_label")
        self.assertEqual(c["count"]["kind"], "integer")
        self.assertEqual(c["rate"]["kind"], "number")
        self.assertTrue(c["sex"]["demographic"])
        self.assertEqual(c["sex"]["small_set"], ["Female", "Male", "Not stated"])
        self.assertEqual(p["key"], ["area_code", "period"])
        spec = profile.suggest(df, {"id": "t"})
        by_check = {}
        for r in spec["rules"]:
            by_check.setdefault(r["check"], []).append(r)
        self.assertNotIn("rate", [r.get("column") for r in by_check["not_null"]])  # 25% empty
        self.assertEqual(by_check["unique"][0]["columns"], ["area_code", "period"])
        self.assertTrue(any(r.get("column") == "sex" for r in by_check["not_unknown"]))
        self.assertTrue(any(r.get("column") == "area_code" for r in by_check["regex"]))
        text = profile.to_yaml(spec)
        self.assertIn("#   check: group_disparity", text)
        self.assertIn("DRAFT", text)
        rules.run(df, yaml.safe_load(text), date(2026, 10, 14))  # runs without errors

    def test_cli_suggest_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "r.yaml"
            with redirect_stdout(io.StringIO()):
                rc = cli.main(["suggest", str(CHART_DIR / "people__births.csv"), "--owner", "ONS", "--out", str(out)])
            self.assertEqual(rc, 0)
            spec = rules.load_rules(out)
            self.assertEqual(spec["asset"]["id"], "people-births")
            self.assertEqual(spec["asset"]["owner"], "ONS")


class Validation(unittest.TestCase):
    def test_bad_portfolio_gives_friendly_message(self):
        bad = {"portfolio": {"id": "x", "title": "X"},  # owner missing
               "assets": [{"rules": "rules/ndl/births.yaml", "data": "x.csv"},
                          {"rules": "rules/ndl/air-quality.yaml", "schedule": "fortnightly"}]}
        with self.assertRaises(portfolio.PortfolioError) as cm:
            portfolio.validate(bad, "test.yaml")
        msg = str(cm.exception)
        self.assertIn("Asset 2 (rules/ndl/air-quality.yaml)", msg)
        self.assertIn("'data' is a required property", msg)
        self.assertIn("fortnightly", msg)
        self.assertIn("'owner' is a required property", msg)

    def test_missing_data_file_and_cli_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.yaml"
            p.write_text(yaml.safe_dump({"portfolio": {"id": "x", "title": "X", "owner": "Me"},
                                         "assets": [{"rules": str(ROOT / "rules/ndl/births.yaml"), "data": "nope.csv"}]}))
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                rc = cli.main(["run", str(p), "--out", str(Path(d) / "out")])
            self.assertEqual(rc, 1)
            self.assertIn("Asset 1", err.getvalue())
            self.assertIn("nope.csv", err.getvalue())

    def test_shipped_portfolio_is_valid(self):
        doc = portfolio.load(PORTFOLIO)
        self.assertEqual(len(doc["assets"]), 8)
        self.assertEqual(doc["defaults"]["history_dir"], "history")


class Workflows(unittest.TestCase):
    """GitHub Actions cannot run here, so check the workflow files' structure instead."""

    @staticmethod
    def _load(name):
        wf = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text())
        wf["on"] = wf.get("on", wf.pop(True, None))  # pyyaml reads the key `on` as True
        return wf

    @staticmethod
    def _uses(job):
        return [s["uses"] for s in job["steps"] if "uses" in s]

    @staticmethod
    def _runs(job):
        return "\n".join(s.get("run", "") for s in job["steps"])

    def test_pipeline_workflow(self):
        wf = self._load("dq-pipeline.yml")
        self.assertEqual(wf["name"], "Data quality pipeline")
        self.assertEqual(wf["on"]["schedule"][0]["cron"], "17 6 * * 1")
        self.assertIn("as_of", wf["on"]["workflow_dispatch"]["inputs"])
        assess, deploy = wf["jobs"]["assess"], wf["jobs"]["deploy"]
        self.assertEqual(assess["permissions"], {"contents": "write", "issues": "write"})
        self.assertEqual(deploy["permissions"], {"pages": "write", "id-token": "write"})
        self.assertEqual(deploy["needs"], "assess")
        self.assertIn("has_portal", deploy["if"])
        runs = self._runs(assess)
        self.assertIn("python -m unittest discover -s tests", runs)
        self.assertIn("python -m dqkit run portfolio.ndl.yaml --out assessments/portfolio", runs)
        self.assertIn('git config user.name "dq-pipeline"', runs)
        self.assertIn("if [ -f scripts/build_dq_portal.py ]", runs)
        self.assertIn("portal/dist/index.html", runs)
        self.assertLess(runs.index("unittest"), runs.index("dqkit run"))
        uses = self._uses(assess) + self._uses(deploy)
        for action in ("actions/checkout@v4", "actions/setup-python@v5", "actions/github-script@v7",
                       "actions/upload-artifact@v4", "actions/upload-pages-artifact@v3", "actions/deploy-pages@v4"):
            self.assertIn(action, uses)
        for u in uses:
            self.assertRegex(u, r"@v\d+$")  # pinned to a major version
        script = next(s["with"]["script"] for s in assess["steps"] if s.get("uses", "").startswith("actions/github-script"))
        for needle in ("dq-escalation", "escalations.json", "createLabel", "issues.create", "createComment", "state: 'closed'", "\\[DQ\\]"):
            self.assertIn(needle, script)
        art = next(s for s in assess["steps"] if s.get("uses", "").startswith("actions/upload-artifact"))
        self.assertEqual(art["with"]["path"], "assessments/portfolio")
        for s in assess["steps"] + deploy["steps"]:
            self.assertTrue(s.get("name"), s)  # every step is named, for readers

    def test_ci_workflow(self):
        wf = self._load("ci.yml")
        runs = self._runs(wf["jobs"]["test"])
        self.assertIn("python -m dqkit run portfolio.ndl.yaml --out /tmp/dq-ci --as-of 2026-10-14", runs)
        self.assertTrue("python-docx" in runs or "requirements.txt" in runs)
        self.assertIn("python-docx", (ROOT / "requirements.txt").read_text())


if __name__ == "__main__":
    unittest.main()


class EscalationPrivacy(unittest.TestCase):
    def test_examples_left_out_for_personal_data(self):
        from dqkit import portfolio as pf
        res = {"asset": {"id": "a", "personal_data_columns": ["nino"]}, "operations": {"rules": {"R1": {}}},
               "results": [{"id": "R1", "examples": [{"row": 2, "nino": "AB123456C"}], "detail": {}}]}
        s = {"id": "a", "title": "A", "owner": "O", "measured_on": "2026-10-14",
             "route": {"responsibility": "x", "route": "y", "source": "internal", "influence": True}, "files": {"workbook": "w", "results": "r"},
             "issues": [{"rule": "R1", "priority": "High", "overdue": True, "cycles_open": 2, "description": "d",
                         "label": "l", "dimension": "validity", "issue_type": "missing-value", "performance": 50.0,
                         "target": 97.5, "resolution": "Within 1 measurement cycle"}]}
        out = pf.build_escalations([s], {"a": res}, {})
        self.assertEqual(len(out), 1)
        self.assertNotIn("AB123456C", out[0]["body_markdown"])
        res["asset"].pop("personal_data_columns")
        self.assertIn("AB123456C", pf.build_escalations([s], {"a": res}, {})[0]["body_markdown"])
        self.assertNotIn("AB123456C", pf.build_escalations([s], {"a": res}, {"include_examples": False})[0]["body_markdown"])
