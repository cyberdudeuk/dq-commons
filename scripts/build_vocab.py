"""Build SKOS Turtle and JSON-LD from vocab/*.csv. Run: python scripts/build_vocab.py"""
import csv, json
from pathlib import Path

V = Path(__file__).resolve().parent.parent / "vocab"
BASE = "https://cyberdudeuk.github.io/ndl-dq-assurance/vocab#"
dims = list(csv.DictReader(open(V / "dimensions.csv", encoding="utf-8")))
issues = list(csv.DictReader(open(V / "issue-types.csv", encoding="utf-8")))

def lit(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"@en'

ttl = ["@prefix skos: <http://www.w3.org/2004/02/skos/core#> .", "@prefix dqv: <http://www.w3.org/ns/dqv#> .",
       "@prefix dct: <http://purl.org/dc/terms/> .", f"@prefix ndq: <{BASE}> .", "",
       "ndq:GovernmentDataQualityFramework a dqv:Category, skos:ConceptScheme ;",
       '    skos:prefLabel "Data quality dimensions (DAMA UK, Government Data Quality Framework, plus extensions)"@en ;',
       "    dct:license <https://opensource.org/licenses/MIT> .", "",
       "ndq:IssueTypes a skos:ConceptScheme ;", '    skos:prefLabel "Cross-government data quality issue types"@en ;',
       '    dct:source "MHCLG planning data specification, GOV.UK DAM policy and DQAP guidance, NHS England QAFDL"@en .', ""]
for d in dims:
    ttl += [f"ndq:{d['id']} a dqv:Dimension, skos:Concept ;", f"    skos:inScheme ndq:GovernmentDataQualityFramework ;",
            f"    dqv:inCategory ndq:GovernmentDataQualityFramework ;", f"    skos:prefLabel {lit(d['label'])} ;",
            f"    skos:definition {lit(d['definition'])} ;", f"    dct:source {lit(d['source'])} .", ""]
for i in issues:
    t = [f"<{BASE}issue/{i['id']}> a skos:Concept ;", "    skos:inScheme ndq:IssueTypes ;",
         f"    skos:prefLabel {lit(i['label'])} ;", f"    skos:definition {lit(i['definition'])} ;",
         f"    skos:broader ndq:{i['dimension']} ;", f"    ndq:appliesTo {lit(i['applies_to'])} ;",
         f"    ndq:defaultImpact {i['default_impact']} ;", f"    ndq:responsibility {lit(i['responsibility'])} ;"]
    if i["mhclg_equivalent"]:
        t.append(f"    skos:closeMatch {lit(i['mhclg_equivalent'])} ;")
    t.append(f"    dct:source {lit(i['source'])} .")
    ttl += t + [""]
(V / "dq-vocab.ttl").write_text("\n".join(ttl), encoding="utf-8")

graph = [{"@id": f"ndq:{d['id']}", "@type": ["dqv:Dimension", "skos:Concept"], "skos:prefLabel": d["label"],
          "skos:definition": d["definition"], "dct:source": d["source"]} for d in dims]
graph += [{"@id": f"ndq:issue/{i['id']}", "@type": "skos:Concept", "skos:inScheme": {"@id": "ndq:IssueTypes"},
           "skos:prefLabel": i["label"], "skos:definition": i["definition"], "skos:broader": {"@id": f"ndq:{i['dimension']}"},
           "ndq:appliesTo": i["applies_to"], "ndq:defaultImpact": int(i["default_impact"]),
           "ndq:responsibility": i["responsibility"], "dct:source": i["source"],
           **({"skos:closeMatch": i["mhclg_equivalent"]} if i["mhclg_equivalent"] else {})} for i in issues]
doc = {"@context": {"skos": "http://www.w3.org/2004/02/skos/core#", "dqv": "http://www.w3.org/ns/dqv#",
                    "dct": "http://purl.org/dc/terms/", "ndq": BASE}, "@graph": graph}
(V / "dq-vocab.jsonld").write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(dims)} dimensions, {len(issues)} issue types written")
