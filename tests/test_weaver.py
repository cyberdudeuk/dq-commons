"""Metadata Weaver, contract change control, scope extension, community docs and privacy guards."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import contracts, mcp_server, weaver  # noqa: E402

DCAT = {"@context": {"dcat": "http://www.w3.org/ns/dcat#", "dct": "http://purl.org/dc/terms/"}, "@type": "dcat:Dataset",
        "dct:title": "Flood alerts", "dct:description": "Flood alerts and warnings in England, updated daily.",
        "dct:identifier": "ea-flood-alerts", "dct:publisher": {"foaf:name": "Environment Agency"}, "dcat:keyword": ["flood"],
        "dct:license": "OGL-UK-3.0", "dct:issued": "2006-01-01", "dct:temporal": {"dcat:startDate": "2006-01-01"},
        "dcat:distribution": [{"dcat:downloadURL": "https://example.org/a.csv", "dct:format": "csv"}]}


class Weaver(unittest.TestCase):
    def test_detects_each_format(self):
        w = weaver.weave(DCAT)
        self.assertEqual(w["source_format"], "dcat")
        for t in weaver.TARGETS:
            self.assertEqual(weaver.detect(w["outputs"][t]) if t != "ckan" else "ckan", t)
        self.assertEqual(weaver.detect({"result": {"title": "x", "resources": []}}), "ckan")
        with self.assertRaises(ValueError):
            weaver.detect({"nothing": 1})

    def test_round_trip_keeps_what_each_standard_can_carry(self):
        c = weaver.weave(DCAT)["canonical"]
        for t in weaver.TARGETS:
            back = weaver.read(weaver.WRITERS[t](c), t)[1]
            for k in weaver.CARRY[t]:
                if k in ("distributions",) or (t == "odcs" and (k == "conforms_to" or (k in ("version", "identifier") and not c[k]))):  # ODCS needs placeholders
                    continue
                self.assertEqual(back[k], c[k], (t, k))

    def test_never_invents_values(self):
        c = weaver.read({"title": "Only a title", "notes": ""}, "ckan")[1]
        self.assertEqual([k for k in weaver.KEYS if c[k] not in ("", [])], ["title"])
        cda = weaver.cda_check(c)
        self.assertEqual(cda["properties"]["title"]["status"], "pass")
        self.assertEqual(cda["properties"]["licence"]["status"], "missing")

    def test_cda_has_13_properties(self):
        self.assertEqual(len(weaver.CDA), 13)
        self.assertGreater(weaver.weave(DCAT)["cda"]["coverage"], 50)

    def test_not_carried_is_reported(self):
        cov = weaver.weave({**DCAT, "dqc:securityClassification": "OFFICIAL"})["coverage"]
        self.assertIn("security", cov["schema"]["not_carried"])

    def test_cli_and_mcp(self):
        p = ROOT / "tests" / "_tmp_rec.json"
        p.write_text(json.dumps(DCAT), encoding="utf-8")
        try:
            out = subprocess.run([sys.executable, "-m", "dqkit", "weave", str(p), "--report"], cwd=ROOT, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(out.stdout)["source_format"], "dcat")
        finally:
            p.unlink()
        names = {t["name"] for t in mcp_server.TOOLS}
        self.assertTrue({"weave_metadata", "check_contract"} <= names)
        self.assertEqual(mcp_server.call_tool("weave_metadata", {"record": DCAT})["source_format"], "dcat")


class ContractChange(unittest.TestCase):
    OLD = {"apiVersion": "v3.1.0", "kind": "DataContract", "id": "x", "version": "1.2.0", "status": "active", "team": {"name": "Data team"},
           "slaProperties": [{"property": "frequency", "value": 1}],
           "schema": [{"name": "t", "properties": [{"name": "a", "logicalType": "integer", "quality": [
               {"id": "R1", "metric": "nullValues", "mustBeLessOrEqualTo": 1, "unit": "percent"}]}, {"name": "b"}]}]}

    def test_valid_contract_has_no_problems(self):
        self.assertEqual(contracts.validate_odcs(self.OLD), [])

    def test_breaking_changes_need_a_major_version(self):
        new = json.loads(json.dumps(self.OLD))
        new["version"] = "1.3.0"
        new["schema"][0]["properties"].pop()  # remove column b
        d = contracts.diff_odcs(self.OLD, new)
        self.assertTrue(d["breaking"])
        self.assertEqual(d["suggested_version"], "2.0.0")
        self.assertFalse(d["version_ok"])

    def test_tightening_is_not_breaking(self):
        new = json.loads(json.dumps(self.OLD))
        new["version"] = "1.3.0"
        new["schema"][0]["properties"][0]["quality"][0]["mustBeLessOrEqualTo"] = 0.5
        d = contracts.diff_odcs(self.OLD, new)
        self.assertFalse(d["breaking"])
        self.assertTrue(d["version_ok"])
        self.assertIn("1% failing became 0.5%", d["changes"][0]["message"])

    def test_sla_and_support_pass_through(self):
        spec = {"asset": {"id": "a", "sla": [{"property": "availability", "value": 99.5, "unit": "percent"}],
                          "support": [{"channel": "issues", "url": "https://example.org/issues"}]},
                "rules": [{"id": "R1", "check": "not_null", "column": "x"}]}
        o = contracts.to_odcs(spec)
        self.assertEqual(o["slaProperties"][0]["value"], 99.5)
        self.assertEqual(o["support"][0]["channel"], "issues")


class ScopeAndCommunity(unittest.TestCase):
    def test_global_scope(self):
        g = yaml.safe_load((ROOT / "knowledge" / "global.yaml").read_text(encoding="utf-8"))
        self.assertEqual({c["iso"] for c in g["crown_dependencies"]}, {"JE", "GG", "IM"})
        self.assertEqual(len(g["overseas_territories"]), 14)
        for p in g["partners"]:
            self.assertIn(p["checked"], ("yes", "listed"), p["id"])
            self.assertTrue(p["url"].startswith("https://"), p["id"])
        packs = {f.stem for f in (ROOT / "packs").glob("*.yaml")}
        for p in g["partners"]:
            if p["pack"]:
                self.assertIn(p["pack"], packs, p["id"])

    def test_backlog_ids_unique_and_valid(self):
        b = yaml.safe_load((ROOT / "knowledge" / "build.yaml").read_text(encoding="utf-8"))["backlog"]
        ids = [x["id"] for x in b]
        self.assertEqual(len(ids), len(set(ids)))
        for x in b:
            self.assertRegex(x["id"], r"^BL-\d{2}$")
            self.assertIn(x["moscow"], ("must", "should", "could", "wont"))

    def test_community_docs_are_current(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_community_docs.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_backlog_to_issues_dry_run(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "backlog_to_issues.py")], capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Dry run", r.stdout)


class Privacy(unittest.TestCase):
    """No email address, phone number or security marking in anything people read (tests use example.org only)."""
    EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

    def files(self):
        for pat in ("knowledge/*.yaml", "portal/src/**/*.html", "portal/src/**/*.js", "*.md", "docs/*.md",
                    ".github/**/*.yml", "integrations/*.yaml", "integrations/*.json"):
            yield from ROOT.glob(pat)

    def test_no_email_addresses(self):
        allowed = ("@example.org", "@example.com", "noreply@anthropic.com", "@users.noreply.github.com")
        for f in self.files():
            for m in self.EMAIL.findall(f.read_text(encoding="utf-8", errors="ignore")):
                if not m.endswith(allowed) and not re.match(r"^[\w.-]+@\d", m):
                    self.fail(f"{f.relative_to(ROOT)}: {m}")

    def test_no_internal_instance_urls(self):
        for f in self.files():
            self.assertNotRegex(f.read_text(encoding="utf-8", errors="ignore"), r"(?<!your-site)(?<!example)\.atlassian\.net", str(f))



class InternationalPacks(unittest.TestCase):
    def test_un_and_imf_packs_assess(self):
        from dqkit import packs
        result = {"asset": {"id": "a", "owner": "Statistics office", "primary_use": "Planning"},
                  "dimensions": {"validity": {}, "accuracy": {}}, "results": [{"check": "freshness"}, {"check": "in_set"}]}
        for pid in ("un-nqaf", "imf-dqaf"):
            r = packs.assess(pid, result)
            statuses = [x["status"] for x in r["requirements"]]
            self.assertIn("met", statuses, pid)
            self.assertIn("manual", statuses, pid)  # integrity and institutional items need a person


class Health(unittest.TestCase):
    def test_content_health_has_no_errors(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import self_check
        h = self_check.run()
        self.assertEqual(h["counts"]["error"], 0, [i for i in h["items"] if i["level"] == "error"])


if __name__ == "__main__":
    unittest.main()
