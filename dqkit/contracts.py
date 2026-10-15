"""Data contracts: move rules between the toolkit and the open standards other teams use.

- Frictionless Table Schema (Open Knowledge Foundation): fields, types and constraints.
- Open Data Contract Standard (ODCS) v3, Bitol / Linux Foundation: schema, properties and quality rules.
- W3C CSV on the Web (CSVW) table schema metadata.

Rules travel *out* with their thresholds (from the issues framework target), and come back *in*
as toolkit rules. Checks a standard can't express travel as ODCS `custom` rules (engine: dqkit) or
in a `x-dqkit` extension, so nothing is silently lost. Mirrored in portal/src/js/engine.js
(DQ.contracts) and parity-checked.
"""
from __future__ import annotations

import re

from . import framework
from .rules import DEFAULT_ISSUE, ISSUE_TYPES

ODCS_API = "v3.1.0"
TYPE_TO_TS = {"integer": "integer", "number": "number", "year": "year", "date": "date"}
TS_TO_TYPE = {"integer": "integer", "number": "number", "year": "year", "date": "date"}
TYPE_TO_LOGICAL = {"integer": "integer", "number": "number", "year": "integer", "date": "date"}
TYPE_TO_XSD = {"integer": "integer", "number": "decimal", "year": "gYear", "date": "date"}
DIM_TO_ODCS = {"completeness": "completeness", "uniqueness": "uniqueness", "validity": "conformity",
               "consistency": "consistency", "timeliness": "timeliness", "accuracy": "accuracy"}
ODCS_TO_DIM = {"completeness": "completeness", "cp": "completeness", "uniqueness": "uniqueness", "uq": "uniqueness",
               "conformity": "validity", "cf": "validity", "consistency": "consistency", "cs": "consistency",
               "timeliness": "timeliness", "tm": "timeliness", "accuracy": "accuracy", "ac": "accuracy",
               "coverage": "completeness", "cv": "completeness"}


def _allowed_percent(rule: dict, asset: dict) -> float:
    """The share of rows allowed to fail, from the rule's target (or the issues framework default)."""
    imp = int(asset.get("importance", 3))
    impact = int(rule.get("impact", ISSUE_TYPES[rule.get("issue_type", DEFAULT_ISSUE[rule["check"]])]["default_impact"]))
    target = rule.get("target")
    if target is None:
        target = framework.default_target(framework.combined_score(imp, impact), asset.get("target_policy", framework.DEFAULT_POLICY))
    return round(100.0 - float(target), 4)


def _dimension(rule: dict) -> str:
    return rule.get("dimension") or ISSUE_TYPES[rule.get("issue_type", DEFAULT_ISSUE[rule["check"]])]["dimension"]


def _columns(spec: dict) -> list:
    """Every column a rule names, in first-mention order."""
    out = []
    for r in spec.get("rules", []):
        cols = [r.get("column"), r.get("left"), r.get("group")] + list(r.get("columns") or [])
        for c in cols:
            if isinstance(c, str) and c not in out:
                out.append(c)
    return out


# ---------- Frictionless Table Schema ----------

def to_table_schema(spec: dict) -> dict:
    fields = {c: {"name": c} for c in _columns(spec)}
    extra, pk = [], None
    for r in spec.get("rules", []):
        c, col = r["check"], r.get("column")
        f = fields.get(col)
        if c == "type" and f is not None:
            f["type"] = TYPE_TO_TS[r["kind"]]
        elif c == "not_null" and f is not None:
            f.setdefault("constraints", {})["required"] = True
        elif c == "unique":
            cols = list(r["columns"])
            if len(cols) == 1:
                fields[cols[0]].setdefault("constraints", {})["unique"] = True
            else:
                pk = cols
        elif c == "regex" and f is not None:
            f.setdefault("constraints", {})["pattern"] = r["pattern"]
        elif c == "in_set" and f is not None:
            f.setdefault("constraints", {})["enum"] = list(r["values"])
        elif c == "range" and f is not None:
            if r.get("min") is not None:
                f.setdefault("constraints", {})["minimum"] = r["min"]
            if r.get("max") is not None:
                f.setdefault("constraints", {})["maximum"] = r["max"]
        else:
            extra.append(r)
        if f is not None and r.get("description") and "description" not in f:
            f["description"] = r["description"]
    out = {"fields": list(fields.values()), "missingValues": [""]}
    if pk:
        out["primaryKey"] = pk
    if extra:
        out["x-dqkit"] = {"asset": spec.get("asset", {}), "rules": extra}
    return out


