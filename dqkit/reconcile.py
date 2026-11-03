"""Reconcile two versions of a dataset: before and after a migration, or a supplier's extract against yours.

Answers, in plain terms: do the row counts match, is every record in both, are there duplicate keys,
do the totals of number columns agree, and do matched records hold the same values?
Mirrored in the browser engine (DQ.reconcile) and parity-checked.
"""
from __future__ import annotations

import pandas as pd

from .numbers import to_numeric

SEP = "\x1f"


def _key_list(df: pd.DataFrame, keys: list) -> list:
    return [SEP.join("" if pd.isna(v) else str(v) for v in row) for row in df[keys].itertuples(index=False, name=None)]


def _numeric(s: pd.Series):
    n = to_numeric(s)
    filled = int(s.notna().sum())
    return n if filled > 0 and int(n.notna().sum()) == filled else None


def reconcile(source: pd.DataFrame, target: pd.DataFrame, keys: list, tolerance: float = 0.0, max_examples: int = 5) -> dict:
    keys = [keys] if isinstance(keys, str) else list(keys)
    if not keys:
        raise ValueError("choose at least one key column")
    missing = [k for k in keys if k not in source.columns or k not in target.columns]
    if missing:
        raise ValueError("key column(s) not in both files: " + ", ".join(missing))
    sk, tk = _key_list(source, keys), _key_list(target, keys)
    sset, tset = set(sk), set(tk)

    def dups(ks):
        seen, d = set(), []
        for k in ks:
            if k in seen and k not in d:
                d.append(k)
            seen.add(k)
        return d

    def only(a, b):
        out, seen = [], set()
        for k in a:
            if k not in b and k not in seen:
                out.append(k)
                seen.add(k)
        return out
    only_s, only_t, dup_s, dup_t = only(sk, tset), only(tk, sset), dups(sk), dups(tk)
    split = lambda k: k.split(SEP)
    cols_missing = [str(c) for c in source.columns if c not in target.columns]
    cols_extra = [str(c) for c in target.columns if c not in source.columns]
    common = [c for c in source.columns if c in target.columns and c not in keys]

    totals = []
    for c in common:
        a, b = _numeric(source[c]), _numeric(target[c])
        if a is None or b is None:
            continue
        s, t = round(float(a.sum()), 6), round(float(b.sum()), 6)
        d = round(t - s, 6)
        totals.append({"column": str(c), "source": s, "target": t, "difference": d, "ok": abs(d) <= tolerance})

    first_s, first_t = {}, {}
    for i, k in enumerate(sk):
        first_s.setdefault(k, i)
    for i, k in enumerate(tk):
        first_t.setdefault(k, i)
    matched = [k for k in first_s if k in first_t]
    mismatches = []
    for c in common:
        sv, tv = source[c].tolist(), target[c].tolist()
        n, ex = 0, []
        for k in matched:
            a, b = sv[first_s[k]], tv[first_t[k]]
            a = None if pd.isna(a) else str(a)
            b = None if pd.isna(b) else str(b)
            if a != b:
                n += 1
                if len(ex) < max_examples:
                    ex.append({"key": split(k), "source": a, "target": b})
        if n:
            mismatches.append({"column": str(c), "count": n, "examples": ex})

    passed = (len(source) == len(target) and not only_s and not only_t and not dup_s and not dup_t and not cols_missing
              and all(t["ok"] for t in totals) and not mismatches)
    return {"keys": keys, "rows": {"source": len(source), "target": len(target)}, "matched": len(matched),
            "only_in_source": {"count": len(only_s), "examples": [split(k) for k in only_s[:max_examples]]},
            "only_in_target": {"count": len(only_t), "examples": [split(k) for k in only_t[:max_examples]]},
            "duplicate_keys": {"source": len(dup_s), "target": len(dup_t),
                               "examples": [split(k) for k in (dup_s + dup_t)[:max_examples]]},
            "columns_missing_in_target": cols_missing, "columns_extra_in_target": cols_extra,
            "totals": totals, "mismatches": mismatches, "passed": passed}
