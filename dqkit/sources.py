"""Read data from wherever it lives, as a table of text values the checks can run on.

Every reader returns the same shape the CSV reader always has: a pandas DataFrame of strings,
with blanks as missing values. So a rule gives the same answer whether the data came from a CSV,
a spreadsheet, a database or a data portal.

Supported:
    csv, tsv              a file path
    xlsx, xlsm, ods       a spreadsheet file (choose the sheet with `sheet`)
    json, jsonl           a list of records, or {"data": [...]} / {"records": [...]} / {"result": {"records": [...]}}
    parquet               needs the optional pyarrow library
    sqlite                a SQLite file, opened read-only, with `table` or a read-only `query`
    sql                   any database SQLAlchemy can reach (needs SQLAlchemy and a driver), with `url` and `table` or `query`
    ckan                  a CKAN data portal: `url` (portal address), `dataset`, and optionally `resource` (name or format)

A source can be a plain path (the type is taken from the extension) or a dict, for example:
    {"type": "xlsx", "path": "returns.xlsx", "sheet": "2025-26"}
    {"type": "sqlite", "path": "local.db", "query": "select * from people"}
    {"type": "ckan", "url": "https://demo.ckan.org", "dataset": "my-dataset", "resource": "CSV"}
"""
from __future__ import annotations

import io
import json
import re
import sqlite3
from pathlib import Path
from typing import Union
from urllib.parse import quote

import pandas as pd

TYPES = ("csv", "tsv", "xlsx", "xlsm", "ods", "json", "jsonl", "parquet", "sqlite", "sql", "ckan")
EXT = {".csv": "csv", ".tsv": "tsv", ".txt": "csv", ".xlsx": "xlsx", ".xlsm": "xlsm", ".ods": "ods", ".json": "json",
       ".jsonl": "jsonl", ".ndjson": "jsonl", ".parquet": "parquet", ".pq": "parquet", ".db": "sqlite",
       ".sqlite": "sqlite", ".sqlite3": "sqlite"}
READ_ONLY_SQL = re.compile(r"^\s*(select|with)\b", re.I)
WRITE_WORDS = re.compile(r"\b(insert|update|delete|drop|alter|create|replace|attach|pragma|truncate|grant|merge)\b", re.I)


class SourceError(ValueError):
    """A plain-English problem reading a data source."""


def _as_text(df: pd.DataFrame) -> pd.DataFrame:
    """Strings everywhere, blanks and nulls as missing: the same as reading a CSV with dtype=str."""
    def cell(v):
        if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT:
            return None
        if isinstance(v, float) and v.is_integer():
            v = int(v)  # 2024.0 from a spreadsheet reads as 2024, as it would in a CSV
        if hasattr(v, "isoformat") and not isinstance(v, str):
            v = v.isoformat()
            v = v[:-9] if v.endswith("T00:00:00") else v
        s = str(v)
        return None if s == "" else s
    # Round-trip through CSV text so blanks, types and missing values behave exactly as for a CSV file.
    buf = io.StringIO()
    import csv as _csv
    w = _csv.writer(buf, lineterminator="\n")
    w.writerow([str(c) for c in df.columns])
    for row in df.itertuples(index=False):
        w.writerow(["" if (x := cell(v)) is None else x for v in row])
    if not len(df.columns):
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(buf.getvalue()), dtype=str, keep_default_na=False, na_values=[""])


def describe(source) -> str:
    if isinstance(source, (str, Path)):
        return str(source)
    s = dict(source)
    return f"{s.get('type')}: " + ", ".join(f"{k}={v}" for k, v in s.items() if k != "type" and k not in ("password",))


def normalise(source, base: Union[str, Path, None] = None) -> dict:
    """Return a dict source with a type, and paths made absolute against base."""
    if isinstance(source, (str, Path)):
        p = Path(source)
        t = EXT.get(p.suffix.lower())
        if not t:
            raise SourceError(f"can't tell what kind of file '{p.name}' is from its extension. "
                              f"Give a type, one of: {', '.join(TYPES)}")
        source = {"type": t, "path": str(p)}
    s = dict(source)
    if s.get("type") not in TYPES:
        raise SourceError(f"unknown source type {s.get('type')!r}; use one of: {', '.join(TYPES)}")
    if "path" in s and base is not None and not Path(s["path"]).is_absolute():
        s["path"] = str(Path(base) / s["path"])
    return s


def _sql_text(s: dict) -> str:
    if s.get("query"):
        q = str(s["query"])
        if not READ_ONLY_SQL.match(q) or WRITE_WORDS.search(q) or ";" in q.strip().rstrip(";"):
            raise SourceError("the query must be a single read-only SELECT (or WITH ... SELECT) statement")
        return q.strip().rstrip(";")
    t = s.get("table")
    if not t or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", str(t)):
        raise SourceError("give a 'table' (letters, digits and underscores) or a read-only 'query'")
    return f"SELECT * FROM {t}"