def from_table_schema(ts: dict, asset: dict | None = None) -> dict:
    rules, n = [], 0

    def add(**r):
        nonlocal n
        n += 1
        rules.append({"id": f"R{n}", **r})
    for f in ts.get("fields", []):
        name, k = f["name"], f.get("constraints", {})
        if f.get("type") in TS_TO_TYPE:
            add(check="type", column=name, kind=TS_TO_TYPE[f["type"]])
        if k.get("required"):
            add(check="not_null", column=name)
        if k.get("unique"):
            add(check="unique", columns=[name])
        if "pattern" in k:
            add(check="regex", column=name, pattern=k["pattern"])
        if "enum" in k:
            add(check="in_set", column=name, values=list(k["enum"]))
        if "minimum" in k or "maximum" in k:
            add(check="range", column=name, **({"min": k["minimum"]} if "minimum" in k else {}), **({"max": k["maximum"]} if "maximum" in k else {}))
    pk = ts.get("primaryKey")
    if pk:
        add(check="unique", columns=[pk] if isinstance(pk, str) else list(pk))
    extra = (ts.get("x-dqkit") or {})
    for r in extra.get("rules", []):
        add(**{k: v for k, v in r.items() if k != "id"})
    return {"asset": asset or extra.get("asset") or {"id": "imported", "importance": 3}, "rules": rules}


# ---------- ODCS v3 ----------

def _odcs_rule(r: dict, asset: dict) -> dict:
    c, pct = r["check"], _allowed_percent(r, asset)
    q = {"id": str(r["id"]), "description": r.get("description", c)}
    dim = DIM_TO_ODCS.get(_dimension(r))
    if dim:
        q["dimension"] = dim
    if c == "not_null":
        q.update(type="library", metric="nullValues", mustBeLessOrEqualTo=pct, unit="percent")
    elif c == "unique":
        q.update(type="library", metric="duplicateValues", mustBeLessOrEqualTo=pct, unit="percent")
        if len(r["columns"]) > 1:
            q["arguments"] = {"properties": list(r["columns"])}
    elif c == "in_set":
        q.update(type="library", metric="invalidValues", arguments={"validValues": list(r["values"])}, mustBeLessOrEqualTo=pct, unit="percent")
    elif c == "regex":
        q.update(type="library", metric="invalidValues", arguments={"pattern": r["pattern"]}, mustBeLessOrEqualTo=pct, unit="percent")
    elif c == "not_unknown":
        q.update(type="library", metric="missingValues", mustBeLessOrEqualTo=pct, unit="percent")
        if r.get("values"):
            q["arguments"] = {"missingValues": list(r["values"])}
    else:
        q.update(type="custom", engine="dqkit", implementation={k: v for k, v in r.items() if k not in ("id", "description")},
                 mustBeLessOrEqualTo=pct, unit="percent")
    return q


def to_odcs(spec: dict, version: str = "1.0.0", status: str = "draft") -> dict:
    asset = spec.get("asset", {})
    props = {c: {"name": c} for c in _columns(spec)}
    schema_quality = []
    for r in spec.get("rules", []):
        c, col = r["check"], r.get("column")
        if c == "type" and col in props:
            props[col]["logicalType"] = TYPE_TO_LOGICAL[r["kind"]]
            props[col]["customProperties"] = [{"property": "dqkitTypeRuleId", "value": str(r["id"])}]
            if r["kind"] == "year":
                props[col]["logicalTypeOptions"] = {"format": "yyyy"}
            continue
        if c == "range" and col in props:
            o = props[col].setdefault("logicalTypeOptions", {})
            if r.get("min") is not None:
                o["minimum"] = r["min"]
            if r.get("max") is not None:
                o["maximum"] = r["max"]
        if c == "not_null" and col in props:
            props[col]["required"] = True
        if c == "unique" and len(r["columns"]) == 1:
            props[r["columns"][0]]["unique"] = True
        q = _odcs_rule(r, asset)
        target = col if (col in props and c not in ("compare", "group_disparity")) else (r["columns"][0] if c == "unique" and len(r["columns"]) == 1 else None)
        if target:
            props[target].setdefault("quality", []).append(q)
        else:
            schema_quality.append(q)
    obj = {"name": asset.get("id", "dataset"), "physicalName": asset.get("id", "dataset"), "properties": list(props.values())}
    if schema_quality:
        obj["quality"] = schema_quality
    out = {"apiVersion": ODCS_API, "kind": "DataContract", "id": asset.get("id", "dataset"), "version": version, "status": status,
           "name": asset.get("title", asset.get("id", "dataset")), "schema": [obj],
           "customProperties": [{"property": "dqkitImportance", "value": int(asset.get("importance", 3))},
                                {"property": "dqkitTargetPolicy", "value": asset.get("target_policy", framework.DEFAULT_POLICY)}]}
    if asset.get("owner"):
        out["team"] = {"name": asset["owner"]}
    return out


