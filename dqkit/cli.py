"""Command line: python -m dqkit <command> ...

  check   DATA RULES.yaml [--as-of YYYY-MM-DD] [--out DIR] [--history DIR] [--workbook] [--case-study]
          run rules; write results, DQV, DQAP CSVs, trust level and (optionally) a filled DQAP Excel workbook
  export  RULES.yaml --to gx|r-validate                          print a Great Expectations suite or R validate rules
  reconcile SOURCE TARGET --key ID[,ID2] [--tolerance N]   compare two versions of a dataset (migration checks)
  contract RULES.yaml --to table-schema|odcs|csvw  |  CONTRACT --from table-schema|odcs
          convert rules to or from open data contract standards
  contract-check CONTRACT [--against OLD_CONTRACT]   check an ODCS contract; with --against, list changes and breaking ones
  graph   [--format json|jsonld|ttl] [--find TEXT] [--from A --to B]
          the knowledge graph: export it, find concepts, or trace the relationships between two concepts
  weave   RECORD.json [--from dcat|schema|ckan|odcs] [--to dcat|schema|ckan|odcs|all] [--report]
          read one metadata record and write it as DCAT v3, schema.org, CKAN and ODCS, with gaps and CDA coverage
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
import yaml

from . import casestudy, contracts, weaver, dqv, exporters, metadata, operations, pathway, rules, sources, trust


def _source_args(parser):
    parser.add_argument("--type", choices=["csv", "tsv", "xlsx", "xlsm", "ods", "json", "jsonl", "parquet", "sqlite"],
                        help="kind of data file, if the extension doesn't say")
    parser.add_argument("--sheet", help="spreadsheet sheet name or number (first sheet if left out)")
    parser.add_argument("--table", help="SQLite table to read")
    parser.add_argument("--query", help="read-only SELECT query for a SQLite file")


def _source(a):
    """A data source from the command line: a path, plus optional --type, --sheet, --table, --query."""
    extra = {k: getattr(a, k) for k in ("sheet", "table", "query") if getattr(a, k, None) not in (None, "")}
    if getattr(a, "type", None) or extra:
        src = sources.normalise({"type": a.type, "path": a.data} if getattr(a, "type", None) else a.data)
        if isinstance(src.get("sheet"), str) and src["sheet"].isdigit():
            src["sheet"] = int(src["sheet"])
        src.update(extra)
        if isinstance(src.get("sheet"), str) and src["sheet"].isdigit():
            src["sheet"] = int(src["sheet"])
        return src
    return a.data


def _date(s):
    return date.fromisoformat(s) if s else date.today()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="dqkit", description="Data quality assurance kit (GOV.UK DQAP and issues framework)",
                                epilog="Run 'python -m dqkit COMMAND --help' for help on one command.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("data"); c.add_argument("rules"); c.add_argument("--as-of"); c.add_argument("--out", default="dq-results")
    c.add_argument("--history", help="folder that keeps each run, so results show trends over time")
    _source_args(c)
    c.add_argument("--workbook", action="store_true", help="also write a filled-in DQAP workbook (.xlsx)")
    c.add_argument("--case-study", action="store_true", help="also draft a GDS-style case study (.md and .docx)")
    e = sub.add_parser("export")
    e.add_argument("rules"); e.add_argument("--to", choices=["gx", "r-validate"], required=True)
    ct = sub.add_parser("contract", help="convert rules to or from a data contract: Frictionless Table Schema, ODCS v3 or W3C CSVW")
    ct.add_argument("file", help="a rules file (with --to) or a contract file (with --from)")
    ct.add_argument("--to", choices=sorted(contracts.FORMATS))
    ct.add_argument("--from", dest="src", choices=["table-schema", "odcs"])
    cc = sub.add_parser("contract-check", help="check an ODCS contract, and compare it with an earlier version")
    cc.add_argument("file"); cc.add_argument("--against", help="the earlier version of the contract")
    gr = sub.add_parser("graph", help="the knowledge graph: export, find, or trace a path")
    gr.add_argument("--format", default="json", choices=["json", "jsonld", "ttl"])
    gr.add_argument("--find"); gr.add_argument("--from", dest="frm"); gr.add_argument("--to")
    wv = sub.add_parser("weave", help="Metadata Weaver: one record in, every catalogue standard out, with gaps")
    wv.add_argument("file"); wv.add_argument("--from", dest="src", choices=list(weaver.READERS))
    wv.add_argument("--to", default="all", choices=list(weaver.TARGETS) + ["all"])
    wv.add_argument("--report", action="store_true", help="print the gap and CDA report instead of the records")
    rc = sub.add_parser("reconcile", help="compare two versions of a dataset: counts, keys, totals and values")
    rc.add_argument("source"); rc.add_argument("target")
    rc.add_argument("--key", required=True, help="key column(s), comma separated")
    rc.add_argument("--tolerance", type=float, default=0.0, help="allowed difference in column totals")
    m = sub.add_parser("assess-metadata")
    m.add_argument("records"); m.add_argument("--as-of"); m.add_argument("--out")
    pk = sub.add_parser("pack", help="framework and scenario packs: list them, or assess results against one")
    pk.add_argument("action", choices=["list", "assess"])
    pk.add_argument("results", nargs="?", help="a *.results.json file (for assess)")
    pk.add_argument("--pack", help="pack id, for example uk-dam-cda")
    cw = sub.add_parser("crosswalk", help="restate results in another framework's dimensions, or list frameworks")
    cw.add_argument("results", nargs="?", help="a *.results.json file")
    cw.add_argument("--to", help="framework id from knowledge/frameworks.yaml, for example iso-iec-25012")
    cw.add_argument("--list", action="store_true", help="list the frameworks in the registry")
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
    g.add_argument("data", help="the data: a file (CSV, TSV, XLSX, ODS, JSON, JSONL, Parquet, SQLite)")
    _source_args(g)
    g.add_argument("--id", help="short asset id. Default: the file name")
    g.add_argument("--title", help="asset title")
    g.add_argument("--owner", help="organisation that owns the data")
    g.add_argument("--out", help="write the rules file here. Default: print it on screen")
    a = p.parse_args(argv)

    if a.cmd == "check":
        spec = rules.load_rules(a.rules)
        try:
            df = sources.read(_source(a))
        except sources.SourceError as e:
            print(f"Problem: {e}", file=sys.stderr)
            return 1
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
    if a.cmd == "contract":
        if bool(a.to) == bool(a.src):
            print("Give exactly one of --to or --from.", file=sys.stderr)
            return 2
        if a.to:
            print(json.dumps(contracts.FORMATS[a.to](rules.load_rules(a.file)), indent=2, ensure_ascii=False))
            return 0
        doc = yaml.safe_load(Path(a.file).read_text(encoding="utf-8"))
        spec = contracts.from_odcs(doc) if a.src == "odcs" else contracts.from_table_schema(doc)
        rules.validate_spec(spec)
        for u in (contracts.unsupported(doc) if a.src == "odcs" else []):
            print(f"# not imported ({u['type']}): {u['id']} {u['description']}", file=sys.stderr)
        print(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        return 0
    if a.cmd == "contract-check":
        doc = yaml.safe_load(Path(a.file).read_text(encoding="utf-8"))
        probs = contracts.validate_odcs(doc)
        out = {"problems": probs}
        if a.against:
            out["diff"] = contracts.diff_odcs(yaml.safe_load(Path(a.against).read_text(encoding="utf-8")), doc)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        bad = any(p["level"] == "error" for p in probs) or (a.against and out["diff"]["version_ok"] is False)
        return 1 if bad else 0
    if a.cmd == "graph":
        from . import graph
        g = graph.build()
        if a.find:
            for n in graph.find(g, a.find):
                print(f"{n['id']}\t{n['label']}")
            return 0
        if a.frm and a.to:
            pick = lambda v: v if any(n["id"] == v for n in g["nodes"]) else ((graph.find(g, v, 1) or [{}])[0].get("id"))
            ch = graph.path(g, pick(a.frm), pick(a.to)) if pick(a.frm) and pick(a.to) else []
            print(" -> ".join(ch) if ch else "No path found.")
            return 0 if ch else 1
        print(graph.to_turtle(g) if a.format == "ttl" else json.dumps(graph.to_jsonld(g) if a.format == "jsonld" else
              {k: g[k] for k in ("nodes", "edges", "stats")}, indent=1, ensure_ascii=False))
        return 0
    if a.cmd == "weave":
        rec = yaml.safe_load(Path(a.file).read_text(encoding="utf-8"))
        try:
            w = weaver.weave(rec, a.src)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        if a.report:
            print(json.dumps({"source_format": w["source_format"], "coverage": w["coverage"], "cda": w["cda"]}, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(w["outputs"] if a.to == "all" else w["outputs"][a.to], indent=2, ensure_ascii=False))
        return 0
    if a.cmd == "reconcile":
        from .reconcile import reconcile
        r = reconcile(sources.read(a.source), sources.read(a.target), [k.strip() for k in a.key.split(",") if k.strip()], a.tolerance)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        print(("PASSED" if r["passed"] else "DIFFERENCES FOUND") + f": {r['rows']['source']} source rows, {r['rows']['target']} target rows, "
              f"{r['only_in_source']['count']} missing from target, {r['only_in_target']['count']} new in target, "
              f"{sum(m['count'] for m in r['mismatches'])} value differences.", file=sys.stderr)
        return 0 if r["passed"] else 1
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
        try:
            df = sources.read(_source(a))
        except sources.SourceError as e:
            print(f"Problem: {e}", file=sys.stderr)
            return 1
        aid = a.id or src.name.split(".")[0].replace("__", "-").replace("_", "-").lower()
        spec = profile.suggest(df, {"id": aid, "title": a.title, "owner": a.owner})
        text = profile.to_yaml(spec, src.name)
        if a.out:
            Path(a.out).write_text(text, encoding="utf-8")
            print(f"Draft rules file with {len(spec['rules'])} rule(s) written to {a.out}. Review every rule before use.")
        else:
            print(text)
        return 0
    if a.cmd == "pack":
        from . import packs
        if a.action == "list":
            for pk_ in packs.list_packs():
                print(f"{pk_['id']:28} {pk_['name']}")
            return 0
        if not (a.results and a.pack):
            print("Problem: give a results file and --pack", file=sys.stderr)
            return 1
        try:
            out = packs.assess(a.pack, json.loads(Path(a.results).read_text(encoding="utf-8")))
        except (ValueError, OSError) as e:
            print(f"Problem: {e}", file=sys.stderr)
            return 1
        print(f"{out['name']}: {out['coverage']}% of automatically checkable requirements met "
              f"({out['met']} met, {out['partly']} partly, {out['not_met']} not met, {out['manual']} to confirm by hand)")
        for r in out["requirements"]:
            print(f"  [{r['status']}] {r['id']} {r['text']} - {r['reason']}")
        if "index" in out:
            print(f"  DQMI-style index: {out['index']['index']} ({out['index']['note']})")
        return 0
    if a.cmd == "crosswalk":
        from . import packs
        if a.list or not a.results:
            for f in packs.registry():
                print(f"{f['id']:32} {f['jurisdiction']:16} {f['name']}")
            return 0
        try:
            out = packs.convert(json.loads(Path(a.results).read_text(encoding="utf-8")), a.to)
        except (ValueError, OSError, TypeError) as e:
            print(f"Problem: {e}", file=sys.stderr)
            return 1
        print(f"{out['asset']} in {out['name']} terms:")
        for r in out["dimensions"]:
            score = "" if r["score"] is None else f"{r['score']}%"
            print(f"  {r['dimension']:40} {score:>7}  {r['status']}")
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
