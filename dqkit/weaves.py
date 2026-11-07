"""Weaves: turn one Commons rules file into the native rule formats of other data quality platforms.

Each weave returns plain text you can paste into (or load with) that platform. Rules with no
native equivalent are listed as comments at the end, so nothing is silently lost.

The browser engine (portal/src/js/engine.js, DQ.weaves) mirrors this file exactly; the parity
check compares both on every fixture and library rules file.

Targets
- sql          ANSI-style SQL rule pack (one query per rule returning failing rows). For tools
               that accept SQL-defined rules: Collibra DQ, Informatica CDQ, Ataccama ONE, Qlik
               Talend, IBM, Precisely, SAS, Experian, Anomalo, DQLabs and others.
- snowflake    Snowflake data metric functions (system DMFs where they exist, custom DMFs otherwise).
- databricks   Lakeflow Declarative Pipelines (DLT) expectations, SQL CONSTRAINT form.
- glue         AWS Glue Data Quality DQDL ruleset.
- dataplex     Google Knowledge Catalog (Dataplex) data quality scan rules (YAML).
- dbt          dbt schema.yml data tests (dbt core, dbt_utils, dbt_expectations).
- soda         SodaCL checks (Soda Core 3.x syntax).
- deequ        PyDeequ Check (Apache Spark, AWS Deequ).
- openmetadata OpenMetadata test case definitions (YAML).
- datahub      DataHub assertions (Open Data Quality Assertions spec, YAML).
- montecarlo   Monte Carlo monitors-as-code custom SQL monitors (YAML).
"""
from __future__ import annotations

import json
import re

from .rules import DEFAULT_ISSUE, ISSUE_TYPES, iso_duration_days
from . import framework

TARGETS = ["sql", "snowflake", "databricks", "glue", "dataplex", "dbt", "soda", "deequ", "openmetadata", "datahub", "montecarlo"]
UNKNOWN_DEFAULT = ["unknown", "not stated", "not known", "prefer not to say", "z", "x", "u", ""]


# ---------- shared helpers (mirrored in engine.js) ----------

def _num(x) -> str:
    return str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)


def _js(s) -> str:
    return json.dumps(str(s))


def _jlist(vals) -> str:
    return "[" + ", ".join(_js(v) for v in vals) + "]"


def _mostly(r: dict, spec: dict) -> float:
    imp = int(spec["asset"].get("importance", 3))
    policy = spec["asset"].get("target_policy", framework.DEFAULT_POLICY)
    impact = int(r.get("impact", ISSUE_TYPES[r.get("issue_type", DEFAULT_ISSUE[r["check"]])]["default_impact"]))
    target = r.get("target") or framework.default_target(framework.combined_score(imp, impact), policy)
    return round(float(target) / 100.0, 4)


def _pct_fail(m: float) -> str:
    return _num(round((1 - m) * 100, 2))


def _dim(r: dict) -> str:
    return r.get("dimension", ISSUE_TYPES[r.get("issue_type", DEFAULT_ISSUE[r["check"]])]["dimension"])


def _slug(s) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_") or "rule"


def _isnum(v) -> bool:
    return str(v).replace(".", "", 1).isdigit()


class _D:
    """A SQL dialect: identifier quoting, string type, regex test and today's date."""

    def __init__(self, q="\"", st="VARCHAR", rx="REGEXP_LIKE({c}, {p})", today="CURRENT_DATE"):
        self.q, self.st, self.rx, self.today = q, st, rx, today

    def id(self, c) -> str:
        return self.q + str(c).replace(self.q, self.q + self.q) + self.q

    def lit(self, s) -> str:
        return "'" + str(s).replace("'", "''") + "'"


ANSI = _D()
SNOW = _D(rx="REGEXP_LIKE({c}, {p})")
SPARK = _D(q="`", st="STRING", rx="{c} RLIKE {p}")
BQ = _D(q="`", st="STRING", rx="REGEXP_CONTAINS({c}, {p})", today="CURRENT_DATE()")

OPSQL = {"<": "<", "<=": "<=", ">": ">", ">=": ">=", "==": "=", "!=": "<>"}
TYPE_RX = {"integer": r"^[-+]?[0-9]+$", "year": r"^[0-9]{4}$", "number": r"^[-+]?[0-9]*\.?[0-9]+$"}


