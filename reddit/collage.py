"""Reddit collage for Bloody Place Names: reddit/bloody_place_names.png (2400 x 3000 px).
Reads ../data/named_features.csv, ../data/battles_gb.csv, ../data/results.json and ../work/gb_outline.json.
Fonts (Fraunces, Source Serif 4, IBM Plex Mono) from FONT_DIR. Usage: FONT_DIR=... python3 reddit/collage.py
"""
import json
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts") + "/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"

BG, FG, MUT = "#1D2B26", "#EFE6D6", "#A9B3A9"
LAND, RED, RED2, BONE = "#2A3B35", "#E3392F", "#8E2A26", "#E9DFCC"

R = json.load(open(os.path.join(ROOT, "data", "results.json")))
M = pd.read_csv(os.path.join(ROOT, "data", "named_features.csv"))
B = pd.read_csv(os.path.join(ROOT, "data", "battles_gb.csv"))
B = B[(B.flag.fillna("") == "") & ~(B.year > R["latest_year"])]
OUT = json.load(open(os.path.join(ROOT, "work", "gb_outline.json")))
T = R["terms"]


def land(ax, lw=0):
    for p in OUT:
        ax.add_patch(Polygon(np.array(p), closed=True, fc=LAND, ec="#3A4E46", lw=lw, zorder=0))
    ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.045, 0.968, "Bloody place names", fontproperties=DISP, fontsize=58, color=FG, va="top")
fig.text(0.047, 0.899, f"Britain's map is full of Battles, Bloody Meadows, Slaughters and Gallows Hills. I measured all {R['n_matched_features']:,}\n"
         f"grim names on the Ordnance Survey map against {R['battles']['n_main']:,} recorded battles and sieges. Do they mark real fights?",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.4)

# hero map
ax = fig.add_axes([0.0, 0.285, 0.6, 0.53]); land(ax, .6)
ax.set_xlim(-10000, 660000); ax.set_ylim(0, 1000000)
ax.scatter(B.x, B.y, s=14, marker="x", c=BONE, linewidths=.9, alpha=.45, zorder=2)
far, near = M[M.dist_km > 2], M[M.dist_km <= 2]
ax.scatter(far.x, far.y, s=7, c=RED2, lw=0, alpha=.95, zorder=3)
ax.scatter(near.x, near.y, s=150, c=RED, lw=0, alpha=.18, zorder=4)
ax.scatter(near.x, near.y, s=22, c=RED, lw=0, zorder=5)


def ann(name, area, text, dx, dy, ha="left"):
    r = M[(M.name == name) & (M.area == area)].iloc[0]
    ax.annotate(text, (r.x, r.y), xytext=(r.x + dx, r.y + dy), family=MONO, fontsize=10.5, color=FG, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=FG, lw=.7, shrinkA=0, shrinkB=3), zorder=6)


ann("Battle", "East Sussex", f"Battle\n{T['battle']['closest'][3]['km']:.1f} km from Hastings", -60000, -75000, "right")
ann("Battlefield", "Shropshire", "Battlefield\nShrewsbury, 1403", -150000, 50000, "right")
ann("Bloody Meadow", "Gloucestershire", "Bloody Meadow\nTewkesbury, 1471", -120000, -40000, "right")
ann("Upper Slaughter", "Gloucestershire", "Upper Slaughter\nthe name means\n'wet land'*", 95000, 15000)
ann("Killiecrankie", "Perth and Kinross", "Killiecrankie\nthe battle took\nthe place's name", -150000, 30000, "right")
ann("Battle Moor", "Northumberland", "Battle Moor\nGrindon, 1558", 70000, 30000)
hs = [plt.Line2D([], [], ls="none", marker="o", color=RED, ms=7), plt.Line2D([], [], ls="none", marker="o", color=RED2, ms=5),
      plt.Line2D([], [], ls="none", marker="x", color=BONE, ms=7, mew=1.2)]
fig.legend(hs, [f"name within 2 km of a battle  {R['n_near2']}", f"name further away  {R['n_matched_features'] - R['n_near2']}",
               f"recorded battle or siege  {R['battles']['n_main']}"], loc="upper left", bbox_to_anchor=(0.035, 0.846), ncol=3, columnspacing=1.6, frameon=False,
          prop={"family": MONO, "size": 11}, labelcolor=FG, handletextpad=.4, labelspacing=.6)

# right column: big numbers
tx = fig.add_axes([0.62, 0.30, 0.36, 0.505]); tx.axis("off")
notes = [(f"{R['n_near2']} of {R['n_matched_features']}", "grim names lie within 2 km of a battle\nor siege recorded in Wikidata."),
         (f"{R['share_far_10'] * 100:.0f}%", "are more than 10 km from any.\nMost are red herrings."),
         (f"{T['battle']['ratio_within_2']:.1f}×", f"Names with \"Battle\" are the exception:\n{T['battle']['n_within_2']} of {T['battle']['n']} lie within 2 km of a battle,\n"
          f"against {T['battle']['exp_within_2']:.1f} expected from matched\nordinary names of the same kind."),
         (f"{R['battles_with_name_2km']} vs {R['battles_with_name_2km_base']:.0f}", "battles with a grim name within 2 km,\nagainst the number chance would give.\nAbout half the hits are coincidence.")]
for (big, small), y in zip(notes, [1.0, .75, .52, .2]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=31, color=RED, va="top", transform=tx.transAxes)
    tx.text(0, y - .085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# bottom row: distance curves against the matched baseline
fig.text(0.045, 0.27, "HOW CLOSE TO A RECORDED BATTLE?  share of names within each distance (red) against matched ordinary names (band)",
         family=MONO, fontsize=10.5, color=MUT)
for i, k in enumerate(["battle", "blood", "gallows", "kill"]):
    a = fig.add_axes([0.06 + i * 0.235, 0.098, 0.19, 0.14], facecolor=BG)
    c = T[k]["curve"]; g = np.arange(len(c["obs"]))
    a.fill_between(g, c["lo"], c["hi"], color=MUT, alpha=.28, lw=0)
    a.plot(g, c["base"], color=MUT, lw=1, ls=(0, (3, 2)))
    a.plot(g, c["obs"], color=RED, lw=2.6)
    a.set_xlim(0, 20); a.set_ylim(0, .85)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    for s in ("left", "bottom"): a.spines[s].set_color(MUT)
    a.tick_params(colors=MUT, labelsize=10)
    a.set_xticks([0, 5, 10, 15, 20]); a.set_xticklabels(["0", "5", "10", "15", "20 km"], family=MONO)
    a.set_yticks([0, .4, .8]); a.set_yticklabels(["0%", "40%", "80%"], family=MONO)
    lab = T[k]["label"].replace("Blood / Bloody", "Blood(y)")
    a.set_title(f"{lab}  ({T[k]['n']} names)", family=MONO, fontsize=12, color=FG, loc="left", pad=6)
    a.text(.97, .06, f"{T[k]['n_within_2']} within 2 km\n{T[k]['exp_within_2']:.1f} expected", transform=a.transAxes, ha="right",
           va="bottom", family=MONO, fontsize=10, color=FG)

fig.text(0.045, 0.016, "Data: OS Open Names, contains OS data © Crown copyright and database right 2026 (OGL v3). Battles and sieges to 1900 with a\n"
         "Wikidata coordinate (CC0). Baseline: 2,000 random OS names of the same type in the same 50 km square. *Wikipedia, Upper Slaughter.\n"
         "A match means only that a name contains the word. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(HERE, "bloody_place_names.png"), facecolor=BG, dpi=200)
print("ok")
