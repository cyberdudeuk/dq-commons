"""Import evidence from public code (v2.12.0, BL-29): counts of public sector code projects with evidence of each DAMA
knowledge area and each standard, from the GitHub Repos Asset Catalogue's open edition.

Usage: python scripts/import_code_evidence.py PATH/TO/github-repos-asset-catalogue/dist/index.html
Writes knowledge/code-evidence.yaml. Aggregates and a few example public repository names only: no people, no
organisation-level judgements. Re-run whenever the catalogue publishes new data (its data date is recorded).
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AREA_MAP = {"gov": "governance", "arch": "architecture", "model": "modelling", "store": "storage", "sec": "security",
            "integ": "integration", "doc": "content", "ref": "masterdata", "dwbi": "dwbi", "meta": "metadata", "dq": "quality"}
STRONG = set("fid")  # evidence in a file, infrastructure or a dependency (the catalogue's own rule)


def load(path: Path) -> dict:
    h = path.read_text(encoding="utf-8")
    i = h.index("const DATA = ") + len("const DATA = ")
    data, _ = json.JSONDecoder().raw_decode(h[i:])
    if (data.get("sec") or {}).get("audience") != "public":
        sys.exit("Refusing: this is not the catalogue's open (public) edition.")
    return data


def main(path: str) -> None:
    d = load(Path(path))
    wheel = {a["id"] for a in yaml.safe_load((ROOT / "knowledge" / "dama-wheel.yaml").read_text(encoding="utf-8"))["areas"]}
    caps = d["dama"]["caps"]
    repos, strong, examples = defaultdict(set), defaultdict(set), defaultdict(list)
    for key, cs, _vend, _mask in d["dama"]["recs"]:
        for ci, kind, _s in cs:
            a = AREA_MAP.get(caps[ci].split("-")[0])
            if not a:
                continue
            repos[a].add(key)
            if STRONG & set(kind):
                strong[a].add(key)
                if key not in examples[a] and len(examples[a]) < 5:
                    examples[a].append(key)
    areas = []
    for a in sorted(repos, key=lambda x: -len(repos[x])):
        if a not in wheel:
            continue
        areas.append({"id": a, "repos": len(repos[a]), "in_code": len(strong[a]),
                      "orgs": len({k.split("/")[0] for k in repos[a]}), "examples": examples[a]})
    S = d["std"]
    lv = defaultdict(Counter)
    orgs = defaultdict(set)
    ex = defaultdict(list)
    for key, v in S["repos"].items():
        for name, (level, _notes) in v.get("s", {}).items():
            lv[name][int(level)] += 1
            orgs[name].add(key.split("/")[0])
            if level >= 3 and len(ex[name]) < 5:
                ex[name].append(key)
    standards = [{"name": n, "repos": sum(lv[n].values()), "applied_in_data": lv[n][3] + lv[n][4], "every_record": lv[n][4],
                  "orgs": len(orgs[n]), "examples": ex[n]} for n in sorted(lv, key=lambda n: -sum(lv[n].values()))]
    out = {"review": {"last_reviewed": date.today().isoformat(), "owner_role": "Product owner (Commons)"},
           "source": {"name": "GitHub Repos Asset Catalogue (open edition)", "url": "https://cyberdudeuk.github.io/github-repos-asset-catalogue/",
                      "version": d.get("version", ""), "data_as_of": d["meta"].get("ref_date", ""), "licence": "Open Government Licence v3.0",
                      "method": "Counts of public code projects whose files, dependencies or infrastructure (in code) or names and descriptions show each knowledge area, and standards graded 1 to 4 per repository (mentioned, schema or profile, applied in data, every record). Evidence of use, not a census: private code and catalogue databases are not visible."},
           "levels": {int(k): v for k, v in S["levels"].items()},
           "areas": areas, "standards": standards}
    target = ROOT / "knowledge" / "code-evidence.yaml"
    target.write_text("# Evidence from public code, imported by scripts/import_code_evidence.py (BL-29). Do not edit by hand.\n" +
                      yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8")
    print(f"Wrote {target}: {len(areas)} areas, {len(standards)} standards (data as of {out['source']['data_as_of']})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT.parent / "github-repos-asset-catalogue" / "dist" / "index.html"))