def passes(r: dict, d: _D):
    """A SQL expression that is true for a passing row, or None when the rule is not row-level.
    Nulls are left to the not-null rule (as in most tools): a null makes the expression unknown, not false."""
    c = r["check"]
    if c == "not_null":
        return f"{d.id(r['column'])} IS NOT NULL"
    if c == "regex":
        return d.rx.format(c=d.id(r["column"]), p=d.lit("^(" + r["pattern"] + ")$"))
    if c == "in_set":
        return f"{d.id(r['column'])} IN (" + ", ".join(d.lit(v) for v in r["values"]) + ")"
    if c == "range" and ("min" in r or "max" in r):
        parts = []
        if "min" in r:
            parts.append(f"{d.id(r['column'])} >= {_num(r['min'])}")
        if "max" in r:
            parts.append(f"{d.id(r['column'])} <= {_num(r['max'])}")
        return " AND ".join(parts)
    if c == "type" and r["kind"] in TYPE_RX:
        return d.rx.format(c=f"CAST({d.id(r['column'])} AS {d.st})", p=d.lit(TYPE_RX[r["kind"]]))
    if c == "compare" and r["op"] in OPSQL:
        right = _num(float(r["right"])) if _isnum(r["right"]) else d.id(r["right"])
        return f"{d.id(r['left'])} {OPSQL[r['op']]} {right}"
    if c == "not_future":
        return f"CAST({d.id(r['column'])} AS DATE) <= {d.today}"
    if c == "not_unknown":
        vals = r.get("values", UNKNOWN_DEFAULT)
        return f"LOWER(TRIM({d.id(r['column'])})) NOT IN (" + ", ".join(d.lit(str(v).strip().lower()) for v in vals) + ")"
    return None


def _cols(r: dict) -> list:
    c = r["check"]
    if c == "compare":
        return [r["left"]] + ([] if _isnum(r["right"]) else [r["right"]])
    if "columns" in r:
        return list(r["columns"])
    return [r["column"]] if "column" in r else []


def _fresh_days(r: dict) -> int:
    return int(iso_duration_days(r["expected"]) + iso_duration_days(r.get("lag", "P0D")) + 0.5)


def _note(r: dict, why: str) -> str:
    return f"{r['id']} ({r['check']}): {why}"


def _finish(head: list, body: list, notes: list, cm: str) -> str:
    out = head + body
    if notes:
        out.append(cm + " Not exported (run these with dqkit or add them by hand):")
        out += [f"{cm}   {n}" for n in notes]
    return "\n".join(out) + "\n"


def _head(spec: dict, what: str, cm: str) -> list:
    return [f"{cm} {what} for {spec['asset']['id']} (generated by dqkit weaves; check against the platform's current docs before use)"]


# ---------- targets ----------

def w_sql(spec: dict) -> str:
    t, body, notes = ANSI.id(spec["asset"]["id"]), [], []
    for r in spec["rules"]:
        c, p = r["check"], passes(r, ANSI)
        body.append(f"-- {r['id']} ({c}, {_dim(r)}): {r.get('description', '')}".rstrip())
        if p:
            body.append(f"-- target: at least {_num(round(_mostly(r, spec) * 100, 2))}% of rows pass")
            body.append(f"SELECT {ANSI.lit(r['id'])} AS rule_id, COUNT(*) AS failing_rows FROM {t} WHERE NOT ({p});")
        elif c == "unique":
            ks = ", ".join(ANSI.id(x) for x in r["columns"])
            body.append(f"SELECT {ANSI.lit(r['id'])} AS rule_id, COUNT(*) AS failing_rows FROM (SELECT {ks} FROM {t} GROUP BY {ks} HAVING COUNT(*) > 1) d;")
        elif c == "sum_max":
            mx = _num(r["max"] + r.get("tolerance", 0))
            body.append(f"SELECT {ANSI.lit(r['id'])} AS rule_id, CASE WHEN SUM({ANSI.id(r['column'])}) <= {mx} THEN 0 ELSE 1 END AS failing_rows FROM {t};")
        else:
            body.pop()
            notes.append(_note(r, "no portable SQL form"))
    return _finish(_head(spec, "SQL rule pack", "--") + ["-- Each query returns the number of failing rows; 0 means the rule passes."], body, notes, "--")


_SNOW_T = {"regex": "VARCHAR", "in_set": "VARCHAR", "not_unknown": "VARCHAR", "type": "VARCHAR", "not_future": "DATE"}


