"""The data quality management playbook, made usable from the toolkit.

  init(out, asset_id, title)  start a playbook workspace for one critical data asset: blank CSV templates,
                              a checklist README and a status file
  status(workspace)           look at the files in a workspace and say which stages have evidence, which
                              are still to do, and what to do next
  guide(stage=None)           the playbook (or one stage) as plain data, for the CLI and the MCP server

Source: knowledge/playbook.yaml (the same file the portal page and docs/DQ-MANAGEMENT-PLAYBOOK.md use).
Evidence is judged only from files that exist and have content; nothing is inferred about people.
"""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_FILES = {"t-register": "01-register.csv", "t-rule": "02-rules.csv", "t-issue": "04-issues.csv",
                  "t-plan": "04-action-plan.csv", "t-statement": "06-quality-statement.csv", "t-review": "08-annual-review.csv"}


def load() -> dict:
    return yaml.safe_load((ROOT / "knowledge" / "playbook.yaml").read_text(encoding="utf-8"))


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return s or "asset"


def guide(stage: str | int | None = None) -> dict:
    pb = load()
    if stage in (None, ""):
        return {"summary": pb["summary"], "stages": [{"n": s["n"], "id": s["id"], "name": s["name"], "goal": s["goal"]} for s in pb["stages"]],
                "principles": [p["name"] for p in pb["principles"]]}
    for s in pb["stages"]:
        if str(stage) in (str(s["n"]), s["id"]):
            return s
    raise ValueError(f"No stage {stage!r}. Use 1-8 or one of: " + ", ".join(s["id"] for s in pb["stages"]))


def _csv_header(fields: list) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\r\n").writerow(fields)
    return buf.getvalue()


def init(out: str | Path, asset_id: str, title: str = "", force: bool = False) -> list[Path]:
    """Create a workspace. Never overwrites an existing file unless force=True. Returns the files written."""
    pb, out = load(), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    written = []

    def put(name, text):
        p = out / name
        if p.exists() and not force:
            return
        p.write_text(text, encoding="utf-8")
        written.append(p)

    tpl = {t["id"]: t for t in pb["templates"]}
    for tid, fname in TEMPLATE_FILES.items():
        put(fname, _csv_header(tpl[tid]["fields"]))
    lines = [f"# Data quality playbook: {title or asset_id}", "",
             f"Asset ID: `{asset_id}`. Started {date.today().isoformat()}. Work through the stages in order; tick items in this file as you go.",
             "Run `python -m dqkit playbook status .` in this folder to see which stages have evidence.", "",
             "Use roles and contact forms, not personal names or emails, in every file here.", ""]
    for s in pb["stages"]:
        lines += [f"## Stage {s['n']}: {s['name']}", "", f"Goal: {s['goal']}", ""] + [f"- [ ] {c}" for c in s["checklist"]]
        lines += ["", f"Inclusion check: {s['inclusion']}", ""]
    put("README.md", "\n".join(lines))
    put("playbook-status.yaml", yaml.safe_dump({"asset_id": asset_id, "title": title or asset_id, "started": date.today().isoformat(),
                                               "rules_file": f"{_slug(asset_id)}.rules.yaml", "results_dir": "results"}, sort_keys=False))
    return written


def _rows(p: Path) -> int:
    """Data rows in a CSV (header excluded); 0 if missing or empty."""
    if not p.exists():
        return 0
    with p.open(encoding="utf-8", newline="") as fh:
        return sum(1 for r in list(csv.reader(fh))[1:] if any(c.strip() for c in r))


def _ticks(readme: Path) -> dict:
    """Checklist ticks per stage number from the workspace README."""
    out, cur = {}, None
    if not readme.exists():
        return out
    for line in readme.read_text(encoding="utf-8").splitlines():
        m = re.match(r"## Stage (\d+):", line)
        if m:
            cur = int(m.group(1)); out[cur] = [0, 0]
        elif cur and re.match(r"- \[[ xX]\] ", line):
            out[cur][1] += 1
            out[cur][0] += line[3] in "xX"
    return out


