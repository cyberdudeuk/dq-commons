"""Framework packs, the framework registry, and crosswalks between quality vocabularies.

A *pack* applies a framework, standard, policy or scenario to the kit's results: it lists the
framework's requirements and says what evidence in a result meets each one. `assess()` reports which
requirements are met, partly met, not met, or need a person to confirm ("manual").

The *registry* (knowledge/frameworks.yaml) describes about 30 frameworks and maps each one's own
dimensions to the kit's. `convert()` uses that map to restate a result in another framework's
vocabulary - for example ISO/IEC 25012 or the Government of Canada's 9 dimensions - and says which
of that framework's dimensions the data rules can't measure.
"""
from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACK_DIR = ROOT / "packs"
REGISTRY = ROOT / "knowledge" / "frameworks.yaml"
PLACEHOLDER = "[steward to confirm]"
EVIDENCE_KINDS = {"asset_field", "dimensions", "any_dimension", "checks", "any_checks", "min_rules", "history_cycles",
                  "control_points", "personal_data_inclusion", "automatic", "manual", "note"}


# ---------- loading ----------

def registry() -> list:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["frameworks"]


def framework(fid: str) -> dict:
    for f in registry():
        if f["id"] == fid:
            return f
    raise ValueError(f"unknown framework {fid!r}; see knowledge/frameworks.yaml")


def list_packs() -> list:
    return [load_pack(p.stem) for p in sorted(PACK_DIR.glob("*.yaml"))]


def load_pack(pid: str) -> dict:
    p = PACK_DIR / f"{pid}.yaml"
    if not p.exists() or "/" in pid or "\\" in pid:
        raise ValueError(f"unknown pack {pid!r}; packs: {', '.join(x.stem for x in sorted(PACK_DIR.glob('*.yaml')))}")
    pack = yaml.safe_load(p.read_text(encoding="utf-8"))
    validate_pack(pack)
    return pack


def validate_pack(pack: dict) -> None:
    for k in ("id", "name", "requirements"):
        if k not in pack:
            raise ValueError(f"pack is missing {k!r}")
    known = {f["id"] for f in registry()}
    for f in pack.get("frameworks", []):
        if f not in known:
            raise ValueError(f"pack {pack['id']}: framework {f!r} is not in the registry")
    seen = set()
    for r in pack["requirements"]:
        if r["id"] in seen:
            raise ValueError(f"pack {pack['id']}: duplicate requirement {r['id']}")
        seen.add(r["id"])
        bad = set(r.get("evidence", {})) - EVIDENCE_KINDS
        if bad or not r.get("evidence"):
            raise ValueError(f"pack {pack['id']} requirement {r['id']}: unknown or missing evidence {sorted(bad)}")


# ---------- assessing a result against a pack ----------

def _measured(result: dict) -> set:
    return set(result.get("dimensions", {}))


def _checks(result: dict) -> set:
    out = set()
    for r in result.get("results", []):
        out.add(r["check"])
    return out


def _check(req: dict, result: dict, cycles: int) -> tuple[str, str]:
    """(status, reason) for one requirement."""
    ev, asset = req["evidence"], result.get("asset", {})
    if "manual" in ev:
        return "manual", f"Needs a person to confirm: {ev['manual']}"
    if ev.get("automatic"):
        return "met", "Produced by the kit" + (f" ({ev['note']})" if ev.get("note") else "")
    if "asset_field" in ev:
        v = asset.get(ev["asset_field"])
        ok = v not in (None, "", [], {}) and PLACEHOLDER not in str(v) and "[organisation]" not in str(v)
        return ("met", f"{ev['asset_field']} is recorded") if ok else ("not met", f"Add '{ev['asset_field']}' to the asset block")
    if "dimensions" in ev:
        missing = [d for d in ev["dimensions"] if d not in _measured(result)]
        if not missing:
            return "met", "Measured: " + ", ".join(ev["dimensions"])
        some = len(missing) < len(ev["dimensions"])
        return ("partly" if some else "not met"), "Not yet measured: " + ", ".join(missing)
    if "any_dimension" in ev:
        hit = [d for d in ev["any_dimension"] if d in _measured(result)]
        return ("met", "Measured: " + ", ".join(hit)) if hit else ("not met", "Add a rule for " + " or ".join(ev["any_dimension"]))
    if "checks" in ev:
        missing = [c for c in ev["checks"] if c not in _checks(result)]
        return ("met", "Uses " + ", ".join(ev["checks"])) if not missing else ("not met", "Add a rule using: " + ", ".join(missing))
    if "any_checks" in ev:
        hit = [c for c in ev["any_checks"] if c in _checks(result)]
        return ("met", "Uses " + ", ".join(hit)) if hit else ("not met", "Add a rule using one of: " + ", ".join(ev["any_checks"]))
    if "min_rules" in ev:
        n = len(result.get("results", []))
        return ("met", f"{n} rules") if n >= ev["min_rules"] else ("partly" if n else "not met", f"{n} rules; at least {ev['min_rules']} expected")
    if "history_cycles" in ev:
        need = ev["history_cycles"]
        return ("met", f"{cycles} measurement cycle(s) recorded") if cycles >= need else (
            "partly" if cycles else "not met", f"{cycles} of {need} measurement cycle(s) recorded; keep a history (--history)")
    if "control_points" in ev:
        cps = {r.get("meta", {}).get("control_point") for r in result.get("results", [])} - {None}
        return ("met", "Controls at " + ", ".join(sorted(cps))) if len(cps) >= ev["control_points"] else (
            "partly", f"Controls at {len(cps)} point(s) only: " + ", ".join(sorted(cps)))
    if ev.get("personal_data_inclusion"):
        if not asset.get("personal_data_columns"):
            return "not applicable", "No personal data columns declared"
        inc = {"not_unknown", "group_disparity"} & _checks(result)
        return ("met", "Uses " + ", ".join(sorted(inc))) if inc else ("not met", "Add not_unknown or group_disparity rules")
    return "manual", "No automatic evidence defined"


