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


class IssuesFrameworkBands(unittest.TestCase):
    """Performance bands follow the issues framework's stated rule."""

    def test_table8_bands_at_low_end_targets(self):
        # The High band starts halfway between the Middle band start point and the target.
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
                                             "Issues log", "Causes", "Actions", "Communication plan", "Operations", "RACI", "Steps", "Checklist"])
            # DQAP implementation guide, steps 4 to 6: review dates, resolution dates, options and a communication plan
            heads = lambda n: [c.value for c in wb[n][1]]
            for col in ("Target resolution date", "Actual resolution date", "Review date"):
                self.assertIn(col, heads("Issues log"))
            for col in ("Review date", "Goal (target %)"):
                self.assertIn(col, heads("Actions"))
            self.assertIn("Resolution options considered", heads("Causes"))
            self.assertEqual(wb["Checklist"].max_row, 8)
            self.assertEqual(wb["Issues log"].max_row - 1, len(res["issues"]))


class OperationsAndCaseStudy(unittest.TestCase):
    """Issue ageing, escalation, recurrence (GDS DQAP adoption material) and the case study draft."""

    def _cycle(self, d, as_of, broken):
        df = DF.copy()
        if not broken:
            df = df.dropna()
        res = rules.run(df, SPEC, as_of=as_of)
        from dqkit import workbook
        workbook.append_history(res, d)
        return res

    def test_control_points_default_and_override(self):
        res = rules.run(DF, SPEC, as_of=date(2026, 10, 14))
        self.assertTrue(all(r["meta"]["control_point"] in rules.CONTROL_POINTS for r in res["results"]))
        bad = {"asset": {"id": "a"}, "rules": [{"id": "R1", "check": "not_null", "column": "x", "control_point": "magic"}]}
        with self.assertRaises(ValueError):
            rules.validate_spec(bad)

    def test_overdue_and_recurrence(self):
        import tempfile
        from dqkit import operations
        with tempfile.TemporaryDirectory() as d:
            self._cycle(d, date(2026, 1, 1), True)
            self._cycle(d, date(2026, 4, 1), False)
            self._cycle(d, date(2026, 7, 1), True)
            res = self._cycle(d, date(2026, 10, 1), True)
            ops = operations.assess(res, d)
            self.assertEqual(ops["cycles_measured"], 4)
            failing = [r["id"] for r in res["results"] if not r["assessment"]["meets_target"]]
            self.assertTrue(failing)
            # every rule that failed, passed, then failed again is a recurrence
            recurring = [k for k, v in ops["rules"].items() if v["recurrences"]]
            self.assertTrue(recurring)
            for k, v in ops["rules"].items():
                if v["open"]:
                    self.assertEqual(v["overdue"], v["cycles_open"] > operations.WINDOW[v["priority"]])

    def test_case_study_has_template_sections_and_no_personal_data(self):
        import tempfile
        from dqkit import casestudy
        with tempfile.TemporaryDirectory() as d:
            self._cycle(d, date(2026, 4, 1), True)
            res = self._cycle(d, date(2026, 10, 1), False)
            dr = casestudy.draft(SPEC, res, d)
            md = casestudy.to_markdown(dr)
            for section in ("Permissions", "What triggered this work?", "Where did you start?", "What did you do?",
                            "What outcome did you achieve?", "Reusable assets"):
                self.assertIn(section, md)
            self.assertEqual(len(dr["steps"]), 7)
            self.assertIn("Contact route: the Commons contact form", md)
            self.assertNotIn("email:", md.lower())
            p = casestudy.to_docx(dr, f"{d}/c.docx")
            self.assertTrue(p.exists())


