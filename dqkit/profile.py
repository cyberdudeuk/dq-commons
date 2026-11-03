"""Profile a data file and suggest a starter rules file.

`profile(df)` looks at each column: how many values are missing, how many distinct values there
are, and what the values look like (a year, a financial-year label, a date, a whole number, a
number, a short list of codes, a UK geography code). It also finds a probable key: a column, or
pair of columns, that is never empty and never repeats.

`suggest(df, asset)` turns the profile into a rules spec (a dict) using the kit's existing checks.
`to_yaml(spec, prof)` writes it as a commented YAML rules file.

The suggestions are a starting point that should pass on the data they came from ("green, then
tighten"). A data steward must review every rule: confirm its purpose, set real targets and
ranges, and remove anything that does not matter for the asset's use.
"""
from __future__ import annotations

import re
from typing import Optional

import pandas as pd
import yaml

from . import rules

TBC = "[steward to confirm]"
GEOGRAPHY = re.compile(r"^[EKNSW]\d{8}$")
YEAR_LABEL = re.compile(r"^\d{4}\s*[-/]\s*(\d{2}|\d{4})$")
DATE_SHAPE = re.compile(r"^(\d{4}-\d{2}(-\d{2})?|\d{1,2}/\d{1,2}/\d{2,4})$")
INTEGER = re.compile(r"^[-+]?\d+$")
PERIOD_WORDS = {"year", "yr", "period", "date", "time", "month", "quarter", "fy"}
KEY_WORDS = {"id", "code", "key", "ref", "reference", "identifier", "name"}
# Column names that suggest people's characteristics: an inclusion prompt (Equality Act 2010
# protected characteristics, plus common demographic fields).
DEMOGRAPHIC_WORDS = {"sex", "gender", "ethnicity", "ethnic", "age", "disability", "disabled", "religion", "belief"}
SMALL_SET_MAX = 12
SMALL_SET_COVERAGE = 0.8
NOT_NULL_MAX_NULL_RATE = 0.05


def _tokens(name: str) -> set:
    return set(t for t in re.split(r"[^a-z0-9]+", str(name).lower()) if t)


