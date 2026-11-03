"""Record linkage quality: how well were records about people joined? (backlog BL-08, issue #8)

Works with the output of any linkage tool, including Splink (https://github.com/moj-analytical-services/splink),
which is open source and widely used in UK government. It needs no linkage library itself.

In plain English:
- match_rate: of the records you tried to link, how many found a partner.
- Clerical review: give a sample of pairs that people have checked (true match or not), and it estimates
  precision (how many accepted links are right: false matches lower it) and recall (how many true matches
  were found: missed matches lower it).
- Fairness: match rates by group (for example by ethnic group, age band or nation). Linkage often works less
  well for some groups, for example where names are transliterated or records are thinner, and missed links
  can make people disappear from statistics. A gap above the tolerance is flagged.

Use aggregate results only. Pair lists contain personal data: keep them where the data already lives.
"""
from __future__ import annotations

import pandas as pd


def match_rate(records: pd.DataFrame, id_col: str, linked_ids) -> float:
    """Share (%) of records in `records` whose id appears in `linked_ids`."""
    ids = records[id_col].dropna().astype(str)
    if not len(ids):
        return 0.0
    return round(100 * ids.isin(set(map(str, linked_ids))).mean(), 3)


def clerical_review(pairs: pd.DataFrame, threshold: float = 0.9, prob_col: str = "match_probability",
                    truth_col: str = "is_match") -> dict:
    """Precision and recall from a reviewed sample. `pairs` has one row per candidate pair, with the tool's
    match probability and the reviewer's verdict (True/False). Pairs at or above `threshold` were accepted."""
    p = pairs[[prob_col, truth_col]].dropna()
    accepted = p[prob_col].astype(float) >= threshold
    truth = p[truth_col].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    tp, fp, fn = int((accepted & truth).sum()), int((accepted & ~truth).sum()), int((~accepted & truth).sum())
    precision = round(100 * tp / (tp + fp), 3) if tp + fp else None
    recall = round(100 * tp / (tp + fn), 3) if tp + fn else None
    return {"reviewed": len(p), "threshold": threshold, "true_matches_found": tp, "false_matches": fp, "missed_matches": fn,
            "precision": precision, "recall": recall,
            "note": "Estimated from a reviewed sample. Review pairs from across the probability range, not only borderline ones."}


def match_rate_by_group(records: pd.DataFrame, id_col: str, group_col: str, linked_ids, tolerance: float = 5.0,
                        min_group: int = 10) -> dict:
    """Match rate per group, and whether the gap between the best and worst group is within `tolerance` points.
    Groups with fewer than `min_group` records are reported as suppressed, so small groups can't be identified."""
    linked = set(map(str, linked_ids))
    by, suppressed = {}, []
    for g, part in records.groupby(records[group_col].fillna("Not known").astype(str)):
        if len(part) < min_group:
            suppressed.append(g)
            continue
        by[g] = round(100 * part[id_col].astype(str).isin(linked).mean(), 3)
    gap = round(max(by.values()) - min(by.values()), 3) if len(by) > 1 else 0.0
    return {"by_group": by, "gap_points": gap, "tolerance": tolerance, "within_tolerance": gap <= tolerance,
            "suppressed_groups": suppressed, "min_group": min_group}


def from_splink(predictions: pd.DataFrame, threshold: float = 0.9, left: str = "unique_id_l", right: str = "unique_id_r") -> set:
    """The record ids that were linked at or above `threshold`, from Splink's predictions table
    (linker.inference.predict().as_pandas_dataframe())."""
    acc = predictions[predictions["match_probability"].astype(float) >= threshold]
    return set(acc[left].astype(str)) | set(acc[right].astype(str))
