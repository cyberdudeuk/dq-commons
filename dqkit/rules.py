"""Data quality rules engine.

One rules file (YAML) describes an asset and its rules. The same file is used to:
- run checks here, on a pandas DataFrame;
- export a Great Expectations suite or an R `validate` rule file (see exporters.py);
- fill the GOV.UK DQAP template (see dqap.py) and publish DQV metadata (see dqv.py).

Every rule produces a pass rate (0 to 100%), which is scored with the GOV.UK
data quality issues framework (see framework.py).
"""
from __future__ import annotations

import copy
import csv
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd
import yaml

from . import framework

VOCAB_DIR = Path(__file__).resolve().parent.parent / "vocab"


def load_issue_types() -> dict:
    with open(VOCAB_DIR / "issue-types.csv", newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


ISSUE_TYPES = load_issue_types()

# Which issue type a failing check raises, unless the rule names one itself.
DEFAULT_ISSUE = {
    "not_null": "missing-value",
    "required_columns": "missing-field",
    "unique": "duplicate-reference",
    "type": "invalid-type",
    "regex": "pattern-mismatch",
    "in_set": "invalid-category",
    "range": "out-of-range",
    "not_future": "future-date",
    "compare": "cross-field-inconsistency",
    "sum_max": "totals-mismatch",
    "freshness": "stale-data",
    "no_gaps": "unexplained-gap",
    "header_has_unit": "undocumented-measure",
    "not_unknown": "characteristic-defaulted",
    "group_disparity": "group-disparity",
    "identifier": "invalid-identifier",
}

# Where the control that prevents each failure best belongs, following the controls model in
# cross-government DQ tooling research: at source (capture), in the pipeline, or in reporting
# (publication). A rule can override it with `control_point`.
CONTROL_POINTS = ("source", "pipeline", "reporting")
DEFAULT_CONTROL = {
    "not_null": "source", "required_columns": "pipeline", "unique": "pipeline", "type": "source",
    "regex": "source", "in_set": "source", "range": "source", "not_future": "source", "compare": "source",
    "sum_max": "pipeline", "freshness": "pipeline", "no_gaps": "pipeline", "header_has_unit": "reporting",
    "not_unknown": "source", "group_disparity": "reporting", "identifier": "source",
}

UNIT_TOKENS = ("%", "percent", "per cent", "number", "count", "millions", "million", "billion",
               "thousand", "£", "gbp", "days", "rate", "miles", "index", "share", "mean", "average")


@dataclass
class RuleResult:
    id: str
    check: str
    description: str
    dimension: str
    issue_type: str
    columns: list
    checked: int
    passed: int
    performance: float
    examples: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)
    assessment: Optional[dict] = None
    meta: dict = field(default_factory=dict)   # purpose, requirement, method, notes (DQAP Metrics tab)

    @property
    def failed(self) -> int:
        return self.checked - self.passed

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["failed"] = self.failed
        return d


# ---------- helpers ----------

def _parse_date(value: Any) -> Optional[date]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m", "%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    m = re.match(r"^(\d{4})\s*[-/]\s*(\d{2}|\d{4})$", s)  # 2023-24 or 2023/2024 financial years
    if m:
        return date(int(m.group(1)), 4, 1)
    return None


def _is_type(value: Any, kind: str) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        return False
    s = str(value).strip().replace(",", "")
    if kind == "integer":
        return re.fullmatch(r"[-+]?\d+", s) is not None
    if kind == "number":
        try:
            float(s)
            return True
        except ValueError:
            return False
    if kind == "year":
        return re.fullmatch(r"\d{4}", s) is not None and 1000 <= int(s) <= 2999
    if kind == "date":
        return _parse_date(s) is not None
    raise ValueError(f"unknown type {kind!r}")


