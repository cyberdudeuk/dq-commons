"""Build the NDL Data Quality Portal from the pipeline's latest results.

Usage:
    python scripts/build_dq_portal.py [--results assessments/portfolio] [--out portal/dist]
                                      [--repo https://github.com/OWNER/REPO] [--artifact DIR]

What it does, in plain English:
1. Reads the latest pipeline results (portfolio.json, metadata-assessment.json, each asset's
   results and history).
2. Fills the portal's page templates (portal/src/pages/*.html) with those results, so every
   number on the portal comes from the same run.
3. Adds the shared top bar, skip link and footer to every page.
4. Writes a complete static website to portal/dist (GitHub Pages publishes this), with the
   result files under downloads/.
5. Optionally (--artifact DIR) writes a copy for a claude.ai artifact: the home page without its
   own <html>/<head> wrapper, and download links pointing to the GitHub repository instead.

It makes no network calls. Nothing here changes the results; it only presents them.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "portal" / "src"
VERSION = "0.4.0"

# (file stem, short label for the bar, longer description for the menu)
PAGES = [
    ("index", "Home", "What the portal is, and where to start for your role"),
    ("pipeline", "Pipeline status", "The latest automated run: trust levels, issues and escalations"),
    ("check", "Check your data", "Run the data quality kit in your browser on your own CSV"),
    ("ndl-assurance", "NDL assurance", "84 NDL data pages tested against GOV.UK requirements"),
    ("baseline", "January baseline", "Effort to report data quality for every critical data asset"),
    ("guidance", "Guidance", "15 sources compared, 18 findings, and the issues framework calculator"),
    ("tooling", "Tooling", "Data quality tools, standards and open code across government"),
    ("share", "Share and learn", "Case studies, the tooling survey review, and messages to other teams"),
]
DOWNLOAD_FILES = ["portfolio.json", "run-summary.md", "cda-return.csv", "escalations.json", "catalogue.dqv.jsonld",
                  "metadata-assessment.json"]


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def js_json(obj) -> str:
    """JSON safe to place inside a <script> element."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")


# ---------- data for each page ----------

def ndl_data(results_dir: Path, port: dict) -> dict:
    """The NDL assurance page's data, rebuilt from the pipeline outputs (same shape as before)."""
    m = json.loads((results_dir / "metadata-assessment.json").read_text(encoding="utf-8"))
    pages = [{"c": p["collection"], "s": p["slug"], "t": p["title"], "p": p["provider"], "sc": p["score"], "r": p["rag"],
              "cov": p["cda_metadata_coverage"], "ev": {c["id"]: c["evidence"] for c in p["checks"]},
              "f": [c["id"] for c in p["checks"] if c["status"] == "fail"],
              "pa": [c["id"] for c in p["checks"] if c["status"] == "partial"]} for p in m["pages"]]
    checks = [{k: c[k] for k in ("id", "label", "source", "dimension", "issue_type", "applicable", "pass", "partial", "fail",
                                 "performance")}
              | {"priority": c["assessment"]["priority"], "target": c["assessment"]["target"],
                 "resolution": c["assessment"]["resolution"]} for c in m["checks"]]
    charts = []
    for a in port["assets"]:
        res = json.loads((results_dir / a["files"]["results"]).read_text(encoding="utf-8"))
        charts.append({"id": a["id"], "t": a["title"].split(": ", 1)[-1].capitalize(), "url": a.get("iri", ""),
                       "rows": res["rows"], "met": res["rules_met"], "tot": res["rules_total"],
                       "trust": res["trust"]["level"], "share": res["trust"]["sharing"],
                       "res": [{"id": r["id"], "d": r["description"], "dim": r["dimension"], "p": r["performance"],
                                "tg": r["assessment"]["target"], "m": r["assessment"]["meets_target"],
                                "pr": r["assessment"]["priority"], "det": r["detail"]} for r in res["results"]]})
    return {"as_of": m["as_of"], "mean": m["mean_score"], "cov": m["mean_cda_coverage"], "rag": m["rag"],
            "collections": m["collections"], "props": m["cda_property_coverage"], "checks": checks, "pages": pages,
            "charts": charts}


