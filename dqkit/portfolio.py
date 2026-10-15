"""Run a whole portfolio of data assets in one go, on a schedule.

A portfolio file (YAML, checked against portfolio.schema.json) lists each asset's rules file and
data file. For every enabled asset that is due, the runner does everything `dqkit check` does with
--workbook --case-study --history (results, DQV, DQAP CSVs, workbook, case study, trust level,
route and issue operations). It then writes portfolio-level outputs:

  portfolio.json          one compact summary per asset, totals, metadata assessment, changes since last run
  catalogue.dqv.jsonld    every DQV graph merged into one JSON-LD @graph
  escalations.json        issues that need escalating, with a plain-English body for a ticket
  run-summary.md          a human-readable digest
  metadata-assessment.json  (only if metadata records are configured) the full record-by-record assessment
  assets/<id>.*           the per-asset files
  history/<id>.history.csv  the measurement history (one row per rule per measurement date)

The run is deterministic for a given --as-of date. The only value that changes between identical
runs is `run_at` (the clock time); set SOURCE_DATE_EPOCH to fix it. `fingerprint` is a hash of
everything except run_at, so automation can tell whether anything really changed.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from . import casestudy, cdareturn, dqv, exporters, metadata, operations, pathway, rules, sources, trust, workbook

SCHEMA_PATH = Path(__file__).resolve().parent / "portfolio.schema.json"
PRIORITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
# Minimum days since the last measurement before a scheduled asset is due again. Slightly under the
# nominal period so a weekly automated run on a fixed weekday still lands on time.
DUE_AFTER_DAYS = {"weekly": 6, "monthly": 28, "quarterly": 89, "annual": 364}
WINDOW_TEXT = {"Critical": "immediately (by the next measurement)", "High": "within 1 measurement cycle",
               "Medium": "within 3 measurement cycles", "Low": "within 6 measurement cycles"}


class PortfolioError(Exception):
    """A problem with the portfolio file or one of its assets, described in plain English."""


# ---------- loading and validating ----------

def _where(path) -> str:
    parts = list(path)
    if not parts:
        return "the top level of the file"
    out = ""
    for p in parts:
        out += f"[{p}]" if isinstance(p, int) else (f".{p}" if out else str(p))
    return out


def validate(doc, source: str = "portfolio file") -> None:
    """Check a loaded portfolio against the JSON Schema. Raise PortfolioError with a friendly message."""
    import jsonschema
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise PortfolioError(f"{source}: the file is empty or is not a YAML mapping (it should start with 'portfolio:').")
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.absolute_path))
    if not errors:
        return
    lines = []
    for e in errors[:10]:
        path = list(e.absolute_path)
        who = ""
        if len(path) >= 2 and path[0] == "assets" and isinstance(path[1], int):
            a = doc["assets"][path[1]]
            name = a.get("rules") if isinstance(a, dict) else None
            who = f"Asset {path[1] + 1}" + (f" ({name})" if name else "") + ": "
        elif len(path) == 1 and path[0] == "assets" or (not path and "assets" in e.message):
            who = "Assets list: "
        lines.append(f"  - {who}{e.message} (at {_where(path)})")
    more = f"\n  ...and {len(errors) - 10} more" if len(errors) > 10 else ""
    raise PortfolioError(f"{source} has {len(errors)} problem(s):\n" + "\n".join(lines) + more)


def load(path) -> dict:
    p = Path(path)
    if not p.exists():
        raise PortfolioError(f"Portfolio file not found: {p}")
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise PortfolioError(f"{p} is not valid YAML: {e}") from None
    validate(doc, str(p))
    return doc


# ---------- helpers ----------

def _read_csv(path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")


def _last_measured(history_dir, asset_id: str, before: str) -> Optional[str]:
    if not history_dir:
        return None
    dates = {d for v in workbook.load_history(history_dir, asset_id).values() for d in v if d < before}
    return max(dates) if dates else None


def _is_due(schedule, last: Optional[str], as_of: date) -> bool:
    if not schedule or not last:
        return True
    return (as_of - date.fromisoformat(last)).days >= DUE_AFTER_DAYS[schedule]


def _run_at() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    t = datetime.fromtimestamp(int(epoch), timezone.utc) if epoch else datetime.now(timezone.utc)
    return t.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fingerprint(doc: dict) -> str:
    # What was measured, not when the job ran: identical measurements give the same fingerprint.
    body = {k: doc.get(k) for k in ("portfolio", "totals", "assets", "skipped", "metadata", "escalation_policy")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, obj, indent=2) -> None:
    path.write_text(json.dumps(obj, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------- one asset ----------

def measure_asset(spec: dict, df: pd.DataFrame, as_of: date, out: Path, history_dir) -> tuple[dict, dict]:
    """Everything `dqkit check --workbook --case-study --history` does. Returns (result, dqv graph)."""
    asset = spec["asset"]
    aid = asset["id"]
    res = rules.run(df, spec, as_of)
    res["trust"] = trust.classify(res, asset.get("personal_data_columns"))
    res["route"] = pathway.route(asset)
    if history_dir:
        workbook.append_history(res, history_dir)
    workbook.build(spec, res, out / f"{aid}.DQAP.xlsx", history_dir)
    res["operations"] = operations.assess(res, history_dir)
    cs = casestudy.draft(spec, res, history_dir)
    (out / f"{aid}.case-study.md").write_text(casestudy.to_markdown(cs), encoding="utf-8")
    casestudy.to_docx(cs, out / f"{aid}.case-study.docx")
    _write_json(out / f"{aid}.results.json", res)
    graph = dqv.result_to_dqv(res, asset.get("iri"), asset.get("dqap"))
    _write_json(out / f"{aid}.dqv.jsonld", graph)
    d = exporters.to_dqap_csv(res)
    (out / f"{aid}.dqap-rules.csv").write_text(d["rules"], encoding="utf-8")
    (out / f"{aid}.dqap-issues.csv").write_text(d["issues"], encoding="utf-8")
    return res, graph


def summarise_asset(res: dict, entry: dict, rules_path: str, data_path: str) -> dict:
    """The compact, stable per-asset record that goes into portfolio.json."""
    asset, ops = res["asset"], res["operations"]
    aid = asset["id"]
    by_rule = {r["id"]: r for r in res["results"]}
    issues = []
    for i in res["issues"]:
        o = ops["rules"][i["rule"]]
        issues.append({"rule": i["rule"], "description": by_rule[i["rule"]]["description"], "label": i["label"],
                       "issue_type": i["issue_type"], "dimension": i["dimension"], "priority": i["priority"],
                       "resolution": i["resolution"], "performance": i["performance"], "target": i["target"],
                       "cycles_open": o["cycles_open"], "overdue": o["overdue"], "recurrences": o["recurrences"]})
    return {
        "id": aid, "title": asset.get("title", aid), "owner": asset.get("owner", ""), "iri": asset.get("iri"),
        "tags": entry.get("tags", []), "schedule": entry.get("schedule"),
        "rules_file": rules_path, "data_file": data_path,
        "measured_on": res["as_of"], "rows": res["rows"],
        "rules_met": res["rules_met"], "rules_total": res["rules_total"],
        "issues": issues,
        "trust": {"level": res["trust"]["level"], "sharing": res["trust"]["sharing"],
                  "action_plan_required": res["trust"]["action_plan_required"]},
        "route": {"route": res["route"]["route"], "source": res["route"]["source"], "influence": res["route"]["influence"],
                  "responsibility": res["route"]["responsibility"]},
        "operations": {k: ops[k] for k in ("cycles_measured", "defect_volume", "control_failure_rate", "open_issues",
                                           "overdue_issues", "mean_cycles_open", "recurrence_rate")},
        "overdue": [{"rule": i["rule"], "priority": i["priority"], "cycles_open": i["cycles_open"],
                     "escalate_to": ops["rules"][i["rule"]]["escalate_to"]} for i in issues if i["overdue"]],
        "dimensions": {k: v["mean_performance"] for k, v in sorted(res["dimensions"].items())},
        "files": {k: f"assets/{aid}.{ext}" for k, ext in (
            ("results", "results.json"), ("dqv", "dqv.jsonld"), ("dqap_rules", "dqap-rules.csv"),
            ("dqap_issues", "dqap-issues.csv"), ("workbook", "DQAP.xlsx"), ("case_study", "case-study.md"),
            ("case_study_docx", "case-study.docx"))},
    }


# ---------- escalations ----------

def _escalate_to(summary: dict, issue: dict, ops_rule: dict) -> str:
    who = ops_rule.get("escalate_to") or "Data owner"
    route = summary["route"]
    if route["source"] == "external" and not route["influence"]:
        who += f"; the fix sits with the supplier ({summary['owner'] or 'the data supplier'})"
    elif route["source"] == "external":
        who += f"; agree the fix with the supplier ({summary['owner'] or 'the data supplier'})"
    return who


def build_escalations(summaries: list, results: dict, notify: dict) -> list:
    priorities = notify.get("escalate_priorities", ["Critical", "High"])
    when = notify.get("escalate_when", "overdue")
    out = []
    for s in summaries:
        res = results[s["id"]]
        by_rule = {r["id"]: r for r in res["results"]}
        for i in s["issues"]:
            if i["priority"] not in priorities or (when == "overdue" and not i["overdue"]):
                continue
            r = by_rule[i["rule"]]
            ops_rule = res["operations"]["rules"][i["rule"]]
            who = _escalate_to(s, i, ops_rule)
            window = operations.WINDOW.get(i["priority"])
            status = (f"It has been below target for {i['cycles_open']} measurement cycle(s) in a row. The issues framework "
                      f"says a {i['priority']} issue should be fixed {WINDOW_TEXT[i['priority']]}, so it is **overdue**."
                      if i["overdue"] else
                      f"It has been below target for {i['cycles_open']} measurement cycle(s). A {i['priority']} issue should be "
                      f"fixed {WINDOW_TEXT[i['priority']]} (window: {window} cycle(s)).")
            evidence = ""
            if r.get("detail"):
                evidence = "\n**Evidence:** " + "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in r["detail"].items()
                                                          if not isinstance(v, (dict, list)))
            elif r.get("examples") and notify.get("include_examples", True) and not res["asset"].get("personal_data_columns"):
                evidence = "\n**Examples of failing rows:** " + "; ".join(
                    ", ".join(f"{k} {v}" for k, v in ex.items()) for ex in r["examples"][:3])
            body = "\n".join([
                f"**Asset:** {s['title']} (`{s['id']}`), owned by {s['owner'] or 'not stated'}",
                f"**Rule:** {i['rule']}: {i['description']}",
                "",
                f"**What failed:** {i['label']} ({i['dimension']}). {rules.ISSUE_TYPES[i['issue_type']]['definition']}",
                f"**Performance:** {i['performance']}% against a target of {i['target']}%. Priority: **{i['priority']}** "
                f"(issues framework resolution: {i['resolution']}).",
                f"**How long:** {status}",
                evidence.strip("\n"),
                "",
                f"**Who acts:** {who}.",
                f"**Suggested next step:** {s['route']['responsibility']} Route: {s['route']['route']}. "
                "Record the root cause and the action in the DQAP workbook (Causes and Actions tabs).",
                "",
                f"Measured on {s['measured_on']} by dqkit. Files: `{s['files']['workbook']}`, `{s['files']['results']}`.",
                f"<!-- dq-escalation asset={s['id']} rule={i['rule']} measured={s['measured_on']} -->",
            ]).replace("\n\n\n", "\n\n")
            out.append({"asset_id": s["id"], "rule_id": i["rule"], "priority": i["priority"],
                        "cycles_open": i["cycles_open"], "escalate_to": who, "measured_on": s["measured_on"],
                        "title": f"[DQ] {s['id']} {i['rule']}: {i['label']} ({i['priority']})",
                        "body_markdown": body})
    out.sort(key=lambda e: (PRIORITY_ORDER.get(e["priority"], 9), -e["cycles_open"], e["asset_id"], e["rule_id"]))
    return out


# ---------- changes since the last run ----------

def _issue_keys(doc: dict) -> dict:
    return {(a["id"], i["rule"]): {"asset_id": a["id"], "rule_id": i["rule"], "priority": i["priority"], "label": i["label"]}
            for a in doc.get("assets", []) for i in a.get("issues", [])}


def compare(previous: Optional[dict], current_assets: list) -> dict:
    now = _issue_keys({"assets": current_assets})
    if not previous:
        return {"compared_with": None, "new": sorted(now.values(), key=_ck), "resolved": [], "still_open": []}
    before = _issue_keys(previous)
    present = {a["id"] for a in current_assets}
    return {
        "compared_with": previous.get("as_of"),
        "new": sorted((v for k, v in now.items() if k not in before), key=_ck),
        "resolved": sorted((v for k, v in before.items() if k not in now and k[0] in present), key=_ck),
        "still_open": sorted((v for k, v in now.items() if k in before), key=_ck),
    }


def _ck(v):
    return (v["asset_id"], v["rule_id"])


# ---------- metadata ----------

def metadata_summary(port: dict, source: str) -> dict:
    return {
        "records_file": source, "records": len(port["pages"]), "mean_score": port["mean_score"],
        "mean_cda_coverage": port["mean_cda_coverage"], "rag": port["rag"],
        "checks": [{"id": c["id"], "label": c["label"], "source": c["source"], "dimension": c["dimension"],
                    "applicable": c["applicable"], "pass": c["pass"], "partial": c["partial"], "fail": c["fail"],
                    "performance": c["performance"], "target": c["assessment"]["target"],
                    "priority": c["assessment"]["priority"]} for c in port["checks"]],
    }


# ---------- the run ----------

def run(portfolio_path, as_of: Optional[date] = None, out_dir=None, history: bool = True,
        ignore_schedule: bool = False, log=print) -> dict:
    """Run the portfolio. Returns {"portfolio": doc, "escalations": [...], "out": Path}."""
    ppath = Path(portfolio_path)
    doc = load(ppath)
    base = ppath.resolve().parent
    meta, defaults = doc["portfolio"], doc.get("defaults", {})
    as_of = as_of or (date.fromisoformat(meta["as_of"]) if meta.get("as_of") else date.today())
    out = Path(out_dir) if out_dir else base / defaults.get("out_dir", "dq-portfolio")
    assets_out = out / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    hist_dir = None
    if history:
        h = Path(defaults.get("history_dir", "history"))
        hist_dir = h if h.is_absolute() else out / h

    previous = None
    prev_path = out / "portfolio.json"
    if prev_path.exists():
        try:
            previous = json.loads(prev_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previous = None
    prev_assets = {a["id"]: a for a in (previous or {}).get("assets", [])}

    summaries, results, graphs, skipped = [], {}, [], []
    for n, entry in enumerate(doc["assets"], 1):
        label = f"Asset {n} ({entry['rules']})"
        if not entry.get("enabled", True):
            skipped.append({"rules_file": entry["rules"], "reason": "disabled"})
            continue
        rp = base / entry["rules"]
        dsrc = entry["data"]
        dp = base / dsrc if isinstance(dsrc, str) else None
        if not rp.exists():
            raise PortfolioError(f"{label}: the rules file was not found at {rp}")
        if dp is not None and not dp.exists():
            raise PortfolioError(f"{label}: the data file '{entry['data']}' was not found at {dp}")
        try:
            spec = rules.load_rules(rp)
        except (ValueError, KeyError, TypeError, yaml.YAMLError) as e:
            raise PortfolioError(f"{label}: the rules file has a problem: {e}") from None
        if "target_policy" in defaults:
            spec["asset"].setdefault("target_policy", defaults["target_policy"])
        aid = spec["asset"]["id"]
        if aid in results or any(s["id"] == aid for s in summaries):
            raise PortfolioError(f"{label}: asset id '{aid}' is used by more than one asset in the portfolio")

        last = _last_measured(hist_dir, aid, as_of.isoformat())
        if (not ignore_schedule and not _is_due(entry.get("schedule"), last, as_of) and aid in prev_assets
                and (assets_out / f"{aid}.results.json").exists()):
            # Not due yet: carry the last measurement forward without adding a cycle.
            res = json.loads((assets_out / f"{aid}.results.json").read_text(encoding="utf-8"))
            graph = json.loads((assets_out / f"{aid}.dqv.jsonld").read_text(encoding="utf-8"))
            s = summarise_asset(res, entry, entry["rules"], entry["data"])
            s["measured"] = False
            s["next_due"] = (date.fromisoformat(res["as_of"]).toordinal() + DUE_AFTER_DAYS[entry["schedule"]])
            s["next_due"] = date.fromordinal(s["next_due"]).isoformat()
            log(f"  {aid}: not due ({entry['schedule']}); last measured {res['as_of']}, next due {s['next_due']}")
        else:
            try:
                df = sources.read(dsrc, base)
            except Exception as e:  # noqa: BLE001 - any read problem is reported in plain English
                raise PortfolioError(f"{label}: could not read the data file '{entry['data']}': {e}") from None
            try:
                res, graph = measure_asset(spec, df, as_of, assets_out, hist_dir)
            except KeyError as e:
                raise PortfolioError(f"{label}: a rule refers to something missing ({e}). Check the rules file.") from None
            s = summarise_asset(res, entry, entry["rules"], entry["data"])
            s["measured"] = True
            s["next_due"] = (date.fromordinal(as_of.toordinal() + DUE_AFTER_DAYS[entry["schedule"]]).isoformat()
                             if entry.get("schedule") else None)
            log(f"  {aid}: {res['rules_met']}/{res['rules_total']} rules met; {len(res['issues'])} issue(s); "
                f"trust {res['trust']['level']}")
        summaries.append(s)
        results[aid] = res
        graphs.append(graph)

    # metadata assessment (optional)
    meta_summary = None
    mcfg = doc.get("metadata") or {}
    if mcfg.get("records"):
        mp = base / mcfg["records"]
        if not mp.exists():
            raise PortfolioError(f"Metadata: the records file was not found at {mp}")
        try:
            recs = [json.loads(line) for line in mp.read_text(encoding="utf-8").splitlines() if line.strip()]
            port = metadata.assess_portfolio(recs, as_of)
        except (ValueError, KeyError) as e:
            raise PortfolioError(f"Metadata: could not assess the records in {mcfg['records']}: {e}") from None
        _write_json(out / "metadata-assessment.json", port)
        graphs.append(dqv.metadata_to_dqv(port))
        meta_summary = metadata_summary(port, mcfg["records"])
        log(f"  metadata: {len(port['pages'])} records, mean score {port['mean_score']}%, RAG {port['rag']}")

    escalations = build_escalations(summaries, results, doc.get("notify", {}))
    by_pr = {p: 0 for p in PRIORITY_ORDER}
    for s in summaries:
        for i in s["issues"]:
            by_pr[i["priority"]] = by_pr.get(i["priority"], 0) + 1
    levels = {lv: 0 for lv in trust.LEVELS}
    for s in summaries:
        levels[s["trust"]["level"]] += 1
    totals = {
        "assets": len(summaries), "assets_measured": sum(1 for s in summaries if s["measured"]),
        "assets_skipped": len(skipped),
        "rules_total": sum(s["rules_total"] for s in summaries), "rules_met": sum(s["rules_met"] for s in summaries),
        "open_issues": sum(len(s["issues"]) for s in summaries), "issues_by_priority": by_pr,
        "overdue_issues": sum(len(s["overdue"]) for s in summaries), "escalations": len(escalations),
        "trust_levels": levels,
    }
    pdoc = {
        "schema_version": 1,
        "portfolio": {k: meta[k] for k in ("id", "title", "owner")},
        "as_of": as_of.isoformat(),
        "run_at": _run_at(),
        "fingerprint": "",
        "totals": totals,
        "assets": summaries,
        "skipped": skipped,
        "metadata": meta_summary,
        "changes": compare(previous, summaries),
        "escalation_policy": {"escalate_priorities": doc.get("notify", {}).get("escalate_priorities", ["Critical", "High"]),
                              "escalate_when": doc.get("notify", {}).get("escalate_when", "overdue"),
                              "windows_cycles": operations.WINDOW},
        "files": {"catalogue": "catalogue.dqv.jsonld", "escalations": "escalations.json", "summary": "run-summary.md",
                  "cda_return": "cda-return.csv",
                  **({"metadata": "metadata-assessment.json"} if meta_summary else {}),
                  **({"history": os.path.relpath(hist_dir, out)} if hist_dir else {})},
    }
    pdoc["fingerprint"] = _fingerprint(pdoc)
    _write_json(out / "portfolio.json", pdoc, indent=1)
    _write_json(out / "catalogue.dqv.jsonld", dqv.merge(graphs), indent=1)
    _write_json(out / "escalations.json", escalations)
    (out / "run-summary.md").write_text(to_markdown(pdoc, escalations), encoding="utf-8")
    (out / "cda-return.csv").write_text(cdareturn.to_csv([results[s["id"]] for s in summaries]), encoding="utf-8")
    return {"portfolio": pdoc, "escalations": escalations, "out": out}


# ---------- the human-readable digest ----------

def _cell(x) -> str:
    return str(x).replace("|", "\\|").replace("\n", " ")


def to_markdown(p: dict, escalations: list) -> str:
    t = p["totals"]
    titles = {a["id"]: a["title"] for a in p["assets"]}
    L = [f"# Data quality run: {p['portfolio']['title']}", "",
         f"- **Measured as of:** {p['as_of']} (run at {p['run_at']})",
         f"- **Owner:** {p['portfolio']['owner']}",
         f"- **Assets:** {t['assets']} ({t['assets_measured']} measured this run"
         + (f", {t['assets_skipped']} disabled" if t["assets_skipped"] else "") + ")",
         f"- **Rules meeting target:** {t['rules_met']} of {t['rules_total']}",
         f"- **Open issues:** {t['open_issues']} ("
         + ", ".join(f"{n} {k}" for k, n in t["issues_by_priority"].items() if n) + ")" if t["open_issues"] else
         "- **Open issues:** none",
         f"- **Overdue issues:** {t['overdue_issues']}. **Escalations:** {t['escalations']}",
         "", "## Assets", "",
         "| Asset | Measured on | Rules met | Open issues | Worst priority | Overdue | Trust level | Route |",
         "|---|---|---|---|---|---|---|---|"]
    for a in p["assets"]:
        worst = min((i["priority"] for i in a["issues"]), key=lambda x: PRIORITY_ORDER[x], default="None")
        when = a["measured_on"] + ("" if a["measured"] else " (carried forward)")
        L.append(f"| {_cell(a['title'])} | {when} | {a['rules_met']}/{a['rules_total']} | {len(a['issues'])} | {worst} | "
                 f"{len(a['overdue'])} | {a['trust']['level']} | {_cell(a['route']['route'])} |")
    ch = p["changes"]
    L += ["", "## What changed since the last run", ""]
    L.append(f"Compared with the run measured on {ch['compared_with']}." if ch["compared_with"] else
             "This is the first run in this folder, so every open issue is listed as new.")

    def items(lst, empty):
        if not lst:
            return [f"- {empty}"]
        return [f"- **{x['priority']}** {titles.get(x['asset_id'], x['asset_id'])}, rule {x['rule_id']}: {x['label']}" for x in lst]
    L += ["", "### New issues", ""] + items(ch["new"], "None")
    L += ["", "### Resolved issues", ""] + items(ch["resolved"], "None")
    L += ["", f"Still open from last time: {len(ch['still_open'])}."]
    L += ["", "## Overdue issues", ""]
    od = [(a, o) for a in p["assets"] for o in a["overdue"]]
    if od:
        L += ["| Asset | Rule | Priority | Cycles open | Escalate to |", "|---|---|---|---|---|"]
        L += [f"| {_cell(a['title'])} | {o['rule']} | {o['priority']} | {o['cycles_open']} | {o['escalate_to']} |" for a, o in od]
    else:
        L.append("None. (An issue is overdue when it has been open longer than the issues framework allows: "
                 "Critical and High 1 cycle, Medium 3, Low 6.)")
    L += ["", "## Escalations", ""]
    L += ([f"- {e['title']}: escalate to {e['escalate_to']}" for e in escalations] if escalations else ["None this run."])
    if p.get("metadata"):
        m = p["metadata"]
        L += ["", "## Catalogue records (metadata assessment)", "",
              f"{m['records']} records from `{m['records_file']}`: mean score {m['mean_score']}%, "
              f"CDA metadata coverage {m['mean_cda_coverage']}%. RAG: {m['rag']['green']} green, {m['rag']['amber']} amber, "
              f"{m['rag']['red']} red.", "",
              "| Check | Performance (%) | Target (%) | Priority |", "|---|---|---|---|"]
        L += [f"| {c['id']} {_cell(c['label'])} | {c['performance']} | {c['target']} | {c['priority'] or 'Meets target'} |"
              for c in m["checks"]]
    L += ["", "## Files", "",
          "- `portfolio.json`: the summary above, for the web portal",
          "- `escalations.json`: one entry per escalated issue, ready to become a ticket",
          "- `catalogue.dqv.jsonld`: all results as W3C Data Quality Vocabulary, for a catalogue",
          "- `assets/`: per-asset results, DQAP workbook, CSVs and draft case study", ""]
    return "\n".join(L)
