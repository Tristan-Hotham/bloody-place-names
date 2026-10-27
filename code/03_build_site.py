"""Step 3. Build ../index.html from page_template.html and prose.html, and ../README.md from README_template.md.

Every number in the text is a placeholder like {{terms.battle.obs_within_5|pct0}}, filled from ../data/results.json.
The compact map data (../work/site.json) and the per-term results are embedded in the page as `const D = ...`.
Formats: int (thousands commas), pct0, pct1, f1, f2, words, raw.

Usage: python3 code/03_build_site.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
site = json.load(open(os.path.join(ROOT, "work", "site.json")))

# per-term numbers the charts need (not the long lists)
keep = ["label", "n", "obs_median", "base_median", "base_median_lo", "base_median_hi", "p_median"]
for c in (1, 2, 5, 10):
    keep += [f"obs_within_{c}", f"base_within_{c}", f"base_within_{c}_lo", f"base_within_{c}_hi", f"p_within_{c}"]
site["R"] = {k: dict({f: v[f] for f in keep}, curve=v["curve"], closest=v.get("closest", []), n_within_5=v["n_within_5"],
                     n_within_2=v["n_within_2"]) for k, v in R["terms"].items()}
site["near2"] = R["near2"]


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "words":
        w = "zero one two three four five six seven eight nine ten eleven twelve".split()
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    if f == "Words":
        return fmt(v, "words").capitalize()
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


t = open(os.path.join(HERE, "page_template.html")).read().replace("<!--PROSE-->", open(os.path.join(HERE, "prose.html")).read())
t = re.sub(r"\{\{(.+?)\}\}", sub, t)
data = json.dumps(site, separators=(",", ":"), ensure_ascii=False).replace("–", "-").replace("—", "-").replace("</", "<\\/")
t = t.replace("/*DATA*/", "const D = " + data + ";")
open(os.path.join(ROOT, "index.html"), "w").write(t)
print("index.html", len(t.encode()) // 1024, "KB")
md = re.sub(r"\{\{(.+?)\}\}", sub, open(os.path.join(HERE, "README_template.md")).read())
open(os.path.join(ROOT, "README.md"), "w").write(md)
print("README.md written")
