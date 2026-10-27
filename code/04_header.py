"""Step 4. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: set FONT_DIR to a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf and IBMPlexMono-Regular.ttf
(from github.com/google/fonts); otherwise system serif fonts are used.
Usage: FONT_DIR=/path/to/fonts python3 code/04_header.py
"""
import json
import math
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = json.load(open(os.path.join(ROOT, "work", "site.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")


def proj(lat, lon):
    return lon * math.cos(math.radians(54.5)), -lat


pts = [proj(r[0], r[1]) for r in S["pts"]]
bat = [proj(r[0], r[1]) for r in S["battles"]]
xs, ys = zip(*(pts + bat))
x0, y0, y1 = min(xs), min(ys), max(ys)
H = 600
PAD = 8
sc = (H - 2 * PAD) / (y1 - y0)
P = lambda p: ((p[0] - x0) * sc + PAD, (p[1] - y0) * sc + PAD)
W = (max(xs) - x0) * sc + 2 * PAD
dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6"/>' for x, y in map(P, pts))
sw = "".join(f'<path d="M{x-2.6:.1f} {y-2.6:.1f}l5.2 5.2M{x+2.6:.1f} {y-2.6:.1f}l-5.2 5.2"/>' for x, y in map(P, bat))
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:#F4EFE6;color:#1E1A17;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:70px;font:400 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#6C6259;display:flex;gap:12px;align-items:center}}
.k b{{background:#A4161A;color:#fff;padding:7px 9px;font-weight:400}}
h1{{position:absolute;left:64px;top:112px;margin:0;font:900 118px/.88 Fraunces,Georgia,serif;letter-spacing:-.02em}}
h1 em{{font-style:normal;color:#A4161A;display:block}}
p{{position:absolute;left:70px;top:440px;width:560px;margin:0;font-size:26px;line-height:1.36}}
.f{{position:absolute;left:70px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#6C6259}}
svg{{position:absolute;right:70px;top:15px}}
</style></head><body>
<div class="k"><b>Data study</b><span>History × place names</span></div>
<h1>Bloody<em>place names</em></h1>
<p>{R['n_matched_features']:,} grim names on the map of Britain, tested against {R['battles']['n_main']:,} recorded battles.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{W:.0f}" height="{H}" viewBox="0 0 {W:.0f} {H}"><g stroke="#2A2522" stroke-width="1.3" stroke-opacity=".45" fill="none">{sw}</g><g fill="#A4161A" fill-opacity=".85">{dots}</g></svg>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html")
open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp))
    pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png"))
    b.close()
os.remove(tmp)
print("header.png written")
