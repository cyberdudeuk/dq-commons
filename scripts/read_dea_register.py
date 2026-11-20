"""Read the Digital Economy Act register of information sharing agreements into one CSV, for the worked example in
examples/register-method-field.

  python3 -I scripts/read_dea_register.py --pages DIR --out FILE [--count 667]

DIR holds the register's agreement pages saved as <id>.html, fetched from
https://www.digital-economy-act-register.data.gov.uk/agreements/<id>. The pages are read as untrusted data with the
standard library's HTML parser; nothing in them is run. Contact details on the register are not copied.

Columns: the register's own fields (id, status, method, dates, retention, power, number of controllers), plus two
derived 0/1 columns the rules compare: method_is_api (the method field says API) and text_mentions_api (the
purpose, benefits or disclosed-information text names an API or an Application Programming Interface)."""
import argparse
import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

API = re.compile(r"\bAPIs?\b|Application Programming Interface")
FIELDS = ["agreement_id", "status", "sharing_method", "start_date", "end_date", "review_date", "retention_period", "power",
          "controller_count", "method_is_api", "text_mentions_api"]


class Page(HTMLParser):
    """Collects the summary list (dt/dd pairs) and the items under the Powers and Controllers headings."""
    def __init__(self):
        super().__init__()
        self.fields, self.lists, self._tag, self._buf, self._key, self._head = {}, {}, None, "", None, None

    def handle_starttag(self, tag, attrs):
        if tag in ("dt", "dd", "h2", "h3", "li"):
            self._tag, self._buf = tag, ""

    def handle_data(self, data):
        if self._tag:
            self._buf += data

    def handle_endtag(self, tag):
        if tag != self._tag:
            return
        text = " ".join(self._buf.split())
        if tag == "dt":
            self._key = text
        elif tag == "dd" and self._key:
            self.fields[self._key] = text
            self._key = None
        elif tag in ("h2", "h3"):
            self._head = text
        elif tag == "li" and self._head in ("Powers", "Controllers"):
            self.lists.setdefault(self._head, []).append(text)
        self._tag = None


def read(path: Path, agreement_id: int) -> dict:
    p = Page()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    f = p.fields
    text = " ".join(f.get(k, "") for k in ("Purpose", "Information sharing benefits", "Disclosed information"))
    method = f.get("Information sharing method", "")
    return {"agreement_id": agreement_id, "status": f.get("Isa status", ""), "sharing_method": method,
            "start_date": f.get("Start date", ""), "end_date": f.get("End date", ""), "review_date": f.get("Review date", ""),
            "retention_period": f.get("Retention period", ""), "power": "; ".join(p.lists.get("Powers", [])),
            "controller_count": len(p.lists.get("Controllers", [])),
            "method_is_api": int(method.strip().upper() == "API"), "text_mentions_api": int(bool(API.search(text)))}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=667)
    a = ap.parse_args()
    rows = [read(Path(a.pages) / f"{i}.html", i) for i in range(1, a.count + 1)]
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    summary = {"rows": len(rows), "sha256": hashlib.sha256(Path(a.out).read_bytes()).hexdigest(),
               "active": sum(r["status"] == "Active" for r in rows), "method_api": sum(r["method_is_api"] for r in rows),
               "text_api_not_method": [r["agreement_id"] for r in rows if r["text_mentions_api"] and not r["method_is_api"]]}
    print(json.dumps(summary))
