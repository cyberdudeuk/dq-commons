"""Prove the browser engine (portal/src/js/engine.js) gives the same answers as the Python kit.

For each case this script runs the Python kit, runs the JavaScript engine in Node
(scripts/parity_check.mjs), and compares the two outputs field by field: every rule result
(checked, passed, performance, dimension, issue type, columns, examples, detail, every
assessment key, meta), the dimension summaries, the issue order, the trust level and reasons,
the DQAP route, the DQV JSON-LD (as objects) and the DQAP CSVs (line by line).
Numbers may differ by at most 1e-9.

Run:  python scripts/parity_check.py          (exits 1 on any mismatch)
      python scripts/parity_check.py -v       (also prints every mismatch in full)
"""
from __future__ import annotations

import copy
import csv
import io
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import dqv, exporters, framework, operations, pathway, rules, trust, workbook  # noqa: E402

TOL = 1e-9
AS_OF = date(2026, 10, 14)
RUNNER = ROOT / "scripts" / "parity_check.mjs"
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
VOCAB = {"issue_types": rules.ISSUE_TYPES, "dimensions": dqv._dimensions()}


def node_path():
    return shutil.which("node") or os.environ.get("NODE") or ("/opt/node22/bin/node" if Path("/opt/node22/bin/node").exists() else None)


# ---------- comparing ----------

def norm(x):
    """JSON-safe, comparable form: tuples become lists, NaN and infinity become markers."""
    if isinstance(x, float) and not math.isfinite(x):
        return {"__float__": "nan" if math.isnan(x) else ("inf" if x > 0 else "-inf")}
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, np.generic):
        return norm(x.item())
    return x


def compare(py, js, path="", errs=None):
    errs = [] if errs is None else errs
    if isinstance(py, bool) or isinstance(js, bool):
        if type(py) is not type(js) or py != js:
            errs.append(f"{path}: python {py!r} != js {js!r}")
    elif isinstance(py, (int, float)) and isinstance(js, (int, float)):
        if abs(py - js) > TOL and not (abs(py) > 1e6 and abs(py - js) <= abs(py) * 1e-15):
            errs.append(f"{path}: python {py!r} != js {js!r}")
    elif isinstance(py, dict) and isinstance(js, dict):
        for k in sorted(set(py) | set(js)):
            if k not in py or k not in js:
                errs.append(f"{path}.{k}: only in {'python' if k in py else 'js'}")
            else:
                compare(py[k], js[k], f"{path}.{k}", errs)
    elif isinstance(py, list) and isinstance(js, list):
        if len(py) != len(js):
            errs.append(f"{path}: length python {len(py)} != js {len(js)}")
        for i, (a, b) in enumerate(zip(py, js)):
            compare(a, b, f"{path}[{i}]", errs)
    elif py != js:
        errs.append(f"{path}: python {py!r} != js {js!r}")
    return errs


