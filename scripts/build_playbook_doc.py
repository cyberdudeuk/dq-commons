#!/usr/bin/env python3
"""Write docs/DQ-MANAGEMENT-PLAYBOOK.md from knowledge/playbook.yaml, so the document and the portal page never drift.

Usage:  python3 scripts/build_playbook_doc.py          # write the file
        python3 scripts/build_playbook_doc.py --check  # exit 1 if the committed file is out of date (used in CI)
"""
import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DQ-MANAGEMENT-PLAYBOOK.md"


def render() -> str:
    pb = yaml.safe_load((ROOT / "knowledge" / "playbook.yaml").read_text(encoding="utf-8"))
    with open(ROOT / "knowledge" / "requirements.csv", encoding="utf-8") as fh:
        req = {r["clause"]: r for r in csv.DictReader(fh)}
    fw = {f["id"]: f for f in yaml.safe_load((ROOT / "knowledge" / "frameworks.yaml").read_text(encoding="utf-8"))["frameworks"]}
    roles = {r["id"]: r["name"] for r in pb["roles"]}
    L = ["# Data quality management playbook for critical data assets", "",
         "> Generated from `knowledge/playbook.yaml` by `scripts/build_playbook_doc.py`. Edit the YAML, not this file.",
         f"> Last reviewed {pb['review']['last_reviewed']}. Owner: {pb['review']['owner_role']}. Content licence: OGL v3.0.", "",
         pb["summary"], "", "**Interactive version:** the portal page `playbook.html` has a checklist you can tick, template downloads and a jurisdiction finder.", "",
         "## Who it is for", ""] + [f"- {a}" for a in pb["applies_to"]] + ["",
         "## Use it anywhere", "", pb["adapt"]["intro"], "", "| In this playbook | You might call it |", "|---|---|"] + \
        [f"| {t['here']} | {t['elsewhere']} |" for t in pb["adapt"]["terms"]] + ["", pb["adapt"]["rule"], "", "## Principles", ""] + \
        [f"{i}. **{p['name']}.** {p['text']}" for i, p in enumerate(pb["principles"], 1)] + ["", "## The eight stages", ""]
    for s in pb["stages"]:
        L += [f"### Stage {s['n']}: {s['name']}", "", f"**Goal:** {s['goal']} *Typical effort: {s['effort']}.*", "", "**Steps**", ""]
        L += [f"{i}. {x}" for i, x in enumerate(s["steps"], 1)]
        L += ["", "**Outputs:** " + "; ".join(s["outputs"]) + ".", "", "**Checklist**", ""] + [f"- [ ] {x}" for x in s["checklist"]]
        L += ["", "**Who leads:** " + ", ".join(f"{roles[k]} ({v})" for k, v in s["raci"].items() if v in ("A", "R")) + ".", "",
              "**UK DAM policy and DQAP:**", ""]
        L += [f"- `{c}` {req[c]['requirement']}" if c in req else f"- `{c}`" for c in s["dam"]]
        L += ["", f"**Elsewhere:** {s['elsewhere']}", "", f"**Inclusion check:** {s['inclusion']}", "",
              f"**Toolkit:** {s['toolkit']['text']} (`{s['toolkit']['link']}`).", ""]
    L += ["## Who does what (RACI)", "", "R = does the work, A = accountable, C = consulted, I = informed.", "",
          "| Role | " + " | ".join(str(s["n"]) for s in pb["stages"]) + " |", "|---|" + "---|" * len(pb["stages"])]
    L += [f"| {r['name']} | " + " | ".join(s["raci"].get(r["id"], "") for s in pb["stages"]) + " |" for r in pb["roles"]]
    L += [""] + [f"- **{r['name']}:** {r['text']}" for r in pb["roles"]]
    L += ["", "## Rhythm", "", "| When | What | Who |", "|---|---|---|"] + [f"| {c['when']} | {c['what']} | {c['who']} |" for c in pb["cadence"]]
    L += ["", "## Escalation", "", "| Level | Trigger | Action | By |", "|---|---|---|---|"] + \
         [f"| {c['level']} | {c['trigger']} | {c['action']} | {c['timescale']} |" for c in pb["escalation"]]
    L += ["", "## Measures", "", "| Measure | Target |", "|---|---|"] + [f"| {m['name']} | {m['target']} |" for m in pb["measures"]]
    L += ["", "## Templates", "", "Use roles and contact forms, not personal names or emails.", ""]
    for t in pb["templates"]:
        L += [f"### {t['name']}", "", "| " + " | ".join(t["fields"]) + " |", "|" + "---|" * len(t["fields"]), ""]
    L += ["## Inclusion checks", ""] + [f"- [ ] {q}" for q in pb["inclusion_checks"]]
    L += ["", "## Where it applies", "", "| Where | Basis | Frameworks in the Commons |", "|---|---|---|"]
    L += [f"| {j['where']} | {j['basis']} | " + "; ".join(fw[i]["name"] for i in j["frameworks"] if i in fw) + " |" for j in pb["jurisdictions"]]
    L += ["", "## Sources", ""] + [f"- [{s['title']}]({s['url']})" for s in pb["sources"]] + [""]
    return "\n".join(L)


if __name__ == "__main__":
    text = render()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("docs/DQ-MANAGEMENT-PLAYBOOK.md is out of date. Run: python3 scripts/build_playbook_doc.py")
            sys.exit(1)
        print("Playbook document is current.")
    else:
        OUT.write_text(text, encoding="utf-8")
        print(f"Wrote {OUT.relative_to(ROOT)}")
