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

DIMENSIONS = ("completeness", "uniqueness", "consistency", "timeliness", "validity", "accuracy")
COLUMNS = (["cda_identifier", "cda_title", "owner_organisation", "gds_dqapstatus", "gds_dqapurl", "gds_dqbaselinedate"]
           + [f"gds_dq_{d}" for d in DIMENSIONS]
           + ["gds_dqrulesmet", "gds_dqrulestotal", "gds_dqissues_critical", "gds_dqissues_high", "gds_dqissues_medium",
              "gds_dqissues_low", "gds_dqinclusionassessed", "gds_dqtrustlevel", "gds_dqroute"])
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
        "gds_dqapurl": a.get("dqap", ""), "gds_dqbaselinedate": res["as_of"],
        "gds_dqrulesmet": res["rules_met"], "gds_dqrulestotal": res["rules_total"],
        "gds_dqissues_critical": pr["Critical"], "gds_dqissues_high": pr["High"],
        "gds_dqissues_medium": pr["Medium"], "gds_dqissues_low": pr["Low"],
        "gds_dqinclusionassessed": "Yes" if any(r["check"] in INCLUSION_CHECKS for r in res["results"]) else "No",
        "gds_dqtrustlevel": (res.get("trust") or {}).get("level", ""),
        "gds_dqroute": (res.get("route") or {}).get("route", ""),
    }
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