def w_snowflake(spec: dict) -> str:
    t, body, notes = SNOW.id(spec["asset"]["id"]), [], []
    body.append(f"ALTER TABLE {t} SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';")
    for r in spec["rules"]:
        c = r["check"]
        if c == "not_null":
            body.append(f"-- {r['id']}: nulls must stay at or below {_pct_fail(_mostly(r, spec))}% of rows")
            body.append(f"ALTER TABLE {t} ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON ({SNOW.id(r['column'])});")
            continue
        if c == "unique" and len(r["columns"]) == 1:
            body.append(f"-- {r['id']}: duplicates")
            body.append(f"ALTER TABLE {t} ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT ON ({SNOW.id(r['columns'][0])});")
            continue
        if c == "freshness":
            body.append(f"-- {r['id']}: latest value must be no more than {_fresh_days(r)} days old")
            body.append(f"ALTER TABLE {t} ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.FRESHNESS ON ({SNOW.id(r['column'])});")
            continue
        p, cols, fn = passes(r, SNOW), _cols(r), "dq_" + _slug(r["id"])
        if p:
            q = f"SELECT COUNT_IF(NOT ({p})) FROM arg_t"
        elif c == "sum_max":
            q = f"SELECT IFF(SUM({SNOW.id(r['column'])}) <= {_num(r['max'] + r.get('tolerance', 0))}, 0, 1) FROM arg_t"
        elif c == "unique":
            ks = ", ".join(SNOW.id(x) for x in cols)
            q = f"SELECT COUNT(*) FROM (SELECT {ks} FROM arg_t GROUP BY {ks} HAVING COUNT(*) > 1)"
        else:
            notes.append(_note(r, "no data metric function form"))
            continue
        ty = _SNOW_T.get(c, "NUMBER")
        sig = ", ".join(f"{SNOW.id(x)} {ty}" for x in cols)
        body.append(f"-- {r['id']} ({c}): {r.get('description', '')}".rstrip())
        body.append(f"CREATE OR REPLACE DATA METRIC FUNCTION {fn}(arg_t TABLE({sig})) RETURNS NUMBER AS $${q}$$;")
        body.append(f"ALTER TABLE {t} ADD DATA METRIC FUNCTION {fn} ON (" + ", ".join(SNOW.id(x) for x in cols) + ");")
    return _finish(_head(spec, "Snowflake data metric functions", "--"), body, notes, "--")


def w_databricks(spec: dict) -> str:
    body, notes = [], []
    for r in spec["rules"]:
        p = passes(r, SPARK)
        if not p:
            notes.append(_note(r, "not row-level; use a separate aggregate check or Databricks DQX"))
            continue
        body.append(f"  CONSTRAINT {_slug(r['id'])} EXPECT ({p}),  -- {r['check']}, target {_num(round(_mostly(r, spec) * 100, 2))}%")
    if body:
        body[-1] = body[-1].replace("),  --", ")  --", 1)
    head = _head(spec, "Lakeflow Declarative Pipelines (DLT) expectations", "--") + [
        "-- Paste inside CREATE OR REFRESH STREAMING TABLE ... ( ... ). Add ON VIOLATION DROP ROW or FAIL UPDATE to enforce."]
    return _finish(head, body, notes, "--")


_GLUE_TYPE = {"integer": "INTEGER", "year": "INTEGER", "number": "DOUBLE", "date": "DATE"}


