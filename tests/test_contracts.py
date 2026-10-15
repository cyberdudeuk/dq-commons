"""Data contracts: rules survive a trip through ODCS and Table Schema, and give the same results."""
import glob
import json
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import contracts, rules  # noqa: E402


def specs():
    for f in sorted(glob.glob(str(ROOT / "rules" / "**" / "*.yaml"), recursive=True)):
        s = yaml.safe_load(Path(f).read_text(encoding="utf-8"))
        if isinstance(s, dict) and "rules" in s:
            yield f, rules.expand_valuesets(s)


class Contracts(unittest.TestCase):
    def test_round_trip_keeps_every_rule(self):
        n = 0
        for f, s in specs():
            back = contracts.from_odcs(contracts.to_odcs(s))
            rules.validate_spec(back)
            self.assertEqual(sorted((str(r["id"]), r["check"]) for r in s["rules"]),
                             sorted((str(r["id"]), r["check"]) for r in back["rules"]), f)
            rules.validate_spec(contracts.from_table_schema(contracts.to_table_schema(s)))
            n += 1
        self.assertGreaterEqual(n, 10)

    def test_round_trip_gives_identical_results(self):
        port = yaml.safe_load((ROOT / "portfolio.ndl.yaml").read_text(encoding="utf-8"))
        for e in port["assets"][:4]:
            s = rules.load_rules(ROOT / e["rules"])
            df = pd.read_csv(ROOT / e["data"], dtype=str, keep_default_na=False, na_values=[""])
            a = rules.run(df, s, pd.Timestamp("2026-10-14").date())
            b = rules.run(df, contracts.from_odcs(contracts.to_odcs(s)), pd.Timestamp("2026-10-14").date())
            key = lambda res: {r["id"]: (r["performance"], r["assessment"]["target"], r["assessment"]["meets_target"]) for r in res["results"]}
            self.assertEqual(key(a), key(b), e["rules"])

    def test_odcs_shape_and_thresholds(self):
        s = {"asset": {"id": "claims", "importance": 4, "owner": "Example department"},
             "rules": [{"id": "R1", "check": "not_null", "column": "nino"},
                       {"id": "R2", "check": "identifier", "column": "nino", "scheme": "nino"},
                       {"id": "R3", "check": "unique", "columns": ["nino", "month"]},
                       {"id": "R4", "check": "in_set", "column": "status", "values": ["open", "closed"]}]}
        c = contracts.to_odcs(s)
        self.assertEqual((c["apiVersion"], c["kind"]), ("v3.1.0", "DataContract"))
        nino = c["schema"][0]["properties"][0]
        self.assertTrue(nino["required"])
        q = {x["id"]: x for x in nino["quality"]}
        self.assertEqual(q["R1"]["metric"], "nullValues")
        self.assertEqual(q["R1"]["unit"], "percent")
        self.assertEqual((q["R2"]["type"], q["R2"]["engine"]), ("custom", "dqkit"))
        self.assertEqual(c["schema"][0]["quality"][0]["arguments"]["properties"], ["nino", "month"])
        # foreign rules are reported, not silently dropped
        c["schema"][0]["quality"].append({"id": "X1", "type": "sql", "query": "select 1", "description": "custom SQL"})
        self.assertEqual([u["id"] for u in contracts.unsupported(c)], ["X1"])

    def test_csvw_and_table_schema(self):
        s = {"asset": {"id": "a", "title": "A"}, "rules": [
            {"id": "R1", "check": "type", "column": "year", "kind": "year"},
            {"id": "R2", "check": "range", "column": "rate", "min": 0, "max": 100},
            {"id": "R3", "check": "regex", "column": "code", "pattern": "[A-Z]{3}"},
            {"id": "R4", "check": "unique", "columns": ["code", "year"]}]}
        ts = contracts.to_table_schema(s)
        self.assertEqual(ts["primaryKey"], ["code", "year"])
        w = contracts.to_csvw(s)
        self.assertEqual(w["@context"], "http://www.w3.org/ns/csvw")
        cols = {c["titles"]: c for c in w["tableSchema"]["columns"]}
        self.assertEqual(cols["year"]["datatype"], "gYear")
        self.assertEqual(cols["rate"]["datatype"], {"base": "string", "minimum": 0, "maximum": 100})

    def test_cli(self):
        f = sorted(glob.glob(str(ROOT / "rules" / "ndl" / "*.yaml")))[0]
        out = subprocess.run([sys.executable, "-m", "dqkit", "contract", f, "--to", "odcs"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        tmp = ROOT / "assessments" / "_contract_test.json"
        tmp.write_text(out.stdout)
        try:
            back = subprocess.run([sys.executable, "-m", "dqkit", "contract", str(tmp), "--from", "odcs"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(back.returncode, 0, back.stderr)
            self.assertIn("rules:", back.stdout)
        finally:
            tmp.unlink()


if __name__ == "__main__":
    unittest.main()
