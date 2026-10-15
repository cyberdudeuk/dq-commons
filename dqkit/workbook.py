"""Write a filled-in DQAP workbook (Excel), shaped like the published templates.

Tabs follow the DQAP Implementation Guide v2.0 and the GOV.UK DQAP template (Details, Data
Criticality Matrix, Metrics, Results, Data Issues Log, Causes, Actions, RACI), and the Defra
"Start here" annexes (record, rule template, monitoring template). The steward fills in the
grey columns (causes, actions, owners); everything else comes from the kit's results.

Also keeps a measurement history (one CSV per asset), so the Results tab shows the trend
over time, as the Defra monitoring template does.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from . import operations, pathway, trust
from .rules import ISSUE_TYPES

HEAD = PatternFill("solid", fgColor="0D6B6E")
INPUT = PatternFill("solid", fgColor="EEF1F3")
WRAP = Alignment(wrap_text=True, vertical="top")

# RACI from the DQAP Implementation Guide v2.0 (A(R) = accountable for risk, A(Q) = accountable for quality).
RACI_ROLES = ["Data steward / business SME", "Data custodian / technical SME", "Business analyst", "Data analyst",
              "Information asset owner", "Data owner / process owner", "Data user"]
RACI = [
    ("1. Identify critical data", "Identify primary purpose, critical data items and their purpose", ["R", "", "", "", "A(R)", "A(Q)", "C"]),
    ("1. Identify critical data", "Identify and log suspected data issues", ["R", "C", "", "", "A(R)", "A(Q)", "C"]),
    ("2. Identify data quality rules", "Define rules and acceptable thresholds; document metrics", ["R", "C", "", "", "", "A(Q)", "C"]),
    ("3. Initial assessment", "Run technical rules against critical data items", ["", "R", "", "R", "", "A(Q)", ""]),
    ("3. Initial assessment", "Review results; prioritise with the Data Quality Issues Framework", ["R", "", "", "R", "A(R)/C", "A(Q)/C", ""]),
    ("4. Document findings", "Document findings and update the DQAP", ["R", "", "", "", "", "A(Q)", ""]),
    ("5. Prioritise improvements", "Identify and prioritise areas for improvement", ["R", "", "", "", "A(R)/C", "A(Q)/C", "C"]),
    ("6. Define goals", "Consider factors, return on investment, set improvement goals", ["R", "C", "", "", "A(R)", "A(Q)/R", "C"]),
    ("7. Root cause and action", "Root cause analysis, options, priorities and target dates", ["R", "C", "", "C", "A(R)/C", "A(Q)/C", "C"]),
    ("7. Root cause and action", "Resolve root causes and cleanse data", ["R", "", "C", "", "A(R)/C", "A(Q)/C", "C"]),
    ("8. Report", "Identify stakeholders, plan communications, share target and resolution dates", ["R", "", "", "C", "A(R)/I", "A(Q)/I", "C"]),
    ("9. Repeat measurement", "Set check frequency, run checks, feedback loops, act on results", ["R", "R", "", "R", "A(R)/I", "A(Q)/I", "C"]),
]


# ---------- history ----------

HISTORY_HEADER = ["date", "rule_id", "value", "target", "meets_target"]


def append_history(result: dict, history_dir: str | Path) -> Path:
    """Add this run to the asset's history CSV.

    Re-running the same date replaces that date's rows instead of adding duplicates, so a
    measurement cycle is counted once however many times it is re-run. Rows stay in date order.
    """
    d = Path(history_dir); d.mkdir(parents=True, exist_ok=True)
    p = d / f"{result['asset']['id']}.history.csv"
    kept = []
    if p.exists():
        with open(p, newline="", encoding="utf-8") as f:
            kept = [row for row in csv.DictReader(f) if row.get("date") != result["as_of"]]
    new_rows = [{"date": result["as_of"], "rule_id": r["id"], "value": r["performance"],
                 "target": r["assessment"]["target"], "meets_target": r["assessment"]["meets_target"]}
                for r in result["results"]]
    rows = sorted(kept + new_rows, key=lambda row: row["date"])  # stable: keeps rule order within a date
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_HEADER, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


def load_history(history_dir: str | Path | None, asset_id: str) -> dict:
    if not history_dir:
        return {}
    p = Path(history_dir) / f"{asset_id}.history.csv"
    if not p.exists():
        return {}
    out: dict = {}
    with open(p, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.setdefault(row["rule_id"], {})[row["date"]] = float(row["value"])
    return out


# ---------- workbook ----------

def _sheet(wb, title, headers, rows, widths=None, input_cols=()):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = HEAD; c.alignment = WRAP
    for row in rows:
        ws.append(row)
    for i, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(h, max(12, min(45, len(str(h)) + 6)))
        for cell in ws[get_column_letter(i)][1:]:
            cell.alignment = WRAP
            if h in input_cols:
                cell.fill = INPUT
    ws.freeze_panes = "A2"
    return ws


def build(spec: dict, result: dict, out_path: str | Path, history_dir: str | Path | None = None) -> Path:
    asset = spec["asset"]
    route = pathway.route(asset)
    tr = trust.classify(result, asset.get("personal_data_columns"))
    hist = load_history(history_dir, asset["id"])
    ops = operations.assess(result, history_dir)
    wb = Workbook()
    ws = wb.active; ws.title = "Start here"
    lines = [
        ("Data quality action plan", asset.get("title", asset["id"])),
        ("Generated", f"{date.today().isoformat()} by dqkit, from rules measured on {result['as_of']}"),
        ("How to use this workbook", "Grey cells are for you to complete (causes, actions, owners). Everything else comes from the measured results. Re-run the kit to refresh."),
        ("Route (decision tree)", route["route"]), ("Who fixes what", route["responsibility"]),
        ("Suggested trust level", f"{tr['level']} ({tr['sharing']})"), ("Why", " ".join(tr["reasons"])),
        ("Action plan required", "Yes" if tr["action_plan_required"] else "No"),
        ("Rules meeting target", f"{result['rules_met']} of {result['rules_total']}"),
        ("Open issues", f"{len(result['issues'])} ({ops['overdue_issues']} overdue: escalate)"),
        ("Tabs", "Details · Criticality matrix · Metrics · Results · Issues log · Causes · Actions · Operations · RACI · Steps"),
        ("Guidance", "GOV.UK DQAP guide and data quality issues framework (2026); DQAP Implementation Guide v2.0; Defra 'Start here'; IOPC data trust scales"),
    ]
    for k, v in lines:
        ws.append([k, v])
    ws.column_dimensions["A"].width = 26; ws.column_dimensions["B"].width = 110
    for row in ws.iter_rows():
        row[0].font = Font(bold=True); row[1].alignment = WRAP
    ws["A1"].font = Font(bold=True, size=14)

    _sheet(wb, "Details", ["Field", "Value"], [
        ["Data asset name", asset.get("title", asset["id"])], ["Asset identifier", asset.get("iri", asset["id"])],
        ["Data owner", asset.get("owner", "")], ["Data steward(s)", asset.get("steward", "")],
        ["Description and primary use", asset.get("primary_use", asset.get("description", ""))],
        ["Known secondary uses", asset.get("secondary_uses", "")],
        ["Source", asset.get("source", "internal")], ["Influence over the data structure", "Yes" if route["influence"] else "No"],
        ["Importance of purpose (1-4)", asset.get("importance", 3)], ["Target policy", asset.get("target_policy", "low")],
        ["Measurement frequency", asset.get("measurement_cycle", asset.get("measurement_frequency", ""))],
        ["Date of this assessment", result["as_of"]], ["DQAP status", asset.get("dqap_status", "in_place")],
    ], widths={"Field": 34, "Value": 90})

    items = {}
    for r in result["results"]:
        for c in r["columns"] or ["(whole dataset)"]:
            items.setdefault(c, {"rules": [], "purpose": r.get("meta", {}).get("purpose", ""), "personal": False})
            items[c]["rules"].append(r["id"])
            items[c]["personal"] |= bool(r.get("meta", {}).get("personal_data")) or c in asset.get("personal_data_columns", [])
    _sheet(wb, "Criticality matrix", ["Critical data item", "Purpose it supports", "Rules", "Personal data", "Known issues"],
           [[c, v["purpose"], ", ".join(v["rules"]), "Yes" if v["personal"] else "No",
             ", ".join(i["rule"] for i in result["issues"] if i["rule"] in v["rules"])] for c, v in items.items()],
           widths={"Critical data item": 34, "Purpose it supports": 40})

    _sheet(wb, "Metrics", ["ID", "Purpose", "Part of data", "Requirement", "Relevant aspect (dimension)", "Measure", "Metric",
                           "Method", "Importance", "Impact", "Combined score", "Target (%)", "Tolerated error rate", "Control point", "Notes"],
           [[r["id"], r.get("meta", {}).get("purpose", ""), r.get("meta", {}).get("part_of_data", ", ".join(r["columns"])),
             r.get("meta", {}).get("requirement", r["description"]), r["dimension"], r["description"],
             "Percentage of records passing" if r["checked"] > 1 else "Pass (100) or fail (0) for the dataset",
             r.get("meta", {}).get("method", f"dqkit check '{r['check']}'"), r["assessment"]["importance"],
             r["assessment"]["impact"], r["assessment"]["combined"], r["assessment"]["target"],
             r["assessment"]["error_rate_target"], r.get("meta", {}).get("control_point", ""),
             r.get("meta", {}).get("notes", "")] for r in result["results"]],
           widths={"Purpose": 30, "Requirement": 36, "Measure": 36, "Method": 26, "Notes": 30})

    dates = sorted({d for v in hist.values() for d in v} | {result["as_of"]})[-8:]
    rows = []
    for r in result["results"]:
        series = dict(hist.get(r["id"], {})); series[result["as_of"]] = r["performance"]
        rows.append([r["id"], r["description"], r["assessment"]["target"]] + [series.get(d, "") for d in dates]
                    + ["Yes" if r["assessment"]["meets_target"] else "No", r["assessment"]["error_rate_actual"]])
    _sheet(wb, "Results", ["ID", "Requirement", "Target (%)"] + [f"Value {d}" for d in dates] + ["Meets target", "Actual error rate"],
           rows, widths={"Requirement": 40})

    issues = []
    for n, r in enumerate([x for x in result["results"] if not x["assessment"]["meets_target"]], 1):
        it = ISSUE_TYPES[r["issue_type"]]; a = r["assessment"]; o = ops["rules"][r["id"]]
        issues.append([f"I{n:03d}", r["id"], it["label"], it["definition"], r["dimension"], r["performance"], a["target"],
                       a["band"], a["priority_score"], a["priority"], a["resolution"], it["responsibility"],
                       r.get("meta", {}).get("control_point", ""), o["cycles_open"],
                       f"Overdue: escalate to {o['escalate_to'].lower()}" if o["overdue"] else "Within timescale",
                       "Yes" if o["recurrences"] else "No", asset.get("steward", ""), "", "", result["as_of"], "Open"])
    wsI = _sheet(wb, "Issues log", ["Issue ID", "Rule ID", "Issue type", "Description", "Dimension", "Performance (%)", "Target (%)",
                                     "Band", "Priority score", "Priority", "Resolution timescale", "Responsibility",
                                     "Control point", "Cycles open", "Escalation", "Recurring", "Owner", "Source system",
                                     "Immediate risk", "Date raised", "Status"], issues, widths={"Description": 44, "Escalation": 34},
                 input_cols=("Owner", "Source system", "Immediate risk", "Status"))
    fixer = "Supplier" if route["source"] == "external" and not route["influence"] else ""
    _sheet(wb, "Causes", ["Issue ID", "Priority", "Description of issue", "Contributing causes (5 whys)", "Systemic or one-off",
                          "Can we fix it ourselves? (addressability)", "Issue to address"],
           [[i[0], i[9], i[3], "", "", "No: supplier must fix; record and communicate the limitation" if fixer else "", ""] for i in issues],
           widths={"Description of issue": 44, "Contributing causes (5 whys)": 44, "Can we fix it ourselves? (addressability)": 30},
           input_cols=("Contributing causes (5 whys)", "Systemic or one-off", "Can we fix it ourselves? (addressability)", "Issue to address"))
    wsA = _sheet(wb, "Actions", ["Issue ID", "Action type", "Action to fix the issue", "Action owner", "Target date",
                                  "How we will know it worked", "Status"],
                 [[i[0], "", "", "", "", f"Rule {i[1]} meets {i[6]}% at the next measurement", "Not started"] for i in issues],
                 widths={"Action to fix the issue": 50, "How we will know it worked": 34},
                 input_cols=("Action type", "Action to fix the issue", "Action owner", "Target date", "Status"))
    _sheet(wb, "Operations", ["Measure", "Value", "What it tells you"], [
        ["Measurement cycles recorded", ops["cycles_measured"], "Keep a history (--history) so trends and ageing can be tracked"],
        ["Defect volume", ops["defect_volume"], "Records (or dataset checks) failing a rule now"],
        ["Control failure rate (%)", ops["control_failure_rate"], "Share of rules below target now"],
        ["Open issues", ops["open_issues"], "Rules below target now"],
        ["Mean cycles open", ops["mean_cycles_open"], "How long open issues have stayed open"],
        ["Overdue issues", ops["overdue_issues"], "Open longer than the issues framework allows: escalate"],
        ["Recurrence rate (%)", ops["recurrence_rate"], "Issues that were fixed and came back: look at root causes and controls at source"],
    ], widths={"Measure": 30, "Value": 12, "What it tells you": 80})
    _sheet(wb, "RACI", ["DQAP step", "Activity"] + RACI_ROLES, [[s, a] + roles for s, a, roles in RACI],
           widths={"Activity": 50, "DQAP step": 26})
    _sheet(wb, "Steps", ["#", "Step (decision tree route)"], [[i, s] for i, s in enumerate(route["steps"], 1)], widths={"Step (decision tree route)": 90})

    status = DataValidation(type="list", formula1='"Open,In progress,Resolved,Accepted risk"', allow_blank=True)
    wsI.add_data_validation(status); status.add(f"U2:U{max(2, len(issues) + 50)}")
    astatus = DataValidation(type="list", formula1='"Not started,In progress,Done,Blocked"', allow_blank=True)
    wsA.add_data_validation(astatus); astatus.add(f"G2:G{max(2, len(issues) + 50)}")
    atype = DataValidation(type="list", formula1='"Containment,Corrective,Preventive"', allow_blank=True)
    wsA.add_data_validation(atype); atype.add(f"B2:B{max(2, len(issues) + 50)}")
    wb["Causes"].add_data_validation(sys_ := DataValidation(type="list", formula1='"Systemic,One-off,Not known yet"', allow_blank=True))
    sys_.add(f"E2:E{max(2, len(issues) + 50)}")
    out = Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out
