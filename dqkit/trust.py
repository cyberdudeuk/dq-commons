"""Data trust scale: turn rule results into a plain trust level that tells people how they may use the data.

Based on the four-level data trust scale published by the Independent Office for Police Conduct
(IOPC, "Data Quality Trust Scales", 2023, updated 2024):

  Untrustworthy | Requires improvement | Useable | Trustworthy
  ---- internal use only ----          | ---- can be used externally ----

IOPC deliberately uses no fixed formula and combines measures with expert judgement. This module
gives a *suggested* level with its reasons, for the data owner to confirm or override. Rules:

1. Start from the worst open issue, prioritised with the GOV.UK issues framework:
   Critical -> Untrustworthy, High -> Requires improvement, Medium -> Useable, Low or none -> Trustworthy.
2. Personal data accuracy (IOPC rule): if any accuracy rule on a personal data field is below 90%,
   the asset cannot be Trustworthy. Below 100% always needs an action plan.
3. Coverage: if fewer than 3 of the 6 core dimensions were measured, the level is capped at Useable,
   because there is not enough evidence to call the data trustworthy.
"""
from __future__ import annotations

LEVELS = ["Untrustworthy", "Requires improvement", "Useable", "Trustworthy"]
SHARING = {"Untrustworthy": "Internal use only", "Requires improvement": "Internal use only",
           "Useable": "Can be used externally, with caveats", "Trustworthy": "Can be used externally"}
FROM_PRIORITY = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
CORE = {"completeness", "uniqueness", "consistency", "timeliness", "validity", "accuracy"}

# How the trust levels line up with other published scales (indicative only).
CROSSWALK = {
    "Untrustworthy": {"mhclg_quality_ladder": "none / some", "ndl_rag": "red"},
    "Requires improvement": {"mhclg_quality_ladder": "indicative / verifiable", "ndl_rag": "red"},
    "Useable": {"mhclg_quality_ladder": "authoritative / usable", "ndl_rag": "amber"},
    "Trustworthy": {"mhclg_quality_ladder": "trustworthy", "ndl_rag": "green"},
}


def classify(result: dict, personal_data_columns: list | None = None) -> dict:
    personal = set(personal_data_columns or result.get("asset", {}).get("personal_data_columns", []))
    reasons = []
    level = 3
    for r in result["results"]:
        pr = r["assessment"]["priority"]
        if pr is not None and FROM_PRIORITY[pr] < level:
            level = FROM_PRIORITY[pr]
            reasons.append(f"{pr} priority issue on {r['id']} ({r['description']}): {r['performance']}% against a {r['assessment']['target']}% target")
    action_plan = False
    for r in result["results"]:
        is_personal = r.get("meta", {}).get("personal_data") or any(c in personal for c in r["columns"])
        if is_personal and r["dimension"] == "accuracy":
            if r["performance"] < 100:
                action_plan = True
            if r["performance"] < 90 and level > 2:
                level = 2
                reasons.append(f"Accuracy of personal data on {r['id']} is {r['performance']}%, below 90%, so the data cannot be rated Trustworthy")
    measured = {r["dimension"] for r in result["results"]} & CORE
    if len(measured) < 3 and level > 2:
        level = 2
        reasons.append(f"Only {len(measured)} of the 6 core dimensions were measured ({', '.join(sorted(measured)) or 'none'}), so there isn't enough evidence for Trustworthy")
    if not reasons:
        reasons.append("All rules meet their targets, or only Low priority issues remain")
    name = LEVELS[level]
    return {"level": name, "sharing": SHARING[name], "reasons": reasons,
            "action_plan_required": action_plan or level < 3,
            "dimensions_measured": sorted(measured), "crosswalk": CROSSWALK[name],
            "note": "Suggested level. The data owner confirms or overrides it, with reasons (IOPC approach)."}
