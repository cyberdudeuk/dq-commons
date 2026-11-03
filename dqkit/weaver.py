"""Metadata Weaver: read one metadata record, write it in every catalogue standard, and show the gaps.

In plain English:
- You give it a record in one of four shapes: W3C DCAT (JSON-LD), schema.org Dataset (JSON-LD), a CKAN
  package (as data.gov.uk and many portals return it) or an ODCS data contract.
- It reads the record into one neutral set of fields (the "canonical" record). Each field is tied to a
  concept in the Metadata Rosetta (knowledge/rosetta.yaml), so the mapping is explained, not hidden.
- It writes the record back out as DCAT v3, schema.org, CKAN and an ODCS contract skeleton.
- It reports, for every output, which fields were filled and which are missing, and checks the 13
  critical data asset (CDA) metadata properties from the GOV.UK data asset management guidance.

Nothing is invented: a field that isn't in the input stays empty and is reported as a gap. Fields with no
home in a target standard are listed as "not carried", never dropped silently. The browser engine
(portal/src/js/engine.js, DQ.weaver) is a line-by-line port, checked by scripts/parity_check.py.
"""
from __future__ import annotations

import json

DQC = "https://cyberdudeuk.github.io/ndl-dq-assurance/vocab#"  # the Commons vocabulary (persistent identifiers)
DCAT_CONTEXT = {"dcat": "http://www.w3.org/ns/dcat#", "dct": "http://purl.org/dc/terms/", "foaf": "http://xmlns.com/foaf/0.1/",
                "vcard": "http://www.w3.org/2006/vcard/ns#", "dqc": DQC}

# key, label, Rosetta concept, CDA property (or ""), and whether each output standard can carry it.
FIELDS = [
    ("title", "Title", "Title", "title", "dcat schema ckan odcs"),
    ("description", "Description", "Description", "description", "dcat schema ckan odcs"),
    ("identifier", "Identifier", "Identifier", "identifier", "dcat schema ckan odcs"),
    ("publisher", "Publisher or creator", "Publisher", "creator", "dcat schema ckan odcs"),
    ("contact", "Contact point (a team or role)", "Contact point", "", "dcat schema ckan odcs"),
    ("keywords", "Keywords", "Keyword", "", "dcat schema ckan odcs"),
    ("theme", "Theme or domain", "Theme", "", "dcat ckan odcs"),
    ("licence", "Licence", "Licence", "licence", "dcat schema ckan odcs"),
    ("access_rights", "Access rights", "Access rights", "accessRights", "dcat schema ckan odcs"),
    ("security", "Security classification", "Security classification", "securityClassification", "dcat ckan odcs"),
    ("issued", "Date created or issued", "Issued", "dateCreated", "dcat schema ckan odcs"),
    ("modified", "Date modified", "Modified", "", "dcat schema ckan"),
    ("expires", "Expiry date", "Expires", "expires", "dcat schema ckan odcs"),
    ("superseded_by", "Superseded by", "Superseded by", "supersededBy", "dcat ckan odcs"),
    ("accrual", "Update frequency", "Accrual periodicity", "", "dcat ckan odcs"),
    ("spatial", "Geographic coverage", "Spatial coverage", "", "dcat schema ckan"),
    ("temporal", "Time period covered", "Temporal coverage", "temporalCoverage", "dcat schema ckan odcs"),
    ("conforms_to", "Conforms to (schema or standard)", "Conforms to", "conformsTo", "dcat schema ckan odcs"),
    ("landing_page", "Landing page", "Landing page", "", "dcat schema ckan"),
    ("version", "Version", "Version", "", "dcat schema ckan odcs"),
    ("language", "Language", "Language", "", "dcat schema ckan"),
    ("distributions", "Distributions (files and APIs)", "Distribution", "mediaType", "dcat schema ckan odcs"),
]
KEYS = [f[0] for f in FIELDS]
CDA = [(f[0], f[3]) for f in FIELDS if f[3]]
TARGETS = ("dcat", "schema", "ckan", "odcs")
CARRY = {t: [f[0] for f in FIELDS if t in f[4].split()] for t in TARGETS}


