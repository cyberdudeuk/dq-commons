"""Publish repository docs to Confluence pages (create or update), as listed in integrations/config.yaml.

Run by .github/workflows/docs-to-confluence.yml on merge to main. Needs CONFLUENCE_BASE_URL,
JIRA_EMAIL and JIRA_API_TOKEN (Atlassian Cloud uses the same account token for both). Without
them it prints what it would publish and exits 0.

Markdown is converted to Confluence storage format with a small built-in converter (headings,
paragraphs, lists, tables, code, bold, links). Confluence keeps the page history, so every publish
can be compared and rolled back there.
"""
from __future__ import annotations

import base64
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', t)
    return t


def md_to_storage(md: str) -> str:
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            code = "\n".join(lines[i + 1:j]).replace("]]>", "]]]]><![CDATA[>")
            out.append(f'<ac:structured-macro ac:name="code"><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>')
            i = j + 1
            continue
        m = re.match(r"(#{1,6}) (.*)", ln)
        if m:
            out.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>")
            i += 1
            continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"\|[-| :]+\|$", lines[i + 1].strip()):
            head = [c.strip() for c in ln.strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip("|").split("|")])
                j += 1
            t = "<table><tbody><tr>" + "".join(f"<th>{inline(h)}</th>" for h in head) + "</tr>"
            t += "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table>"
            out.append(t)
            i = j
            continue
        if re.match(r"\s*([-*]|\d+\.) ", ln):
            ordered = bool(re.match(r"\s*\d+\. ", ln))
            items, j = [], i
            while j < len(lines) and re.match(r"\s*([-*]|\d+\.) ", lines[j]):
                items.append(re.sub(r"\s*([-*]|\d+\.) ", "", lines[j], count=1))
                j += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            i = j
            continue
        if ln.strip():
            para = [ln]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(r"(#|\||```|\s*([-*]|\d+\.) )", lines[j]):
                para.append(lines[j])
                j += 1
            out.append(f"<p>{inline(' '.join(p.strip() for p in para))}</p>")
            i = j
            continue
        i += 1
    return "\n".join(out)


def _req(method, url, auth, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")


def publish(title: str, storage: str, cfg: dict) -> str:
    base = os.environ["CONFLUENCE_BASE_URL"].rstrip("/")
    auth = base64.b64encode(f"{os.environ['JIRA_EMAIL']}:{os.environ['JIRA_API_TOKEN']}".encode()).decode()
    c = cfg["confluence"]
    q = urllib.parse.urlencode({"spaceKey": c["space"], "title": title, "expand": "version"})
    found = _req("GET", f"{base}/rest/api/content?{q}", auth).get("results", [])
    body = {"type": "page", "title": title, "space": {"key": c["space"]},
            "body": {"storage": {"value": storage, "representation": "storage"}}}
    if found:
        page = found[0]
        body["version"] = {"number": page["version"]["number"] + 1, "message": "Published from the repository"}
        _req("PUT", f"{base}/rest/api/content/{page['id']}", auth, body)
        return f"updated {page['id']}"
    body["ancestors"] = [{"id": c["parent_page_id"]}]
    return "created " + _req("POST", f"{base}/rest/api/content", auth, body)["id"]


def main() -> int:
    cfg = yaml.safe_load((ROOT / "integrations" / "config.yaml").read_text(encoding="utf-8"))
    live = all(os.environ.get(k) for k in ("CONFLUENCE_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"))
    for path, title in cfg["confluence"]["pages"].items():
        p = ROOT / path
        if not p.exists():
            print(f"skip {path}: not found")
            continue
        storage = md_to_storage(p.read_text(encoding="utf-8"))
        print(f"{title}: " + (publish(title, storage, cfg) if live else f"dry run ({len(storage)} characters)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