def read(source, base: Union[str, Path, None] = None, session=None) -> pd.DataFrame:
    """Read any supported source into a table of text values."""
    s = normalise(source, base)
    t = s["type"]
    try:
        if t in ("csv", "tsv"):
            return pd.read_csv(s["path"], dtype=str, keep_default_na=False, na_values=[""], encoding=s.get("encoding", "utf-8-sig"),
                               sep="\t" if t == "tsv" else s.get("sep", ","))
        if t in ("xlsx", "xlsm", "ods"):
            df = pd.read_excel(s["path"], sheet_name=s.get("sheet", 0), header=s.get("header_row", 0),
                               engine="odf" if t == "ods" else "openpyxl")
            return _as_text(df)
        if t in ("json", "jsonl"):
            text = Path(s["path"]).read_text(encoding="utf-8-sig")
            if t == "jsonl":
                recs = [json.loads(line) for line in text.splitlines() if line.strip()]
            else:
                doc = json.loads(text)
                recs = doc
                if isinstance(doc, dict):
                    recs = doc.get("data") or doc.get("records") or (doc.get("result") or {}).get("records")
                if not isinstance(recs, list):
                    raise SourceError("the JSON must be a list of records, or have a 'data' or 'records' list")
            return _as_text(pd.DataFrame.from_records(recs))
        if t == "parquet":
            try:
                import pyarrow  # noqa: F401
            except ImportError:
                raise SourceError("reading Parquet needs the pyarrow library: pip install pyarrow") from None
            return _as_text(pd.read_parquet(s["path"]))
        if t == "sqlite":
            p = Path(s["path"])
            if not p.exists():
                raise SourceError(f"no SQLite file at {p}")
            con = sqlite3.connect(f"file:{quote(str(p.resolve()))}?mode=ro", uri=True)
            try:
                return _as_text(pd.read_sql_query(_sql_text(s), con))
            finally:
                con.close()
        if t == "sql":
            try:
                import sqlalchemy
            except ImportError:
                raise SourceError("reading from a database needs SQLAlchemy and a driver: pip install sqlalchemy") from None
            eng = sqlalchemy.create_engine(s["url"])
            with eng.connect() as con:
                return _as_text(pd.read_sql_query(sqlalchemy.text(_sql_text(s)), con))
        if t == "ckan":
            return _read_ckan(s, session)
    except SourceError:
        raise
    except FileNotFoundError:
        raise SourceError(f"no file at {s.get('path')}") from None
    except Exception as e:  # noqa: BLE001 - any reader problem is reported plainly
        raise SourceError(f"couldn't read {describe(s)}: {e}") from None
    raise SourceError(f"unsupported source type {t}")


def _read_ckan(s: dict, session=None) -> pd.DataFrame:
    """Find a dataset's resource on a CKAN portal and read it (CSV, XLSX or JSON)."""
    import requests
    http = session or requests.Session()
    base = str(s["url"]).rstrip("/")
    if not base.startswith("https://"):
        raise SourceError("the CKAN portal address must start with https://")
    r = http.get(f"{base}/api/3/action/package_show", params={"id": s["dataset"]}, timeout=s.get("timeout", 30))
    r.raise_for_status()
    pkg = r.json()
    if not pkg.get("success"):
        raise SourceError(f"the portal didn't find dataset {s['dataset']!r}")
    resources = pkg["result"].get("resources", [])
    want = str(s.get("resource", "CSV")).lower()
    pick = [x for x in resources if want in (str(x.get("name", "")).lower(), str(x.get("format", "")).lower(), str(x.get("id", "")).lower())]
    if not pick:
        names = ", ".join(f"{x.get('name')} ({x.get('format')})" for x in resources) or "none"
        raise SourceError(f"no resource matching {s.get('resource', 'CSV')!r} in {s['dataset']}. Resources: {names}")
    res = pick[0]
    fmt = str(res.get("format", "")).lower() or Path(res.get("url", "")).suffix.lstrip(".").lower()
    d = http.get(res["url"], timeout=s.get("timeout", 60))
    d.raise_for_status()
    if fmt in ("csv", "text/csv"):
        return pd.read_csv(io.BytesIO(d.content), dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
    if fmt in ("xlsx", "xls"):
        return _as_text(pd.read_excel(io.BytesIO(d.content), sheet_name=s.get("sheet", 0)))
    if fmt == "json":
        doc = d.json()
        recs = doc if isinstance(doc, list) else doc.get("data") or doc.get("records")
        return _as_text(pd.DataFrame.from_records(recs))
    raise SourceError(f"resource format {fmt!r} isn't supported yet; use CSV, XLSX or JSON")