# ---------- helpers ----------

def _first(v):
    if isinstance(v, list):
        return _first(v[0]) if v else None
    return v


def _text(v):
    """A plain string from a JSON-LD value: a string, {"@value"}, {"@id"}, a name object or a list of these."""
    v = _first(v)
    if v is None:
        return ""
    if isinstance(v, dict):
        for k in ("@value", "name", "foaf:name", "vcard:fn", "fn", "title", "@id", "url", "label"):
            if v.get(k):
                return _text(v[k])
        return ""
    if isinstance(v, bool):
        return ""
    return str(v).strip()


def _list(v):
    if v is None or v == "":
        return []
    if not isinstance(v, list):
        v = [v]
    out = []
    for x in v:
        t = _text(x)
        if t and t not in out:
            out.append(t)
    return out


def _get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, "", []):
            return d[k]
    return None


def _strip(d, *prefixes):
    """Drop JSON-LD prefixes so 'dct:title' and 'title' read the same."""
    out = {}
    for k, v in (d or {}).items():
        kk = k
        for p in prefixes:
            if kk.startswith(p):
                kk = kk[len(p):]
        if kk not in out:
            out[kk] = v
    return out


def _temporal(start, end):
    start, end = _text(start), _text(end)
    if start and end:
        return f"{start}/{end}"
    return start or (f"../{end}" if end else "")


def _dist(title="", url="", fmt="", media_type=""):
    return {"title": title or "", "url": url or "", "format": (fmt or "").upper() if fmt and "/" not in fmt else (fmt or ""),
            "media_type": media_type or ""}


def empty():
    return {k: ([] if k in ("keywords", "theme", "distributions") else "") for k in KEYS}


# ---------- detect and read ----------

def detect(rec: dict) -> str:
    """Which shape the record is in: dcat, schema, ckan or odcs."""
    if not isinstance(rec, dict):
        raise ValueError("A metadata record must be a JSON object.")
    if rec.get("kind") == "DataContract" or "apiVersion" in rec:
        return "odcs"
    t = rec.get("@type") or rec.get("type")
    ts = " ".join(t) if isinstance(t, list) else str(t or "")
    ctx = json.dumps(rec.get("@context", ""))
    if "dcat:Dataset" in ts or "dcat" in ctx or any(k.startswith(("dcat:", "dct:")) for k in rec):
        return "dcat"
    if ts.endswith("Dataset") and "schema.org" in ctx or ts == "Dataset":
        return "schema"
    r = rec["result"] if isinstance(rec.get("result"), dict) else rec  # CKAN API responses wrap the package in "result"
    if any(k in r for k in ("resources", "notes", "license_id", "organization", "extras", "maintainer")):
        return "ckan"
    raise ValueError("Couldn't tell the format. Use DCAT or schema.org JSON-LD, a CKAN package, or an ODCS contract.")


def read_dcat(rec: dict) -> dict:
    r, c = _strip(rec, "dct:", "dcat:", "dcterms:"), empty()
    c["title"] = _text(r.get("title"))
    c["description"] = _text(r.get("description"))
    c["identifier"] = _text(r.get("identifier")) or _text(rec.get("@id"))
    c["publisher"] = _text(r.get("publisher")) or _text(r.get("creator"))
    c["contact"] = _text(r.get("contactPoint"))
    c["keywords"] = _list(r.get("keyword"))
    c["theme"] = _list(r.get("theme"))
    c["licence"] = _text(r.get("license"))
    c["access_rights"] = _text(r.get("accessRights"))
    c["security"] = _text(rec.get("dqc:securityClassification"))
    c["issued"] = _text(r.get("issued")) or _text(r.get("created"))
    c["modified"] = _text(r.get("modified"))
    c["expires"] = _text(rec.get("dqc:expires"))
    c["superseded_by"] = _text(r.get("isReplacedBy"))
    c["accrual"] = _text(r.get("accrualPeriodicity"))
    c["spatial"] = _text(r.get("spatial"))
    t = _first(r.get("temporal"))
    if isinstance(t, dict):
        t = _strip(t, "dcat:", "dct:", "schema:")
        c["temporal"] = _temporal(t.get("startDate"), t.get("endDate"))
    else:
        c["temporal"] = _text(t)
    c["conforms_to"] = _text(r.get("conformsTo"))
    c["landing_page"] = _text(r.get("landingPage"))
    c["version"] = _text(r.get("version")) or _text(rec.get("owl:versionInfo"))
    c["language"] = _text(r.get("language"))
    ds = r.get("distribution") or []
    for d in ds if isinstance(ds, list) else [ds]:
        d = _strip(d, "dct:", "dcat:")
        c["distributions"].append(_dist(_text(d.get("title")), _text(d.get("downloadURL")) or _text(d.get("accessURL")),
                                        _text(d.get("format")), _text(d.get("mediaType"))))
    return c


