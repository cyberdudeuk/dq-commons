"""Turn one rules file into the formats other teams already use.

- Great Expectations: an expectation suite (JSON) that GX 0.18 and 1.x can import.
- R `validate` (Statistics Netherlands / European Statistical System): a YAML rule file.
- GOV.UK DQAP template: rows for its Rules, Data Issues Log and Details sections (CSV).

Checks with no direct equivalent are exported as comments so nothing is silently lost.
"""
from __future__ import annotations

import csv
import io
import json

import yaml

from .rules import DEFAULT_ISSUE, ISSUE_TYPES
from . import framework


def _mostly(rule: dict, importance: int, policy: str = framework.DEFAULT_POLICY) -> float:
    impact = int(rule.get("impact", ISSUE_TYPES[rule.get("issue_type", DEFAULT_ISSUE[rule["check"]])]["default_impact"]))
    target = rule.get("target") or framework.default_target(framework.combined_score(importance, impact), policy)
    return round(float(target) / 100.0, 4)


def to_great_expectations(spec: dict) -> dict:
    imp = int(spec["asset"].get("importance", 3))
    out, unsupported = [], []
    for r in spec["rules"]:
        m, c = _mostly(r, imp, spec["asset"].get("target_policy", framework.DEFAULT_POLICY)), r["check"]
        meta = {"rule_id": r["id"], "dimension": r.get("dimension", ISSUE_TYPES[r.get("issue_type", DEFAULT_ISSUE[c])]["dimension"]),
                "description": r.get("description", "")}
        kw = None
        if c == "not_null":
            et, kw = "expect_column_values_to_not_be_null", {"column": r["column"], "mostly": m}
        elif c == "unique":
            if len(r["columns"]) == 1:
                et, kw = "expect_column_values_to_be_unique", {"column": r["columns"][0], "mostly": m}
            else:
                et, kw = "expect_compound_columns_to_be_unique", {"column_list": r["columns"], "mostly": m}
        elif c == "regex":
            et, kw = "expect_column_values_to_match_regex", {"column": r["column"], "regex": r["pattern"], "mostly": m}
        elif c == "in_set":
            et, kw = "expect_column_values_to_be_in_set", {"column": r["column"], "value_set": r["values"], "mostly": m}
        elif c == "range":
            et, kw = "expect_column_values_to_be_between", {"column": r["column"], "min_value": r.get("min"), "max_value": r.get("max"), "mostly": m}
        elif c == "required_columns":
            for col in r["columns"]:
                out.append({"expectation_type": "expect_column_to_exist", "kwargs": {"column": col}, "meta": meta})
            continue
        elif c == "type" and r["kind"] in ("integer", "year"):
            et, kw = "expect_column_values_to_match_regex", {"column": r["column"], "regex": r"^[-+]?\d+$", "mostly": m}
        elif c == "type" and r["kind"] == "number":
            et, kw = "expect_column_values_to_match_regex", {"column": r["column"], "regex": r"^[-+]?\d*\.?\d+$", "mostly": m}
        elif c == "sum_max":
            et, kw = "expect_column_sum_to_be_between", {"column": r["column"], "max_value": r["max"] + r.get("tolerance", 0)}
        elif c == "compare" and r["right"] not in ("",):
            et, kw = "expect_column_pair_values_A_to_be_greater_than_B", None
            if r["op"] in (">", ">="):
                kw = {"column_A": r["left"], "column_B": r["right"], "or_equal": r["op"] == ">=", "mostly": m}
            elif r["op"] in ("<", "<="):
                kw = {"column_A": r["right"], "column_B": r["left"], "or_equal": r["op"] == "<=", "mostly": m}
        if kw is None:
            unsupported.append({"rule_id": r["id"], "check": c, "note": "no built-in GX expectation; run with dqkit or add a custom expectation"})
            continue
        out.append({"expectation_type": et, "kwargs": kw, "meta": meta})
    return {"expectation_suite_name": f"{spec['asset']['id']}.dqap", "expectations": out,
            "meta": {"generated_by": "ndl-dq-assurance dqkit", "asset": spec["asset"], "not_exported": unsupported}}