def assess(pack: dict | str, result: dict, cycles: Optional[int] = None) -> dict:
    """How far a result meets a pack's requirements."""
    pack = load_pack(pack) if isinstance(pack, str) else pack
    if cycles is None:
        cycles = (result.get("operations") or {}).get("cycles_measured", 1)
    rows = []
    for req in pack["requirements"]:
        status, reason = _check(req, result, cycles)
        rows.append({"id": req["id"], "text": req["text"], "status": status, "reason": reason})
    scored = [r for r in rows if r["status"] not in ("manual", "not applicable")]
    points = sum(1 if r["status"] == "met" else 0.5 if r["status"] == "partly" else 0 for r in scored)
    out = {"pack": pack["id"], "name": pack["name"], "asset": result.get("asset", {}).get("id"),
           "coverage": round(100 * points / len(scored), 1) if scored else None,
           "met": sum(r["status"] == "met" for r in rows), "partly": sum(r["status"] == "partly" for r in rows),
           "not_met": sum(r["status"] == "not met" for r in rows), "manual": sum(r["status"] == "manual" for r in rows),
           "requirements": rows}
    if pack.get("index") == "dqmi_style":
        out["index"] = dqmi_style(result, (result.get("asset") or {}).get("coverage"))
    return out


def dqmi_style(result: dict, coverage=None) -> dict:
    """An indicative NHS DQMI-style index: mean data item score x coverage.

    Data item score = the lowest pass rate among that column's completeness and validity rules (a
    record must be both valid and complete). Not the official DQMI, which NHS England calculates
    from submitted datasets with its own default-value thresholds."""
    items: dict = {}
    for r in result.get("results", []):
        if r["dimension"] in ("completeness", "validity") and len(r.get("columns") or []) == 1:
            items.setdefault(r["columns"][0], []).append(r["performance"])
    scores = {c: min(v) for c, v in items.items()}
    cov = 1.0 if coverage in (None, "") else float(coverage)
    cov = cov / 100 if cov > 1 else cov
    return {"items": scores, "coverage": cov, "index": round(mean(scores.values()) * cov, 1) if scores else None,
            "note": "Indicative, built like the NHS DQMI. Not the official DQMI."}


# ---------- crosswalk and conversion ----------

def crosswalk_matrix() -> dict:
    """{framework id: {kit dimension: [framework dimensions that map to it]}} for every framework."""
    out = {}
    for f in registry():
        m: dict = {}
        for src, kit in f["map"].items():
            for k in kit:
                m.setdefault(k, []).append(src)
        out[f["id"]] = m
    return out


def convert(result: dict, to: str) -> dict:
    """Restate a result's dimension scores in another framework's vocabulary.

    Each target dimension's score is the mean performance of the kit dimensions it maps to that
    were measured. Target dimensions with no kit equivalent, or nothing measured, are listed as
    needing other evidence."""
    f = framework(to)
    dims = result.get("dimensions", {})
    rows = []
    for name in f["dimensions"]:
        kit = f["map"].get(name, [])
        got = [dims[k]["mean_performance"] for k in kit if k in dims]
        rows.append({"dimension": name, "maps_to": kit,
                     "score": round(mean(got), 1) if got else None,
                     "status": "measured" if got and len(got) == len(kit) else "partly measured" if got
                     else "not measured by data rules" if not kit else "not measured yet"})
    return {"framework": f["id"], "name": f["name"], "asset": result.get("asset", {}).get("id"), "dimensions": rows}
