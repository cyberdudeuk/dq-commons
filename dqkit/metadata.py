"""Assess a catalogue record against published GOV.UK requirements.

Each check cites the requirement it tests. Sources:
- DAM  = Data asset management policy in government (GDS, 27 May 2026)
- CDA  = Recording metadata to describe critical data assets (GDS, 16 April 2026)
- DQAP = Implementing a data quality action plan, and the issues framework (GDS, 2026)
- NDL  = National Data Library data curation criteria (data.gov.uk/data-curation)
- FAIR = FAIR principles, scored the way the EU Metadata Quality Assessment does
- INC  = Inclusion checks added by this project (see docs/EQUALITY-AND-DATA-PROTECTION-SCREENING.md)

A record is a dict with the keys produced by the NDL harvest (assessments/ndl/harvest.jsonl).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional
from urllib.parse import urlparse

from . import framework
from .rules import ISSUE_TYPES

PASS, PARTIAL, FAIL, NA = "pass", "partial", "fail", "n/a"
SCORE = {PASS: 1.0, PARTIAL: 0.5, FAIL: 0.0}

OPEN_MACHINE = {"CSV", "JSON", "XML", "API", "GEOJSON", "GPKG", "GEOPACKAGE", "ODS", "PARQUET", "SHP", "SHAPEFILE",
                "KML", "GML", "ATOM", "GEOTIFF", "TXT", "RDS"}
PROPRIETARY_STRUCTURED = {"XLSX", "XLS", "EXCEL", "GDB", "LYR", "ECW", "ZIP"}
PUBLIC_SECTOR_SUFFIXES = (".gov.uk", ".nhs.uk", ".parliament.uk", ".gov.scot", ".gov.wales", ".nhs.scot", ".nhs.wales",
                          ".hscni.net", "legislation.gov.uk", "bankofengland.co.uk", "ordnancesurvey.co.uk",
                          "nationalarchives.gov.uk", "publichealthscotland.scot", "nidirect.gov.uk", "sepa.org.uk",
                          "naturalresources.wales", "ros.gov.uk", "nisra.gov.uk", "ukhsa-dashboard.data.gov.uk",
                          "growingupinscotland.org.uk", "education-ni.gov.uk", "health-ni.gov.uk", "phw.nhs.wales")
PEOPLE_COLLECTIONS = {"people", "early-years"}


def parse_uk_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return None


def _domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _is_public_sector(url: str) -> bool:
    d = _domain(url)
    return any(d == s.lstrip(".") or d.endswith("." + s.lstrip(".")) for s in PUBLIC_SECTOR_SUFFIXES)


@dataclass
class Check:
    id: str
    label: str
    source: str
    issue_type: str
    test: Callable[[dict, date], tuple[str, str]]  # returns (status, evidence)

    @property
    def impact(self) -> int:
        return int(ISSUE_TYPES[self.issue_type]["default_impact"])

    @property
    def dimension(self) -> str:
        return ISSUE_TYPES[self.issue_type]["dimension"]


# ---------- the checks ----------

def t_owner(r, _):
    return (PASS, r["provider_stated"]) if r.get("provider_stated") else (FAIL, "No data provider or owner organisation named on the page")


def t_owner_role(r, _):
    return FAIL, "No named owner role or contact for the asset is shown (policy requires a named data owner for each asset)"


def t_dqap(r, _):
    if r.get("methodology_link"):
        return PASS, "Methodology or quality information linked"
    if r.get("quality_caveats"):
        return PARTIAL, "Limitations described, but no DQAP, quality statement or methodology linked"
    return FAIL, "No DQAP, quality statement, methodology or caveats"


def t_review(r, as_of):
    d = parse_uk_date(r.get("last_updated"))
    if not d:
        return FAIL, "No last-updated date"
    age = (as_of - d).days
    return (PASS if age <= 365 else FAIL), f"Page last updated {d.isoformat()} ({age} days ago)"


def t_recent(r, as_of):
    d = parse_uk_date(r.get("last_updated"))
    if not d:
        return FAIL, "No last-updated date"
    age = (as_of - d).days
    if age <= 183:
        return PASS, f"Checked {age} days ago"
    return (PARTIAL if age <= 365 else FAIL), f"Last checked {age} days ago; curation asks for up-to-date data"


def t_classification(r, _):
    return FAIL, "Security classification not stated (open data is OFFICIAL, but the record should say so)"


def t_frequency(r, _):
    return (PASS, r["update_frequency"]) if r.get("update_frequency") else (FAIL, "Update frequency not stated")


def t_link_publishers(r, _):
    links = r.get("get_the_data") or []
    if not links:
        return FAIL, "No data links"
    named = sum(1 for l in links if l.get("publisher_stated"))
    if named == len(links):
        return PASS, f"All {len(links)} links name a publisher"
    return (PARTIAL if named else FAIL), f"{named} of {len(links)} links name a publisher"


def t_authoritative(r, _):
    links = r.get("get_the_data") or []
    if not links:
        return FAIL, "No data links"
    gov = [l["url"] for l in links if _is_public_sector(l["url"])]
    other = sorted({_domain(l["url"]) for l in links if not _is_public_sector(l["url"])})
    if len(gov) == len(links):
        return PASS, "All links go to public sector websites"
    return (PARTIAL if gov else FAIL), "Some links go to non-government hosts: " + ", ".join(other)


def t_temporal(r, _):
    return (PASS, r["time_period"]) if r.get("time_period") else (FAIL, "Time period covered not stated (temporalCoverage)")


def t_geography(r, _):
    return (PASS, r["geography"]) if r.get("geography") else (FAIL, "Geography covered not stated")


def t_caveats(r, _):
    return (PASS, r["quality_caveats"]) if r.get("quality_caveats") else (FAIL, "No limitations or caveats described")


def t_methodology(r, _):
    return (PASS, "Methodology linked") if r.get("methodology_link") else (FAIL, "No methodology link")


def _formats(r) -> set:
    f = {str(x).upper().strip() for x in (r.get("formats_mentioned") or [])}
    if r.get("api_available"):
        f.add("API")
    return f


def t_machine_readable(r, _):
    f = _formats(r)
    if f & OPEN_MACHINE:
        return PASS, "Open machine-readable: " + ", ".join(sorted(f & OPEN_MACHINE))
    if f & PROPRIETARY_STRUCTURED:
        return PARTIAL, "Structured but proprietary only: " + ", ".join(sorted(f & PROPRIETARY_STRUCTURED))
    return FAIL, ("Formats: " + ", ".join(sorted(f))) if f else "No format stated"


def t_api(r, _):
    return (PASS, "API offered") if r.get("api_available") else (FAIL, "No API")


def t_licence(r, _):
    return PARTIAL, "Only the site-wide Open Government Licence notice applies; the asset's own licence is not stated"


def t_schema(r, _):
    labels = " ".join(l.get("label", "") for l in r.get("get_the_data") or []).lower()
    if re.search(r"schema|data dictionary|documentation|api doc|guides", labels):
        return PASS, "Schema or documentation linked"
    if r.get("api_available"):
        return PARTIAL, "API offered; no schema or data dictionary linked from the page"
    return FAIL, "No schema, standard or data dictionary declared (conformsTo)"


def t_breakdowns(r, _):
    if r.get("collection") not in PEOPLE_COLLECTIONS:
        return NA, "Not data about people"
    b = r.get("protected_characteristics_breakdowns") or []
    return (PASS, "Breakdowns: " + ", ".join(b)) if b else (FAIL, "Page does not say which groups of people can be compared")


def t_nations(r, _):
    geo = (r.get("geography") or "").lower()
    if not geo or "uk" in geo.split() or "united kingdom" in geo or "great britain" in geo or "national" in geo:
        return NA, "UK-wide or not stated"
    labels = " ".join(l.get("label", "") for l in r.get("get_the_data") or []).lower()
    covered = [n for n in ("scotland", "wales", "northern ireland") if n in geo or n in labels]
    missing = [n for n in ("scotland", "wales", "northern ireland") if n not in covered]
    if not missing:
        return PASS, "All UK nations covered or signposted"
    return (PARTIAL if covered else FAIL), "Not signposted: " + ", ".join(m.title() for m in missing)


def t_content(r, _):
    return (FAIL, r["page_issue"]) if r.get("page_issue") else (PASS, "No content error found")


CHECKS: list[Check] = [
    Check("DAM-1", "Owner organisation named", "DAM", "owner-missing", t_owner),
    Check("DAM-2", "Accountable data owner role shown", "DAM", "owner-missing", t_owner_role),
    Check("DAM-3", "DQAP or equivalent linked", "DAM / DQAP", "dqap-missing", t_dqap),
    Check("DAM-4", "Reviewed in the last 12 months", "DAM / CDA", "review-overdue", t_review),
    Check("CDA-1", "Security classification stated", "CDA", "classification-missing", t_classification),
    Check("CDA-2", "Time period stated (temporalCoverage)", "CDA", "temporal-coverage-missing", t_temporal),
    Check("CDA-3", "Licence stated for the asset", "CDA", "licence-not-specific", t_licence),
    Check("CDA-4", "Schema or standard declared (conformsTo)", "CDA", "schema-not-declared", t_schema),
    Check("NDL-1", "Up to date (checked in the last 6 months)", "NDL", "review-overdue", t_recent),
    Check("NDL-2", "Update frequency stated", "NDL", "frequency-missing", t_frequency),
    Check("NDL-3", "Every data link names its publisher", "NDL", "link-publisher-missing", t_link_publishers),
    Check("NDL-4", "Links go to authoritative public sector sources", "NDL", "link-publisher-missing", t_authoritative),
    Check("DQ-1", "Geography stated", "DQAP", "geography-missing", t_geography),
    Check("DQ-2", "Quality caveats stated", "DQAP", "caveats-missing", t_caveats),
    Check("DQ-3", "Methodology linked", "DQAP", "methodology-missing", t_methodology),
    Check("FAIR-1", "Open machine-readable format offered", "FAIR", "not-machine-readable", t_machine_readable),
    Check("FAIR-2", "API offered", "FAIR", "no-api", t_api),
    Check("INC-1", "People breakdowns stated", "INC", "breakdowns-not-stated", t_breakdowns),
    Check("INC-2", "Other UK nations signposted", "INC", "nations-not-covered", t_nations),
    Check("QA-1", "No factual errors on the page", "Content", "content-error", t_content),
]

# CDA metadata properties (GOV.UK guidance) and how each is evidenced on an NDL page.
CDA_PROPERTIES = [
    ("title", lambda r: PASS if r.get("title") else FAIL),
    ("description", lambda r: PASS if len(r.get("description") or "") >= 40 else PARTIAL),
    ("creator", lambda r: PASS if r.get("provider_stated") else FAIL),
    ("dateCreated", lambda r: FAIL),
    ("identifier", lambda r: PARTIAL),  # a stable page URL, not a dataset identifier
    ("expires", lambda r: FAIL),
    ("supersededBy", lambda r: FAIL),
    ("temporalCoverage", lambda r: PASS if r.get("time_period") else FAIL),
    ("conformsTo", lambda r: {PASS: PASS, PARTIAL: PARTIAL, FAIL: FAIL}[t_schema(r, None)[0]]),
    ("securityClassification", lambda r: FAIL),
    ("accessRights", lambda r: PASS if r.get("quality_caveats") and re.search(r"paid|charged|restricted|licen", r["quality_caveats"], re.I) else PARTIAL),
    ("licence", lambda r: PARTIAL),
    ("mediaType", lambda r: PASS if r.get("formats_mentioned") else FAIL),
]


def assess_record(r: dict, as_of: date) -> dict:
    checks = []
    for c in CHECKS:
        status, evidence = c.test(r, as_of)
        checks.append({"id": c.id, "label": c.label, "source": c.source, "status": status, "evidence": evidence,
                       "issue_type": c.issue_type, "dimension": c.dimension, "impact": c.impact})
    scored = [c for c in checks if c["status"] != NA]
    weight = sum(c["impact"] for c in scored)
    score = round(100 * sum(SCORE[c["status"]] * c["impact"] for c in scored) / weight, 1) if weight else 0.0
    props = {name: fn(r) for name, fn in CDA_PROPERTIES}
    coverage = round(100 * sum(SCORE[v] for v in props.values()) / len(props), 1)
    rag = "green" if score >= 75 else "amber" if score >= 50 else "red"
    return {"collection": r["collection"], "slug": r["slug"], "title": r["title"], "provider": r.get("provider_stated"),
            "url": f"https://www.data.gov.uk/collections/{r['collection']}/{r['slug']}",
            "score": score, "rag": rag, "cda_metadata_coverage": coverage, "cda_properties": props, "checks": checks}


def assess_portfolio(records: list, as_of: date, importance: int = 3) -> dict:
    """Treat each check as a DQ rule measured across all records, scored with the issues framework."""
    pages = [assess_record(r, as_of) for r in records]
    by_check = []
    for c in CHECKS:
        statuses = [next(x for x in p["checks"] if x["id"] == c.id)["status"] for p in pages]
        applicable = [s for s in statuses if s != NA]
        perf = round(100 * sum(SCORE[s] for s in applicable) / len(applicable), 1) if applicable else 100.0
        a = framework.assess(importance, c.impact, perf)
        by_check.append({"id": c.id, "label": c.label, "source": c.source, "issue_type": c.issue_type,
                         "dimension": c.dimension, "applicable": len(applicable),
                         "pass": statuses.count(PASS), "partial": statuses.count(PARTIAL), "fail": statuses.count(FAIL),
                         "performance": perf, "assessment": a.to_dict()})
    by_collection = {}
    for p in pages:
        b = by_collection.setdefault(p["collection"], {"pages": 0, "score_sum": 0.0, "coverage_sum": 0.0})
        b["pages"] += 1
        b["score_sum"] += p["score"]
        b["coverage_sum"] += p["cda_metadata_coverage"]
    for b in by_collection.values():
        b["mean_score"] = round(b.pop("score_sum") / b["pages"], 1)
        b["mean_cda_coverage"] = round(b.pop("coverage_sum") / b["pages"], 1)
    prop_cov = {name: round(100 * sum(SCORE[p["cda_properties"][name]] for p in pages) / len(pages), 1) for name, _ in CDA_PROPERTIES}
    return {"as_of": as_of.isoformat(), "pages": pages, "checks": by_check, "collections": by_collection,
            "cda_property_coverage": prop_cov,
            "mean_score": round(sum(p["score"] for p in pages) / len(pages), 1),
            "mean_cda_coverage": round(sum(p["cda_metadata_coverage"] for p in pages) / len(pages), 1),
            "rag": {k: sum(1 for p in pages if p["rag"] == k) for k in ("green", "amber", "red")}}
