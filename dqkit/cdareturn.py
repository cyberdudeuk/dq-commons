"""Rows for the annual critical data asset (CDA) return, in the proposed Dataverse column layout.

The departmental return workspace keeps one row per CDA. These columns (see docs/ARCHITECTURE.md,
"Mapping to the Dataverse return table") carry the data quality part of the return, so the
January baseline can be filled from measured results instead of re-keyed by hand.

Column names are a proposal (prefix gds_), not a published GDS schema. Values that can't be
measured are left blank, never guessed.
"""
from __future__ import annotations

import csv
import io

from . import qfair

DIMENSIONS = ("completeness", "uniqueness", "consistency", "timeliness", "validity", "accuracy")
COLUMNS = (["cda_identifier", "cda_title", "owner_organisation", "gds_dqapstatus", "gds_dqapurl", "gds_dqbaselinedate"]
           + [f"gds_dq_{d}" for d in DIMENSIONS]
           + ["gds_dqrulesmet", "gds_dqrulestotal", "gds_dqissues_critical", "gds_dqissues_high", "gds_dqissues_medium",
              "gds_dqissues_low", "gds_dqinclusionassessed", "gds_dqtrustlevel", "gds_dqroute"]
           # Q-FAIR (v1.6): four record fields and the five Good / Improving / Attention required ratings
           + ["gds_accessroute", "gds_conformsto", "gds_licence", "gds_provenance"]
           + [f"gds_qfair_{p}" for p in qfair.PILLARS] + ["gds_qfair_overall", "gds_baselineconfidence"]
           # v2.4: what "Identifying and recording critical data assets", the data ownership model and the DQAP guide ask
           # to be recorded. Names stay in the department's own return; the Commons never stores them.
           + ["gds_purposes", "gds_dataowner", "gds_datasteward", "gds_iao", "gds_providedto", "gds_sourcedataset",
              "gds_dqmeasurementfrequency", "gds_metadatalastreview", "gds_metadatanextreview"])
INCLUDED_PURPOSES = ("Public service delivery", "Legislative, legal or contractual requirement", "Defence, national security and resilience",
                     "Policy development and evaluation", "Official statistics", "Public interest", "Fraud and error")
INCLUSION_CHECKS = ("not_unknown", "group_disparity")


def row(res: dict) -> dict:
    a = res["asset"]
    dims = res.get("dimensions", {})
    pr = {p: 0 for p in ("Critical", "High", "Medium", "Low")}
    for i in res.get("issues", []):
        pr[i["priority"]] = pr.get(i["priority"], 0) + 1
    out = {
        "cda_identifier": a.get("iri", a["id"]), "cda_title": a.get("title", a["id"]),
        "owner_organisation": a.get("owner", ""), "gds_dqapstatus": a.get("dqap_status", "in_place"),
        "gds_dqapurl": a.get("dqap_link", a.get("dqap", "")), "gds_dqbaselinedate": res["as_of"],
        "gds_dqrulesmet": res["rules_met"], "gds_dqrulestotal": res["rules_total"],
        "gds_dqissues_critical": pr["Critical"], "gds_dqissues_high": pr["High"],
        "gds_dqissues_medium": pr["Medium"], "gds_dqissues_low": pr["Low"],
        "gds_dqinclusionassessed": "Yes" if any(r["check"] in INCLUSION_CHECKS for r in res["results"]) else "No",
        "gds_dqtrustlevel": (res.get("trust") or {}).get("level", ""),
        "gds_dqroute": (res.get("route") or {}).get("route", ""),
    }
    q = qfair.rate(res)
    out.update({"gds_accessroute": a.get("access_route", ""), "gds_conformsto": "; ".join(a.get("conforms_to") or []),
                "gds_licence": a.get("licence", ""), "gds_provenance": a.get("provenance", ""),
                "gds_qfair_overall": q["overall"]["rating"],
                # measured by rules = high; a stated value overrides (for example 'medium' when sampled)
                "gds_baselineconfidence": a.get("baseline_confidence", "high" if res.get("rules_total") else "low")})
    for p in qfair.PILLARS:
        out[f"gds_qfair_{p}"] = q[p]["rating"]
    listed = lambda v: "; ".join(v) if isinstance(v, list) else (v or "")
    out.update({"gds_purposes": listed(a.get("purposes")), "gds_dataowner": a.get("data_owner", ""), "gds_datasteward": a.get("steward", ""),
                "gds_iao": a.get("iao", ""), "gds_providedto": listed(a.get("provided_to")), "gds_sourcedataset": a.get("source_dataset", ""),
                "gds_dqmeasurementfrequency": a.get("measurement_cycle", a.get("measurement_frequency", "")),
                "gds_metadatalastreview": a.get("metadata_last_review", ""), "gds_metadatanextreview": a.get("next_review", "")})
    for d in DIMENSIONS:
        out[f"gds_dq_{d}"] = dims[d]["mean_performance"] if d in dims else ""
    return out


def to_csv(results: list) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in results:
        w.writerow(row(r))
    return buf.getvalue()