def read_schema(rec: dict) -> dict:
    r, c = _strip(rec, "schema:"), empty()
    c["title"] = _text(r.get("name"))
    c["description"] = _text(r.get("description"))
    c["identifier"] = _text(r.get("identifier")) or _text(rec.get("@id"))
    c["publisher"] = _text(r.get("publisher")) or _text(r.get("creator"))
    c["contact"] = _text((_first(r.get("creator")) or {}).get("contactPoint") if isinstance(_first(r.get("creator")), dict) else None)
    kw = r.get("keywords")
    c["keywords"] = [k.strip() for k in kw.split(",") if k.strip()] if isinstance(kw, str) else _list(kw)
    c["licence"] = _text(r.get("license"))
    c["access_rights"] = _text(r.get("conditionsOfAccess")) or ("Open" if r.get("isAccessibleForFree") is True else "")
    c["issued"] = _text(r.get("dateCreated")) or _text(r.get("datePublished"))
    c["modified"] = _text(r.get("dateModified"))
    c["expires"] = _text(r.get("expires"))
    c["spatial"] = _text(r.get("spatialCoverage"))
    c["temporal"] = _text(r.get("temporalCoverage"))
    c["conforms_to"] = _text(r.get("schemaVersion"))
    c["landing_page"] = _text(r.get("url"))
    c["version"] = _text(r.get("version"))
    c["language"] = _text(r.get("inLanguage"))
    ds = r.get("distribution") or []
    for d in ds if isinstance(ds, list) else [ds]:
        d = _strip(d, "schema:")
        c["distributions"].append(_dist(_text(d.get("name")), _text(d.get("contentUrl")) or _text(d.get("url")),
                                        "", _text(d.get("encodingFormat"))))
    return c


def read_ckan(rec: dict) -> dict:
    r = rec.get("result", rec) if isinstance(rec.get("result"), dict) else rec
    ex = {e.get("key"): e.get("value") for e in r.get("extras") or [] if isinstance(e, dict)}
    c = empty()
    c["title"] = _text(r.get("title"))
    c["description"] = _text(r.get("notes"))
    c["identifier"] = _text(ex.get("identifier")) or _text(r.get("id")) or _text(r.get("name"))
    c["publisher"] = _text((r.get("organization") or {}).get("title")) or _text(r.get("author"))
    c["contact"] = _text(r.get("maintainer")) or _text(ex.get("contact-name"))
    c["keywords"] = _list([t.get("display_name") or t.get("name") for t in r.get("tags") or [] if isinstance(t, dict)])
    c["theme"] = _list([g.get("title") or g.get("name") for g in r.get("groups") or [] if isinstance(g, dict)]) or _list(ex.get("theme"))
    c["licence"] = _text(r.get("license_url")) or _text(r.get("license_id")) or _text(r.get("license_title"))
    c["access_rights"] = _text(ex.get("access_rights")) or ("Open" if r.get("isopen") is True else "")
    c["security"] = _text(ex.get("security_classification"))
    c["issued"] = _text(ex.get("issued")) or _text(r.get("metadata_created"))
    c["modified"] = _text(ex.get("modified")) or _text(r.get("metadata_modified"))
    c["expires"] = _text(ex.get("expires"))
    c["superseded_by"] = _text(ex.get("superseded_by"))
    c["accrual"] = _text(ex.get("frequency")) or _text(ex.get("update_frequency"))
    c["spatial"] = _text(ex.get("spatial_text")) or _text(ex.get("spatial"))
    c["temporal"] = _temporal(ex.get("temporal_start"), ex.get("temporal_end")) or _text(ex.get("temporal_coverage"))
    c["conforms_to"] = _text(ex.get("conforms_to")) or _text(ex.get("schema"))
    c["landing_page"] = _text(r.get("url"))
    c["version"] = _text(r.get("version"))
    c["language"] = _text(ex.get("language"))
    for d in r.get("resources") or []:
        c["distributions"].append(_dist(_text(d.get("name")), _text(d.get("url")), _text(d.get("format")), _text(d.get("mimetype"))))
    return c