def w_glue(spec: dict) -> str:
    body, notes, done = [], [], []
    for r in spec["rules"]:
        n0 = len(body)
        c, m = r["check"], _num(_mostly(r, spec))
        col = _js(r.get("column", ""))
        if c == "not_null":
            body.append(f"Completeness {col} >= {m}")
        elif c == "unique":
            if len(r["columns"]) == 1:
                body.append(f"Uniqueness {_js(r['columns'][0])} >= {m}")
            else:
                body.append("IsPrimaryKey " + " ".join(_js(x) for x in r["columns"]))
        elif c == "regex":
            body.append(f"ColumnValues {col} matches {_js('^(' + r['pattern'] + ')$')} with threshold >= {m}")
        elif c == "in_set":
            body.append(f"ColumnValues {col} in {_jlist(r['values'])} with threshold >= {m}")
        elif c == "not_unknown":
            body.append(f"ColumnValues {col} not in {_jlist(r.get('values', UNKNOWN_DEFAULT))} with threshold >= {m}")
        elif c == "range" and ("min" in r or "max" in r):
            if "min" in r:
                body.append(f"ColumnValues {col} >= {_num(r['min'])} with threshold >= {m}")
            if "max" in r:
                body.append(f"ColumnValues {col} <= {_num(r['max'])} with threshold >= {m}")
        elif c == "required_columns":
            body += [f"ColumnExists {_js(x)}" for x in r["columns"]]
        elif c == "type" and r["kind"] in _GLUE_TYPE:
            body.append(f"ColumnDataType {col} = {_js(_GLUE_TYPE[r['kind']])} with threshold >= {m}")
        elif c == "sum_max":
            body.append(f"Sum {col} <= {_num(r['max'] + r.get('tolerance', 0))}")
        elif c == "freshness":
            body.append(f"DataFreshness {col} <= {_fresh_days(r)} days")
        elif c in ("compare", "not_future") and passes(r, SPARK):
            body.append(f"CustomSql {_js('select count(*) from primary where not (' + passes(r, SPARK) + ')')} = 0")
        else:
            notes.append(_note(r, "no DQDL rule type"))
        if len(body) > n0:
            done.append(str(r["id"]))
    lines = (["# Exported rules, in order: " + ", ".join(done)] if done else []) + ["Rules = ["] + [f"    {b}," for b in body]
    if body:
        lines[-1] = lines[-1][:-1]
    lines.append("]")
    return _finish(_head(spec, "AWS Glue Data Quality DQDL ruleset", "#"), lines, notes, "#")


_DPX_DIM = {"completeness": "COMPLETENESS", "uniqueness": "UNIQUENESS", "validity": "VALIDITY", "accuracy": "ACCURACY",
            "consistency": "CONSISTENCY", "timeliness": "FRESHNESS"}


def w_dataplex(spec: dict) -> str:
    body, notes = ["rules:"], []
    for r in spec["rules"]:
        c, m = r["check"], _num(_mostly(r, spec))
        name = re.sub(r"[^a-z0-9-]+", "-", str(r["id"]).lower()).strip("-") or "rule"
        dim = _DPX_DIM.get(_dim(r), "VALIDITY")
        exp = None
        if c == "not_null":
            exp = ["  nonNullExpectation: {}"]
        elif c == "unique" and len(r["columns"]) == 1:
            exp = ["  uniquenessExpectation: {}"]
        elif c == "unique":
            ks = ", ".join(BQ.id(x) for x in r["columns"])
            exp = ["  sqlAssertion:", "    sqlStatement: " + _js(f"SELECT {ks} FROM ${{data()}} GROUP BY {ks} HAVING COUNT(*) > 1")]
        elif c == "regex":
            exp = ["  regexExpectation:", "    regex: " + _js("^(" + r["pattern"] + ")$")]
        elif c == "in_set":
            exp = ["  setExpectation:", "    values: " + _jlist(r["values"])]
        elif c == "range" and ("min" in r or "max" in r):
            exp = ["  rangeExpectation:"] + (["    minValue: " + _js(_num(r["min"]))] if "min" in r else []) + (
                ["    maxValue: " + _js(_num(r["max"]))] if "max" in r else [])
        elif c == "sum_max":
            exp = ["  tableConditionExpectation:", "    sqlExpression: " + _js(f"SUM({BQ.id(r['column'])}) <= {_num(r['max'] + r.get('tolerance', 0))}")]
        elif c in ("compare", "not_future", "not_unknown", "type") and passes(r, BQ):
            exp = ["  rowConditionExpectation:", "    sqlExpression: " + _js(passes(r, BQ))]
        if exp is None:
            notes.append(_note(r, "no Dataplex rule type"))
            continue
        col = r.get("column") or (r["columns"][0] if c == "unique" and len(r["columns"]) == 1 else (r["left"] if c == "compare" else None))
        body.append(f"- name: {_js(name)}")
        if col and c not in ("sum_max",) and not (c == "unique" and len(r["columns"]) > 1):
            body.append(f"  column: {_js(col)}")
        body.append(f"  dimension: {dim}")
        if c not in ("sum_max", "unique") or (c == "unique" and len(r["columns"]) == 1):
            if "sqlAssertion" not in exp[0]:
                body.append(f"  threshold: {m}")
        if r.get("description"):
            body.append(f"  description: {_js(r['description'])}")
        body += exp
    return _finish(_head(spec, "Knowledge Catalog (Dataplex) data quality rules", "#"), body, notes, "#")


