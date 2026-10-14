"""Issue operations: how long issues stay open, which are overdue, which keep coming back.

Built from the measurement history the kit keeps (one CSV per asset). It answers the
"metrics, monitoring and escalation" questions in GDS DQAP adoption material:

- defect volume (failing records now)
- control failure rate (share of rules below target now)
- age of open issues (consecutive measurement cycles below target)
- overdue issues (open longer than the issues framework's resolution timescale) -> escalate
- recurrence (an issue that was fixed and came back)

Resolution timescales come from the GOV.UK data quality issues framework: Critical
"immediately" (treated here as by the next cycle), High 1 cycle, Medium 3, Low 6.
"""
from __future__ import annotations

import csv
from pathlib import Path

# Cycles an issue may stay open before it is overdue.
WINDOW = {"Critical": 1, "High": 1, "Medium": 3, "Low": 6}


def load_runs(history_dir, asset_id: str) -> dict:
    """{rule_id: {date: meets_target(bool)}} from the history CSV (empty if none)."""
    if not history_dir:
        return {}
    p = Path(history_dir) / f"{asset_id}.history.csv"
    if not p.exists():
        return {}
    out: dict = {}
    with open(p, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.setdefault(row["rule_id"], {})[row["date"]] = str(row["meets_target"]).lower() == "true"
    return out


def assess(result: dict, history_dir=None) -> dict:
    """Operational metrics for the current result, using any history."""
    runs = load_runs(history_dir, result["asset"]["id"])
    for r in result["results"]:  # make sure the current run is included exactly once
        runs.setdefault(r["id"], {})[result["as_of"]] = bool(r["assessment"]["meets_target"])
    dates = sorted({d for v in runs.values() for d in v})
    per_rule = {}
    for r in result["results"]:
        series = [runs[r["id"]].get(d) for d in dates if d in runs[r["id"]]]
        age = 0
        for ok in reversed(series):
            if ok:
                break
            age += 1
        # recurrence: a failure that follows a pass, after an earlier failure
        recurrences, seen_fail, prev = 0, False, None
        for ok in series:
            if ok is False and prev is True and seen_fail:
                recurrences += 1
            if ok is False:
                seen_fail = True
            prev = ok
        pr = r["assessment"]["priority"]
        overdue = bool(pr) and age > WINDOW.get(pr, 99)
        per_rule[r["id"]] = {"open": age > 0, "cycles_open": age, "priority": pr, "recurrences": recurrences,
                             "overdue": overdue,
                             "escalate_to": ("Data owner and governance board" if overdue and pr in ("Critical", "High")
                                             else "Data owner" if overdue else "")}
    total = len(result["results"]) or 1
    failing = [r for r in result["results"] if not r["assessment"]["meets_target"]]
    ever_failed = [k for k, v in runs.items() if False in v.values()]
    return {
        "cycles_measured": len(dates),
        "defect_volume": sum(int(r["checked"]) - int(r["passed"]) for r in failing),
        "control_failure_rate": round(100 * len(failing) / total, 1),
        "open_issues": sum(1 for v in per_rule.values() if v["open"]),
        "overdue_issues": sum(1 for v in per_rule.values() if v["overdue"]),
        "mean_cycles_open": round(sum(v["cycles_open"] for v in per_rule.values() if v["open"]) /
                                  max(1, sum(1 for v in per_rule.values() if v["open"])), 1),
        "recurrence_rate": round(100 * sum(1 for k in ever_failed if per_rule.get(k, {}).get("recurrences")) /
                                 max(1, len(ever_failed)), 1),
        "rules": per_rule,
    }
