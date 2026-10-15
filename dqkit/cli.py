"""Command line: python -m dqkit <command> ...

  check   DATA.csv RULES.yaml [--as-of YYYY-MM-DD] [--out DIR] [--history DIR] [--workbook] [--case-study]
          run rules; write results, DQV, DQAP CSVs, trust level and (optionally) a filled DQAP Excel workbook
  export  RULES.yaml --to gx|r-validate                          print a Great Expectations suite or R validate rules
  survey  FORMS_EXPORT.xlsx [--out DIR]                           reshape and summarise the DQ tooling survey (personal data removed)
  assess-metadata RECORDS.jsonl [--as-of YYYY-MM-DD] [--out FILE] assess catalogue records against GOV.UK requirements
  run     PORTFOLIO.yaml [--as-of YYYY-MM-DD] [--out DIR] [--no-history] [--ignore-schedule] [--fail-on-escalation]
          measure every asset in a portfolio file; write portfolio.json, escalations.json, catalogue DQV and a run summary
  suggest DATA.csv [--id ID] [--title T] [--owner O] [--out rules.yaml]
          look at a data file and draft a starter rules file for a steward to review
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from . import casestudy, dqv, exporters, metadata, operations, pathway, rules, trust


def _date(s):
    return date.fromisoformat(s) if s else date.today()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="dqkit", description="Data quality assurance kit (GOV.UK DQAP and issues framework)",
                                epilog="Run 'python -m dqkit COMMAND --help' for help on one command.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("data"); c.add_argument("rules"); c.add_argument("--as-of"); c.add_argument("--out", default="dq-results")
    c.add_argument("--history", help="folder that keeps each run, so results show trends over time")
    c.add_argument("--workbook", action="store_true", help="also write a filled-in DQAP workbook (.xlsx)")
    c.add_argument("--case-study", action="store_true", help="also draft a GDS-style case study (.md and .docx)")
    e = sub.add_parser("export")
    e.add_argument("rules"); e.add_argument("--to", choices=["gx", "r-validate"], required=True)
    m = sub.add_parser("assess-metadata")
    m.add_argument("records"); m.add_argument("--as-of"); m.add_argument("--out")
    sv = sub.add_parser("survey")
    sv.add_argument("export"); sv.add_argument("--out", default="survey-results")
    r = sub.add_parser("run", help="measure every asset in a portfolio file",
                       description="Measure every asset listed in a portfolio file, then write a portfolio summary "
                                   "(portfolio.json), escalations (escalations.json), one DQV catalogue file and a "
                                   "plain-English run summary (run-summary.md). Exit code: 0 OK, 1 problem, "
                                   "2 escalations found (only with --fail-on-escalation).")
    r.add_argument("portfolio", help="the portfolio file (YAML), for example portfolio.ndl.yaml")
    r.add_argument("--as-of", help="measure as if on this date (YYYY-MM-DD). Default: the portfolio's as_of, or today")
    r.add_argument("--out", help="folder for the results. Default: defaults.out_dir in the portfolio file")
    r.add_argument("--no-history", action="store_true", help="do not read or add to the measurement history")
    r.add_argument("--ignore-schedule", action="store_true", help="measure every enabled asset now, even if not due")
    r.add_argument("--fail-on-escalation", action="store_true", help="finish with exit code 2 if anything needs escalating")
    g = sub.add_parser("suggest", help="draft a starter rules file from a data file",
                       description="Look at a data file (missing values, types, codes, years, keys) and draft a rules "
                                   "file. Every rule is a suggestion for a data steward to review.")
    g.add_argument("data", help="the data file (CSV)")
    g.add_argument("--id", help="short asset id. Default: the file name")
    g.add_argument("--title", help="asset title")
    g.add_argument("--owner", help="organisation that owns the data")
    g.add_argument("--out", help="write the rules file here. Default: print it on screen")
    a = p.parse_args(argv)

    if a.cmd == "check":
        spec = rules.load_rules(a.rules)
        df = pd.read_csv(a.data, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
        res = rules.run(df, spec, _date(a.as_of))
        res["trust"] = trust.classify(res, spec["asset"].get("personal_data_columns"))
        res["route"] = pathway.route(spec["asset"])
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        aid = spec["asset"]["id"]
        if a.history:
            from .workbook import append_history
            append_history(res, a.history)
        if a.workbook:
            from .workbook import build
            build(spec, res, out / f"{aid}.DQAP.xlsx", a.history)
        res["operations"] = operations.assess(res, a.history)
        if a.case_study:
            d = casestudy.draft(spec, res, a.history)
            (out / f"{aid}.case-study.md").write_text(casestudy.to_markdown(d))
            casestudy.to_docx(d, out / f"{aid}.case-study.docx")
        (out / f"{aid}.results.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
        (out / f"{aid}.dqv.jsonld").write_text(json.dumps(dqv.result_to_dqv(res, spec["asset"].get("iri"), spec["asset"].get("dqap")), indent=2, ensure_ascii=False))
        d = exporters.to_dqap_csv(res)
        (out / f"{aid}.dqap-rules.csv").write_text(d["rules"])
        (out / f"{aid}.dqap-issues.csv").write_text(d["issues"])
        print(f"{aid}: {res['rules_met']}/{res['rules_total']} rules meet target; {len(res['issues'])} issue(s). Results in {out}/")
        o = res["operations"]
        print(f"  Operations: {o['open_issues']} open, {o['overdue_issues']} overdue (escalate), recurrence {o['recurrence_rate']}%, {o['cycles_measured']} cycle(s)")
        print(f"  Suggested trust level: {res['trust']['level']} ({res['trust']['sharing']}). Route: {res['route']['route']}")
        for i in res["issues"]:
            print(f"  - [{i['priority']}] {i['rule']} {i['label']} ({i['dimension']}): {i['performance']}% vs {i['target']}% -> {i['resolution']}")
        return 0
    if a.cmd == "export":
        spec = rules.load_rules(a.rules)
        print(json.dumps(exporters.to_great_expectations(spec), indent=2) if a.to == "gx" else exporters.to_r_validate(spec))
        return 0
    if a.cmd == "assess-metadata":
        recs = [json.loads(l) for l in open(a.records, encoding="utf-8") if l.strip()]
        res = metadata.assess_portfolio(recs, _date(a.as_of))
        text = json.dumps(res, indent=2, ensure_ascii=False)
        if a.out:
            Path(a.out).write_text(text)
        print(f"{len(res['pages'])} records: mean score {res['mean_score']}%, CDA metadata coverage {res['mean_cda_coverage']}%, RAG {res['rag']}")
        return 0
    if a.cmd == "run":
        from . import portfolio
        try:
            out = portfolio.run(a.portfolio, _date(a.as_of) if a.as_of else None, a.out, history=not a.no_history,
                                ignore_schedule=a.ignore_schedule)
        except portfolio.PortfolioError as e:
            print(f"Problem: {e}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Problem: {e}", file=sys.stderr)
            return 1
        t, ch = out["portfolio"]["totals"], out["portfolio"]["changes"]
        print(f"{t['assets']} asset(s), {t['assets_measured']} measured as of {out['portfolio']['as_of']}: "
              f"{t['rules_met']}/{t['rules_total']} rules meet target; {t['open_issues']} open issue(s), "
              f"{t['overdue_issues']} overdue; {len(ch['new'])} new, {len(ch['resolved'])} resolved; "
              f"{t['escalations']} escalation(s). Results in {out['out']}/")
        return 2 if a.fail_on_escalation and out["escalations"] else 0
    if a.cmd == "suggest":
        from . import profile
        src = Path(a.data)
        if not src.exists():
            print(f"Problem: data file not found: {src}", file=sys.stderr)
            return 1
        df = pd.read_csv(src, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
        aid = a.id or src.name.split(".")[0].replace("__", "-").replace("_", "-").lower()
        spec = profile.suggest(df, {"id": aid, "title": a.title, "owner": a.owner})
        text = profile.to_yaml(spec, src.name)
        if a.out:
            Path(a.out).write_text(text, encoding="utf-8")
            print(f"Draft rules file with {len(spec['rules'])} rule(s) written to {a.out}. Review every rule before use.")
        else:
            print(text)
        return 0
    if a.cmd == "survey":
        from . import survey
        orgs, sols = survey.reshape(survey.load(a.export))
        summ = survey.summarise(orgs, sols)
        d = survey.write(orgs, sols, summ, a.out)
        print(f"{summ['responses']} responses, {summ['solution_assessments']} solution assessments. Results in {d}/ (names and emails removed)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
