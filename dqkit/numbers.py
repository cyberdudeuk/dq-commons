"""Reading numbers from text, the same way in Python and in the browser.

The toolkit used to rely on pandas.to_numeric, whose parser changed in pandas 3.1. Results then
depended on the installed pandas version. This module owns the rule instead, so the Python kit and
the browser engine (portal/src/js/engine.js, function pdNumber) always agree (issue #25, D-TK-02):

- A number is optional spaces, an optional sign, digits with an optional decimal point (".5" and
  "5." both count), an optional exponent ("1e-3"), then optional spaces. Spaces mean space, tab,
  new line, carriage return, vertical tab and form feed only.
- "inf" and "infinity" (any case, optional sign, no spaces) are infinite.
- The value is the correctly rounded nearest double (IEEE 754), as Python float() and JavaScript
  Number() both give. Anything else (blank, "n/a", "1,000", "1_000", "0x10") is not a number.
- If every value in a column is a whole number written without a point or exponent, the column is
  whole numbers (kept exact when they fit in 64 bits).
"""
from __future__ import annotations

import math
import re

import pandas as pd

_NUM = re.compile(r"[ \t\n\r\v\f]*([+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+))([eE][+-]?[0-9]+)?[ \t\n\r\v\f]*")
_INF = re.compile(r"[+-]?inf(inity)?", re.I)
_I64 = 2 ** 63


def parse(value) -> tuple[float, bool]:
    """(value, written as a whole number). NaN when the text is not a number."""
    if value is None:
        return math.nan, False
    if isinstance(value, bool):
        return float(value), True
    if isinstance(value, int):
        return float(value), True
    if isinstance(value, float):
        return value, False
    s = str(value)
    m = _NUM.fullmatch(s)
    if m:
        text = m.group(1) + (m.group(2) or "")
        return float(text), m.group(2) is None and "." not in m.group(1)
    if _INF.fullmatch(s):
        return (-math.inf if s[0] == "-" else math.inf), False
    return math.nan, False


def to_numeric(values) -> pd.Series:
    """Like pandas.to_numeric(errors="coerce"), with the rule above. Keeps the index of a Series."""
    s = values if isinstance(values, pd.Series) else pd.Series(list(values), dtype=object)
    raw = [None if (v is None or (isinstance(v, float) and math.isnan(v))) else v for v in s.tolist()]
    parsed = [parse(v) for v in raw]
    if parsed and all(w for _, w in parsed):
        ints = [int(v) if isinstance(v, (int, bool)) else int(str(v).strip()) for v in raw]
        if all(-_I64 <= i < _I64 for i in ints):
            return pd.Series(ints, index=s.index, dtype="int64")
    return pd.Series([v for v, _ in parsed], index=s.index, dtype="float64")