def w_dbt(spec: dict) -> str:
    table, cols, notes, order, done = [], {}, [], [], []

    def col(name):
        if name not in cols:
            cols[name] = []
            order.append(name)
        return cols[name]

    for r in spec["rules"]:
        c = r["check"]
        n0 = len(notes)
        if c == "not_null":
            col(r["column"]).append(["not_null"])
        elif c == "unique" and len(r["columns"]) == 1:
            col(r["columns"][0]).append(["unique"])
        elif c == "unique":
            table.append(["dbt_utils.unique_combination_of_columns:", "    combination_of_columns: " + _jlist(r["columns"])])
        elif c == "in_set":
            col(r["column"]).append(["accepted_values:", "    values: " + _jlist(r["values"])])
        elif c == "not_unknown":
            col(r["column"]).append(["dbt_utils.not_accepted_values:", "    values: " + _jlist(r.get("values", UNKNOWN_DEFAULT))])
        elif c == "range" and ("min" in r or "max" in r):
            col(r["column"]).append(["dbt_utils.accepted_range:"] + (["    min_value: " + _num(r["min"])] if "min" in r else []) + (
                ["    max_value: " + _num(r["max"])] if "max" in r else []))
        elif c == "regex":
            col(r["column"]).append(["dbt_expectations.expect_column_values_to_match_regex:", "    regex: " + _js("^(" + r["pattern"] + ")$")])
        elif c == "required_columns":
            for x in r["columns"]:
                col(x).append(["dbt_expectations.expect_column_to_exist"])
        elif c == "sum_max":
            col(r["column"]).append(["dbt_expectations.expect_column_sum_to_be_between:", "    max_value: " + _num(r["max"] + r.get("tolerance", 0))])
        elif c in ("compare", "not_future") and passes(r, ANSI):
            table.append(["dbt_utils.expression_is_true:", "    expression: " + _js(passes(r, ANSI))])
        elif c == "freshness":
            table.append(["dbt_utils.recency:", "    datepart: day", "    field: " + _js(r["column"]), f"    interval: {_fresh_days(r)}"])
        elif c == "no_gaps":
            col(r["column"]).append(["dbt_utils.sequential_values:", f"    interval: {_num(r.get('step', 1))}"])
        else:
            notes.append(_note(r, "no dbt test"))
        if len(notes) == n0:
            done.append(str(r["id"]))
    body = (["# Exported rules: " + ", ".join(done)] if done else []) + ["version: 2", "models:", f"  - name: {_js(spec['asset']['id'])}"]

    def emit(tests, ind):
        for tst in tests:
            body.append(f"{ind}- {tst[0]}")
            body.extend(ind + "  " + line[2:] for line in tst[1:])

    if table:
        body.append("    data_tests:")
        emit(table, "      ")
    if order:
        body.append("    columns:")
        for name in order:
            body.append(f"      - name: {_js(name)}")
            body.append("        data_tests:")
            emit(cols[name], "          ")
    head = _head(spec, "dbt schema.yml data tests", "#") + ["# Needs the dbt_utils and dbt_expectations packages. dbt tests fail on any failing row: add warn_if / error_if to allow a tolerance."]
    return _finish(head, body, notes, "#")


def _soda_col(c) -> str:
    return c if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(c)) else _js(c)


def w_soda(spec: dict) -> str:
    body, notes = [f"checks for {_soda_col(spec['asset']['id'])}:"], []
    for r in spec["rules"]:
        c, pf = r["check"], _pct_fail(_mostly(r, spec))
        name = f"      name: {_js(r['id'] + ' ' + r.get('description', c))}"
        if c == "not_null":
            body += [f"  - missing_percent({_soda_col(r['column'])}) <= {pf}:", name]
        elif c == "unique":
            if len(r["columns"]) == 1:
                body += [f"  - duplicate_percent({_soda_col(r['columns'][0])}) <= {pf}:", name]
            else:
                body += ["  - duplicate_count(" + ", ".join(_soda_col(x) for x in r["columns"]) + ") = 0:", name]
        elif c == "regex":
            body += [f"  - invalid_percent({_soda_col(r['column'])}) <= {pf}:", name, "      valid regex: " + _js("^(" + r["pattern"] + ")$")]
        elif c == "in_set":
            body += [f"  - invalid_percent({_soda_col(r['column'])}) <= {pf}:", name, "      valid values: " + _jlist(r["values"])]
        elif c == "not_unknown":
            body += [f"  - invalid_percent({_soda_col(r['column'])}) <= {pf}:", name, "      invalid values: " + _jlist(r.get("values", UNKNOWN_DEFAULT))]
        elif c == "range" and ("min" in r or "max" in r):
            body += [f"  - invalid_percent({_soda_col(r['column'])}) <= {pf}:", name] + (
                ["      valid min: " + _num(r["min"])] if "min" in r else []) + (["      valid max: " + _num(r["max"])] if "max" in r else [])
        elif c == "required_columns":
            body += ["  - schema:", name, "      fail:", "        when required column missing: " + _jlist(r["columns"])]
        elif c == "sum_max":
            body += [f"  - sum({_soda_col(r['column'])}) <= {_num(r['max'] + r.get('tolerance', 0))}:", name]
        elif c == "freshness":
            body += [f"  - freshness({_soda_col(r['column'])}) < {_fresh_days(r) + 1}d:", name]
        elif c in ("compare", "not_future", "type") and passes(r, ANSI):
            body += ["  - failed rows:", name, "      fail condition: " + _js("NOT (" + passes(r, ANSI) + ")")]
        else:
            notes.append(_note(r, "no SodaCL check"))
    return _finish(_head(spec, "SodaCL checks", "#"), body, notes, "#")