def read_odcs(rec: dict) -> dict:
    cp = {p.get("property"): p.get("value") for p in rec.get("customProperties") or [] if isinstance(p, dict)}
    desc = rec.get("description") or {}
    c = empty()
    c["title"] = _text(rec.get("name"))
    c["description"] = _text(desc.get("purpose")) if isinstance(desc, dict) else _text(desc)
    c["identifier"] = _text(rec.get("id"))
    c["publisher"] = _text(cp.get("publisher")) or _text(rec.get("tenant"))
    team = rec.get("team")
    c["contact"] = _text(team.get("name")) if isinstance(team, dict) else ""
    c["keywords"] = _list(rec.get("tags"))
    c["theme"] = _list(rec.get("domain"))
    c["licence"] = _text(cp.get("licence")) or _text(cp.get("license"))
    c["access_rights"] = _text(desc.get("limitations")) if isinstance(desc, dict) else ""
    c["security"] = _text(cp.get("securityClassification"))
    c["issued"] = _text(rec.get("contractCreatedTs"))
    c["expires"] = _text(cp.get("expires"))
    c["superseded_by"] = _text(cp.get("supersededBy"))
    for s in rec.get("slaProperties") or []:
        if isinstance(s, dict) and s.get("property") in ("frequency", "latency", "freshness"):
            c["accrual"] = " ".join(x for x in (_text(s.get("value")), _text(s.get("unit"))) if x)
            break
    c["temporal"] = _text(cp.get("temporalCoverage"))
    c["conforms_to"] = (f"ODCS {_text(rec.get('apiVersion')) or 'v3'}" if rec.get("schema") else "")
    c["version"] = _text(rec.get("version"))
    for s in rec.get("servers") or []:
        if isinstance(s, dict):
            c["distributions"].append(_dist(_text(s.get("server")), _text(s.get("location")) or _text(s.get("host")),
                                            _text(s.get("format")) or _text(s.get("type")), ""))
    return c


READERS = {"dcat": read_dcat, "schema": read_schema, "ckan": read_ckan, "odcs": read_odcs}


def read(rec: dict, fmt: str | None = None) -> tuple[str, dict]:
    fmt = fmt or detect(rec)
    if fmt not in READERS:
        raise ValueError(f"Unknown format {fmt}. Use one of: {', '.join(READERS)}.")
    return fmt, READERS[fmt](rec)


# ---------- write ----------

def _media(d):
    return d["media_type"] or d["format"]