def iso_duration_days(period: str) -> float:
    """Approximate an ISO 8601 duration such as P1Y, P3M, P1W, P1D, P6M in days."""
    m = re.fullmatch(r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?", period or "")
    if not m or not any(m.groups()):
        raise ValueError(f"not an ISO 8601 duration: {period!r}")
    y, mo, w, d = (int(x) if x else 0 for x in m.groups())
    return y * 365.25 + mo * 30.44 + w * 7 + d


def _examples(df: pd.DataFrame, mask: pd.Series, cols: list, n: int = 5) -> list:
    bad = df.loc[~mask, cols].head(n)
    return [{"row": int(i) + 2, **{c: (None if pd.isna(v) else str(v)) for c, v in r.items()}}  # +2: header + 1-based
            for i, r in bad.iterrows()]


def _rowwise(df, cols, mask) -> tuple[int, int, list]:
    # Force a boolean mask: on an empty or all-text column, pandas 3 can return an object/string
    # Series whose sum() is "" rather than 0 (found by the JavaScript parity check).
    mask = mask.astype(bool) if len(mask) else pd.Series([], dtype=bool, index=mask.index)
    return len(mask), int(mask.sum()), _examples(df, mask, cols)


# ---------- public sector identifiers ----------
# Format rules, plus check digits where the scheme has one. "Format only" schemes can't prove an
# identifier exists; they catch typing and formatting errors. Sources are in vocab/identifiers.md.

POSTCODE_RE = re.compile(r"(GIR ?0AA|[A-PR-UWYZ]([0-9]{1,2}|[A-HK-Y][0-9]{1,2}|[0-9][A-HJKPS-UW]|[A-HK-Y][0-9][ABEHMNPRV-Y]) ?[0-9][ABD-HJLNP-UW-Z]{2})")
NINO_RE = re.compile(r"(?!BG|GB|KN|NK|NT|TN|ZZ)[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z][0-9]{6}[A-D]")
ID_FORMATS = {
    "uprn": re.compile(r"[0-9]{1,12}"),
    "gss_code": re.compile(r"[EKLMNSW][0-9]{8}"),
    "company_number": re.compile(r"[0-9]{8}|[A-Z]{2}[0-9]{6}"),
    "charity_number": re.compile(r"[0-9]{6,7}|SC[0-9]{6}|NIC[0-9]{6}"),
    "school_urn": re.compile(r"[0-9]{6}"),
    "ods_code": re.compile(r"[A-Z0-9]{3,6}"),
}
IDENTIFIER_SCHEMES = ("nhs_number", "nino", "uk_postcode", "lei") + tuple(ID_FORMATS)


def _nhs_number_ok(s: str) -> bool:
    s = s.replace(" ", "").replace("-", "")
    if re.fullmatch(r"[0-9]{10}", s) is None:
        return False
    total = sum(int(d) * w for d, w in zip(s[:9], range(10, 1, -1)))
    check = 11 - total % 11
    if check == 11:
        check = 0
    return check != 10 and check == int(s[9])


def _lei_ok(s: str) -> bool:
    if re.fullmatch(r"[A-Z0-9]{18}[0-9]{2}", s) is None:
        return False
    digits = "".join(str(int(c, 36)) for c in s)
    return int(digits) % 97 == 1


def identifier_ok(value: Any, scheme: str) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    s = str(value).strip()
    if s == "":
        return False
    if scheme == "nhs_number":
        return _nhs_number_ok(s)
    if scheme == "nino":
        return NINO_RE.fullmatch(s.replace(" ", "")) is not None
    if scheme == "uk_postcode":
        return POSTCODE_RE.fullmatch(s) is not None
    if scheme == "lei":
        return _lei_ok(s)
    if scheme == "uprn":
        return ID_FORMATS["uprn"].fullmatch(s) is not None and int(s) > 0
    if scheme in ID_FORMATS:
        return ID_FORMATS[scheme].fullmatch(s) is not None
    raise ValueError(f"unknown identifier scheme {scheme!r}")


# ---------- checks ----------

def check_not_null(df, r):
    col = r["column"]
    mask = df[col].notna() & (df[col].astype(str).str.strip() != "")
    return _rowwise(df, [col], mask) + ({},)


def check_required_columns(df, r):
    want = r["columns"]
    present = [c for c in want if c in df.columns]
    missing = [c for c in want if c not in df.columns]
    return len(want), len(present), [{"missing_column": c} for c in missing], {}


def check_unique(df, r):
    cols = r["columns"]
    mask = ~df.duplicated(subset=cols, keep=False)
    return _rowwise(df, cols, mask) + ({},)


def check_type(df, r):
    col, kind = r["column"], r["kind"]
    mask = df[col].map(lambda v: _is_type(v, kind))
    return _rowwise(df, [col], mask) + ({"kind": kind},)


def check_regex(df, r):
    col, pat = r["column"], re.compile(r["pattern"])
    # A blank never matches. (pandas 3 keeps blanks as NaN after astype(str), which re cannot read.)
    mask = df[col].map(lambda v: not pd.isna(v) and pat.fullmatch(str(v)) is not None)
    return _rowwise(df, [col], mask) + ({},)


def check_in_set(df, r):
    col, allowed = r["column"], set(map(str, r["values"]))
    mask = df[col].astype(str).isin(allowed)
    return _rowwise(df, [col], mask) + ({},)


def check_identifier(df, r):
    col, scheme = r["column"], r["scheme"]
    if scheme not in IDENTIFIER_SCHEMES:
        raise ValueError(f"unknown identifier scheme {scheme!r}")
    mask = df[col].map(lambda v: identifier_ok(v, scheme))
    return _rowwise(df, [col], mask) + ({"scheme": scheme},)


def check_range(df, r):
    col = r["column"]
    num = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
    mask = num.notna()
    if "min" in r:
        mask &= num >= r["min"]
    if "max" in r:
        mask &= num <= r["max"]
    return _rowwise(df, [col], mask) + ({"min": r.get("min"), "max": r.get("max")},)


def check_not_future(df, r, as_of: date):
    col = r["column"]
    def ok(v):
        d = _parse_date(v)
        return d is not None and d <= as_of
    mask = df[col].map(ok)
    return _rowwise(df, [col], mask) + ({"as_of": as_of.isoformat()},)


OPS: dict[str, Callable] = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b,
                            ">=": lambda a, b: a >= b, "==": lambda a, b: a == b, "!=": lambda a, b: a != b}


