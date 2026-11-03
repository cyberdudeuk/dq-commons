"""Write CHARTER.md and CONTRIBUTORS.md from knowledge/build.yaml, so the portal and the repository say the same thing.

Usage: python scripts/gen_community_docs.py [--check]
With --check it exits 1 if the files are out of date (used by the tests and CI).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def charter(k: dict) -> str:
    c = k["charter"]
    out = ["# Co-design and contribution charter", "",
           "_Generated from `knowledge/build.yaml` by `scripts/gen_community_docs.py`. Edit the YAML, not this file._", "",
           c["purpose"], "", "## Principles", ""]
    out += [f"- **{p['title']}.** {p['text']}" for p in c["principles"]]
    out += ["", "## House rules", ""] + [f"- {r}" for r in c["rules"]]
    out += ["", "## Guidelines", ""] + [f"- {r}" for r in c["guidelines"]]
    out += ["", "## Safeguards", ""] + [f"- **{s['title']}.** {s['text']}" for s in c["safeguards"]]
    out += ["", "## How we co-design", "", "| Method | When | How |", "|---|---|---|"]
    out += [f"| {m['method']} | {m['when']} | {m['how']} |" for m in c["codesign"]]
    out += ["", "## Decisions", "",
            "Votes and co-design inform priorities. The product owner role decides and records the reason in `docs/DECISIONS.md`.",
            "", "See also [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).", ""]
    return "\n".join(out)


def contributors(k: dict) -> str:
    c = k["contributors"]
    out = ["# Contributors", "", "_Generated from `knowledge/build.yaml` by `scripts/gen_community_docs.py`._", "", c["how"], "",
           "## Kinds of contribution we recognise", "", "| Kind | What it covers |", "|---|---|"]
    out += [f"| {t['type']} | {t['text']} |" for t in c["types"]]
    out += ["", "## Contributors", "",
            "<!-- ALL-CONTRIBUTORS-LIST:START -->",
            "Contributors are added here by the all-contributors bot when they agree to be credited, by GitHub username or organisation only.",
            "<!-- ALL-CONTRIBUTORS-LIST:END -->", "",
            "To add yourself, comment on an issue or pull request: `@all-contributors please add @your-username for content`.", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    k = yaml.safe_load((ROOT / "knowledge" / "build.yaml").read_text(encoding="utf-8"))
    files = {ROOT / "CHARTER.md": charter(k), ROOT / "CONTRIBUTORS.md": contributors(k)}
    if "--check" in (argv if argv is not None else sys.argv[1:]):
        stale = [p.name for p, t in files.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        if stale:
            print("Out of date:", ", ".join(stale), "- run python scripts/gen_community_docs.py")
            return 1
        return 0
    for p, t in files.items():
        p.write_text(t, encoding="utf-8")
        print("Wrote", p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