def _r_name(col: str) -> str:
    return "`" + col.replace("`", "") + "`"


def to_r_validate(spec: dict) -> str:
    rules, notes = [], []
    for r in spec["rules"]:
        c = r["check"]
        expr = None
        if c == "not_null":
            expr = f"!is.na({_r_name(r['column'])})"
        elif c == "unique":
            expr = "is_unique(" + ", ".join(_r_name(x) for x in r["columns"]) + ")"
        elif c == "regex":
            expr = f"grepl({json.dumps('^(' + r['pattern'] + ')$')}, {_r_name(r['column'])})"
        elif c == "in_set":
            expr = f"{_r_name(r['column'])} %in% c(" + ", ".join(json.dumps(str(v)) for v in r["values"]) + ")"
        elif c == "range":
            lo = r.get("min", "-Inf")
            hi = r.get("max", "Inf")
            expr = f"in_range({_r_name(r['column'])}, min = {lo}, max = {hi})"
        elif c == "type" and r["kind"] in ("integer", "number", "year"):
            expr = f"is.numeric({_r_name(r['column'])})"
        elif c == "compare":
            right = _r_name(r["right"]) if not str(r["right"]).replace(".", "", 1).isdigit() else r["right"]
            expr = f"{_r_name(r['left'])} {r['op']} {right}"
        elif c == "sum_max":
            expr = f"sum({_r_name(r['column'])}, na.rm = TRUE) <= {r['max'] + r.get('tolerance', 0)}"
        elif c == "required_columns":
            expr = "all(c(" + ", ".join(json.dumps(x) for x in r["columns"]) + ") %in% names(.))"
        if expr is None:
            notes.append(f"{r['id']} ({c}): run with dqkit; no direct validate equivalent")
            continue
        rules.append({"expr": expr, "name": r["id"], "label": r.get("description", c)[:80],
                      "description": f"dimension: {r.get('dimension', ISSUE_TYPES[r.get('issue_type', DEFAULT_ISSUE[c])]['dimension'])}"})
    doc = {"rules": rules}
    header = f"# R validate rules for {spec['asset']['id']} (generated by dqkit)\n# Use: library(validate); v <- validator(.file = 'this.yaml'); confront(dat, v)\n"
    if notes:
        header += "".join(f"# not exported: {n}\n" for n in notes)
    return header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)


DQAP_RULES_HEADER = ["Critical data item", "Rule ID", "Rule description", "Dimension", "Measure",
                     "Importance (1-4)", "Impact (1-4)", "Combined score", "Target (%)", "Baseline (%)", "Date measured"]
DQAP_ISSUES_HEADER = ["Issue ID", "Rule ID", "Issue type", "Description", "Dimension", "Performance (%)", "Target (%)",
                      "Band", "Priority score", "Priority", "Resolution timescale", "Responsibility", "Owner", "Status"]


def to_dqap_csv(result: dict) -> dict:
    """Return {'rules': csv_text, 'issues': csv_text} shaped like the GOV.UK DQAP template sections."""
    asset = result["asset"]
    rules_io, issues_io = io.StringIO(), io.StringIO()
    rw, iw = csv.writer(rules_io), csv.writer(issues_io)
    rw.writerow(DQAP_RULES_HEADER)
    iw.writerow(DQAP_ISSUES_HEADER)
    n = 0
    for r in result["results"]:
        a = r["assessment"]
        rw.writerow([", ".join(r["columns"]) or "(dataset)", r["id"], r["description"], r["dimension"], r["check"],
                     a["importance"], a["impact"], a["combined"], a["target"], r["performance"], result["as_of"]])
        if not a["meets_target"]:
            n += 1
            it = ISSUE_TYPES[r["issue_type"]]
            iw.writerow([f"{asset['id']}-I{n:03d}", r["id"], it["label"], it["definition"], r["dimension"], r["performance"],
                         a["target"], a["band"], a["priority_score"], a["priority"], a["resolution"], it["responsibility"],
                         asset.get("steward") or asset.get("owner") or "", "Open"])
    return {"rules": rules_io.getvalue(), "issues": issues_io.getvalue()}