def check_compare(df, r):
    left, op, right = r["left"], r["op"], r["right"]
    a = pd.to_numeric(df[left], errors="coerce")
    b = pd.to_numeric(df[right], errors="coerce") if right in df.columns else float(right)
    mask = OPS[op](a, b).fillna(False)
    cols = [left] + ([right] if right in df.columns else [])
    return _rowwise(df, cols, mask) + ({"expression": f"{left} {op} {right}"},)


def check_sum_max(df, r):
    col = r["column"]
    total = pd.to_numeric(df[col], errors="coerce").sum()
    ok = total <= r["max"] + r.get("tolerance", 0)
    return 1, int(ok), ([] if ok else [{"sum": round(float(total), 4), "max": r["max"]}]), {"sum": round(float(total), 4)}


def check_freshness(df, r, as_of: date):
    """Dataset-level: is the latest period recent enough for the stated update frequency?"""
    col = r["column"]
    vals = [str(v).strip() for v in df[col] if v is not None and not (isinstance(v, float) and pd.isna(v)) and str(v).strip()]
    if vals and all(re.fullmatch(r"\d{4}", v) for v in vals):
        latest = date(max(int(v) for v in vals), 12, 31)  # a year label covers the whole year
    else:
        dates = [d for d in (_parse_date(v) for v in vals) if d]
        if not dates:
            return 1, 0, [{"reason": "no readable dates"}], {}
        latest = max(dates)
    allowed = iso_duration_days(r["expected"]) + iso_duration_days(r.get("lag", "P0D"))
    age = (as_of - latest).days
    ok = age <= allowed
    detail = {"latest_period": latest.isoformat(), "age_days": age, "allowed_days": round(allowed),
              "expected": r["expected"], "lag": r.get("lag", "P0D"), "as_of": as_of.isoformat()}
    return 1, int(ok), ([] if ok else [detail]), detail


def check_no_gaps(df, r):
    col = r["column"]
    years = sorted({int(str(v)[:4]) for v in df[col] if _is_type(str(v)[:4], "year")})
    if not years:
        return 1, 0, [{"reason": "no years found"}], {}
    expected = list(range(years[0], years[-1] + 1, r.get("step", 1)))
    missing = [y for y in expected if y not in years]
    return len(expected), len(expected) - len(missing), [{"missing_period": y} for y in missing[:5]], {
        "first": years[0], "last": years[-1]}