class RuleLibrary(unittest.TestCase):
    """Public sector identifiers, value sets and the rule library templates."""

    def test_identifier_schemes(self):
        good = {"nhs_number": ["9434765919", "943 476 5919"], "nino": ["AB123456C", "AB 12 34 56 C"],
                "uk_postcode": ["SW1A 1AA", "EC1A1BB", "GIR 0AA"], "uprn": ["100023336956"], "gss_code": ["E09000001"],
                "company_number": ["SC123456", "01234567"], "charity_number": ["1234567", "SC012345", "NIC100002"],
                "school_urn": ["100000"], "ods_code": ["RX1"], "lei": ["5493001KJTIIGC8Y1R12"]}
        bad = {"nhs_number": ["9434765918", "123"], "nino": ["QQ123456C", "BG123456A", "AB123456E"],
               "uk_postcode": ["sw1a 1aa", "SW1A 1AAA"], "uprn": ["0", "1234567890123"], "gss_code": ["X12345678"],
               "company_number": ["AB12345"], "charity_number": ["SC12345"], "school_urn": ["12345"], "ods_code": ["ab1"],
               "lei": ["5493001KJTIIGC8Y1R13"]}
        for scheme, vals in good.items():
            for v in vals:
                self.assertTrue(rules.identifier_ok(v, scheme), (scheme, v))
        for scheme, vals in bad.items():
            for v in vals:
                self.assertFalse(rules.identifier_ok(v, scheme), (scheme, v))
        self.assertEqual(set(good), set(rules.IDENTIFIER_SCHEMES))

    def test_identifier_rule_and_unknown_scheme(self):
        df = pd.DataFrame({"nhs": ["9434765919", "9434765918", None]})
        spec = {"asset": {"id": "x"}, "rules": [{"id": "R1", "check": "identifier", "column": "nhs", "scheme": "nhs_number"}]}
        res = rules.run(df, spec, as_of=date(2026, 10, 15))
        self.assertEqual((res["results"][0]["checked"], res["results"][0]["passed"]), (3, 1))
        self.assertEqual(res["results"][0]["issue_type"], "invalid-identifier")
        with self.assertRaises(ValueError):
            rules.validate_spec({"asset": {"id": "x"}, "rules": [{"id": "R1", "check": "identifier", "column": "a", "scheme": "passport"}]})

    def test_valueset_expansion(self):
        spec = {"asset": {"id": "x"}, "rules": [{"id": "R1", "check": "in_valueset", "column": "n", "valueset": "uk_nations"}]}
        res = rules.run(pd.DataFrame({"n": ["Wales", "UK"]}), spec, as_of=date(2026, 10, 15))
        self.assertEqual(res["results"][0]["passed"], 1)
        self.assertEqual(spec["rules"][0]["check"], "in_valueset")  # caller's spec is not changed
        with self.assertRaises(ValueError):
            rules.load_valueset("../etc/passwd")

    def test_library_templates_load(self):
        from pathlib import Path
        files = sorted((Path(__file__).resolve().parent.parent / "rules" / "library").glob("*.yaml"))
        self.assertGreaterEqual(len(files), 5)
        for f in files:
            self.assertTrue(rules.load_rules(f)["rules"], f.name)


class OutliersAndNumbers(unittest.TestCase):
    """Issue #7 (outliers) and #25 (numbers read the same whatever the pandas version)."""

    def test_numbers_rule(self):
        from dqkit.numbers import to_numeric
        s = to_numeric(["1", " 2 ", "+3", "-0"])
        self.assertEqual(str(s.dtype), "int64")
        f = to_numeric(["0.30000000000000004", ".5", "5.", "1e-19", "inf", "-Infinity", "1_000", "0x10", "", "n/a", None])
        self.assertEqual(f[0], 0.30000000000000004)
        self.assertEqual(f[3], 1e-19)
        self.assertEqual(f[4], float("inf"))
        self.assertTrue(all(f[i] != f[i] for i in range(6, 11)))  # NaN

    def test_outlier_iqr_and_zscore(self):
        import pandas as pd
        from dqkit import rules
        df = pd.DataFrame({"v": ["10", "11", "12", "11", "10", "12", "11", "500", "", "n/a"]}, dtype=str)
        checked, passed, ex, d = rules.check_outlier(df, {"column": "v"})
        self.assertEqual((checked, passed), (8, 7))
        self.assertEqual(ex[0]["v"], "500")
        checked, passed, ex, d = rules.check_outlier(df, {"column": "v", "method": "zscore", "threshold": 2})
        self.assertEqual((checked, passed), (8, 7))
        self.assertEqual(rules.check_outlier(df.head(3), {"column": "v"})[:2], (3, 3))
        with self.assertRaises(ValueError):
            rules.check_outlier(df, {"column": "v", "method": "mad"})


class Linkage(unittest.TestCase):
    """Issue #8: record linkage quality, including fairness across groups."""

    def test_rates_review_and_groups(self):
        import pandas as pd
        from dqkit import linkage
        rec = pd.DataFrame({"id": [str(i) for i in range(40)], "grp": ["A"] * 20 + ["B"] * 15 + ["C"] * 5})
        pred = pd.DataFrame({"unique_id_l": [str(i) for i in range(0, 30, 2)], "unique_id_r": [str(i) for i in range(1, 31, 2)],
                             "match_probability": [0.95] * 12 + [0.5] * 3})
        ids = linkage.from_splink(pred)
        self.assertEqual(len(ids), 24)
        self.assertEqual(linkage.match_rate(rec, "id", ids), 60.0)
        g = linkage.match_rate_by_group(rec, "id", "grp", ids)
        self.assertEqual(g["by_group"], {"A": 100.0, "B": 26.667})
        self.assertFalse(g["within_tolerance"])
        self.assertEqual(g["suppressed_groups"], ["C"])
        rv = linkage.clerical_review(pd.DataFrame({"match_probability": [0.99, 0.95, 0.4, 0.2], "is_match": [True, False, True, False]}))
        self.assertEqual((rv["precision"], rv["recall"]), (50.0, 50.0))