def to_dcat(c: dict) -> dict:
    out = {"@context": DCAT_CONTEXT, "@type": "dcat:Dataset"}
    put = lambda k, v: out.__setitem__(k, v) if v not in ("", [], None) else None
    put("dct:title", c["title"])
    put("dct:description", c["description"])
    put("dct:identifier", c["identifier"])
    put("dct:publisher", {"@type": "foaf:Agent", "foaf:name": c["publisher"]} if c["publisher"] else "")
    put("dcat:contactPoint", {"@type": "vcard:Kind", "vcard:fn": c["contact"]} if c["contact"] else "")
    put("dcat:keyword", c["keywords"])
    put("dcat:theme", c["theme"])
    put("dct:license", c["licence"])
    put("dct:accessRights", c["access_rights"])
    put("dqc:securityClassification", c["security"])
    put("dct:issued", c["issued"])
    put("dct:modified", c["modified"])
    put("dqc:expires", c["expires"])
    put("dct:isReplacedBy", c["superseded_by"])
    put("dct:accrualPeriodicity", c["accrual"])
    put("dct:spatial", c["spatial"])
    if c["temporal"]:
        s, _, e = c["temporal"].partition("/")
        t = {"@type": "dct:PeriodOfTime"}
        if s and s != "..":
            t["dcat:startDate"] = s
        if e and e != "..":
            t["dcat:endDate"] = e
        out["dct:temporal"] = t
    put("dct:conformsTo", c["conforms_to"])
    put("dcat:landingPage", c["landing_page"])
    put("dcat:version", c["version"])
    put("dct:language", c["language"])
    if c["distributions"]:
        out["dcat:distribution"] = [{k: v for k, v in (("@type", "dcat:Distribution"), ("dct:title", d["title"]),
                                                       ("dcat:downloadURL", d["url"]), ("dct:format", d["format"]),
                                                       ("dcat:mediaType", d["media_type"])) if v} for d in c["distributions"]]
    return out


def to_schema(c: dict) -> dict:
    out = {"@context": "https://schema.org/", "@type": "Dataset"}
    put = lambda k, v: out.__setitem__(k, v) if v not in ("", [], None) else None
    put("name", c["title"])
    put("description", c["description"])
    put("identifier", c["identifier"])
    if c["publisher"] or c["contact"]:
        org = {"@type": "Organization"}
        if c["publisher"]:
            org["name"] = c["publisher"]
        if c["contact"]:
            org["contactPoint"] = {"@type": "ContactPoint", "name": c["contact"]}
        out["creator"] = org
    put("keywords", c["keywords"])
    put("license", c["licence"])
    put("conditionsOfAccess", c["access_rights"])
    put("dateCreated", c["issued"])
    put("dateModified", c["modified"])
    put("expires", c["expires"])
    put("spatialCoverage", c["spatial"])
    put("temporalCoverage", c["temporal"])
    put("schemaVersion", c["conforms_to"])
    put("url", c["landing_page"])
    put("version", c["version"])
    put("inLanguage", c["language"])
    if c["distributions"]:
        out["distribution"] = [{k: v for k, v in (("@type", "DataDownload"), ("name", d["title"]), ("contentUrl", d["url"]),
                                                  ("encodingFormat", _media(d))) if v} for d in c["distributions"]]
    return out


def to_ckan(c: dict) -> dict:
    extras = [{"key": k, "value": v} for k, v in (
        ("identifier", c["identifier"]), ("access_rights", c["access_rights"]), ("security_classification", c["security"]),
        ("issued", c["issued"]), ("modified", c["modified"]), ("expires", c["expires"]), ("superseded_by", c["superseded_by"]),
        ("frequency", c["accrual"]), ("spatial_text", c["spatial"]), ("temporal_coverage", c["temporal"]),
        ("conforms_to", c["conforms_to"]), ("language", c["language"]), ("theme", ", ".join(c["theme"]))) if v]
    out = {"title": c["title"], "notes": c["description"], "url": c["landing_page"], "version": c["version"],
           "maintainer": c["contact"], "organization": {"title": c["publisher"]} if c["publisher"] else None,
           "license_id": c["licence"], "tags": [{"name": k} for k in c["keywords"]], "extras": extras,
           "resources": [{k: v for k, v in (("name", d["title"]), ("url", d["url"]), ("format", d["format"]),
                                            ("mimetype", d["media_type"])) if v} for d in c["distributions"]]}
    return {k: v for k, v in out.items() if v not in ("", [], None)}