def check_header_has_unit(df, r):
    cols = r.get("columns") or [c for c in df.columns if c not in r.get("ignore", [])]
    tokens = tuple(t.lower() for t in r.get("tokens", UNIT_TOKENS))
    flags = {c: any(t in str(c).lower() for t in tokens) for c in cols}
    return len(cols), sum(flags.values()), [{"column": c} for c, ok in flags.items() if not ok], {}


def check_not_unknown(df, r):
    col = r["column"]
    unknown = {str(v).strip().lower() for v in r.get("values", ["unknown", "not stated", "not known", "prefer not to say", "z", "x", "u", ""])}
    mask = df[col].notna() & ~df[col].astype(str).str.strip().str.lower().isin(unknown)
    return _rowwise(df, [col], mask) + ({},)


def check_group_disparity(df, r, as_of: date):
    """Run an inner check per group; pass if the gap between best and worst group is within tolerance."""
    inner = dict(r["inner"])
    rates = {}
    for g, part in df.groupby(r["group"], dropna=False):
        checked, passed, _, _ = CHECKS[inner["check"]](part.reset_index(drop=True), inner, as_of)
        rates[str(g)] = round(100.0 * passed / checked, 3) if checked else 100.0
    gap = (max(rates.values()) - min(rates.values())) if rates else 0.0
    ok = gap <= r.get("tolerance", 5.0)
    return 1, int(ok), ([] if ok else [{"gap_points": round(gap, 3), "by_group": rates}]), {"by_group": rates, "gap_points": round(gap, 3)}


CHECKS = {
    "not_null": lambda df, r, a: check_not_null(df, r),
    "required_columns": lambda df, r, a: check_required_columns(df, r),
    "unique": lambda df, r, a: check_unique(df, r),
    "type": lambda df, r, a: check_type(df, r),
    "regex": lambda df, r, a: check_regex(df, r),
    "in_set": lambda df, r, a: check_in_set(df, r),
    "range": lambda df, r, a: check_range(df, r),
    "not_future": check_not_future,
    "compare": lambda df, r, a: check_compare(df, r),
    "sum_max": lambda df, r, a: check_sum_max(df, r),
    "freshness": check_freshness,
    "no_gaps": lambda df, r, a: check_no_gaps(df, r),
    "header_has_unit": lambda df, r, a: check_header_has_unit(df, r),
    "not_unknown": lambda df, r, a: check_not_unknown(df, r),
    "group_disparity": check_group_disparity,
    "identifier": lambda df, r, a: check_identifier(df, r),
}


# ---------- running a rules file ----------

VALUESET_DIR = VOCAB_DIR / "valuesets"


def load_valueset(name: str) -> list:
    p = VALUESET_DIR / f"{name}.csv"
    if not re.fullmatch(r"[a-z0-9_]+", name or "") or not p.exists():
        raise ValueError(f"unknown value set {name!r}; see vocab/valuesets/")
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def expand_valuesets(spec: dict, valuesets: dict | None = None) -> dict:
    """Turn every `in_valueset` rule into an `in_set` rule with the listed values (in place)."""
    for r in spec.get("rules", []):
        if r.get("check") == "in_valueset":
            rows = (valuesets or {}).get(r.get("valueset")) or load_valueset(r.get("valueset"))
            key = r.get("match", "label")
            if key not in ("label", "code"):
                raise ValueError(f"rule {r.get('id')}: match must be label or code")
            r["check"] = "in_set"
            r["values"] = [row[key] for row in rows]
            r.setdefault("description", f"Value is in the {r['valueset']} list")
    return spec


