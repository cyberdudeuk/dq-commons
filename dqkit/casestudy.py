"""Draft a data quality case study from the kit's results, shaped like the GDS case study template.

The GDS Data Management Team collects case studies for its Shared Learning Library. Most of the
"What did you do?" and "What outcome did you achieve?" answers already exist in the kit's rules,
results and history, so this module drafts them. People still write the parts only they know:
the trigger, the lessons, and permissions.

No personal data is filled in. Responder fields are left blank for the organisation to complete.
Sections marked "(added by dqkit)" are not in the GDS template; they are proposals to make case
studies comparable (CDA identifier, before-and-after table, inclusion).
"""
from __future__ import annotations

from pathlib import Path

from . import operations, pathway, trust
from .workbook import load_history

TODO = "[To complete]"
STAGES = ["1. Just getting started", "2. Early implementation", "3. Established approach", "4. Scaling / optimising"]


def _stage(cycles: int) -> str:
    return STAGES[1] if cycles < 3 else STAGES[2]


def draft(spec: dict, result: dict, history_dir=None) -> dict:
    asset = spec["asset"]
    hist = load_history(history_dir, asset["id"])
    ops = operations.assess(result, history_dir)
    tr = trust.classify(result, asset.get("personal_data_columns"))
    rt = pathway.route(asset)
    dates = sorted({d for v in hist.values() for d in v} | {result["as_of"]})
    first = dates[0]
    by_id = {r["id"]: r for r in result["results"]}
    before_after = []
    for rid, r in by_id.items():
        start = hist.get(rid, {}).get(first, r["performance"])
        before_after.append([rid, r["description"], r["assessment"]["target"], round(start, 2), r["performance"],
                             "Improved" if r["performance"] > start else "Worse" if r["performance"] < start else "No change"])
    met_first = sum(1 for rid, r in by_id.items() if hist.get(rid, {}).get(first, r["performance"]) >= r["assessment"]["target"])
    dims = sorted(result["dimensions"])
    cps = sorted({r.get("meta", {}).get("control_point", "") for r in result["results"]} - {""})
    pri = {}
    for i in result["issues"]:
        pri[i["priority"]] = pri.get(i["priority"], 0) + 1
    inclusion = [r["id"] for r in result["results"] if r["check"] in ("not_unknown", "group_disparity")]
    items = sorted({c for r in result["results"] for c in r["columns"]})

    steps = [
        ("1. Identify critical data", f"Focused on {len(items)} critical data items in '{asset.get('title', asset['id'])}'"
         f"{' (personal data items marked)' if asset.get('personal_data_columns') else ''}."),
        ("2. Identify data quality rules", f"Wrote {result['rules_total']} rules in one open rules file, covering {len(dims)} "
         f"dimensions ({', '.join(dims)}). Targets set with the GOV.UK data quality issues framework "
         f"(importance {asset.get('importance', 3)}, '{asset.get('target_policy', 'low')}' target policy)."),
        ("3. Assess current data quality", f"Baseline on {first}: {met_first} of {result['rules_total']} rules met target."),
        ("4. Prioritise improvements and set goals", "Issues scored with the issues framework: "
         + (", ".join(f"{n} {p}" for p, n in pri.items()) if pri else "no open issues") + "."),
        ("5. Identify root cause and take action", f"Controls placed at: {', '.join(cps)}. Route: {rt['route']}. {TODO}: root causes found and actions taken."),
        ("6. Report on data quality", f"Results published as W3C DQV metadata and a DQAP workbook. Suggested trust level: {tr['level']}."),
        ("7. Repeat measure over time", f"{ops['cycles_measured']} measurement cycle(s) recorded; "
         f"{ops['overdue_issues']} overdue issue(s); recurrence rate {ops['recurrence_rate']}%."),
    ]
    return {
        "title": f"Improving the quality of {asset.get('title', asset['id'])}",
        "organisation": asset.get("owner", TODO),
        "stage": f"{_stage(ops['cycles_measured'])} (suggested from {ops['cycles_measured']} measurement cycle(s); please confirm)",
        "period": f"{first} to {result['as_of']}",
        "trigger": TODO + " Choose one: service or operational issue; policy or legislative driver; audit or assurance "
                   "recommendation; delivery risk or incident; user complaints or frontline issue; analytics or AI readiness need; other.",
        "start": " ".join(x for x in [f"{asset.get('title', asset['id'])}.", (asset.get("primary_use") or asset.get("description") or "").strip(),
                           f"Importance of purpose: {asset.get('importance', 3)} of 4.", f"{TODO}: why you chose it."] if x),
        "steps": steps,
        "tools": "dqkit (open source, MIT): rules, issues framework scoring, DQAP workbook, W3C DQV export. "
                 "Same rules exportable to Great Expectations and R validate." + f" {TODO}: other tools.",
        "outcome": f"Rules meeting target went from {met_first} to {result['rules_met']} of {result['rules_total']}. {TODO}: what this meant in practice.",
        "lessons": TODO,
        "assets": ["Example business and data quality rules", "Example data quality metrics",
                   "A prioritisation matrix", "A dashboard / report"],
        "cda_id": asset.get("iri", asset["id"]),
        "before_after": before_after,
        "inclusion": (f"Inclusion rules used: {', '.join(inclusion)}." if inclusion else
                      "No inclusion rules used. Consider not_unknown and group_disparity checks on people's characteristics."),
    }


