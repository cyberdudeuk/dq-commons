"""Test the National Data Library's own curated collections against GOV.UK DAM policy and DQ guidance.

Inputs:  assessments/ndl/harvest.jsonl      (84 curated data pages, harvested 14 Oct 2026)
         assessments/ndl/chart-data/*.csv   (NDL's own chart data downloads, sampled)
         rules/ndl/*.yaml                   (data quality rules for each chart file)
Outputs: assessments/ndl/results/          (JSON, DQV JSON-LD, DQAP CSVs, summary for the dashboard)
Run:     python scripts/run_ndl_assessment.py
"""
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import dqv, exporters, metadata, pathway, rules, trust, workbook  # noqa: E402

AS_OF = date(2026, 10, 14)
A = ROOT / "assessments" / "ndl"
OUT = A / "results"
OUT.mkdir(parents=True, exist_ok=True)

CHARTS = {  # rules file -> chart data file
    "births.yaml": "people__births.csv",
    "childhood-vaccinations.yaml": "early-years__childhood-vaccinations.csv",
    "road-traffic.yaml": "transport__road-traffic.csv",
    "air-quality.yaml": "environment__air-quality.csv",
    "election-results.yaml": "government-and-parliament__election-results.csv",
    "mot-results.yaml": "transport__mot-results.csv",
    "council-tax.yaml": "government-and-parliament__council-tax-statistics.csv",
    "social-mobility.yaml": "people__social-mobility.csv",
}

records = [json.loads(l) for l in open(A / "harvest.jsonl", encoding="utf-8") if l.strip()]
portfolio = metadata.assess_portfolio(records, AS_OF)
(OUT / "metadata-assessment.json").write_text(json.dumps(portfolio, indent=2, ensure_ascii=False))

# DQV JSON-LD for every page: metadata checks expressed as quality measurements
pages_dqv = []
for p in portfolio["pages"]:
    res = {"asset": {"id": f"ndl-{p['collection']}-{p['slug']}", "title": p["title"], "owner": p["provider"]},
           "as_of": portfolio["as_of"],
           "results": [{"id": c["id"], "description": c["label"], "dimension": c["dimension"], "issue_type": c["issue_type"],
                        "performance": metadata.SCORE.get(c["status"], 1.0) * 100, "checked": 1,
                        "assessment": {"target": 100.0, "meets_target": c["status"] in ("pass", "n/a"),
                                       "priority": None if c["status"] in ("pass", "n/a") else ("High" if c["impact"] >= 3 else "Medium" if c["impact"] == 2 else "Low"),
                                       "resolution": None}} for c in p["checks"]]}
    pages_dqv.append(dqv.result_to_dqv(res, asset_iri=p["url"]))
(OUT / "ndl-pages.dqv.jsonld").write_text(json.dumps({"@context": dqv.CONTEXT, "@graph": [n for d in pages_dqv for n in d["@graph"]]}, indent=1, ensure_ascii=False))

charts = []
for rf, cf in CHARTS.items():
    spec = rules.load_rules(ROOT / "rules" / "ndl" / rf)
    df = pd.read_csv(A / "chart-data" / cf, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
    res = rules.run(df, spec, AS_OF)
    res["trust"] = trust.classify(res)
    res["route"] = pathway.route(spec["asset"])
    aid = spec["asset"]["id"]
    workbook.build(spec, res, OUT / "dqap-workbooks" / f"{aid}.DQAP.xlsx")
    (OUT / f"{aid}.results.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    (OUT / f"{aid}.dqv.jsonld").write_text(json.dumps(dqv.result_to_dqv(res, spec["asset"].get("iri")), indent=2, ensure_ascii=False))
    d = exporters.to_dqap_csv(res)
    (OUT / f"{aid}.dqap-rules.csv").write_text(d["rules"])
    (OUT / f"{aid}.dqap-issues.csv").write_text(d["issues"])
    (OUT / f"{aid}.gx-suite.json").write_text(json.dumps(exporters.to_great_expectations(spec), indent=2))
    (OUT / f"{aid}.validate.yaml").write_text(exporters.to_r_validate(spec))
    charts.append({"id": aid, "title": spec["asset"]["title"], "url": spec["asset"].get("iri"), "rows": res["rows"],
                   "rules_total": res["rules_total"], "rules_met": res["rules_met"], "issues": res["issues"],
                   "trust": {k: res["trust"][k] for k in ("level", "sharing", "reasons")}, "route": res["route"]["route"],
                   "results": [{k: r[k] for k in ("id", "description", "dimension", "performance", "detail", "examples")} | {"target": r["assessment"]["target"], "meets": r["assessment"]["meets_target"], "priority": r["assessment"]["priority"]} for r in res["results"]]})

summary = {
    "as_of": portfolio["as_of"], "pages": len(portfolio["pages"]), "mean_score": portfolio["mean_score"],
    "mean_cda_coverage": portfolio["mean_cda_coverage"], "rag": portfolio["rag"], "collections": portfolio["collections"],
    "cda_property_coverage": portfolio["cda_property_coverage"],
    "checks": [{k: c[k] for k in ("id", "label", "source", "dimension", "issue_type", "applicable", "pass", "partial", "fail", "performance")}
               | {"priority": c["assessment"]["priority"], "target": c["assessment"]["target"], "resolution": c["assessment"]["resolution"]}
               for c in portfolio["checks"]],
    "page_scores": [{k: p[k] for k in ("collection", "slug", "title", "provider", "url", "score", "rag", "cda_metadata_coverage")}
                    | {"fails": [c["id"] for c in p["checks"] if c["status"] == "fail"],
                       "partials": [c["id"] for c in p["checks"] if c["status"] == "partial"],
                       "evidence": {c["id"]: c["evidence"] for c in p["checks"]}} for p in portfolio["pages"]],
    "charts": charts,
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
print(f"Pages: {summary['pages']}  mean score {summary['mean_score']}%  CDA metadata coverage {summary['mean_cda_coverage']}%  RAG {summary['rag']}")
for c in summary["checks"]:
    print(f"  {c['id']:7} {c['performance']:5.1f}%  {c['priority'] or 'meets':8} {c['label']}")
for ch in charts:
    print(f"CHART {ch['id']}: {ch['rules_met']}/{ch['rules_total']} met; trust {ch['trust']['level']}; issues: " + "; ".join(f"{i['rule']} {i['label']} [{i['priority']}]" for i in ch["issues"]))