def run_js(case: dict, workdir: Path) -> dict:
    p = workdir / f"{re.sub(r'[^A-Za-z0-9_-]+', '_', case['name'])}.json"
    p.write_text(json.dumps(norm({**case, "vocab": VOCAB}), ensure_ascii=False), encoding="utf-8")
    out = subprocess.run([node_path(), str(RUNNER), str(p)], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(f"node failed on {case['name']}:\n{out.stderr[-3000:]}")
    return json.loads(out.stdout)


def attempt(fn):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 - we compare failures too
        return {"error": str(e)}


# ---------- Python side ----------

def read_csv_text(text: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(text.encode("utf-8")), dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")


def table_of(df: pd.DataFrame) -> dict:
    return {"columns": [str(c) for c in df.columns],
            "rows": [{str(c): (None if pd.isna(v) else v) for c, v in zip(df.columns, row)} for row in df.itertuples(index=False)]}


def py_run_case(case: dict) -> dict:
    df = read_csv_text(case["csv"]) if "csv" in case else case["df"]
    res = rules.run(df, case["spec"], date.fromisoformat(case["as_of"]))
    out = {"result": res}
    if "csv" in case:
        out["parsed"] = table_of(df)
    out["trust"] = trust.classify(res, case.get("personal"))
    out["route"] = pathway.route(case["spec"]["asset"])
    out["dqv"] = dqv.result_to_dqv(res, case.get("asset_iri"), case.get("dqap_iri"))
    out["dqap"] = exporters.to_dqap_csv(res)
    out["validate"] = attempt(lambda: rules.validate_spec(case["spec"]) or "ok")
    return out


def check_run(case: dict, workdir: Path) -> list:
    py = py_run_case(case)
    jcase = {k: v for k, v in case.items() if k != "df"}
    if "df" in case:
        jcase["table"] = table_of(case["df"])
    js = run_js({**jcase, "kind": "run"}, workdir)
    errs = []
    for k in ("parsed", "result", "trust", "route", "dqv", "validate"):
        if k in py:
            compare(norm(py[k]), js.get(k), k, errs)
    for part in ("rules", "issues"):  # CSVs line by line
        a, b = py["dqap"][part].split("\r\n"), js["dqap"][part].split("\r\n")
        if len(a) != len(b):
            errs.append(f"dqap.{part}: python {len(a)} lines != js {len(b)} lines")
        errs += [f"dqap.{part} line {i + 1}: python {x!r} != js {y!r}" for i, (x, y) in enumerate(zip(a, b)) if x != y]
    return errs


# ---------- fixtures ----------

TEST_SPEC = {  # tests/test_dqkit.py SPEC
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


def test_df():
    return pd.DataFrame({"year": ["2020", "2021", "2021", "2023", None],
                         "value": ["10", "20", "x", "150", ""],
                         "sex": ["F", "M", "Unknown", "F", "M"]})


def csv_text(rows, header, crlf=False, bom=False):
    s = io.StringIO()
    csv.writer(s, lineterminator="\r\n" if crlf else "\n").writerows([header] + rows)
    return ("﻿" if bom else "") + s.getvalue()


# Fixture A: an internal register of people. Messy values everywhere; mid target policy.
A_HEADER = ["person_id", "nhs_no", "name", "sex", "ethnicity", "dob", "visit_date", "region", "score",
            "max_score", "amount", "year", "share", "code", "band (number)"]
A_ROWS = [
    ["1", "943 476 5919", "Smith, John", "M", "White British", "1980-05-01", "2026-09-30", "North East", "45", "50", "1,234", "2019", "12.5", "ab-12", "1"],
    ["2", "9434765919", "Zoë Ångström", "F", "Unknown", "05/01/1990", "2026-10-14", "Wales", "50", "50", "12.50", "2020", "30.25", "AB-7", "2"],
    ["3", "943-476-5919", "José \"Pepe\" Núñez", "F", "", "1975-13-01", "2030-01-01", "London", "60", "50", "-5", "2021", "40", "x-1", "3"],
    ["3", "", "  ", "X", "prefer not to say", "2024-02-30", "14/10/2026", "", "", "100", "abc", "2021", "", "cd-", "4"],
    ["5", "1234567890", "李小龍", "U", "Asian", "2024", "2026-10", " 2026-10-13 ", "99.5", "100", "1e3", "2023", "17.255", "ef-99", "5"],
    ["+6", "123 456 7890", "Smith, John", "m", " NOT STATED ", "1/2/85", "2023-24", "Scotland", "0", "10", "inf", "٢٠٢٤", "0.1", "GH-0", "1"],
    [" 7 ", "1234567890", "Ola\nNordmann", "F", "Mixed", "1980-05-01", "2026-02-29", "Northern Ireland", "-1", "", "1_000", "2024", "0.2", "ij-3", "2"],
    ["8.0", "١٢٣٤٥٦٧٨٩٠", "", "", "White Irish", "2001/02", "2025-12-31", "North East", "100", "100", "  42  ", "2026", "", "kl-12x", "3"],
    ["", "943 476 591", "Ada", "M", "z", "29/02/2024", "", "Wales", "75.25", "80", "--1", "", "0.3", "mn-1", ""],
]
A_SPEC = {
    "asset": {"id": "fixture-a-people", "title": "Fixture A: people register", "importance": 4, "owner": "Test Department",
              "target_policy": "mid", "source": "internal", "personal_data_columns": ["name", "dob"]},
    "rules": [
        {"id": "A01", "check": "required_columns", "columns": ["person_id", "name", "dob", "postcode"]},
        {"id": "A02", "check": "not_null", "column": "name", "personal_data": True, "purpose": "Identify people",
         "requirement": "Every record names a person", "method": "Count blanks", "notes": "Whitespace counts as blank",
         "part_of_data": "name"},
        {"id": "A03", "check": "unique", "columns": ["person_id"], "target": 99},
        {"id": "A04", "check": "unique", "columns": ["name", "dob"], "impact": 1},
        {"id": "A05", "check": "type", "column": "person_id", "kind": "integer"},
        {"id": "A06", "check": "type", "column": "amount", "kind": "number"},
        {"id": "A07", "check": "type", "column": "dob", "kind": "date", "dimension": "accuracy", "personal_data": True},
        {"id": "A08", "check": "type", "column": "year", "kind": "year"},
        {"id": "A09", "check": "regex", "column": "nhs_no", "pattern": r"\d{3} ?\d{3} ?\d{4}"},
        {"id": "A10", "check": "regex", "column": "code", "pattern": r"(?i)(?P<pre>[a-z]+)-\d+\b", "control_point": "pipeline"},
        {"id": "A11", "check": "in_set", "column": "sex", "values": ["F", "M", "X"], "issue_type": "characteristic-defaulted"},
        {"id": "A12", "check": "in_set", "column": "band (number)", "values": [1, 2, 3, True]},
        {"id": "A13", "check": "range", "column": "score", "min": 0, "max": 100, "target": "95"},
        {"id": "A14", "check": "range", "column": "amount", "min": 0},
        {"id": "A15", "check": "range", "column": "score", "max": 50, "impact": 4},
        {"id": "A16", "check": "not_future", "column": "visit_date"},
        {"id": "A17", "check": "compare", "left": "score", "op": "<=", "right": "max_score", "description": "Score within maximum"},
        {"id": "A18", "check": "compare", "left": "score", "op": ">", "right": "0"},
        {"id": "A19", "check": "compare", "left": "max_score", "op": "!=", "right": "50"},
        {"id": "A20", "check": "compare", "left": "score", "op": "==", "right": "max_score"},
        {"id": "A21", "check": "sum_max", "column": "share", "max": 100, "tolerance": 0.5},
        {"id": "A22", "check": "freshness", "column": "visit_date", "expected": "P1M", "lag": "P7D"},
        {"id": "A23", "check": "freshness", "column": "year", "expected": "P1Y"},
        {"id": "A24", "check": "no_gaps", "column": "year"},
        {"id": "A25", "check": "no_gaps", "column": "year", "step": 2},
        {"id": "A26", "check": "header_has_unit", "ignore": ["person_id", "name"]},
        {"id": "A27", "check": "header_has_unit", "columns": ["score", "share", "score"], "tokens": ["SCORE", "share"]},
        {"id": "A28", "check": "not_unknown", "column": "ethnicity", "dimension": "representativeness"},
        {"id": "A29", "check": "not_unknown", "column": "ethnicity", "values": ["Prefer not to say", " NK ", 0]},
        {"id": "A30", "check": "group_disparity", "group": "sex", "tolerance": 5, "inner": {"check": "not_null", "column": "ethnicity"}},
        {"id": "A31", "check": "group_disparity", "group": "region", "tolerance": 50,
         "inner": {"check": "type", "column": "amount", "kind": "number"}},
        {"id": "A32", "check": "not_null", "column": "ghost"},
        {"id": "A33", "check": "unique", "columns": ["person_id", "ghost2"]},
        {"id": "A34", "check": "compare", "left": "amount", "op": ">=", "right": "1.5e2"},
        {"id": "A35", "check": "range", "column": "dob", "min": 0, "issue_type": "out-of-bounds", "impact": 2, "target": 50},
    ],
}

# Fixture B: an external supplier's financial returns. BOM, CRLF, financial years, 300 rows of
# many-decimal floats (exercises numpy's pairwise sum beyond 128 values); high target policy.


def fixture_b():
    rnd = random.Random(20261014)
    header = ["Financial year", "Spend (£ millions)", "Budget (£ millions)", "Share (%)", "Count", "Notes"]
    rows = []
    for i in range(300):
        fy = 2000 + i % 27
        label = rnd.choice([f"{fy}-{(fy + 1) % 100:02d}", f"{fy}/{fy + 1}", f"{fy} - {(fy + 1) % 100:02d}", str(fy)])
        spend = rnd.choice([f"{rnd.uniform(0, 5000):.{rnd.randint(0, 9)}f}", f"{rnd.randint(0, 9999):,}", "", " 12 ", "n/a"])
        budget = rnd.choice([f"{rnd.uniform(0, 5000):.3f}", str(rnd.randint(0, 6000)), "", "1e3", "0.30000000000000004"])
        share = f"{rnd.random() / 3:.17f}" if i % 7 else ""
        count = rnd.choice([str(rnd.randint(-5, 500)), "+5", " 7 ", "1,000", "1.0", "", "١٢"])
        notes = rnd.choice(["", "ok", "Revised, see note", 'He said "fine"', "line one\nline two", "naïve café"])
        rows.append([label, spend, budget, share, count, notes])
    text = csv_text(rows, header, crlf=True, bom=True)
    spec = {
        "asset": {"id": "fixture-b-finance", "title": "Fixture B: financial returns", "importance": 2, "steward": "Finance team",
                  "owner": "Treasury-like body", "target_policy": "high", "source": "external", "influence": True,
                  "fields_adequate": False, "iri": "https://example.org/data/finance"},
        "rules": [
            {"id": "B01", "check": "regex", "column": "Financial year", "pattern": r"\d{4}[-/]\d{2,4}"},
            {"id": "B02", "check": "regex", "column": "Financial year", "pattern": r"(\d{4})\s*-\s*(\d{2})$"},
            {"id": "B03", "check": "no_gaps", "column": "Financial year"},
            {"id": "B04", "check": "freshness", "column": "Financial year", "expected": "P1Y", "lag": "P3M"},
            {"id": "B05", "check": "compare", "left": "Spend (£ millions)", "op": "<", "right": "Budget (£ millions)"},
            {"id": "B06", "check": "compare", "left": "Budget (£ millions)", "op": ">=", "right": "Spend (£ millions)"},
            {"id": "B07", "check": "sum_max", "column": "Share (%)", "max": 30},
            {"id": "B08", "check": "sum_max", "column": "Budget (£ millions)", "max": 1e9},
            {"id": "B09", "check": "range", "column": "Spend (£ millions)", "min": 0, "max": 4999.5},
            {"id": "B10", "check": "type", "column": "Count", "kind": "integer"},
            {"id": "B11", "check": "type", "column": "Spend (£ millions)", "kind": "number"},
            {"id": "B12", "check": "unique", "columns": ["Financial year", "Count"]},
            {"id": "B13", "check": "not_null", "column": "Notes", "target": 10},
            {"id": "B14", "check": "header_has_unit"},
            {"id": "B15", "check": "sum_max", "column": "Count", "max": 100000},
            {"id": "B16", "check": "type", "column": "Financial year", "kind": "date"},
            {"id": "B17", "check": "not_future", "column": "Financial year"},
            {"id": "B18", "check": "range", "column": "Budget (£ millions)", "min": 0.3, "max": 0.3, "target": 0},
        ],
    }
    return text, spec


# Fixture C: survey results by group. External, no influence, can enrich; low policy; dd/mm/yy dates.
C_HEADER = ["Group", "Response", "Answered on", "Age band", "Satisfaction (%)", "Year"]
C_ROWS = [
    ["Wales", "Yes", "01/02/24", "16-24", "80", "2018"],
    ["wales", "No", "31/12/69", "25-34", "75.5", "2019"],
    ["", "Yes", "15/06/68", "Z", "101", "2020"],
    ["Ålesund", "", "1/1/26", "x ", "-0.5", ""],
    ["😀 group", "Maybe", "29/02/23", "U", "", "2022"],
    ["！wide", "Yes", "2026-10-15", "35-44", "50", "nan"],
    ["Wales", "yes", "2026-10-14", "45-54", "99.99", "2025"],
    ["", "No", "not a date", "prefer not to say", "100", "2026"],
    ["Ålesund", "No", "", "55+", "60", "2026"],
    ["nan", "Yes", "2024/25", "16-24", "70", "2018"],
]
C_SPEC = {
    "asset": {"id": "fixture-c-survey", "title": "Fixture C: survey", "importance": 1, "target_policy": "low",
              "source": "external", "influence": False, "fields_adequate": False, "can_enrich": True},
    "rules": [
        {"id": "C01", "check": "group_disparity", "group": "Group", "inner": {"check": "in_set", "column": "Response", "values": ["Yes", "No"]}},
        {"id": "C02", "check": "group_disparity", "group": "Group", "tolerance": 100,
         "inner": {"check": "range", "column": "Satisfaction (%)", "min": 0, "max": 100}},
        {"id": "C03", "check": "group_disparity", "group": "Group", "inner": {"check": "regex", "column": "Response", "pattern": "[A-Z][a-z]+"}},
        {"id": "C04", "check": "group_disparity", "group": "Group", "inner": {"check": "not_unknown", "column": "Age band"}},
        {"id": "C05", "check": "not_unknown", "column": "Age band"},
        {"id": "C06", "check": "not_future", "column": "Answered on"},
        {"id": "C07", "check": "type", "column": "Answered on", "kind": "date"},
        {"id": "C08", "check": "freshness", "column": "Answered on", "expected": "P2W", "lag": "P1D"},
        {"id": "C09", "check": "freshness", "column": "Age band", "expected": "P1Y"},
        {"id": "C10", "check": "no_gaps", "column": "Age band"},
        {"id": "C11", "check": "no_gaps", "column": "Year"},
        {"id": "C12", "check": "header_has_unit", "columns": ["Satisfaction (%)", "Year", "Year"]},
        {"id": "C13", "check": "required_columns", "columns": ["Group", "Response"]},
        {"id": "C14", "check": "in_set", "column": "Group", "values": ["Wales", "nan", "Ålesund"]},
        {"id": "C15", "check": "compare", "left": "Satisfaction (%)", "op": "<=", "right": "100"},
        {"id": "C16", "check": "group_disparity", "group": "Response", "tolerance": 0,
         "inner": {"check": "freshness", "column": "Answered on", "expected": "P1Y"}},
    ],
}

# Fixture D: a header with no rows (every check at zero records).
D_TEXT = "a,b,Year,Share (%)\n"
D_SPEC = {
    "asset": {"id": "fixture-d-empty", "importance": 2},
    "rules": [{"id": f"D{i:02d}", **r} for i, r in enumerate([
        {"check": "not_null", "column": "a"}, {"check": "unique", "columns": ["a", "b"]},
        {"check": "type", "column": "a", "kind": "year"}, {"check": "regex", "column": "a", "pattern": "x"},
        {"check": "in_set", "column": "a", "values": ["x"]}, {"check": "range", "column": "a", "min": 1},
        {"check": "not_future", "column": "a"}, {"check": "compare", "left": "a", "op": "<", "right": "b"},
        {"check": "sum_max", "column": "Share (%)", "max": 100}, {"check": "freshness", "column": "Year", "expected": "P1Y"},
        {"check": "no_gaps", "column": "Year"}, {"check": "header_has_unit"},
        {"check": "not_unknown", "column": "a"}, {"check": "required_columns", "columns": ["a", "zzz"]},
        {"check": "group_disparity", "group": "a", "inner": {"check": "not_null", "column": "b"}},
    ], start=1)],
}


# ---------- micro batteries: the Python behaviours the engine copies ----------

def fuzz_numbers(n=3000):
    rnd = random.Random(7)
    out = []
    for _ in range(n):
        d = "".join(rnd.choice("0123456789") for _ in range(rnd.randint(1, 22)))
        k = rnd.random()
        if k < 0.4:
            p = rnd.randint(0, len(d))
            d = d[:p] + "." + d[p:]
        if rnd.random() < 0.3:
            d += rnd.choice("eE") + rnd.choice(["", "+", "-"]) + str(rnd.randint(0, 340))
        if rnd.random() < 0.3:
            d = rnd.choice("+-") + d
        out.append(d)
    out += [repr(rnd.uniform(-1e6, 1e6)) for _ in range(500)] + [f"{rnd.uniform(0, 100):.{rnd.randint(1, 20)}f}" for _ in range(500)]
    return out


NUMBERS = ["1", "-1", "+1", " 1", "1 ", "\t1", "1.5", ".5", "5.", "1e3", "1E3", "1e", "e3", "1_000", "inf", "-inf", "Inf",
           "infinity", "-Infinity", "+inf", " inf ", "nan", "NaN", "null", "None", "N/A", "1,234", "١٢", "１２", "0x10", "1.5.5",
           "--1", "1e400", "-1e400", "1e-400", "12345678901234567890", "0.1", "  ", "", " 1 2", "1d3", "true", "1.0e+2", "+.5",
           "-.5e-1", "1.e2", " 1", "00012", "-0", "0.30000000000000004", "1e0000000000005", "0.001e309", "10e308", "1e309",
           "123e-330", "0.0000000000000000001", "00000000000000000001", "1e-320", "1e-617", "-0e400", "1e5 ", "1e+", "1e5.5",
           "1.7976931348623158e308", "4.9e-324", "\n1", "\v1", "\r1", "1\x0c", "+", "-", ".", "1e99999999999999999999999"]
TYPES = [(v, k) for k in ("integer", "number", "year", "date") for v in
         ["1", " 12 ", "+5", "-3", "1,000", "1.0", "", "  ", None, "١٢", "１２", "1_000", "1__0", "_1", "1_", "inf", "nan", "-Infinity",
          "1e3", "1e", "1,2,3", "2024", "0999", "3000", "٢٠٢٤", "2024-01-05", "05/01/2024", "2024-13", "1/2/85", "2023-24",
          "31/02/2024", "2024-1-5", "2024-01- 5", "2024-01-5x", " 2024-02-03 ", "0000-01-01", "2023/2024", "2023 - 24",
          "2023-2", "29/02/24", "1.5.5", "abc", "1 ", " 1 ", "1e5\x1c"]]
DATES = [v for v, k in TYPES if k == "date"] + ["2024-02-29", "2023-02-29", "1900-02-29", "2000-02-29", "1/1/68", "1/1/69",
                                               "2024-12", "9999-12-31", "2024-W01", "2024-01-01T00:00", "2024 - 2025",
                                               "２０２４-０１-０５", "2024-1٥-01", "12/12/12", " 5/ 5/2024", "5/5/2024"]
REGEX = [(p, s) for p, ss in [
    (r"\d{4}[-/]\d{2,4}", ["2024-25", "2024", "2024/2025", "٢٠٢٤-٢٥", "2024-2", "2024-25\n"]),
    (r"(\d{4})\s*-\s*(\d{2})$", ["2024-25", "2024 - 25", "2024 - 25", "2024-25\n"]),
    (r"(?i)(?P<pre>[a-z]+)-\d+\b", ["ab-12", "AB-7", "x-1", "cd-", "kl-12x", "ÅB-1"]),
    (r"[A-Z][a-z]+", ["Yes", "yes", "No", "Maybe", "Ñu", "É"]),
    (r"\w+", ["abc", "a_b", "ñ", "日本", "١٢", "a b", "a-b", "́"]),
    (r"\s*\S+\s*", [" x ", "　x　", "x\x1c", "﻿x"]),
    (r"a.c", ["abc", "a\nc", "a\rc", "a c"]),
    (r"(?s)a.c", ["a\nc"]),
    (r"[]a]+", ["]a]", "b"]), (r"[^]a]+", ["bc", "]"]),
    (r"a{2}", ["aa", "a{2}"]), (r"a{,2}", ["", "a", "aa", "aaa", "a{,2}"]), (r"a{}", ["a{}"]), (r"a{x}", ["a{x}"]),
    (r"x}", ["x}"]), (r"\x41é\101\0", ["Aé" + "A\x00"]), (r"(a)\1", ["aa", "ab"]), (r"(?P<x>a)(?P=x)", ["aa"]),
    (r"a|b|", ["a", "", "c"]), (r"[\d.]+", ["1.2", "١.٢", "a"]), (r"[\w-]+", ["a-b_c", "a b"]), (r"\bcat\b", ["cat"]),
    (r"(?#comment)abc", ["abc"]), (r"^abc$", ["abc", "abc\n"]), (r"\Aabc\Z", ["abc", "abc\n"]), (r"[\s]+", ["\x85\x1f "]),
    (r"(?m)^a$\n^b$", ["a\nb"]), (r"\D+", ["abc", "a1", "a١"]), (r"(?a)\d+", ["12", "١٢"]), (r"\$\.\-", ["$.-"]),
    (r"a++", ["aa"]), (r"(?>a)", ["a"]), (r"[\W]", ["!"]),
] for s in ss]


def round_cases():
    rnd = random.Random(3)
    xs = [2.675, 0.125, 0.375, 2.5, 3.5, -2.5, 0.5, 1.5, 96.24999999999999, 33.3335, 1e-20, 123456789.123456789, -0.0004, 547.89,
          100 * 2 / 3, 100 * 1 / 3, 100 * 7 / 9, 4.35, 0.045, 1e300, 5e-324]
    xs += [rnd.uniform(-1000, 1000) for _ in range(300)] + [round(rnd.uniform(0, 100), 4) + 0.00005 for _ in range(300)]
    return [[x, n] for x in xs for n in (0, 1, 3, 4)]


REPRS = [80.0, 0.1, 1e16, 1e15, 123456789012345.6, 0.0001, 0.00001, 1.5e-7, -2.5, 1e22, 96.25, 1 / 3, 99.9, 100.0, 5e-324,
         1.7976931348623157e308, 12345.678, 0.0, -0.0, 33.333, 1234567890123456.7]
ERROR_PERCENTS = [0, 50, 74.9, 75, 80, 89.99, 90, 95, 96, 96.25, 97.5, 99, 99.5, 99.89, 99.9, 99.95, 99.99, 99.999, 100,
                  100 * 2 / 3, 100 * 5 / 7, 99.99999999999999, 92.5, 60, 20, 1, 37.5, 87.5, 91.0, 99.0, 98.4]
DURATIONS = ["P1Y", "P6M", "P1W", "P1D", "P1Y6M", "P2W1D", "P0D", "P", "", None, "1Y", "P1.5Y", "P١Y", "P1Y2M3W4D", "p1y", "P10Y"]


def sum_cases():
    rnd = random.Random(11)
    out = []
    for n in [0, 1, 7, 8, 9, 15, 16, 17, 127, 128, 129, 255, 256, 300, 1000, 1500]:
        out.append([rnd.choice([rnd.uniform(-1e3, 1e3), round(rnd.uniform(0, 100), 3), 1e-9 * rnd.random()]) for _ in range(n)])
    return out


CSV_TEXTS = ['a,b\n\n1,2\n\n3,4\n', 'a,b\n  \n1,2\n\t\n3,4\n', '\n\na,b\n1,2\n', 'a,b\r\n1,2\r\n3,4\r\n', 'a,b\r1,2\r3,4\r',
             'a,b\n"x,y","he said ""hi"""\n"multi\nline",2\n', 'a,b\n"",2\n,""\n', 'a,b\nab"c,2\n"ab"c,3\n',
             'a,b,c\n1\n1,2\n', 'a,b,\n1,2,\n', 'a,a,b,a\n1,2,3,4\n', ',b\n1,2\n', 'a,b\n 1 , 2 \n', 'a,b\n1,2', 'a,b\n,\n',
             '﻿a,b\n1,2\n', 'naïve,b\n١٢,"£1,234"\n', 'a,b\n "x" ,2\n', '" a ",b\n1,2\n', 'a,b\r\n"x\r\ny",2\r\n',
             'a,b\n  ,\n1,2\n', 'a,a.1,a\n1,2,3\n', 'Unnamed: 1,,c\n1,2,3\n', 'a,b\n', 'a\n\t\n1\n', 'a,b\r\n1,2\n3,4\r5,6\n',
             'a,b\n"x"\n1,2\n', 'a,b\n1,2\n   ', 'a,b\n   x,1\n', 'a,b\n1,"x"y"z"\n', 'a,b\n1,2\n1,2,3\n', 'a,b\n"open,1\n', '',
             '\n\n', '__proto__,constructor\n1,2\n']


def py_parse(text):
    try:
        return table_of(read_csv_text(text))
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


VALIDATE = [
    {"asset": {"id": "t"}}, {"rules": []}, {"asset": {"id": "t", "importance": 5}, "rules": []},
    {"asset": {"id": "t", "importance": "3"}, "rules": []}, {"asset": {"id": "t", "importance": None}, "rules": []},
    {"asset": {"id": "t", "target_policy": "max"}, "rules": []}, {"asset": {"id": "t", "target_policy": None}, "rules": []},
    {"asset": {"id": "t"}, "rules": [{"id": "A", "check": "magic"}]}, {"asset": {"id": "t"}, "rules": [{"check": "magic"}]},
    {"asset": {"id": "t"}, "rules": [{"id": "A", "check": "not_null"}, {"id": "A", "check": "unique"}]},
    {"asset": {"id": "t"}, "rules": [{"id": "A", "check": "not_null", "control_point": "magic"}]},
    {"asset": {"id": "t"}, "rules": [{"id": "A", "check": "not_null", "issue_type": "nope"}]},
    {"asset": {"id": "t"}, "rules": [{"id": "A", "check": "not_null", "issue_type": "it's"}]},
    {"asset": {"id": "t"}, "rules": [{"id": 7, "check": "not_null"}, {"id": 7, "check": "not_null"}]},
    {"asset": {"id": "t", "importance": 4, "target_policy": "high"}, "rules": [{"id": "A", "check": "group_disparity", "control_point": "reporting"}]},
]
ROUTES = [{}, {"source": "internal"}, {"source": "external"}, {"source": "external", "influence": True},
          {"source": "external", "influence": False, "fields_adequate": False},
          {"source": "external", "influence": False, "fields_adequate": False, "can_enrich": True},
          {"source": "internal", "fields_adequate": False}, {"source": "external", "influence": "false"},
          {"source": "external", "influence": [], "fields_adequate": 0}, {"source": "partner"}]


def trust_cases():
    out = []
    for perf, dims, personal, use_meta in [(89.0, ("completeness", "validity", "accuracy"), None, True),
                                         (100.0, ("completeness", "validity", "accuracy"), None, True),
                                         (100.0, ("completeness",), None, True), (95.0, ("accuracy", "timeliness"), ["name"], False),
                                         (50.0, ("validity", "uniqueness", "accuracy", "representativeness"), ["name"], False)]:
        results = []
        for i, d in enumerate(dims):
            p = perf if d == "accuracy" else 100.0
            a = framework.assess(3, 3, p).to_dict()
            results.append({"id": f"R{i}", "description": d, "dimension": d, "columns": ["name"] if d == "accuracy" else ["x"],
                            "performance": p, "assessment": a, "meta": {"personal_data": use_meta and d == "accuracy"}})
        out.append([{"asset": {"id": "t", "personal_data_columns": ["x"]}, "results": results}, personal])
    return out


def contract_specs():
    """Every fixture and library rules file, plus a contract with foreign rules, for the converters."""
    specs = [copy.deepcopy(c["spec"]) for c in cases()]
    for f in sorted((ROOT / "rules" / "library").glob("*.yaml")):
        specs.append(rules.expand_valuesets(yaml.safe_load(f.read_text(encoding="utf-8")), VALUESETS))
    return specs


def py_contracts(spec):
    from dqkit import contracts
    o = contracts.to_odcs(spec)
    t = contracts.to_table_schema(spec)
    from dqkit import exporters
    return {"odcs": o, "ts": t, "csvw": contracts.to_csvw(spec), "back": contracts.from_odcs(o), "backTs": contracts.from_table_schema(t),
            "unsupported": contracts.unsupported(o), "gx": exporters.to_great_expectations(spec), "rv": list(exporters.r_validate_rules(spec))}


def micro_case():
    numbers = NUMBERS + fuzz_numbers()
    sums = sum_cases()
    trusts = trust_cases()
    rx = []
    for p, s in REGEX:
        def f(p=p, s=s):
            if re.search(r"\+\+|\(\?>|\[\\W\]", p):
                return {"error": "unsupported in the browser"}  # possessive/atomic/\W-in-class: JS refuses (documented)
            return re.fullmatch(p, s) is not None
        rx.append(attempt(f))
    py = {
        "numbers": pd.to_numeric(pd.Series(numbers, dtype="str"), errors="coerce").map(lambda x: x).tolist(),
        "types": [attempt(lambda v=v, k=k: rules._is_type(v, k)) for v, k in TYPES],
        "dates": [attempt(lambda s=s: (d.isoformat() if (d := rules._parse_date(s)) else None)) for s in DATES],
        "regex": rx,
        "rounds": [round(x, n) for x, n in round_cases()],
        "reprs": [float(repr(x)) for x in REPRS],
        "repr_text": [repr(x) for x in REPRS],
        "error_rates": [framework.error_rate(x) for x in ERROR_PERCENTS],
        "pairwise": [float(np.sum(np.array(xs, dtype=float))) for xs in sums],
        "pysum": [sum(xs) for xs in sums],
        "durations": [attempt(lambda s=s: rules.iso_duration_days(s)) for s in DURATIONS],
        "csvs": [py_parse(t) for t in CSV_TEXTS],
        "validate": [attempt(lambda s=s: rules.validate_spec(s) or "ok") for s in VALIDATE],
        "identifiers": [attempt(lambda v=v, k=k: rules.identifier_ok(v, k)) for v, k in IDENTIFIERS],
        "valuesets": [attempt(lambda: rules.expand_valuesets(copy.deepcopy(E_SPEC_RAW), VALUESETS)),
                      attempt(lambda: rules.expand_valuesets({"rules": [{"id": "X", "check": "in_valueset", "valueset": "uk_nations", "match": "code"}]}, VALUESETS)),
                      attempt(lambda: rules.expand_valuesets({"rules": [{"id": "X", "check": "in_valueset", "valueset": "uk_nations", "match": "both"}]}, VALUESETS))],
        "contracts": [attempt(lambda s=s: py_contracts(copy.deepcopy(s))) for s in contract_specs()],
        "misc": {"targets": [framework.default_target(s) for s in (3, 6, 9, 16)], "mid4": framework.default_target(4, "mid"),
                 "bands": [framework.bands(t) for t in (75, 90, 95, 97.5, 99.9, 100)],
                 "route": [pathway.route(a) for a in ROUTES], "trust": [trust.classify(r, p) for r, p in trusts]},
    }
    js_in = {"name": "micro", "kind": "micro", "numbers": numbers, "types": TYPES, "dates": DATES, "regex": REGEX,
             "rounds": round_cases(), "reprs": REPRS, "error_rates": ERROR_PERCENTS, "sums": sums, "durations": DURATIONS,
             "csvs": CSV_TEXTS, "validate": VALIDATE, "routes": ROUTES, "trusts": trusts, "identifiers": IDENTIFIERS, "valueset_specs": [copy.deepcopy(E_SPEC_RAW), {"rules": [{"id": "X", "check": "in_valueset", "valueset": "uk_nations", "match": "code"}]}, {"rules": [{"id": "X", "check": "in_valueset", "valueset": "uk_nations", "match": "both"}]}], "valuesets_data": VALUESETS,
             "contract_specs": contract_specs()}
    return py, js_in


def check_micro(workdir) -> dict:
    py, js_in = micro_case()
    js = run_js(js_in, workdir)
    out = {}
    # Numbers, rounding and sums must match bit for bit, not just within 1e-9.
    errs = []
    for i, (a, b) in enumerate(zip(py["numbers"], js["numbers"])):
        a = norm(a)
        if not (a == b or (isinstance(a, float) and isinstance(b, (int, float)) and a == float(b))):
            errs.append(f"numbers[{i}] {js_in['numbers'][i]!r}: python {a!r} != js {b!r}")
    if len(py["numbers"]) != len(js["numbers"]):
        errs.append("numbers: lengths differ")
    out["pandas to_numeric (exact)"] = errs
    errs = [f"rounds[{i}] round{tuple(js_in['rounds'][i])}: python {a!r} != js {b!r}"
            for i, (a, b) in enumerate(zip(py["rounds"], js["rounds"])) if float(a) != float(b)]
    out["Python round() (exact)"] = errs
    errs = [f"sum[{i}]: python {a!r} != js {b!r}" for i, (a, b) in enumerate(zip(py["pairwise"] + py["pysum"], js["pairwise"] + js["pysum"]))
            if float(a) != float(b)]
    out["numpy and Python sums (exact)"] = errs
    out["float repr"] = [f"repr {x!r}: python {a!r} != js {b!r}"
                         for x, a, b in zip(REPRS, py["repr_text"], js["reprs"]) if a != b]
    labelled = {"types": "type checks (_is_type)", "dates": "date parsing (_parse_date)", "regex": "regex translation (fullmatch)",
                "error_rates": "error_rate text", "durations": "ISO durations", "csvs": "CSV reading (read_csv)",
                "validate": "validate_spec messages", "misc": "targets, bands, routes, trust",
                "identifiers": "identifier formats and check digits", "valuesets": "value set expansion",
                "contracts": "data contracts and exports (ODCS, Table Schema, CSVW, GX, R validate)"}
    for k, label in labelled.items():
        a, b = norm(py[k]), js[k]
        if k in ("regex", "types", "dates", "durations", "csvs", "identifiers", "valuesets"):  # failures: compare that both fail, not the wording
            a = [({"error": True} if isinstance(x, dict) and "error" in x else x) for x in a]
            b = [({"error": True} if isinstance(x, dict) and "error" in x else x) for x in b]
        errs = compare(a, b, k)
        if k == "regex":  # say which pattern and text
            errs = [e + "  " + repr(REGEX[int(re.search(r"\[(\d+)\]", e).group(1))]) for e in errs]
        out[label] = errs
    return out


def check_grid(workdir) -> list:
    perfs = [0, 50, 74.9, 75, 89.99, 90, 95, 96.24, 96.25, 96.5, 97.5, 99, 99.89, 99.9, 99.95, 100]
    items = [[i, m, p, None, pol] for i in range(1, 5) for m in range(1, 5) for p in perfs for pol in ("low", "mid", "high")]
    items += [[i, m, p, t, "low"] for i in (1, 2, 4) for m in (1, 3) for p in perfs for t in (0, 75, 95, 99.9, 100, "97.5")]
    items += [[5, 1, 50, None, "low"], [2, 2, 101, None, "low"], [2, 2, -1, None, "low"], [2, 2, 50, None, "max"], [0, 1, 50, None, "low"]]
    py = [attempt(lambda it=it: framework.assess(it[0], it[1], it[2], it[3], it[4]).to_dict()) for it in items]
    js = run_js({"name": "assess-grid", "kind": "grid", "items": items}, workdir)
    return compare(norm(py), js["assess"], "assess")


def check_ops(name, cycles, spec, workdir, extra_history=None) -> list:
    """cycles: [(as_of, csv_text)]. History written by workbook.append_history, as the kit does."""
    with tempfile.TemporaryDirectory() as d:
        res = None
        for as_of, text in cycles:
            res = rules.run(read_csv_text(text), spec, date.fromisoformat(as_of))
            workbook.append_history(res, d)
        hp = Path(d) / f"{spec['asset']['id']}.history.csv"
        if extra_history:
            with open(hp, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(extra_history)
        py_ops = operations.assess(res, d)
        with open(hp, encoding="utf-8") as f:
            history = list(csv.DictReader(f))
    js = run_js({"name": name, "kind": "ops", "csv": cycles[-1][1], "spec": spec, "as_of": cycles[-1][0], "history": history}, workdir)
    return compare(norm(res), js["result"], "result") + compare(norm(py_ops), js["ops"], "ops")


E_HEADER = ["nhs", "nino", "postcode", "uprn", "gss", "company", "charity", "urn", "ods", "lei", "ethnic", "nation"]
E_ROWS = [
    ["9434765919", "AB123456C", "SW1A 1AA", "100023336956", "E09000001", "SC123456", "NIC100002", "100000", "RX1", "5493001KJTIIGC8Y1R12", "White", "Wales"],
    ["943 476 5919", "AB 12 34 56 C", "EC1A1BB", "1", "W06000015", "01234567", "1234567", "12345", "A1B2C3D", "5493001KJTIIGC8Y1R13", "Other ethnic group", "England"],
    ["9434765918", "QQ123456C", "sw1a 1aa", "0", "X12345678", "AB12345", "SC12345", "1234567", "ab1", "549300", "white", "UK"],
    ["", "BG123456A", "GIR 0AA", "1234567890123", "E0900000", "OC000001", "123456", "abcdef", "R1A", "", "Mixed or Multiple ethnic groups", "Northern Ireland"],
    ["0000000000", "AB123456E", "M1 1AE", "12a", "S12000033", "12345678", "1234567-1", "654321", "12345", "5493001KJTIIGC8Y1R1", "", "Scotland"],
]
E_SPEC_RAW = {"asset": {"id": "fixture-e-identifiers", "importance": 4, "target_policy": "high"}, "rules": [
    {"id": "E01", "check": "identifier", "column": "nhs", "scheme": "nhs_number"},
    {"id": "E02", "check": "identifier", "column": "nino", "scheme": "nino"},
    {"id": "E03", "check": "identifier", "column": "postcode", "scheme": "uk_postcode"},
    {"id": "E04", "check": "identifier", "column": "uprn", "scheme": "uprn"},
    {"id": "E05", "check": "identifier", "column": "gss", "scheme": "gss_code"},
    {"id": "E06", "check": "identifier", "column": "company", "scheme": "company_number"},
    {"id": "E07", "check": "identifier", "column": "charity", "scheme": "charity_number"},
    {"id": "E08", "check": "identifier", "column": "urn", "scheme": "school_urn"},
    {"id": "E09", "check": "identifier", "column": "ods", "scheme": "ods_code"},
    {"id": "E10", "check": "identifier", "column": "lei", "scheme": "lei"},
    {"id": "E11", "check": "in_valueset", "column": "ethnic", "valueset": "ethnic_group_ew_2021_high_level"},
    {"id": "E12", "check": "in_valueset", "column": "nation", "valueset": "uk_nations", "match": "label"},
]}
VALUESETS = {n: rules.load_valueset(n) for n in ("uk_nations", "ethnic_group_ew_2021_high_level")}
IDENTIFIERS = [[r[i], s] for r in E_ROWS for i, s in enumerate(
    ["nhs_number", "nino", "uk_postcode", "uprn", "gss_code", "company_number", "charity_number", "school_urn", "ods_code", "lei"])]
IDENTIFIERS += [[" 9434765919 ", "nhs_number"], ["94347659１9", "nhs_number"], ["AB123456 C", "nino"], ["SW1A  1AA", "uk_postcode"], [None, "nino"],
                ["x", "not_a_scheme"]]


def cases():
    out = []
    for rf, cf in CHARTS.items():
        spec = yaml.safe_load((ROOT / "rules" / "ndl" / rf).read_text(encoding="utf-8"))
        text = (ROOT / "assessments" / "ndl" / "chart-data" / cf).read_bytes().decode("utf-8")
        out.append({"name": f"NDL {rf[:-5]}", "csv": text, "spec": spec, "as_of": AS_OF.isoformat(), "asset_iri": spec["asset"].get("iri")})
    out.append({"name": "tests/test_dqkit DF + SPEC", "df": test_df(), "spec": TEST_SPEC, "as_of": AS_OF.isoformat()})
    out.append({"name": "fixture A people (mid policy)", "csv": csv_text(A_ROWS, A_HEADER), "spec": A_SPEC, "as_of": AS_OF.isoformat(),
                "dqap_iri": "https://example.org/dqap/a"})
    out.append({"name": "fixture A, personal columns given", "csv": csv_text(A_ROWS, A_HEADER), "spec": A_SPEC,
                "as_of": "2025-01-31", "personal": ["nhs_no", "dob"]})
    tb, sb = fixture_b()
    out.append({"name": "fixture B finance (high policy)", "csv": tb, "spec": sb, "as_of": AS_OF.isoformat()})
    out.append({"name": "fixture C survey (low policy)", "csv": csv_text(C_ROWS, C_HEADER), "spec": C_SPEC, "as_of": AS_OF.isoformat()})
    out.append({"name": "fixture D header only", "csv": D_TEXT, "spec": D_SPEC, "as_of": AS_OF.isoformat()})
    out.append({"name": "fixture E identifiers and value sets", "csv": csv_text(E_ROWS, E_HEADER),
                "spec": rules.expand_valuesets(copy.deepcopy(E_SPEC_RAW), VALUESETS), "as_of": AS_OF.isoformat()})
    return out


def check_coverage(all_cases) -> list:
    """Every one of the 15 checks, and every option variant asked for, must appear in the fixtures."""
    used = [r for c in all_cases for r in c["spec"]["rules"]]
    used += [r["inner"] for r in used if r.get("check") == "group_disparity"]
    missing = sorted(set(rules.CHECKS) - {r["check"] for r in used})
    need = {"target override": any("target" in r for r in used), "impact override": any("impact" in r for r in used),
            "policies low/mid/high": {c["spec"]["asset"].get("target_policy", "low") for c in all_cases} >= {"low", "mid", "high"},
            "range min only": any(r["check"] == "range" and "min" in r and "max" not in r for r in used),
            "range max only": any(r["check"] == "range" and "max" in r and "min" not in r for r in used),
            "compare ops": {r["op"] for r in used if r["check"] == "compare"} >= {"<", "<=", ">", ">=", "==", "!="},
            "type kinds": {r["kind"] for r in used if r["check"] == "type"} >= {"integer", "number", "year", "date"},
            "unique on several columns": any(r["check"] == "unique" and len(r["columns"]) > 1 for r in used),
            "every identifier scheme": {r["scheme"] for r in used if r["check"] == "identifier"} >= set(rules.IDENTIFIER_SCHEMES)}
    return [f"check type never exercised: {m}" for m in missing] + [f"variant never exercised: {k}" for k, ok in need.items() if not ok]


def main(verbose=False) -> int:
    if not node_path():
        print("node not found; cannot run the parity check")
        return 2
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        w = Path(tmp)
        all_cases = cases()
        rows.append(("fixture coverage (15 checks, all variants)", check_coverage(all_cases)))
        for c in all_cases:
            rows.append((c["name"], check_run(c, w)))
        rows.append(("assess grid (4 x 4 x 16 x 3 + targets)", check_grid(w)))
        broken, fixed = test_df(), test_df().dropna()
        rows.append(("operations: tests DF, 4 cycles", check_ops("ops-test-df", [
            ("2026-01-01", broken.to_csv(index=False)), ("2026-04-01", fixed.to_csv(index=False)),
            ("2026-07-01", broken.to_csv(index=False)), ("2026-10-01", broken.to_csv(index=False))], TEST_SPEC, w,
            extra_history=[["2025-10-01", "OLD", "50.0", "75.0", "False"], ["2025-10-01", "R1", "100.0", "97.5", "True"]])))
        good = [r for r in A_ROWS if r[0] in ("1", "2", "5")]
        rows.append(("operations: fixture A, 4 cycles", check_ops("ops-fixture-a", [
            ("2026-01-15", csv_text(A_ROWS, A_HEADER)), ("2026-04-15", csv_text(good, A_HEADER)),
            ("2026-07-15", csv_text(A_ROWS[:5], A_HEADER)), ("2026-10-14", csv_text(good + A_ROWS[3:4], A_HEADER))], A_SPEC, w)))
        for label, errs in check_micro(w).items():
            rows.append((f"micro: {label}", errs))
    width = max(len(n) for n, _ in rows)
    print(f"{'Case':{width}}  Result")
    print("-" * (width + 30))
    for name, errs in rows:
        print(f"{name:{width}}  {'PASS' if not errs else f'FAIL ({len(errs)} differences)'}")
        for e in (errs if verbose else errs[:5]):
            print(f"{'':{width}}    {e[:400]}")
    failed = sum(1 for _, e in rows if e)
    print("-" * (width + 30))
    print(f"{len(rows) - failed} of {len(rows)} cases pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main("-v" in sys.argv))
