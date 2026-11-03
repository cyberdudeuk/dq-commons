"""Effort to produce a first data quality baseline for critical data assets (same model as the portal's baseline page).

  estimate(days=..., lite=False, kit=False, **overrides) -> person-days, FTE, days per CDA, share achievable
  scenarios(days)                                       -> the four standard scenarios
  working_days(start, end)                              -> England and Wales working days, Christmas holidays removed

Every number is an assumption from knowledge/effort.yaml; GOV.UK publishes no time estimates.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
# England and Wales bank holidays, 2026 to 2028 (GOV.UK). Other UK nations differ; adjust if needed.
HOLIDAYS = {date(2026, 1, 1), date(2026, 4, 3), date(2026, 4, 6), date(2026, 5, 4), date(2026, 5, 25), date(2026, 8, 31),
            date(2026, 12, 25), date(2026, 12, 28),
            date(2027, 1, 1), date(2027, 3, 26), date(2027, 3, 29), date(2027, 5, 3), date(2027, 5, 31), date(2027, 8, 30),
            date(2027, 12, 27), date(2027, 12, 28),
            date(2028, 1, 3), date(2028, 4, 14), date(2028, 4, 17), date(2028, 5, 1), date(2028, 5, 29), date(2028, 8, 28),
            date(2028, 12, 25), date(2028, 12, 26)}


def model() -> dict:
    return yaml.safe_load((ROOT / "knowledge" / "effort.yaml").read_text(encoding="utf-8"))


def working_days(start: date, end: date) -> int:
    n, d = 0, start
    while d <= end:
        if d.weekday() < 5 and d not in HOLIDAYS:
            n += 1
        d += timedelta(days=1)
    return n


def effective_days(today: date | None = None, deadline: date | None = None) -> int:
    """Working days available: to your deadline, or the default window (12 weeks) if you give none."""
    m = model()
    today = today or date.today()
    deadline = deadline or today + timedelta(weeks=m.get("default_window_weeks", 12))
    return max(10, working_days(today, deadline) - m["defaults"]["lag_days"])


def estimate(days: int, lite: bool = False, kit: bool = False, cdas: int | None = None, tier_mix=None,
             critical_items: int | None = None, contingency: float | None = None, capacity_fte: float | None = None) -> dict:
    m, dft = model(), model()["defaults"]
    n = max(1, cdas or dft["cdas"])
    mix = [x / 100 for x in (tier_mix or dft["tier_mix"])]
    cdi = critical_items or dft["critical_items"]
    cont = (dft["contingency"] if contingency is None else contingency) / 100
    cap = capacity_fte or dft["capacity_fte"]
    eff_cdi = min(cdi, m["lite_items_cap"]) if lite else cdi
    dept, per_tier, roles = 0.0, [0.0, 0.0, 0.0], {}
    for a in m["activities"]:
        f = (eff_cdi / 15) ** m["scale_exponent"] if a["sc"] else 1
        v = [a["d"][t] * f * (a["lite"] if lite else 1) * (a["kit"] if kit else 1) for t in range(3)]
        per_tier = [p + x for p, x in zip(per_tier, v)]
        w = sum(x * mx for x, mx in zip(v, mix)) * n
        roles[a["r"]] = roles.get(a["r"], 0) + w
        dept += w
    central = m["central"]["per_cda_days"] * n + m["central"]["fte_for_window"] * days
    total = dept * (1 + cont) + central
    return {"person_days": round(total), "fte": round(total / days), "days_per_cda": round(dept * (1 + cont) / n, 1),
            "share_achievable": round(min(1, cap * days / total) * 100), "cdas_achievable": min(n, round(n * min(1, cap * days / total))),
            "per_cda_by_tier": [round(x, 1) for x in per_tier], "roles": {k: round(v) for k, v in roles.items()} | {"GDS central": round(central)},
            "assumptions": {"cdas": n, "tier_mix": [round(x * 100) for x in mix], "critical_items": cdi, "contingency": round(cont * 100),
                            "capacity_fte": cap, "days": days, "depth": "proportionate" if lite else "full", "shared_kit": kit}}


def scenarios(days: int | None = None) -> list[dict]:
    days = days or effective_days()
    out = []
    for label, lite, kit in (("Full baseline, each department builds its own", False, False), ("Full baseline, shared toolkit", False, True),
                             ("Proportionate baseline, no toolkit", True, False), ("Proportionate baseline, shared toolkit", True, True)):
        out.append({"label": label, **estimate(days, lite, kit)})
    return out
