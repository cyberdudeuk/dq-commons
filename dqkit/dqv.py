"""Publish quality results as W3C Data Quality Vocabulary (DQV) JSON-LD.

DQV (https://www.w3.org/TR/vocab-dqv/) sits alongside DCAT, which the UK
cross-government metadata exchange model already uses. This is the mechanism
proposed in decision D-014: quality travels with the asset's metadata.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .rules import ISSUE_TYPES, VOCAB_DIR

BASE = "https://cyberdudeuk.github.io/ndl-dq-assurance/vocab#"

CONTEXT = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "dqv": "http://www.w3.org/ns/dqv#",
    "prov": "http://www.w3.org/ns/prov#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "oa": "http://www.w3.org/ns/oa#",
    "ndq": BASE,
    "value": {"@id": "dqv:value", "@type": "xsd:decimal"},
    "measuredOn": {"@id": "dct:date", "@type": "xsd:date"},
}


def _dimensions() -> dict:
    with open(VOCAB_DIR / "dimensions.csv", newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def result_to_dqv(result: dict, asset_iri: str | None = None, dqap_iri: str | None = None) -> dict:
    asset = result["asset"]
    iri = asset_iri or asset.get("iri") or f"{BASE}asset/{asset['id']}"
    measurements, annotations, metrics = [], [], {}
    for r in result["results"]:
        metric_iri = f"{BASE}metric/{asset['id']}/{r['id']}"
        metrics[metric_iri] = {
            "@id": metric_iri, "@type": "dqv:Metric", "skos:prefLabel": r["description"],
            "dqv:expectedDataType": {"@id": "xsd:decimal"},
            "dqv:inDimension": {"@id": f"ndq:{r['dimension']}"},
        }
        measurements.append({
            "@id": f"{iri}#m-{r['id']}", "@type": "dqv:QualityMeasurement",
            "dqv:computedOn": {"@id": iri}, "dqv:isMeasurementOf": {"@id": metric_iri},
            "value": r["performance"], "measuredOn": result["as_of"],
            "ndq:target": r["assessment"]["target"], "ndq:meetsTarget": r["assessment"]["meets_target"],
            "ndq:recordsChecked": r["checked"],
        })
        if not r["assessment"]["meets_target"]:
            it = ISSUE_TYPES[r["issue_type"]]
            annotations.append({
                "@id": f"{iri}#issue-{r['id']}", "@type": "dqv:QualityAnnotation",
                "oa:hasTarget": {"@id": iri}, "oa:motivatedBy": {"@id": "dqv:qualityAssessment"},
                "oa:hasBody": {"@type": "oa:TextualBody", "oa:value": f"{it['label']}: {it['definition']}"},
                "ndq:issueType": {"@id": f"ndq:issue/{r['issue_type']}"},
                "ndq:priority": r["assessment"]["priority"], "ndq:resolution": r["assessment"]["resolution"],
                "ndq:responsibility": it["responsibility"],
            })
    dims = _dimensions()
    graph = [{
        "@id": iri, "@type": "dcat:Dataset", "dct:title": asset.get("title", asset["id"]),
        **({"dct:publisher": asset["owner"]} if asset.get("owner") else {}),
        **({"ndq:dataQualityActionPlan": {"@id": dqap_iri}} if dqap_iri else {}),
        "dqv:hasQualityMeasurement": [{"@id": m["@id"]} for m in measurements],
        "dqv:hasQualityAnnotation": [{"@id": a["@id"]} for a in annotations],
    }]
    graph += measurements + annotations + list(metrics.values())
    graph += [{"@id": f"ndq:{k}", "@type": "dqv:Dimension", "skos:prefLabel": v["label"],
               "skos:definition": v["definition"], "dqv:inCategory": {"@id": "ndq:GovernmentDataQualityFramework"}}
              for k, v in dims.items() if any(r["dimension"] == k for r in result["results"])]
    return {"@context": CONTEXT, "@graph": graph}
