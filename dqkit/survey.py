"""Analyse the Cross-Government Data Quality Solutions Survey (Microsoft Forms export).

The survey asks organisation questions once, then repeats the same 33 questions for up to three
solutions. A Forms export has one row per organisation with the repeated questions side by side,
which is hard to analyse. This module turns it into one row per organisation and solution, then
counts and averages the answers.

Privacy by design: name, role and email (Q2, Q3, Q5) and the Forms "Name" and "Email" columns are
dropped on load and never written out.

Column matching works whether or not the builders prefix repeated questions with S1, S2, S3: it
matches on the question wording, and counts repeats in order.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

# Organisation-level questions (asked once).
ORG_QUESTIONS = {
    "organisation": "Organisation name",
    "team": "Your team",
    "inventory": "Which data quality solution(s) are currently in use",
    "n_assessed": "How many solutions would you like to comment on",
    "multi_tool": "wider observations about the use of multiple data quality tools",
    "contact_ok": "May we contact you",
    "anything_else": "Is there anything else you would like to share",
}
PERSONAL = ("Your name", "Your role", "Your email", "Name", "Email")

# The repeated per-solution block, in order (wording stems from the survey).
SOLUTION_QUESTIONS = {
    "solution": "Which solution are you commenting on",
    "years_in_use": "How long has this solution been in use",
    "drivers": "main drivers for implementing this solution",
    "problem": "What business problem were you trying to solve",
    "maturity_before": "how would you describe your organisation's data management maturity",
    "foundations": "Which foundations were already in place",
    "right_stage": "implemented at the right stage of maturity",
    "prerequisites": "Which prerequisites were most important",
    "features_used": "Which features or capabilities of this solution are actively used",
    "features_how": "How have these features or capabilities been implemented",
    "features_important": "Which features or capabilities are most important",
    "features_most_value": "delivered the most value",
    "features_least_value": "delivered the least value",
    "strengths": "What are the main strengths of this solution",
    "limitations": "What are the main limitations or disadvantages",
    "integration": "How well does this solution integrate",
    "not_recommended_for": "contexts or use cases for which you would not recommend",
    "benefits": "What benefits has this solution enabled",
    "top_benefit": "most significant benefit realised",
    "measurable_outcomes": "share any measurable outcomes",
    "procurement": "Which procurement route was used",
    "licensing": "What licensing model is used",
    "costs_higher": "Have any costs proved higher than expected",
    "value_for_money": "How would you rate value for money",
    "difficulty": "How difficult was implementation",
    "time_to_value": "How long did it take before value was realised",
    "challenges": "What were the biggest implementation challenges",
    "success_factors": "What contributed most to implementation success",
    "recommend": "Would you recommend this solution",
    "recommend_maturity": "At what maturity level would you recommend",
    "benefits_who": "Who would benefit most from this solution",
    "lesson": "most important lesson",
    "another": "Would you like to provide details about another solution",
}
MULTI = {"inventory", "drivers", "foundations", "features_used", "benefits", "costs_higher", "benefits_who"}
RANKED = {"prerequisites", "features_important", "features_most_value", "features_least_value"}
RATINGS = {"integration": "higher is better", "value_for_money": "higher is better",
           "difficulty": "higher is harder (reversed scale)"}
RECOMMEND_ORDER = ["Definitely", "Probably", "Depends", "Probably not", "Definitely not"]


def _norm(h: str) -> str:
    h = str(h).replace("\u2019", "'").replace("\u2018", "'")
    h = re.sub(r"\.\d+$", "", h)                       # pandas duplicate suffix
    h = re.sub(r"^\s*S[1-9]\s*[-:.]?\s*", "", h)       # S1/S2/S3 prefix
    h = re.sub(r"^\s*Q?\d+[.)]\s*", "", h)             # question number
    return h.strip().lower()


def _split(v) -> list:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    return [x.strip() for x in str(v).split(";") if x.strip()]


def load(path) -> pd.DataFrame:
    p = Path(path)
    df = pd.read_excel(p) if p.suffix.lower() in (".xlsx", ".xls") else pd.read_csv(p)
    return df.drop(columns=[c for c in df.columns if any(_norm(c) == x.lower() or _norm(c).startswith(x.lower() + " ")
                                                          for x in PERSONAL)])


def reshape(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (organisations, solutions): one row per organisation, one row per organisation x solution."""
    cols = list(df.columns)
    org_map, sol_map = {}, {}
    for key, stem in ORG_QUESTIONS.items():
        hit = [c for c in cols if stem.lower() in _norm(c)]
        if hit:
            org_map[key] = hit[0]
    for key, stem in SOLUTION_QUESTIONS.items():
        hits = [c for c in cols if stem.lower() in _norm(c)]
        if key == "features_important":
            hits = [c for c in hits if "actively used" not in _norm(c)]
        sol_map[key] = hits  # in order: block 1, 2, 3
    orgs = pd.DataFrame({k: df[c] for k, c in org_map.items()})
    orgs.insert(0, "response_id", range(1, len(df) + 1))
    rows = []
    n_blocks = max((len(v) for v in sol_map.values()), default=0)
    for i, rec in df.iterrows():
        for b in range(n_blocks):
            sol_col = sol_map["solution"][b] if b < len(sol_map["solution"]) else None
            if sol_col is None or pd.isna(rec[sol_col]) or not str(rec[sol_col]).strip():
                continue
            row = {"response_id": i + 1, "organisation": rec[org_map["organisation"]] if "organisation" in org_map else "",
                   "block": b + 1}
            for key, hits in sol_map.items():
                row[key] = rec[hits[b]] if b < len(hits) else None
            rows.append(row)
    return orgs, pd.DataFrame(rows)