def w_deequ(spec: dict) -> str:
    body, notes = [], []
    for r in spec["rules"]:
        c, m, h = r["check"], _num(_mostly(r, spec)), _js(r["id"])
        if c == "not_null":
            body.append(f"    .hasCompleteness({_js(r['column'])}, lambda x: x >= {m}, hint={h})")
        elif c == "unique":
            body.append(f"    .hasUniqueness({_jlist(r['columns'])}, lambda x: x >= {m}, hint={h})")
        elif c == "regex":
            body.append(f"    .hasPattern({_js(r['column'])}, {_js('^(' + r['pattern'] + ')$')}, lambda x: x >= {m}, hint={h})")
        elif c == "in_set":
            body.append(f"    .isContainedIn({_js(r['column'])}, {_jlist(r['values'])}, lambda x: x >= {m}, hint={h})")
        elif c == "sum_max":
            body.append(f"    .hasSum({_js(r['column'])}, lambda x: x <= {_num(r['max'] + r.get('tolerance', 0))}, hint={h})")
        elif passes(r, SPARK) and c != "not_null":
            body.append(f"    .satisfies({_js(passes(r, SPARK))}, {h}, lambda x: x >= {m}, hint={h})")
        else:
            notes.append(_note(r, "no Deequ constraint"))
    lines = ["from pydeequ.checks import Check, CheckLevel", "",
             f"check = (Check(spark, CheckLevel.Error, {_js(spec['asset']['id'])})"] + body + [")"]
    return _finish(_head(spec, "PyDeequ checks", "#"), lines, notes, "#")


def w_openmetadata(spec: dict) -> str:
    body, notes = ["testCases:"], []
    t = ANSI.id(spec["asset"]["id"])

    def case(r, defn, column=None, params=(), suffix=""):
        body.append(f"  - name: {_js(_slug(r['id']) + suffix)}")
        body.append(f"    testDefinitionName: {defn}")
        if column is not None:
            body.append(f"    columnName: {_js(column)}")
        if r.get("description"):
            body.append(f"    description: {_js(r['description'])}")
        if params:
            body.append("    parameterValues:")
            for k, v in params:
                body.append(f"      - name: {k}")
                body.append(f"        value: {_js(v)}")
        else:
            body.append("    parameterValues: []")

    for r in spec["rules"]:
        c = r["check"]
        if c == "not_null":
            case(r, "columnValuesToBeNotNull", r["column"])
        elif c == "unique" and len(r["columns"]) == 1:
            case(r, "columnValuesToBeUnique", r["columns"][0])
        elif c == "unique":
            ks = ", ".join(ANSI.id(x) for x in r["columns"])
            case(r, "tableCustomSQLQuery", None, [("sqlExpression", f"SELECT {ks} FROM {t} GROUP BY {ks} HAVING COUNT(*) > 1")])
        elif c == "regex":
            case(r, "columnValuesToMatchRegex", r["column"], [("regex", "^(" + r["pattern"] + ")$")])
        elif c == "in_set":
            case(r, "columnValuesToBeInSet", r["column"], [("allowedValues", _jlist(r["values"]))])
        elif c == "not_unknown":
            case(r, "columnValuesToBeNotInSet", r["column"], [("forbiddenValues", _jlist(r.get("values", UNKNOWN_DEFAULT)))])
        elif c == "range" and ("min" in r or "max" in r):
            ps = ([("minValue", _num(r["min"]))] if "min" in r else []) + ([("maxValue", _num(r["max"]))] if "max" in r else [])
            case(r, "columnValuesToBeBetween", r["column"], ps)
        elif c == "required_columns":
            for i, x in enumerate(r["columns"]):
                case(r, "tableColumnNameToExist", None, [("columnName", x)], f"_{i + 1}")
        elif c == "sum_max":
            case(r, "columnValuesSumToBeBetween", r["column"], [("maxValueForColSum", _num(r["max"] + r.get("tolerance", 0)))])
        elif passes(r, ANSI):
            case(r, "tableCustomSQLQuery", None, [("sqlExpression", f"SELECT * FROM {t} WHERE NOT ({passes(r, ANSI)})")])
        else:
            notes.append(_note(r, "no OpenMetadata test definition"))
    return _finish(_head(spec, "OpenMetadata test cases", "#"), body, notes, "#")