def to_odcs(c: dict) -> dict:
    """An ODCS v3 contract skeleton for the dataset. Add the schema and quality rules from the checker."""
    from .contracts import ODCS_API
    cp = [{"property": k, "value": v} for k, v in (
        ("publisher", c["publisher"]), ("licence", c["licence"]), ("securityClassification", c["security"]),
        ("expires", c["expires"]), ("supersededBy", c["superseded_by"]), ("temporalCoverage", c["temporal"])) if v]
    out = {"apiVersion": ODCS_API, "kind": "DataContract", "id": c["identifier"] or "dataset", "version": c["version"] or "1.0.0",
           "status": "draft", "name": c["title"] or c["identifier"] or "dataset"}
    desc = {k: v for k, v in (("purpose", c["description"]), ("limitations", c["access_rights"])) if v}
    if desc:
        out["description"] = desc
    if c["theme"]:
        out["domain"] = c["theme"][0]
    if c["keywords"]:
        out["tags"] = list(c["keywords"])
    if c["contact"]:
        out["team"] = {"name": c["contact"]}
    if c["issued"]:
        out["contractCreatedTs"] = c["issued"]
    if c["accrual"]:
        out["slaProperties"] = [{"property": "frequency", "value": c["accrual"]}]
    if c["distributions"]:
        out["servers"] = [{k: v for k, v in (("server", d["title"] or f"distribution-{i + 1}"), ("type", "https"),
                                             ("location", d["url"]), ("format", d["format"] or d["media_type"])) if v}
                          for i, d in enumerate(c["distributions"])]
    if cp:
        out["customProperties"] = cp
    return out


WRITERS = {"dcat": to_dcat, "schema": to_schema, "ckan": to_ckan, "odcs": to_odcs}


# ---------- gaps ----------

def _filled(c, k):
    v = c.get(k)
    if k == "distributions":
        return bool(v) and all(d.get("url") for d in v)
    return v not in ("", [], None)


def cda_check(c: dict) -> dict:
    """The 13 critical data asset metadata properties: pass, partial or missing, with a reason."""
    out = {}
    for k, prop in CDA:
        if k == "distributions":
            ds = c["distributions"]
            st = "pass" if ds and all(_media(d) for d in ds) else ("partial" if ds else "missing")
            why = "Every distribution states a format" if st == "pass" else ("Some distributions have no format" if ds else "No distributions")
        elif k == "description":
            n = len(c["description"])  # characters (code points), as the browser counts them
            st = "pass" if n >= 40 else ("partial" if n else "missing")
            why = f"{n} characters" + ("" if n >= 40 else " (aim for at least 40)")
        else:
            st = "pass" if _filled(c, k) else "missing"
            why = "Present" if st == "pass" else "Not in the record"
        out[prop] = {"status": st, "field": k, "why": why}
    score = round(100 * sum({"pass": 1, "partial": .5}.get(v["status"], 0) for v in out.values()) / len(out), 1)  # noqa: same in JS (pyRound)
    return {"properties": out, "coverage": score}


def coverage(c: dict) -> dict:
    out = {}
    for t in TARGETS:
        can = CARRY[t]
        filled = [k for k in can if _filled(c, k)]
        out[t] = {"filled": len(filled), "total": len(can), "missing": [k for k in can if k not in filled],
                  "not_carried": [k for k in KEYS if k not in can and _filled(c, k)]}
    return out


def weave(rec: dict, fmt: str | None = None) -> dict:
    """Read a record and write every format. Returns source format, canonical record, outputs and gaps."""
    src, c = read(rec, fmt)
    return {"source_format": src, "canonical": c, "outputs": {t: WRITERS[t](c) for t in TARGETS},
            "coverage": coverage(c), "cda": cda_check(c)}


def fields() -> list:
    """The field table, for documentation and the portal."""
    return [{"key": k, "label": lab, "rosetta": ros, "cda": cda, "carried_by": car.split()} for k, lab, ros, cda, car in FIELDS]
