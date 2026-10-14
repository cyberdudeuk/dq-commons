"""Command line: python -m dqkit <command> ...

  check   DATA.csv RULES.yaml [--as-of YYYY-MM-DD] [--out DIR]   run rules, write results, DQV, DQAP CSVs
  export  RULES.yaml --to gx|r-validate                          print a Great Expectations suite or R validate rules
  assess-metadata RECORDS.jsonl [--as-of YYYY-MM-DD] [--out FILE] assess catalogue records against GOV.UK requirements
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from . import dqv, exporters, metadata, rules


def _date(s):
    return date.fromisoformat(s) if s else date.today()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="dqkit", description="Data quality assurance kit (GOV.UK DQAP and issues framework)")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("data"); c.add_argument("rules"); c.add_argument("--as-of"); c.add_argument("--out", default="dq-results")
    e = sub.add_parser("export")
    e.add_argument("rules"); e.add_argument("--to", choices=["gx", "r-validate"], required=True)
    m = sub.add_parser("assess-metadata")
    m.add_argument("records"); m.add_argument("--as-of"); m.add_argument("--out")
    a = p.parse_args(argv)

    if a.cmd == "check":
        spec = rules.load_rules(a.rules)
        df = pd.read_csv(a.data, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
        res = rules.run(df, spec, _date(a.as_of))
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        aid = spec["asset"]["id"]
        (out / f"{aid}.results.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
        (out / f"{aid}.dqv.jsonld").write_text(json.dumps(dqv.result_to_dqv(res, spec["asset"].get("iri"), spec["asset"].get("dqap")), indent=2, ensure_ascii=False))
        d = exporters.to_dqap_csv(res)
        (out / f"{aid}.dqap-rules.csv").write_text(d["rules"])
        (out / f"{aid}.dqap-issues.csv").write_text(d["issues"])
        print(f"{aid}: {res['rules_met']}/{res['rules_total']} rules meet target; {len(res['issues'])} issue(s). Results in {out}/")
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
    return 1


if __name__ == "__main__":
    sys.exit(main())