def w_datahub(spec: dict) -> str:
    urn = f"urn:li:dataset:(urn:li:dataPlatform:PLATFORM,{spec['asset']['id']},PROD)"
    body, notes = ["version: 1", "assertions:"], []
    t = ANSI.id(spec["asset"]["id"])

    def a(r, lines, threshold=True):
        body.append(f"  - entity: {_js(urn)}")
        body.extend("    " + x for x in lines)
        if threshold:
            body.extend(["    failure_threshold:", "      type: percentage", f"      value: {_pct_fail(_mostly(r, spec))}"])
        body.append(f"    description: {_js(r['id'] + ' ' + r.get('description', r['check']))}")

    for r in spec["rules"]:
        c = r["check"]
        if c == "not_null":
            a(r, ["type: field", f"field: {_js(r['column'])}", "condition:", "  type: not_null"])
        elif c == "unique" and len(r["columns"]) == 1:
            a(r, ["type: field", f"field: {_js(r['columns'][0])}", "metric: unique_percentage", "condition:",
                  "  type: greater_than_or_equal_to", f"  value: {_num(round(_mostly(r, spec) * 100, 2))}"], False)
        elif c == "regex":
            a(r, ["type: field", f"field: {_js(r['column'])}", "condition:", "  type: matches_regex", "  value: " + _js("^(" + r["pattern"] + ")$")])
        elif c == "in_set":
            a(r, ["type: field", f"field: {_js(r['column'])}", "condition:", "  type: in", "  value: " + _jlist(r["values"])])
        elif c == "not_unknown":
            a(r, ["type: field", f"field: {_js(r['column'])}", "condition:", "  type: not_in", "  value: " + _jlist(r.get("values", UNKNOWN_DEFAULT))])
        elif c == "range" and "min" in r and "max" in r:
            a(r, ["type: field", f"field: {_js(r['column'])}", "condition:", "  type: between", f"  min: {_num(r['min'])}", f"  max: {_num(r['max'])}"])
        elif c == "required_columns":
            a(r, ["type: schema", "compatibility: SUPERSET", "schema:"] + [f"  - name: {_js(x)}" for x in r["columns"]], False)
        elif c == "freshness":
            a(r, ["type: freshness", f"lookback_interval: {_js(str(_fresh_days(r)) + ' days')}", "schedule:", "  type: interval", "  interval: \"1 day\""], False)
        elif c == "sum_max":
            a(r, ["type: sql", "statement: " + _js(f"SELECT SUM({ANSI.id(r['column'])}) FROM {t}"), "condition:",
                  "  type: less_than_or_equal_to", f"  value: {_num(r['max'] + r.get('tolerance', 0))}"], False)
        elif c == "unique" or passes(r, ANSI):
            if c == "unique":
                ks = ", ".join(ANSI.id(x) for x in r["columns"])
                q = f"SELECT COUNT(*) FROM (SELECT {ks} FROM {t} GROUP BY {ks} HAVING COUNT(*) > 1) d"
            else:
                q = f"SELECT COUNT(*) FROM {t} WHERE NOT ({passes(r, ANSI)})"
            a(r, ["type: sql", "statement: " + _js(q), "condition:", "  type: equal_to", "  value: 0"], False)
        else:
            notes.append(_note(r, "no assertion type"))
    head = _head(spec, "DataHub assertions (Open Data Quality Assertions spec)", "#") + ["# Replace PLATFORM in the URN. Load with: datahub assertions upsert -f this.yaml"]
    return _finish(head, body, notes, "#")