def status(workspace: str | Path) -> dict:
    """Evidence for each stage, from the files in a workspace. 'done' needs evidence and every checklist item ticked."""
    ws, pb = Path(workspace), load()
    cfg = yaml.safe_load((ws / "playbook-status.yaml").read_text(encoding="utf-8")) if (ws / "playbook-status.yaml").exists() else {}
    rules_file = ws / cfg.get("rules_file", "rules.yaml")
    results = sorted((ws / cfg.get("results_dir", "results")).glob("*.results.json")) if (ws / cfg.get("results_dir", "results")).exists() else []
    hist = list((ws / "history").glob("*")) if (ws / "history").exists() else []
    rd = ws / cfg.get("results_dir", "results")
    dqv_files = rd.exists() and any(rd.glob("*.dqv.jsonld"))
    res = json.loads(results[-1].read_text(encoding="utf-8")) if results else None
    issues = _rows(ws / "04-issues.csv") or (len(res["issues"]) if res else 0)
    evidence = {
        1: (_rows(ws / "01-register.csv") > 0, "register has at least one asset row"),
        2: (rules_file.exists() or _rows(ws / "02-rules.csv") > 0, "a rules file or rule rows exist"),
        3: (res is not None, "a results file from dqkit check exists"),
        4: (_rows(ws / "04-action-plan.csv") > 0, "the action plan has at least one row"),
        5: (_rows(ws / "04-issues.csv") > 0 and _actions_owned(ws / "04-issues.csv"), "every logged issue has an action and owner"),
        6: (_rows(ws / "06-quality-statement.csv") > 0 or dqv_files, "a quality statement row or DQV file exists"),
        7: (len(hist) > 0, "measurement history exists (dqkit check --history)"),
        8: (_rows(ws / "08-annual-review.csv") > 0, "an annual review row exists"),
    }
    ticks = _ticks(ws / "README.md")
    stages = []
    for s in pb["stages"]:
        ok, what = evidence[s["n"]]
        t = ticks.get(s["n"], [0, len(s["checklist"])])
        state = "done" if ok and t[1] and t[0] == t[1] else ("in progress" if ok or t[0] else "to do")
        stages.append({"n": s["n"], "id": s["id"], "name": s["name"], "evidence": ok, "evidence_rule": what,
                       "ticked": t[0], "checklist": t[1], "state": state})
    nxt = next((s for s in stages if s["state"] != "done"), None)
    summary = {"asset_id": cfg.get("asset_id", ws.name), "stages": stages, "done": sum(s["state"] == "done" for s in stages),
               "issues_logged": issues, "next": None}
    if res:
        summary["latest_result"] = {"rules_met": res.get("rules_met"), "rules_total": res.get("rules_total"), "issues": len(res.get("issues", []))}
    if nxt:
        st = guide(nxt["n"])
        summary["next"] = {"stage": nxt["n"], "name": nxt["name"], "first_step": st["steps"][0], "toolkit": st["toolkit"]}
    return summary


def _actions_owned(p: Path) -> bool:
    with p.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if any((v or "").strip() for v in r.values())]
    return bool(rows) and all((r.get("Action and owner") or "").strip() for r in rows)


def to_text(st: dict) -> str:
    sym = {"done": "[x]", "in progress": "[~]", "to do": "[ ]"}
    L = [f"Playbook status for {st['asset_id']}: {st['done']} of {len(st['stages'])} stages done"]
    for s in st["stages"]:
        L.append(f"  {sym[s['state']]} {s['n']}. {s['name']:<32} evidence: {'yes' if s['evidence'] else 'no '}  checklist {s['ticked']}/{s['checklist']}")
    if st.get("latest_result"):
        r = st["latest_result"]
        L.append(f"  Latest check: {r['rules_met']}/{r['rules_total']} rules meet target; {r['issues']} issue(s).")
    if st["next"]:
        n = st["next"]
        L.append(f"Next: stage {n['stage']} ({n['name']}). First step: {n['first_step']}")
        L.append(f"  Toolkit: {n['toolkit']['text']} ({n['toolkit']['link']})")
    else:
        L.append("All stages done. Book the next annual review.")
    return "\n".join(L)