def history_series(results_dir: Path, port: dict) -> dict:
    """Per asset: [[date, rules met, rules measured]], from the history CSVs."""
    hdir = results_dir / port.get("files", {}).get("history", "history")
    out = {}
    for a in port["assets"]:
        p = hdir / f"{a['id']}.history.csv"
        by_date: dict = {}
        if p.exists():
            with open(p, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    t = by_date.setdefault(row["date"], [0, 0])
                    t[1] += 1
                    t[0] += str(row["meets_target"]).lower() == "true"
        out[a["id"]] = [[d, v[0], v[1]] for d, v in sorted(by_date.items())]
    return out


def vocab() -> dict:
    """The same vocabulary the parity check gives the browser engine."""
    import sys
    sys.path.insert(0, str(ROOT))
    from dqkit import dqv, rules
    return {"issue_types": rules.ISSUE_TYPES, "dimensions": dqv._dimensions()}


def examples(port_file: Path) -> list:
    """The portfolio's assets as ready-to-run examples for the in-browser checker."""
    doc = yaml.safe_load(port_file.read_text(encoding="utf-8"))
    base = port_file.parent
    out = []
    for e in doc["assets"]:
        rules_text = (base / e["rules"]).read_text(encoding="utf-8")
        spec = yaml.safe_load(rules_text)
        out.append({"id": spec["asset"]["id"], "title": spec["asset"].get("title", spec["asset"]["id"]).split(": ", 1)[-1],
                    "rules": rules_text, "csv": (base / e["data"]).read_text(encoding="utf-8-sig"),
                    "csv_name": Path(e["data"]).name, "rules_name": Path(e["rules"]).name})
    return out


# ---------- page assembly ----------

def nav(active: str, long: bool) -> str:
    parts = []
    for stem, label, desc in PAGES:
        cur = ' aria-current="page"' if stem == active else ""
        inner = f"{html.escape(label)}<small>{html.escape(desc)}</small>" if long else html.escape(label)
        parts.append(f'<a href="{stem}.html"{cur}>{inner}</a>')
    return "".join(parts)


def split_fragment(text: str) -> tuple[str, str]:
    """Split a page fragment into head part (title, links, styles) and body part."""
    m = re.search(r"\n<(div|header|main|section)\b", text)
    if not m:
        raise ValueError("page fragment has no body element")
    return text[:m.start()], text[m.start():]


def assemble(stem: str, fragment: str, build_label: str, footer: str) -> tuple[str, str]:
    """Return (full document, artifact fragment) for one page."""
    shell = (SRC / "shell.html").read_text(encoding="utf-8")
    shell = shell.replace("{{NAV}}", nav(stem, False)).replace("{{NAV_LONG}}", nav(stem, True)).replace("{{BUILD}}", build_label)
    head, body = split_fragment(fragment)
    shell_css, shell_body = shell.split("</style>", 1)
    shell_css += "</style>"
    frag = f"{head}\n{shell_css}\n{shell_body}\n{body}\n{footer}\n"
    doc = ("<!doctype html>\n<html lang=\"en-GB\">\n<head>\n<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
           f"{head}\n{shell_css}\n</head>\n<body style=\"margin:0\">\n{shell_body}\n{body}\n{footer}\n</body>\n</html>\n")
    return doc, frag


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", default=str(ROOT / "assessments" / "portfolio"))
    ap.add_argument("--portfolio", default=str(ROOT / "portfolio.ndl.yaml"))
    ap.add_argument("--out", default=str(ROOT / "portal" / "dist"))
    ap.add_argument("--repo", default="https://github.com/cyberdudeuk/ndl-dq-assurance",
                    help="repository web address, used for source links and (in --artifact mode) downloads")
    ap.add_argument("--artifact", help="also write a claude.ai artifact copy to this folder")
    a = ap.parse_args(argv)

    results_dir, out = Path(a.results), Path(a.out)
    port = json.loads((results_dir / "portfolio.json").read_text(encoding="utf-8"))
    sha = git_sha()
    build_label = f"v{VERSION} · data as of {port['as_of']}"
    data = {
        "__NDL_DATA__": js_json(ndl_data(results_dir, port)),
        "__PORTFOLIO__": js_json(port),
        "__HISTORY__": js_json(history_series(results_dir, port)),
        "__VOCAB__": js_json(vocab()),
        "__EXAMPLES__": js_json(examples(Path(a.portfolio))),
        "__BASE_CSS__": (SRC / "base.css").read_text(encoding="utf-8"),
        "__ENGINE__": (SRC / "js" / "engine.js").read_text(encoding="utf-8").replace("</script", "<\\/script"),
        "__BUILD__": js_json({"version": VERSION, "sha": sha, "built": date.today().isoformat(), "as_of": port["as_of"],
                              "repo": a.repo}),
    }

    def render(target: Path, download_base: str, artifact: bool):
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        footer = (f'<footer class="dqp-foot"><span>NDL Data Quality Portal v{VERSION}</span>'
                  f'<span>Results measured as of {port["as_of"]}; built {date.today().isoformat()} from commit {sha}</span>'
                  f'<span>Code MIT, content OGL v3.0</span><span>A prototype. Not an official GDS product.</span>'
                  f'<a href="{html.escape(a.repo)}">Source code</a></footer>')
        for stem, _, _ in PAGES:
            text = (SRC / "pages" / f"{stem}.html").read_text(encoding="utf-8")
            text = text.replace("__DATA__", data["__NDL_DATA__"]) if stem == "ndl-assurance" else text
            for k, v in data.items():
                text = text.replace(k, v)
            text = text.replace("__DOWNLOADS__", download_base)
            doc, frag = assemble(stem, text, build_label, footer)
            (target / f"{stem}.html").write_text(frag if (artifact and stem == "index") else doc, encoding="utf-8")
        if not artifact:
            dl = target / "downloads"
            (dl / "assets").mkdir(parents=True)
            for f in DOWNLOAD_FILES:
                if (results_dir / f).exists():
                    shutil.copy2(results_dir / f, dl / f)
            for f in (results_dir / "assets").iterdir():
                if f.suffix in (".xlsx", ".docx", ".md", ".csv", ".jsonld", ".json"):
                    shutil.copy2(f, dl / "assets" / f.name)
            (target / ".nojekyll").write_text("", encoding="utf-8")
        print(f"Built {len(PAGES)} pages in {target}")

    render(out, "downloads/", artifact=False)
    if a.artifact:
        rel = results_dir.resolve().relative_to(ROOT).as_posix()
        render(Path(a.artifact), f"{a.repo.rstrip('/')}/blob/main/{rel}/", artifact=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