def w_montecarlo(spec: dict) -> str:
    t, body, notes = ANSI.id(spec["asset"]["id"]), ["montecarlo:", "  custom_sql:"], []
    for r in spec["rules"]:
        c, p = r["check"], passes(r, ANSI)
        if p:
            q = f"SELECT COUNT(*) FROM {t} WHERE NOT ({p})"
        elif c == "unique":
            ks = ", ".join(ANSI.id(x) for x in r["columns"])
            q = f"SELECT COUNT(*) FROM (SELECT {ks} FROM {t} GROUP BY {ks} HAVING COUNT(*) > 1) d"
        elif c == "sum_max":
            q = f"SELECT CASE WHEN SUM({ANSI.id(r['column'])}) <= {_num(r['max'] + r.get('tolerance', 0))} THEN 0 ELSE 1 END FROM {t}"
        else:
            notes.append(_note(r, "no custom SQL form"))
            continue
        body += [f"    - name: {_js(spec['asset']['id'] + ' ' + r['id'])}",
                 f"      description: {_js(r.get('description', c))}",
                 f"      sql: {_js(q)}",
                 "      comparisons:", "        - type: threshold", "          operator: GT", "          threshold_value: 0",
                 "      schedule:", "        type: fixed", "        interval_minutes: 1440"]
    return _finish(_head(spec, "Monte Carlo monitors-as-code", "#"), body, notes, "#")


WEAVES = {"sql": w_sql, "snowflake": w_snowflake, "databricks": w_databricks, "glue": w_glue, "dataplex": w_dataplex,
          "dbt": w_dbt, "soda": w_soda, "deequ": w_deequ, "openmetadata": w_openmetadata, "datahub": w_datahub,
          "montecarlo": w_montecarlo}


def weave(spec: dict, target: str) -> str:
    if target not in WEAVES:
        raise ValueError(f"unknown weave target {target!r}; choose from {', '.join(TARGETS)}")
    return WEAVES[target](spec)


# One small rule per check type, used to work out the crosswalk matrix from the weaves themselves.
SAMPLES = {
    "not_null": {"check": "not_null", "column": "a"},
    "required_columns": {"check": "required_columns", "columns": ["a", "b"]},
    "unique": {"check": "unique", "columns": ["a"]},
    "type": {"check": "type", "column": "a", "kind": "integer"},
    "regex": {"check": "regex", "column": "a", "pattern": "[A-Z]{2}"},
    "in_set": {"check": "in_set", "column": "a", "values": ["x", "y"]},
    "range": {"check": "range", "column": "a", "min": 0, "max": 10},
    "not_future": {"check": "not_future", "column": "a"},
    "compare": {"check": "compare", "left": "a", "op": ">=", "right": "b"},
    "sum_max": {"check": "sum_max", "column": "a", "max": 100},
    "freshness": {"check": "freshness", "column": "a", "expected": "P1M"},
    "no_gaps": {"check": "no_gaps", "column": "a"},
    "header_has_unit": {"check": "header_has_unit"},
    "not_unknown": {"check": "not_unknown", "column": "a"},
    "group_disparity": {"check": "group_disparity", "group": "g", "inner": {"check": "not_null", "column": "a"}},
    "identifier": {"check": "identifier", "column": "a", "scheme": "nhs_number"},
    "outlier": {"check": "outlier", "column": "a"},
}


def crosswalk() -> dict:
    """{check: {target: 'native' | 'sql' | 'none'}} worked out by running each weave on a one-rule spec."""
    out = {}
    for chk, rule in SAMPLES.items():
        row = {}
        for tgt in TARGETS:
            spec = {"asset": {"id": "t", "importance": 3}, "rules": [dict(rule, id="R1")]}
            text = weave(spec, tgt)
            if "R1 (" + chk + "): no" in text or "R1 (" + chk + "): not row-level" in text:
                row[tgt] = "none"
            elif tgt in ("sql", "montecarlo") or "CustomSql" in text or "tableCustomSQLQuery" in text or "type: sql" in text \
                    or "rowConditionExpectation" in text or "sqlAssertion" in text or "expression_is_true" in text \
                    or "failed rows" in text or "satisfies(" in text or "COUNT_IF" in text or ("CREATE OR REPLACE DATA METRIC" in text):
                row[tgt] = "sql"
            else:
                row[tgt] = "native"
        out[chk] = row
    return out