def to_markdown(d: dict) -> str:
    L = [f"# Data quality case study: {d['title']}", "",
         "_Draft generated by dqkit from measured results. Check every line, complete the [To complete] parts, and choose a permission before sharing._", "",
         "## Permissions", "Can GDS share this case study with other public sector organisations? " + TODO,
         "- Yes (OK to publish as is)", "- Yes, with light redactions", "- Yes, anonymised", "- No (GDS learning only)", "",
         "## Responder information", f"- Department or organisation: {d['organisation']}",
         f"- Function or team: {TODO}", f"- Job title: {TODO}", f"- Name and email: {TODO}", "",
         "## Case study", f"**Title:** {d['title']}", "", f"**Stage of data quality journey:** {d['stage']}", "",
         f"**Time period covered:** {d['period']}", "", f"**What triggered this work?** {d['trigger']}", "",
         f"**Where did you start?** {d['start']}", "", "**What did you do?**", ""]
    L += [f"- **{s}:** {t}" for s, t in d["steps"]]
    L += ["", f"**What tools and technology did you use?** {d['tools']}", "", f"**What outcome did you achieve?** {d['outcome']}", "",
          f"**Key lessons:** {d['lessons']}", "", "**Reusable assets developed:**"] + [f"- {a}" for a in d["assets"]]
    L += ["", "## Added by dqkit (proposed additions to the template)", "",
          f"**Critical data asset identifier:** {d['cda_id']}", "", "**Before and after**", "",
          "| Rule | Requirement | Target (%) | First measured (%) | Latest (%) | Change |", "|---|---|---|---|---|---|"]
    L += [f"| {' | '.join(str(x) for x in row)} |" for row in d["before_after"]]
    L += ["", f"**Inclusion:** {d['inclusion']}", ""]
    return "\n".join(L)


def to_docx(d: dict, out_path) -> Path:
    from docx import Document
    doc = Document()
    table = None
    for line in to_markdown(d).splitlines():
        if line.startswith("|---"):
            continue
        if line.startswith("| "):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if table is None:
                table = doc.add_table(rows=0, cols=len(cells)); table.style = "Table Grid"
            for cell, text in zip(table.add_row().cells, cells):
                cell.text = text
            continue
        table = None
        if line.startswith("# "):
            doc.add_heading(line[2:], 0)
        elif line.startswith("## "):
            doc.add_heading(line[3:], 1)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:].replace("**", ""), style="List Bullet")
        elif line.strip():
            doc.add_paragraph(line.replace("**", "").strip("_"))
    p = Path(out_path); p.parent.mkdir(parents=True, exist_ok=True); doc.save(p)
    return p
