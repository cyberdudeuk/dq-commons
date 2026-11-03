"""GOV.UK Data Quality Issues Framework, implemented exactly as published.

Source: "Data quality issues framework", part of "Implement a data quality action
plan" (GDS, 16 April 2026):
https://www.gov.uk/government/publications/implement-a-data-quality-action-plan/data-quality-issues-framework

Plain-English summary
---------------------
1. Score how important the purpose of the data is (1 to 4).
2. Score how badly a failing rule would hurt that purpose (1 to 4).
3. Multiply them. The result (1 to 16) picks a suggested target range.
4. Measure the rule. If performance is below target, place it in a band
   (High = close to target, Middle, Low = far below) and multiply again.
5. That final number gives the priority and how fast to fix it.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

LEVELS = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}

# Table 3: suggested target ranges by combined score (importance x impact).
TARGET_RANGES = [
    (range(1, 4), (75.0, 90.0)),
    (range(4, 7), (90.0, 97.5)),
    (range(8, 10), (97.5, 99.9)),
    (range(12, 17), (99.9, 100.0)),
]

# Default target when a rule sets none (decision D-021, replacing D-016).
# "low" (default) uses the low end of each range. "mid" and "high" are offered for
# stricter owners.
# The data owner should always confirm the target for each rule.
TARGET_POLICIES = {
    "low": {(75.0, 90.0): 75.0, (90.0, 97.5): 90.0, (97.5, 99.9): 97.5, (99.9, 100.0): 99.9},
    "mid": {(75.0, 90.0): 85.0, (90.0, 97.5): 95.0, (97.5, 99.9): 99.0, (99.9, 100.0): 100.0},
    "high": {(75.0, 90.0): 89.9, (90.0, 97.5): 97.4, (97.5, 99.9): 99.8, (99.9, 100.0): 100.0},
}
DEFAULT_POLICY = "low"
DEFAULT_TARGETS = TARGET_POLICIES[DEFAULT_POLICY]

# Table 8: investigation and remediation timescales.
RESOLUTION = {
    "Critical": "Immediately",
    "High": "Within 1 measurement cycle",
    "Medium": "Within 3 measurement cycles",
    "Low": "Within 6 measurement cycles",
}


def _check_level(name: str, value: int) -> int:
    if value not in LEVELS:
        raise ValueError(f"{name} must be 1, 2, 3 or 4 (got {value!r})")
    return value


def combined_score(importance: int, impact: int) -> int:
    return _check_level("importance", importance) * _check_level("impact", impact)


def target_range(combined: int) -> tuple[float, float]:
    for scores, rng in TARGET_RANGES:
        if combined in scores:
            return rng
    raise ValueError(f"combined score {combined} is not a product of two 1-4 scores")


def default_target(combined: int, policy: str = DEFAULT_POLICY) -> float:
    if policy not in TARGET_POLICIES:
        raise ValueError(f"target policy must be low, mid or high, not {policy!r}")
    return TARGET_POLICIES[policy][target_range(combined)]


def error_rate(percent: float) -> str:
    """Plain-English error rate, as used in the framework's tables: 95% -> '1 in 20 records'."""
    err = 100.0 - percent
    if err <= 0:
        return "0 records"
    n = 100.0 / err
    return f"1 in {n:,.0f} records" if n >= 10 else f"1 in {n:.2g} records"


def bands(target: float) -> Optional[dict]:
    """Performance bands below target (Table 4 method). None when target is 100%."""
    if target >= 100.0:
        return None
    allowed_error = 100.0 - target
    middle_start = max(0.0, 100.0 - 2 * allowed_error)
    high_start = (middle_start + target) / 2
    return {"low": (0.0, middle_start), "middle": (middle_start, high_start), "high": (high_start, target)}


def band_for(performance: float, target: float) -> tuple[Optional[str], int]:
    """Return (band name, band score). (None, 0) means the rule meets its target."""
    if performance >= target:
        return None, 0
    b = bands(target)
    if b is None:  # target 100% and not met
        return "critical", 4
    if performance < b["middle"][0]:
        return "low", 3
    if performance < b["high"][0]:
        return "middle", 2
    return "high", 1


def priority_for(score: int) -> Optional[str]:
    if score <= 0:
        return None
    if score <= 7:
        return "Low"
    if score <= 16:
        return "Medium"
    if score <= 32:
        return "High"
    return "Critical"


@dataclass
class Assessment:
    importance: int
    impact: int
    combined: int
    target: float
    target_range: tuple
    performance: float
    meets_target: bool
    band: Optional[str]
    band_score: int
    priority_score: int
    priority: Optional[str]
    resolution: Optional[str]
    error_rate_target: str = ""
    error_rate_actual: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["target_range"] = list(self.target_range)
        return d


def assess(importance: int, impact: int, performance: float, target: Optional[float] = None,
           policy: str = DEFAULT_POLICY) -> Assessment:
    """Score one rule result with the GOV.UK issues framework."""
    if not 0.0 <= performance <= 100.0:
        raise ValueError("performance is a percentage between 0 and 100")
    combined = combined_score(importance, impact)
    rng = target_range(combined)
    tgt = default_target(combined, policy) if target is None else float(target)
    band, band_score = band_for(performance, tgt)
    score = importance * impact * band_score
    pr = priority_for(score)
    return Assessment(
        importance=importance, impact=impact, combined=combined, target=tgt, target_range=rng,
        performance=round(performance, 3), meets_target=band is None, band=band, band_score=band_score,
        priority_score=score, priority=pr, resolution=RESOLUTION.get(pr) if pr else None,
        error_rate_target=error_rate(tgt), error_rate_actual=error_rate(performance),
    )
