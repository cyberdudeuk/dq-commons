"""Q-FAIR ratings for a critical data asset: Quality plus Findable, Accessible, Interoperable, Reusable.

Q-FAIR is the Geospatial Commission's approach (2021); its 2022 benchmark rates each area Good, Improving or
Attention required. This module applies the same three levels to one asset, from two things only:
the measured results (Quality) and what the asset record says (F, A, I, R). Every rating carries its reasons.
A missing field is reported as missing, never guessed: it lowers the rating and says what to record.

Asset fields read (all optional, in the rules file's `asset:` block):
  iri, title, description, owner                         -> Findable
  access_route (open | restricted | on request | closed), classification   -> Accessible
  conforms_to (list of standards), identifiers (list of schemes)           -> Interoperable
  licence, provenance                                     -> Reusable
"""
from __future__ import annotations

LEVELS = ("Good", "Improving", "Attention required")
PILLARS = ("quality", "findable", "accessible", "interoperable", "reusable")
IDENTIFIER_CHECKS = ("identifier", "in_valueset")


def _has(a: dict, k: str) -> bool:
    v = a.get(k)
    return bool(v) and (not isinstance(v, (list, tuple)) or any(v))


def _two(ok: list[tuple[bool, str]]) -> dict:
    """Good if every criterion is met, Improving if some are, Attention required if none."""
    met = [m for m, _ in ok if m]
    level = LEVELS[0] if len(met) == len(ok) else (LEVELS[1] if met else LEVELS[2])
    return {"rating": level, "met": [w for m, w in ok if m], "missing": [w for m, w in ok if not m]}


def quality(res: dict) -> dict:
    total, met = res.get("rules_total", 0), res.get("rules_met", 0)
    pr = [i.get("priority") for i in res.get("issues", [])]
    dims = len(res.get("dimensions", {}))
    if not total:
        return {"rating": LEVELS[2], "met": [], "missing": ["no rules have been measured"]}
    reasons = [f"{met} of {total} rules meet target", f"{dims} dimension(s) measured"]
    if "Critical" in pr or "High" in pr or met / total < 0.75:
        r = {"rating": LEVELS[2], "met": reasons, "missing": [f"{pr.count('Critical')} critical and {pr.count('High')} high issue(s) open" if ("Critical" in pr or "High" in pr) else "fewer than 3 in 4 rules meet target"]}
    elif met == total and dims >= 3:
        r = {"rating": LEVELS[0], "met": reasons, "missing": []}
    else:
        r = {"rating": LEVELS[1], "met": reasons, "missing": ["measure at least 3 dimensions" if dims < 3 else "some rules below target"]}
    return r


def rate(res: dict) -> dict:
    a = res.get("asset", {})
    id_rules = any(r.get("check") in IDENTIFIER_CHECKS for r in res.get("results", []))
    out = {
        "quality": quality(res),
        "findable": _two([(_has(a, "iri"), "persistent identifier or catalogue link"), (_has(a, "title"), "title"),
                          (_has(a, "description"), "description"), (_has(a, "owner"), "owning organisation")]),
        "accessible": _two([(_has(a, "access_route"), "access route recorded"), (_has(a, "classification"), "security classification recorded")]),
        "interoperable": _two([(_has(a, "conforms_to"), "standards it conforms to"), (_has(a, "identifiers") or id_rules, "shared identifiers or code lists used and checked")]),
        "reusable": _two([(_has(a, "licence"), "licence"), (_has(a, "provenance"), "provenance (where the data comes from and how it is made)")]),
    }
    score = {LEVELS[0]: 2, LEVELS[1]: 1, LEVELS[2]: 0}
    total = sum(score[v["rating"]] for v in out.values())
    out["overall"] = {"points": total, "of": 10, "rating": LEVELS[0] if total >= 8 else (LEVELS[1] if total >= 5 else LEVELS[2]),
                      "note": "Indicator, not an absolute measure (as in the Geospatial Commission's 2022 benchmark)."}
    return out
