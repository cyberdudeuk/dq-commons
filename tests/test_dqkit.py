"""Tests: run with `python -m unittest discover -s tests -v`."""
import json
import unittest
from datetime import date

import pandas as pd

from dqkit import dqv, exporters, framework, metadata, rules


class FrameworkMatchesGovUk(unittest.TestCase):
    """Every expected value below comes from the published GOV.UK issues framework."""

    def test_worked_example(self):
        # GOV.UK worked example: importance 2 x impact 2 = 4, target 95%, measured 94.2% -> High band, score 4, Low priority.
        a = framework.assess(2, 2, 94.2, target=95)
        self.assertEqual(a.combined, 4)
        self.assertEqual(a.target_range, (90.0, 97.5))
        self.assertEqual(a.band, "high")
        self.assertEqual(a.priority_score, 4)
        self.assertEqual(a.priority, "Low")

    def test_table4_bands_for_95(self):
        b = framework.bands(95)
        self.assertEqual(b["middle"][0], 90.0)
        self.assertEqual(b["high"][0], 92.5)

    def test_table4_middle_start_for_75(self):
        self.assertEqual(framework.bands(75)["middle"][0], 50.0)

    def test_target_100_is_critical_band(self):
        a = framework.assess(4, 4, 99.95, target=100)
        self.assertEqual((a.band, a.band_score, a.priority_score, a.priority), ("critical", 4, 64, "Critical"))
        self.assertEqual(a.resolution, "Immediately")

    def test_target_ranges(self):
        self.assertEqual(framework.target_range(3), (75.0, 90.0))
        self.assertEqual(framework.target_range(9), (97.5, 99.9))
        self.assertEqual(framework.target_range(12), (99.9, 100.0))
        with self.assertRaises(ValueError):
            framework.target_range(7)

    def test_priority_thresholds(self):
        self.assertEqual([framework.priority_for(s) for s in (7, 8, 16, 17, 32, 33)],
                         ["Low", "Medium", "Medium", "High", "High", "Critical"])

    def test_meeting_target_is_not_an_issue(self):
        a = framework.assess(3, 3, 99.5)
        self.assertTrue(a.meets_target)
        self.assertIsNone(a.priority)

    def test_rejects_bad_scores(self):
        with self.assertRaises(ValueError):
            framework.assess(5, 1, 50)


SPEC = {
    "asset": {"id": "test", "title": "Test asset", "importance": 3, "owner": "Test Dept"},
    "rules": [
        {"id": "R1", "check": "not_null", "column": "year"},
        {"id": "R2", "check": "unique", "columns": ["year"]},
        {"id": "R3", "check": "type", "column": "value", "kind": "number"},
        {"id": "R4", "check": "range", "column": "value", "min": 0, "max": 100},
        {"id": "R5", "check": "freshness", "column": "year", "expected": "P1Y", "lag": "P6M"},
        {"id": "R6", "check": "no_gaps", "column": "year"},
        {"id": "R7", "check": "header_has_unit", "columns": ["value"]},
        {"id": "R8", "check": "not_unknown", "column": "sex"},
        {"id": "R9", "check": "group_disparity", "group": "sex", "tolerance": 5,
         "inner": {"check": "not_null", "column": "value"}},
    ],
}
DF = pd.DataFrame({"year": ["2020", "2021", "2021", "2023", None],
                   "value": ["10", "20", "x", "150", ""],
                   "sex": ["F", "M", "Unknown", "F", "M"]})


class RulesEngine(unittest.TestCase):
    def setUp(self):
        self.res = rules.run(DF, SPEC, as_of=date(2026, 10, 14))
        self.by = {r["id"]: r for r in self.res["results"]}

    def test_rates(self):
        self.assertEqual(self.by["R1"]["performance"], 80.0)
        self.assertEqual(self.by["R2"]["passed"], 3)          # the two 2021 rows are duplicates
        self.assertEqual(self.by["R3"]["passed"], 3)          # "x" and blank fail
        self.assertEqual(self.by["R4"]["passed"], 2)          # 150 out of range, x and blank fail
        self.assertEqual(self.by["R6"]["performance"], 75.0)  # 2022 missing from 2020-2023
        self.assertEqual(self.by["R7"]["passed"], 0)          # "value" has no unit
        self.assertEqual(self.by["R8"]["passed"], 4)

    def test_freshness_is_stale(self):
        self.assertEqual(self.by["R5"]["passed"], 0)
        self.assertEqual(self.by["R5"]["detail"]["latest_period"], "2023-12-31")

    def test_group_disparity_detected(self):
        self.assertEqual(self.by["R9"]["passed"], 0)
        self.assertIn("by_group", self.by["R9"]["detail"])

    def test_issues_sorted_by_priority(self):
        order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        ranks = [order[i["priority"]] for i in self.res["issues"]]
        self.assertEqual(ranks, sorted(ranks))

    def test_missing_column_is_reported_not_crashing(self):
        spec = {"asset": {"id": "t", "importance": 2}, "rules": [{"id": "X", "check": "not_null", "column": "nope"}]}
        r = rules.run(DF, spec, as_of=date(2026, 1, 1))["results"][0]
        self.assertEqual((r["issue_type"], r["passed"]), ("missing-field", 0))

    def test_unknown_check_rejected(self):
        with self.assertRaises(ValueError):
            rules.validate_spec({"asset": {"id": "t"}, "rules": [{"id": "A", "check": "magic"}]})