def load_rules(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    expand_valuesets(spec)
    validate_spec(spec)
    return spec


def _with_valuesets(spec: dict) -> dict:
    if isinstance(spec, dict) and any(isinstance(r, dict) and r.get("check") == "in_valueset" for r in spec.get("rules") or []):
        return expand_valuesets(copy.deepcopy(spec))
    return spec


def validate_spec(spec: dict) -> None:
    if "asset" not in spec or "rules" not in spec:
        raise ValueError("a rules file needs 'asset' and 'rules'")
    spec = _with_valuesets(spec)
    framework._check_level("asset.importance", spec["asset"].get("importance", 3))
    if spec["asset"].get("target_policy", framework.DEFAULT_POLICY) not in framework.TARGET_POLICIES:
        raise ValueError("asset.target_policy must be low, mid or high")
    seen = set()
    for r in spec["rules"]:
        if r.get("check") not in CHECKS:
            raise ValueError(f"rule {r.get('id')}: unknown check {r.get('check')!r}")
        if r["id"] in seen:
            raise ValueError(f"duplicate rule id {r['id']}")
        seen.add(r["id"])
        if r.get("check") == "identifier" and r.get("scheme") not in IDENTIFIER_SCHEMES:
            raise ValueError(f"rule {r['id']}: scheme must be one of {', '.join(IDENTIFIER_SCHEMES)}")
        if r.get("control_point", "source") not in CONTROL_POINTS:
            raise ValueError(f"rule {r['id']}: control_point must be source, pipeline or reporting")
        it = r.get("issue_type", DEFAULT_ISSUE[r["check"]])
        if it not in ISSUE_TYPES:
            raise ValueError(f"rule {r['id']}: unknown issue type {it!r}")


def run(df: pd.DataFrame, spec: dict, as_of: Optional[date] = None) -> dict:
    as_of = as_of or date.today()
    spec = _with_valuesets(spec)
    asset = spec["asset"]
    importance = int(asset.get("importance", 3))
    results = []
    for r in spec["rules"]:
        issue = r.get("issue_type", DEFAULT_ISSUE[r["check"]])
        meta = ISSUE_TYPES[issue]
        dimension = r.get("dimension", meta["dimension"])
        impact = int(r.get("impact", meta["default_impact"]))
        cols = [c for c in (r.get("column"), r.get("left"), r.get("right"), r.get("group")) if c] + list(r.get("columns", []))
        missing_cols = [c for c in cols if c not in df.columns and r["check"] not in ("required_columns", "compare", "header_has_unit")]
        if missing_cols:
            checked, passed, ex, detail = 1, 0, [{"missing_column": c} for c in missing_cols], {}
            issue, dimension = "missing-field", "completeness"
        else:
            checked, passed, ex, detail = CHECKS[r["check"]](df, r, as_of)
        perf = 100.0 * passed / checked if checked else 100.0
        a = framework.assess(importance, impact, perf, r.get("target"), asset.get("target_policy", framework.DEFAULT_POLICY))
        results.append(RuleResult(
            id=r["id"], check=r["check"], description=r.get("description", r["check"]), dimension=dimension,
            issue_type=issue, columns=cols, checked=checked, passed=passed, performance=round(perf, 3),
            examples=ex, detail=detail, assessment=a.to_dict(),
            meta={**{k: r[k] for k in ("purpose", "requirement", "method", "notes", "part_of_data", "personal_data") if k in r},
                  "control_point": r.get("control_point", DEFAULT_CONTROL[r["check"]])}))
    return summarise(asset, results, as_of, len(df))


def summarise(asset: dict, results: list, as_of: date, n_rows: int) -> dict:
    dims: dict = {}
    for r in results:
        d = dims.setdefault(r.dimension, {"rules": 0, "met": 0, "performance": []})
        d["rules"] += 1
        d["met"] += int(r.assessment["meets_target"])
        d["performance"].append(r.performance)
    for d in dims.values():
        d["mean_performance"] = round(sum(d["performance"]) / len(d["performance"]), 3)
        del d["performance"]
    issues = [r for r in results if not r.assessment["meets_target"]]
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    issues.sort(key=lambda r: (order.get(r.assessment["priority"], 9), -r.assessment["priority_score"]))
    return {
        "asset": asset, "as_of": as_of.isoformat(), "rows": n_rows,
        "rules_total": len(results), "rules_met": len(results) - len(issues),
        "dimensions": dims,
        "issues": [{"rule": r.id, "issue_type": r.issue_type, "label": ISSUE_TYPES[r.issue_type]["label"],
                    "dimension": r.dimension, "priority": r.assessment["priority"],
                    "resolution": r.assessment["resolution"], "performance": r.performance,
                    "target": r.assessment["target"]} for r in issues],
        "results": [r.to_dict() for r in results],
    }