def _num(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _column_kind(name: str, vals: list) -> str:
    """One of: year, year_label, date, integer, number, text."""
    if not vals:
        return "empty"
    toks = _tokens(name)
    period_name = bool(toks & PERIOD_WORDS) or any(t.startswith("year") for t in toks)
    if all(INTEGER.match(v) and len(v) == 4 for v in vals):
        ys = [int(v) for v in vals]
        in_range = all(1800 <= y <= 2100 for y in ys)
        looks_like_series = len(set(ys)) == len(ys) and (max(ys) - min(ys)) <= 3 * len(ys)
        if in_range and (period_name or looks_like_series):
            return "year"
    if all(YEAR_LABEL.match(v) for v in vals):
        return "year_label"
    if all(DATE_SHAPE.match(v) for v in vals) and all(rules._parse_date(v) for v in vals):
        return "date"
    if all(INTEGER.match(v.replace(",", "")) for v in vals):
        return "integer"
    if all(_num(v) is not None for v in vals):
        return "number"
    return "text"


def profile(df: pd.DataFrame) -> dict:
    """Describe each column. Returns {"rows": n, "columns": {name: {...}}, "key": [cols] or None}."""
    n = len(df)
    cols = {}
    for c in df.columns:
        s = df[c]
        present = s.notna() & (s.astype(str).str.strip() != "")
        vals = [str(v).strip() for v in s[present]]
        kind = _column_kind(c, vals)
        distinct = len(set(vals))
        null_rate = round(1 - (len(vals) / n), 4) if n else 0.0
        toks = _tokens(c)
        geo_share = (sum(1 for v in vals if GEOGRAPHY.match(v)) / len(vals)) if vals else 0.0
        small_set = (kind in ("text", "integer") and 0 < distinct <= SMALL_SET_MAX and len(vals) >= 2 * distinct
                     and len(vals) / max(n, 1) >= SMALL_SET_COVERAGE)
        cols[c] = {
            "kind": kind, "null_rate": null_rate, "nulls": n - len(vals), "distinct": distinct,
            "unique": distinct == len(vals) and len(vals) > 0, "complete": len(vals) == n and n > 0,
            "numeric": kind in ("integer", "number"), "period": kind in ("year", "year_label", "date"),
            "geography": geo_share >= 0.8, "geography_share": round(geo_share, 4),
            "small_set": sorted(set(vals)) if small_set else None,
            "demographic": bool(toks & DEMOGRAPHIC_WORDS) or any(t.startswith("ethnic") for t in toks),
            "min": min((_num(v) for v in vals), default=None) if kind in ("integer", "number") else None,
            "max": max((_num(v) for v in vals), default=None) if kind in ("integer", "number") else None,
            "examples": vals[:3],
        }
    return {"rows": n, "columns": cols, "key": _find_key(df, cols)}


def _find_key(df: pd.DataFrame, cols: dict) -> Optional[list]:
    """A column (or pair) that is complete and never repeats, preferring periods, codes and labels over measures."""
    def keyish(c):
        p = cols[c]
        return (p["period"] or p["geography"] or p["kind"] == "text" or bool(_tokens(c) & KEY_WORDS)) and not p["demographic"]
    singles = [c for c, p in cols.items() if p["complete"] and p["unique"] and keyish(c)]
    if singles:
        singles.sort(key=lambda c: (not cols[c]["period"], not cols[c]["geography"], list(cols).index(c)))
        return [singles[0]]
    cands = [c for c, p in cols.items() if p["complete"] and keyish(c)]
    for i, a in enumerate(cands):
        for b in cands[i + 1:]:
            if not df.duplicated(subset=[a, b], keep=False).any():
                return [a, b]
    return None


# Identifier detection: (scheme, share of values that must pass, words in the column name that also count)
ID_HINTS = [("nhs_number", 0.9, ("nhs",)), ("nino", 0.9, ("nino", "national insurance", "ni_number", "ni number")),
            ("uk_postcode", 0.8, ("postcode", "post code")), ("lei", 0.9, ("lei",)), ("uprn", 0.9, ("uprn",)),
            ("company_number", 0.9, ("company number", "company_number", "crn")),
            ("charity_number", 0.9, ("charity",)), ("school_urn", 0.9, ("urn",)), ("ods_code", 0.9, ("ods",))]


def _identifier_scheme(series: pd.Series, name: str) -> Optional[tuple]:
    """(scheme, % passing) if a column looks like a known identifier, else None.

    Strong schemes (check digits or distinctive formats) are detected from values alone. Weak ones
    (plain digit runs) also need a hint in the column name, so a column of counts is never mistaken
    for UPRNs."""
    vals = [v for v in series.dropna().astype(str) if v.strip()]
    if len(vals) < 3:
        return None
    lname = name.lower().replace("-", " ")
    for scheme, need, words in ID_HINTS:
        named = any(w in lname or w.replace(" ", "_") in lname for w in words)
        strong = scheme in ("nhs_number", "nino", "uk_postcode", "lei")
        if not (strong or named):
            continue
        share = sum(rules.identifier_ok(v, scheme) for v in vals) / len(vals)
        if share >= need and (named or share >= 0.98):
            return scheme, round(100 * share)
    return None


def _rule(rules_list, check, why, **fields):
    rid = f"R{len(rules_list) + 1}"
    r = {"id": rid, "check": check, **fields}
    r["description"] = fields.pop("description", None) or why
    r["purpose"] = TBC
    rules_list.append(r)
    return r


def suggest(df: pd.DataFrame, asset: dict, prof: Optional[dict] = None) -> dict:
    """Build a starter rules spec from the data's profile. Returns a dict that rules.load_rules accepts."""
    prof = prof or profile(df)
    cols = prof["columns"]
    out: list = []
    why: dict = {}  # rule id -> what in the profile led to it (written as a YAML comment)

    def add(check, reason, **fields):
        r = _rule(out, check, fields.pop("description"), **fields)
        why[r["id"]] = reason
        return r

    names = list(cols)
    add("required_columns", f"The file has {len(names)} column(s); this catches a column being renamed or dropped.",
        columns=names, description="All expected columns are present")
    for c, p in cols.items():
        if p["kind"] != "empty" and p["null_rate"] <= NOT_NULL_MAX_NULL_RATE:
            add("not_null", f"{p['nulls']} empty value(s) in {prof['rows']} rows ({round(100 * p['null_rate'], 1)}%).",
                column=c, description=f"Every row has a value for {c}")
    if prof["key"]:
        k = prof["key"]
        add("unique", f"{' + '.join(k)} never repeats and is never empty, so it looks like the key.",
            columns=k, description=f"One row per {' and '.join(k)}")
    for c, p in cols.items():
        if p["kind"] == "year":
            add("type", f"Every value is a four-digit year ({p['examples'][0]} ...).", column=c, kind="year",
                description=f"{c} is a four-digit year")
        elif p["kind"] == "year_label":
            add("regex", f"Every value looks like a financial or academic year label ({p['examples'][0]} ...).",
                column=c, pattern=r"\d{4}\s*[-/]\s*(\d{2}|\d{4})", description=f"{c} is written like 2024-25")
        elif p["kind"] == "date":
            add("type", f"Every value is a readable date ({p['examples'][0]} ...).", column=c, kind="date",
                description=f"{c} is a valid date")
        elif p["numeric"]:
            kind = "integer" if p["kind"] == "integer" else "number"
            add("type", f"Every value is a {'whole number' if kind == 'integer' else 'number'} "
                f"(from {p['min']:g} to {p['max']:g}).", column=c, kind=kind, description=f"{c} is a {kind}")
        if p["small_set"] and not p["geography"]:
            add("in_set", f"Only {p['distinct']} distinct value(s) across {prof['rows'] - p['nulls']} rows: looks like a code list.",
                column=c, values=p["small_set"], description=f"{c} uses the expected codes")
        if p["geography"]:
            add("regex", f"{round(100 * p['geography_share'])}% of values look like GSS geography codes (for example E06000001).",
                column=c, pattern=GEOGRAPHY.pattern.strip("^$"), description=f"{c} is a 9-character GSS geography code")
    for c, p in cols.items():
        sch = _identifier_scheme(df[c], c)
        if sch:
            add("identifier", f"{sch[1]}% of values pass the {sch[0]} rules, so this looks like that identifier. "
                "Identifiers that fail can't be linked to the right record.",
                column=c, scheme=sch[0], description=f"{c} is a valid {sch[0].replace('_', ' ')}")
    for c, p in cols.items():
        if p["kind"] in ("year", "year_label"):
            add("no_gaps", "This looks like a time series; a missing period is easy to miss in a chart.",
                column=c, description=f"No missing periods in {c}")
            add("freshness", "expected: P1Y assumes an annual release and lag: P1Y allows a year to publish. "
                "Steward to confirm both from the release calendar, then tighten the lag.",
                column=c, expected="P1Y", lag="P1Y", description=f"The latest period in {c} is recent enough")
        elif p["kind"] == "date":
            add("not_future", "Dates should not be in the future (unless this is a forecast).",
                column=c, description=f"{c} is not in the future")
    measures = [c for c, p in cols.items() if p["numeric"] and not p["period"] and c not in (prof["key"] or [])]
    if measures:
        add("header_has_unit", "Numeric measure columns should say what they count or the unit (%, number, £, rate ...). "
            "This may fail on purpose: it is a common, real issue.",
            columns=measures, description="Each measure's heading states its unit")
    demo = [c for c, p in cols.items() if p["demographic"]]
    for c in demo:
        add("not_unknown", "The column name suggests a personal characteristic. Inclusion prompt: check how often it is "
            "'unknown' or 'not stated', because gaps here hide groups of people.",
            column=c, description=f"{c} is recorded, not unknown or not stated")
    spec = {"asset": {k: v for k, v in {
        "id": asset.get("id"), "title": asset.get("title") or asset.get("id"), "owner": asset.get("owner") or TBC,
        "importance": int(asset.get("importance", 3)), "source": asset.get("source", "internal"),
        "target_policy": asset.get("target_policy", "low")}.items() if v is not None},
        "rules": out}
    spec["_why"] = why
    spec["_demographic"] = demo
    spec["_profile"] = prof
    rules.validate_spec({k: v for k, v in spec.items() if not k.startswith("_")})
    return spec


def clean(spec: dict) -> dict:
    """The spec without the private helper keys (what goes into the YAML file)."""
    return {k: v for k, v in spec.items() if not k.startswith("_")}


class _Dumper(yaml.SafeDumper):
    """Indent list items under their key, which is easier to read."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _dump(obj) -> str:
    return yaml.dump(obj, Dumper=_Dumper, sort_keys=False, allow_unicode=True, default_flow_style=False, width=110)


def to_yaml(spec: dict, source_name: str = "the data file") -> str:
    """A commented YAML rules file. Keys keep their order."""
    prof = spec.get("_profile") or {"rows": "?", "columns": {}}
    why = spec.get("_why", {})
    L = [
        "# DRAFT rules file suggested by `dqkit suggest` from " + source_name + ".",
        f"# Profile: {prof['rows']} rows, {len(prof['columns'])} column(s)"
        + (f"; probable key: {', '.join(prof['key'])}" if prof.get("key") else "; no single key found") + ".",
        "#",
        "# This is a starting point, not a finished plan. Before you use it:",
        "#   1. Replace every '[steward to confirm]' with the real purpose of the rule.",
        "#   2. Check importance (1 Low to 4 Critical) and source (internal or external) under asset.",
        "#   3. Confirm the freshness 'expected' and 'lag' values against the release calendar.",
        "#   4. Delete rules that do not matter for how the data is used; add business rules (range, compare).",
        "#   5. Tighten: these rules were chosen to pass on today's data ('green, then tighten').",
        "",
    ]
    L.append(_dump({"asset": spec["asset"]}).rstrip())
    L.append("rules:")
    for r in spec["rules"]:
        if r["id"] in why:
            L.append(f"  # {r['id']}: {why[r['id']]}")
        item = _dump([r]).rstrip().splitlines()
        L += ["  " + line for line in item]
    demo = spec.get("_demographic") or []
    if demo:
        key_col = (prof.get("key") or [next(iter(prof["columns"]), "a_column")])[0]
        L += ["",
              "  # Inclusion prompt: is data quality the same for every group? Uncomment and edit to check that",
              "  # another rule passes at a similar rate for each group (tolerance in percentage points).",
              f"  # - id: R{len(spec['rules']) + 1}",
              "  #   check: group_disparity",
              f"  #   group: {demo[0]}",
              "  #   tolerance: 5",
              f"  #   inner: {{check: not_null, column: {key_col}}}",
              f"  #   description: Completeness is similar across {demo[0]} groups",
              f"  #   purpose: '{TBC}'"]
    return "\n".join(L) + "\n"