class Outputs(unittest.TestCase):
    def setUp(self):
        self.res = rules.run(DF, SPEC, as_of=date(2026, 10, 14))

    def test_dqv_jsonld_shape(self):
        doc = dqv.result_to_dqv(self.res)
        json.dumps(doc)
        types = {n["@type"] for n in doc["@graph"]}
        self.assertTrue({"dcat:Dataset", "dqv:QualityMeasurement", "dqv:Metric", "dqv:Dimension"} <= types)
        ds = doc["@graph"][0]
        self.assertEqual(len(ds["dqv:hasQualityMeasurement"]), len(SPEC["rules"]))

    def test_gx_suite(self):
        suite = exporters.to_great_expectations(SPEC)
        kinds = {e["expectation_type"] for e in suite["expectations"]}
        self.assertIn("expect_column_values_to_not_be_null", kinds)
        self.assertIn("expect_column_values_to_be_between", kinds)
        self.assertTrue(any(n["rule_id"] == "R5" for n in suite["meta"]["not_exported"]))

    def test_r_validate(self):
        text = exporters.to_r_validate(SPEC)
        self.assertIn("is_unique(`year`)", text)
        self.assertIn("in_range(`value`, min = 0, max = 100)", text)

    def test_dqap_csv(self):
        d = exporters.to_dqap_csv(self.res)
        self.assertTrue(d["rules"].startswith("Critical data item,Rule ID"))
        self.assertGreater(d["issues"].count("\n"), 1)


RECORD = {"collection": "people", "slug": "x", "title": "X", "provider_stated": "ONS", "description": "d" * 50,
          "last_updated": "24/3/2026", "update_frequency": None,
          "get_the_data": [{"label": "X", "url": "https://www.ons.gov.uk/x", "publisher_stated": "ONS"}],
          "formats_mentioned": ["XLSX"], "api_available": False, "quality_caveats": None, "methodology_link": False,
          "geography": "England and Wales", "time_period": None, "protected_characteristics_breakdowns": []}


class MetadataAssessment(unittest.TestCase):
    def test_record(self):
        a = metadata.assess_record(RECORD, date(2026, 10, 14))
        st = {c["id"]: c["status"] for c in a["checks"]}
        self.assertEqual(st["DAM-1"], "pass")
        self.assertEqual(st["DAM-3"], "fail")
        self.assertEqual(st["DAM-4"], "pass")        # 204 days
        self.assertEqual(st["NDL-1"], "partial")     # older than 6 months
        self.assertEqual(st["FAIR-1"], "partial")    # XLSX only
        self.assertEqual(st["INC-1"], "fail")
        self.assertEqual(st["INC-2"], "partial")     # covers Wales; Scotland and Northern Ireland not signposted
        self.assertTrue(0 <= a["score"] <= 100)

    def test_public_sector_domains(self):
        self.assertTrue(metadata._is_public_sector("https://www.ons.gov.uk/a"))
        self.assertTrue(metadata._is_public_sector("https://www.opendata.nhs.scot/x"))
        self.assertFalse(metadata._is_public_sector("https://experience.arcgis.com/x"))
        self.assertFalse(metadata._is_public_sector("https://evilgov.uk/x"))

    def test_portfolio(self):
        p = metadata.assess_portfolio([RECORD, dict(RECORD, slug="y", update_frequency="Annual")], date(2026, 10, 14))
        ndl2 = next(c for c in p["checks"] if c["id"] == "NDL-2")
        self.assertEqual(ndl2["performance"], 50.0)
        self.assertIsNotNone(ndl2["assessment"]["priority"])