def from_odcs(contract: dict) -> dict:
    cp = {p.get("property"): p.get("value") for p in contract.get("customProperties") or []}
    asset = {"id": contract.get("id", "imported"), "title": contract.get("name", contract.get("id", "imported")),
             "importance": int(cp.get("dqkitImportance", 3))}
    if cp.get("dqkitTargetPolicy"):
        asset["target_policy"] = cp["dqkitTargetPolicy"]
    if (contract.get("team") or {}).get("name"):
        asset["owner"] = contract["team"]["name"]
    rules, n = [], 0

    def add(r, q=None):
        nonlocal n
        n += 1
        r = {"id": str(q.get("id")) if q and q.get("id") else f"R{n}", **r}
        if q:
            if q.get("description") and q["description"] != r["check"]:
                r["description"] = q["description"]
            if q.get("dimension") in ODCS_TO_DIM and ODCS_TO_DIM[q["dimension"]] != _dimension(r):
                r["dimension"] = ODCS_TO_DIM[q["dimension"]]
            limit = q.get("mustBeLessOrEqualTo", q.get("mustBeLessThan", q.get("mustBe")))
            if limit is not None and q.get("unit") == "percent":
                r["target"] = round(100.0 - float(limit), 4)
        rules.append(r)

    def quality(q, col):
        m, a = q.get("metric"), q.get("arguments") or {}
        if q.get("type") == "custom" and q.get("engine") == "dqkit":
            add(dict(q["implementation"]), q)
        elif m == "nullValues" and col:
            add({"check": "not_null", "column": col}, q)
        elif m == "duplicateValues":
            add({"check": "unique", "columns": list(a.get("properties") or [col])}, q)
        elif m == "invalidValues" and "validValues" in a and col:
            add({"check": "in_set", "column": col, "values": list(a["validValues"])}, q)
        elif m == "invalidValues" and "pattern" in a and col:
            add({"check": "regex", "column": col, "pattern": a["pattern"]}, q)
        elif m == "missingValues" and col:
            add({"check": "not_unknown", "column": col, **({"values": list(a["missingValues"])} if a.get("missingValues") else {})}, q)
        # text, sql and other engines' custom rules can't be run by the toolkit: skipped, listed by unsupported()

    seen_ids = set()
    for obj in contract.get("schema") or []:
        for p in obj.get("properties") or []:
            name = p["name"]
            lt, o = p.get("logicalType"), p.get("logicalTypeOptions") or {}
            pcp = {x.get("property"): x.get("value") for x in p.get("customProperties") or []}
            if lt in ("integer", "number", "date"):
                add({"check": "type", "column": name, "kind": "year" if o.get("format") == "yyyy" else lt},
                    {"id": pcp["dqkitTypeRuleId"]} if pcp.get("dqkitTypeRuleId") else None)
            qs = p.get("quality") or []
            metrics = {q.get("metric") for q in qs}
            if p.get("required") and "nullValues" not in metrics:
                add({"check": "not_null", "column": name})
            if p.get("unique") and "duplicateValues" not in metrics:
                add({"check": "unique", "columns": [name]})
            has_range = any((q.get("implementation") or {}).get("check") == "range" for q in qs)
            if ("minimum" in o or "maximum" in o) and not has_range:
                add({"check": "range", "column": name, **({"min": o["minimum"]} if "minimum" in o else {}), **({"max": o["maximum"]} if "maximum" in o else {})})
            for q in qs:
                quality(q, name)
        for q in obj.get("quality") or []:
            quality(q, None)
    for r in rules:  # keep ids unique when a contract reuses them
        while r["id"] in seen_ids:
            r["id"] += "b"
        seen_ids.add(r["id"])
    return {"asset": asset, "rules": rules}


def unsupported(contract: dict) -> list:
    """ODCS quality rules the toolkit can't run (text, sql, or another engine's custom rules)."""
    out = []
    for obj in contract.get("schema") or []:
        items = [(p["name"], q) for p in obj.get("properties") or [] for q in p.get("quality") or []] + [(None, q) for q in obj.get("quality") or []]
        for col, q in items:
            if q.get("type") in ("text", "sql") or (q.get("type") == "custom" and q.get("engine") != "dqkit"):
                out.append({"column": col, "id": q.get("id"), "type": q.get("type"), "description": q.get("description", "")})
    return out


# ---------- W3C CSVW ----------

def to_csvw(spec: dict, url: str = "data.csv") -> dict:
    ts = to_table_schema(spec)
    cols = []
    for f in ts["fields"]:
        k, col = f.get("constraints", {}), {"name": re.sub(r"[^A-Za-z0-9_]", "_", f["name"]), "titles": f["name"]}
        dt = {"base": TYPE_TO_XSD.get(f.get("type"), "string")}
        if "pattern" in k:
            dt["format"] = k["pattern"]
        if "minimum" in k:
            dt["minimum"] = k["minimum"]
        if "maximum" in k:
            dt["maximum"] = k["maximum"]
        col["datatype"] = dt if len(dt) > 1 else dt["base"]
        if k.get("required"):
            col["required"] = True
        if f.get("description"):
            col["dc:description"] = f["description"]
        cols.append(col)
    schema = {"columns": cols}
    if ts.get("primaryKey"):
        schema["primaryKey"] = [re.sub(r"[^A-Za-z0-9_]", "_", c) for c in ts["primaryKey"]]
    out = {"@context": "http://www.w3.org/ns/csvw", "url": url, "dc:title": spec.get("asset", {}).get("title", ""), "tableSchema": schema}
    return out


FORMATS = {"table-schema": to_table_schema, "odcs": to_odcs, "csvw": to_csvw}
