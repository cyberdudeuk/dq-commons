"""Make the Commons recognition badges (v2.12.0) from knowledge/participation.yaml.

Writes to portal/src/badges/ (committed, copied into the portal by the build):
  <id>.svg            a small flat shield for GitHub READMEs and profiles (about 20 pixels high)
  <id>-signature.svg  and .png   a 320 x 80 badge for email signatures
  <id>-square.svg     and .png   a 400 x 400 badge for social media profiles and posts
PNG files need rsvg-convert (librsvg); without it only the SVG files are written.
Original designs: the Commons mark (three overlapping circles), the words and a colour per badge. White text on each
badge colour meets WCAG AA contrast (checked here).
Usage: python scripts/make_badges.py
"""
import shutil
import subprocess
from html import escape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "portal" / "src" / "badges"
FONT = "DejaVu Sans,Verdana,Arial,sans-serif"
MARK = '<g fill="none" stroke="#fff" stroke-width="{w}"><circle cx="{a}" cy="{b}" r="{r}"/><circle cx="{c}" cy="{d}" r="{r}"/><circle cx="{e}" cy="{d}" r="{r}"/></g>'


def lum(hexc):
    h = hexc.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_white(hexc):
    return 1.05 / (lum(hexc) + 0.05)


def mark(x, y, s, w):
    """The Commons mark centred near (x, y), scale s."""
    return MARK.format(w=w, a=x, b=y - 0.35 * s, c=x - 0.3 * s, d=y + 0.18 * s, e=x + 0.3 * s, r=0.38 * s)


def shield(name, color):
    left, right = "DQ Commons", name
    lw, rw = 26 + int(len(left) * 7.1), 14 + int(len(right) * 7.6)
    w = lw + rw
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="DQ Commons: {escape(name)}">
<title>DQ Commons: {escape(name)}</title><rect width="{w}" height="20" rx="3" fill="#33414d"/><rect x="{lw}" width="{rw}" height="20" rx="3" fill="{color}"/><rect x="{lw}" width="4" height="20" fill="{color}"/>
{mark(10, 10, 12, 1.3)}<g fill="#fff" font-family="{FONT}" font-size="11"><text x="20" y="14">{left}</text><text x="{lw + 6}" y="14" font-weight="bold">{escape(right)}</text></g></svg>
'''


def signature(name, color):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="80" viewBox="0 0 320 80" role="img" aria-label="DQ Commons {escape(name)}">
<title>DQ Commons {escape(name)}</title><rect width="320" height="80" rx="12" fill="{color}"/>{mark(40, 40, 44, 3.2)}
<g fill="#fff" font-family="{FONT}"><text x="78" y="33" font-size="15">DQ Commons</text><text x="78" y="57" font-size="21" font-weight="bold">{escape(name)}</text></g></svg>
'''


def square(name, color):
    size = 40 if len(name) < 12 else 30
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400" role="img" aria-label="DQ Commons {escape(name)}">
<title>DQ Commons {escape(name)}</title><rect width="400" height="400" rx="48" fill="{color}"/>{mark(200, 140, 140, 9)}
<g fill="#fff" font-family="{FONT}" text-anchor="middle"><text x="200" y="285" font-size="26">DQ Commons</text><text x="200" y="335" font-size="{size}" font-weight="bold">{escape(name)}</text>
<text x="200" y="372" font-size="15">Public sector data quality</text></g></svg>
'''


def main():
    P = yaml.safe_load((ROOT / "knowledge" / "participation.yaml").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    rsvg = shutil.which("rsvg-convert")
    for b in P["badges"]:
        c = contrast_white(b["color"])
        assert c >= 4.5, f'{b["id"]}: white text contrast {c:.2f} is below 4.5'
        (OUT / f'{b["id"]}.svg').write_text(shield(b["name"], b["color"]), encoding="utf-8")
        for kind, fn in (("signature", signature), ("square", square)):
            svg = OUT / f'{b["id"]}-{kind}.svg'
            svg.write_text(fn(b["name"], b["color"]), encoding="utf-8")
            if rsvg:
                subprocess.run([rsvg, "-z", "2", "-o", str(svg.with_suffix(".png")), str(svg)], check=True)
    print(f'{len(P["badges"])} badges written to {OUT}' + ("" if rsvg else " (SVG only: install librsvg for PNG)"))


if __name__ == "__main__":
    main()