if __name__ == "__main__":
    unittest.main()


class IssuesFrameworkV1Tables(unittest.TestCase):
    """Reproduce Tables 7, 8 and 10 of the Data Quality Issues Framework v1.0."""

    def test_table8_bands_at_low_end_targets(self):
        # v1.0 Tables 7 and 8 print 96.75% for the 97.5% target. The rule the same document states
        # ("halfway between the Middle band start point and the target") gives 96.25%. The kit follows
        # the stated rule; the printed figure is an arithmetic slip, reported in docs/GUIDANCE-CROSSWALK.md.
        expected = {75: (50.0, 62.5), 90: (80.0, 85.0), 97.5: (95.0, 96.25), 99.9: (99.8, 99.85)}
        for target, (mid, high) in expected.items():
            b = framework.bands(target)
            self.assertAlmostEqual(b["middle"][0], mid, places=6)
            self.assertAlmostEqual(b["high"][0], high, places=6)

    def test_default_policy_is_low_end(self):
        self.assertEqual([framework.default_target(s) for s in (3, 6, 9, 16)], [75.0, 90.0, 97.5, 99.9])
        self.assertEqual(framework.default_target(4, "mid"), 95.0)

    def test_table5_error_rates(self):
        self.assertEqual(framework.error_rate(75), "1 in 4 records")
        self.assertEqual(framework.error_rate(90), "1 in 10 records")
        self.assertEqual(framework.error_rate(97.5), "1 in 40 records")
        self.assertEqual(framework.error_rate(99.9), "1 in 1,000 records")

    def test_v1_worked_example_both_readings(self):
        # v1.0: importance x impact is "either 4 or 6"; 94.2% vs 95% is Low priority either way.
        for imp, impact in ((2, 2), (2, 3)):
            self.assertEqual(framework.assess(imp, impact, 94.2, target=95).priority, "Low")


class TrustPathwayWorkbook(unittest.TestCase):
    def _res(self, perf, dim="accuracy", personal=True, n_dims=("completeness", "validity", "accuracy")):
        results = []
        for i, d in enumerate(n_dims):
            p = perf if d == dim else 100.0
            a = framework.assess(3, 3, p).to_dict()
            results.append({"id": f"R{i}", "description": d, "dimension": d, "columns": ["name"] if d == dim else ["x"],
                            "performance": p, "assessment": a, "meta": {"personal_data": personal and d == dim},
                            "check": "not_null", "checked": 10, "passed": 9, "issue_type": "missing-value"})
        return {"asset": {"id": "t"}, "results": results, "as_of": "2026-10-14", "issues": [], "rules_met": 0, "rules_total": len(results)}

    def test_iopc_personal_accuracy_rule(self):
        from dqkit import trust
        t = trust.classify(self._res(89.0))
        self.assertNotEqual(t["level"], "Trustworthy")
        self.assertTrue(t["action_plan_required"])

    def test_clean_data_is_trustworthy(self):
        from dqkit import trust
        t = trust.classify(self._res(100.0))
        self.assertEqual((t["level"], t["sharing"]), ("Trustworthy", "Can be used externally"))

    def test_too_few_dimensions_caps_at_useable(self):
        from dqkit import trust
        t = trust.classify(self._res(100.0, n_dims=("completeness",)))
        self.assertEqual(t["level"], "Useable")

    def test_decision_tree_routes(self):
        from dqkit import pathway
        self.assertIn("fix at source", pathway.route({"source": "internal"})["route"])
        ext = pathway.route({"source": "external", "influence": False, "fields_adequate": False})
        self.assertIn("communicate", ext["route"])
        self.assertTrue(any("limitations" in s for s in ext["steps"]))

    def test_workbook_tabs(self):
        import tempfile, openpyxl
        from dqkit import workbook
        res = rules.run(DF, SPEC, as_of=date(2026, 10, 14))
        with tempfile.TemporaryDirectory() as d:
            workbook.append_history(res, d)
            p = workbook.build(SPEC, res, f"{d}/t.xlsx", d)
            wb = openpyxl.load_workbook(p)
            self.assertEqual(wb.sheetnames, ["Start here", "Details", "Criticality matrix", "Metrics", "Results",
                                             "Issues log", "Causes", "Actions", "RACI", "Steps"])
            self.assertEqual(wb["Issues log"].max_row - 1, len(res["issues"]))