def summarise(orgs: pd.DataFrame, sols: pd.DataFrame) -> dict:
    inv = Counter(x for v in orgs.get("inventory", []) for x in _split(v))
    out = {"responses": len(orgs), "solution_assessments": len(sols), "inventory": dict(inv.most_common()),
           "small_numbers_warning": "Counts under 5 can identify an organisation; suppress or group them before publishing."}
    if sols.empty:
        return out
    per = {}
    for name, g in sols.groupby("solution"):
        d = {"assessments": len(g)}
        for k in RATINGS:
            vals = pd.to_numeric(g[k], errors="coerce").dropna()
            d[f"mean_{k}"] = round(vals.mean(), 2) if len(vals) else None
        rec = Counter(g["recommend"].dropna())
        d["recommend"] = {k: rec.get(k, 0) for k in RECOMMEND_ORDER}
        d["would_recommend_pct"] = round(100 * (rec.get("Definitely", 0) + rec.get("Probably", 0)) / max(1, sum(rec.values())), 1)
        d["features_used"] = dict(Counter(x for v in g["features_used"] for x in _split(v)).most_common())
        d["time_to_value"] = dict(Counter(g["time_to_value"].dropna()))
        per[name] = d
    out["by_solution"] = per
    out["features_used_all"] = dict(Counter(x for v in sols["features_used"] for x in _split(v)).most_common())
    out["benefits_all"] = dict(Counter(x for v in sols["benefits"] for x in _split(v)).most_common())
    out["costs_higher_all"] = dict(Counter(x for v in sols["costs_higher"] for x in _split(v)).most_common())
    out["drivers_all"] = dict(Counter(x for v in sols["drivers"] for x in _split(v)).most_common())
    out["dam_policy_driver"] = sum(1 for v in sols["drivers"] if "DAM Policy implementation" in _split(v))
    out["maturity_before"] = dict(Counter(sols["maturity_before"].dropna()))
    out["right_stage"] = dict(Counter(sols["right_stage"].dropna()))
    # top-ranked first choice for each ranking question
    for k in RANKED:
        out[f"{k}_first_choice"] = dict(Counter(_split(v)[0] for v in sols[k] if _split(v)).most_common())
    return out


def write(orgs, sols, summary, out_dir) -> Path:
    import json
    d = Path(out_dir); d.mkdir(parents=True, exist_ok=True)
    sols.to_csv(d / "solutions_long.csv", index=False)
    orgs.drop(columns=[c for c in ("contact_ok",) if c in orgs], errors="ignore").to_csv(d / "organisations.csv", index=False)
    (d / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    L = [f"# DQ tooling survey summary", "", f"- Responses (organisations): {summary['responses']}",
         f"- Solution assessments: {summary['solution_assessments']}",
         f"- Assessments naming DAM policy as a driver: {summary.get('dam_policy_driver', 0)}", "",
         f"> {summary['small_numbers_warning']}", "", "## Solutions in use", "", "| Solution | Organisations |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in summary["inventory"].items()]
    if summary.get("by_solution"):
        L += ["", "## By solution", "", "| Solution | Assessments | Would recommend (%) | Value for money (1-5) | Integration (1-5) | Difficulty (1-5, higher is harder) |",
              "|---|---|---|---|---|---|"]
        L += [f"| {k} | {v['assessments']} | {v['would_recommend_pct']} | {v['mean_value_for_money']} | {v['mean_integration']} | {v['mean_difficulty']} |"
              for k, v in summary["by_solution"].items()]
    (d / "summary.md").write_text("\n".join(L) + "\n")
    return d
