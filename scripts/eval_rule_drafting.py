"""Score AI-drafted rules files against the evaluation set (knowledge/ai-eval/rule_drafting.yaml).

Usage: python scripts/eval_rule_drafting.py DRAFTS_DIR
DRAFTS_DIR holds one YAML rules file per case, named <case id>.yaml (for example E01.yaml), as
produced by the assistant or any other drafting tool.

For each case it reports:
  valid     - the draft loads and passes the kit's own validation
  recall    - share of expected rules found (matching check and the listed fields)
  extra     - rules that use columns not in the data (likely invented)
The overall score is the mean recall over valid drafts; invalid drafts score 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import rules  # noqa: E402


def _matches(rule: dict, want: dict) -> bool:
    for k, v in want.items():
        got = rule.get(k)
        if k == "group" and rule.get("check") == "group_disparity":
            got = rule.get("group")
        if isinstance(v, list):
            if sorted(map(str, got or [])) != sorted(map(str, v)):
                return False
        elif got != v:
            return False
    return True


def score_case(case: dict, draft_text: str | None) -> dict:
    if draft_text is None:
        return {"id": case["id"], "valid": False, "recall": 0.0, "extra": [], "error": "no draft"}
    try:
        spec = yaml.safe_load(draft_text)
        rules.validate_spec(spec)
    except Exception as e:  # noqa: BLE001
        return {"id": case["id"], "valid": False, "recall": 0.0, "extra": [], "error": str(e)}
    found = sum(any(_matches(r, w) for r in spec["rules"]) for w in case["expect"])
    cols = set(case["columns"])
    used = set()
    for r in spec["rules"]:
        for k in ("column", "left", "group"):
            if r.get(k):
                used.add(r[k])
        used.update(r.get("columns") or [])
    return {"id": case["id"], "valid": True, "recall": round(found / len(case["expect"]), 3),
            "extra": sorted(used - cols), "error": ""}


def evaluate(drafts_dir) -> dict:
    cases = yaml.safe_load((ROOT / "knowledge" / "ai-eval" / "rule_drafting.yaml").read_text(encoding="utf-8"))["cases"]
    d = Path(drafts_dir)
    rows = []
    for c in cases:
        p = d / f"{c['id']}.yaml"
        rows.append(score_case(c, p.read_text(encoding="utf-8") if p.exists() else None))
    overall = round(sum(r["recall"] for r in rows) / len(rows), 3) if rows else 0.0
    return {"overall": overall, "cases": rows, "invented_columns": sum(len(r["extra"]) for r in rows)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)
    out = evaluate(sys.argv[1])
    for r in out["cases"]:
        print(f"{r['id']}: {'valid' if r['valid'] else 'INVALID'} recall {r['recall']}"
              + (f" invented columns {r['extra']}" if r["extra"] else "") + (f" ({r['error']})" if r["error"] else ""))
    print(f"Overall score: {out['overall']}; invented columns: {out['invented_columns']}")
