"""Step 1. Read OS Open Names and the Wikidata battles; match the terms; keep the battles in Great Britain.

Inputs (read in place, not copied):
  ../osnames_gb.tsv                                   OS Open Names GB extract (OGL v3)
  ../_data2/wikidata/battles_world.json               Wikidata battles, sieges and naval battles (CC0)
  ../how-roman-is-your-road/data/counties.geojson     GB county outlines from ONS boundaries (OGL v3), used as the land mask
Outputs:
  data/named_features.csv   one row per OS feature whose name contains a term
  data/battles_gb.csv       recorded battles and sieges with a Wikidata point on or within 2 km of GB land
  work/all_features.npz     x, y, local type and region of every OS feature (the baseline pool)
  work/gb_outline.json      simplified GB land outline in British National Grid metres (for static maps)

Usage: python3 code/01_data.py
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import shape, mapping

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import terms  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.dirname(ROOT)
TSV = os.path.join(HIST, "osnames_gb.tsv")
BAT = os.path.join(HIST, "_data2", "wikidata", "battles_world.json")
CTY = os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)

TO_BNG = Transformer.from_crs(4326, 27700, always_xy=True)
FLAGS = {"Q842796": "excluded: Wikidata longitude 0.339 E puts the battle in Essex, about 47 km east of St Albans; the sign appears to be wrong"}
TYPES = {"Q178561": "battle", "Q188055": "siege", "Q1261499": "naval battle", "Q831663": "military campaign"}


def main():
    # ---------------- land mask ----------------
    g = json.load(open(CTY))
    geoms = [shapely.transform(shape(f["geometry"]), lambda c: np.column_stack(TO_BNG.transform(c[:, 0], c[:, 1])))
             for f in g["features"]]
    land = shapely.union_all([x.buffer(0) for x in geoms]).simplify(150)
    land2 = land.buffer(2000)
    shapely.prepare(land2)
    out = land.simplify(1200)
    polys = [p for p in getattr(out, "geoms", [out]) if p.area > 25e6]
    json.dump([[list(map(lambda v: round(v), xy)) for xy in np.asarray(p.exterior.coords)] for p in polys],
              open(os.path.join(ROOT, "work", "gb_outline.json"), "w"))

    # ---------------- battles ----------------
    raw = json.load(open(BAT))
    rows = {}
    for r in raw:
        m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", r.get("c", ""))
        if not m:
            continue
        lon, lat = float(m.group(1)), float(m.group(2))
        if not (-9 < lon < 2.5 and 49.5 < lat < 61.5):
            continue
        q = r["b"]
        d = r.get("d") or r.get("d2") or ""
        if q not in rows:
            rows[q] = dict(qid=q, name=r.get("bLabel", q), types=set(), lon=lon, lat=lat, date=d,
                           enwiki=r.get("enwiki", ""), n_points=1)
        else:
            if (lon, lat) != (rows[q]["lon"], rows[q]["lat"]):
                rows[q]["n_points"] += 1
            if d and (not rows[q]["date"] or d < rows[q]["date"]):
                rows[q]["date"] = d
        rows[q]["types"].add(TYPES.get(r["t"], r["t"]))
    b = pd.DataFrame(rows.values())
    b["x"], b["y"] = TO_BNG.transform(b.lon.values, b.lat.values)
    b["on_land"] = [land2.contains(shapely.Point(x, y)) for x, y in zip(b.x, b.y)]
    b["year"] = b.date.str.slice(0, 4).replace("", np.nan).astype(float)
    b["kind"] = b.types.map(lambda s: "battle" if "battle" in s else ("siege" if "siege" in s else sorted(s)[0]))
    b["types"] = b.types.map(lambda s: ";".join(sorted(s)))
    n_bbox = len(b)
    # keep land battles and sieges on GB land (or within 2 km of it); naval-only items and campaigns are dropped
    keep = b[b.on_land & b.kind.isin(["battle", "siege"])].copy()
    # Ireland, Isle of Man and the Channel coast of France fall outside the GB land mask; keep a record
    keep["coord_source"] = "Wikidata P625 (coordinate location), via the shared battles_world.json extract"
    keep = keep.sort_values(["year", "name"])
    # one clear coordinate error found while checking results: excluded, not corrected
    keep["flag"] = keep.qid.map(FLAGS).fillna("")
    # automated check: battles named "Battle/Siege of <Place>" where <Place> is an OS populated place name;
    # distance from the Wikidata point to the nearest OS place of that name (same names elsewhere inflate this)
    pp = d_pp = pd.read_csv(TSV, sep="\t", dtype=str, keep_default_na=False, usecols=["name1", "type", "x", "y"])
    pp = pp[pp.type == "populatedPlace"].copy()
    pp["x"], pp["y"], pp["k"] = pp.x.astype(float), pp.y.astype(float), pp.name1.str.lower()
    grp = pp.groupby("k")
    chk = []
    for r in keep.itertuples():
        mm = re.search(r"(?:Battle|Siege|Sack|Raid) of (?:the )?(.+)$", r.name)
        if not mm:
            chk.append(np.nan); continue
        pl = re.sub(r"\s*\(.*\)", "", mm.group(1).strip().lower())
        chk.append(float(np.hypot(grp.get_group(pl).x - r.x, grp.get_group(pl).y - r.y).min() / 1000) if pl in grp.groups else np.nan)
    keep["namecheck_km"] = np.round(chk, 1)
    keep[["qid", "name", "kind", "types", "year", "date", "lat", "lon", "x", "y", "n_points", "enwiki", "coord_source", "namecheck_km", "flag"]].round(
        {"x": 0, "y": 0}).to_csv(os.path.join(ROOT, "data", "battles_gb.csv"), index=False)
    print("battles in bbox", n_bbox, "kept on GB land", len(keep), keep.kind.value_counts().to_dict())
    json.dump({"n_bbox_items": int(n_bbox), "n_bbox_naval_only": int((b.kind == "naval battle").sum()),
               "n_offland": int((~b.on_land & b.kind.isin(["battle", "siege"])).sum())},
              open(os.path.join(ROOT, "work", "battle_counts.json"), "w"))

    # ---------------- OS names ----------------
    d = pd.read_csv(TSV, sep="\t", dtype=str, keep_default_na=False)
    for c in ("lat", "lon"):
        d[c] = d[c].astype(float)
    for c in ("x", "y"):
        d[c] = d[c].astype(int)
    d["area"] = d["county"].where(d["county"] != "", d["district"])
    d["area"] = d["area"].map(lambda c: c.split(" - ")[-1].strip() if " - " in c else c)
    np.savez_compressed(os.path.join(ROOT, "work", "all_features.npz"), x=d.x.values, y=d.y.values,
                        lt=np.array(d.local_type.tolist(), dtype="U"), country=np.array(d.country.tolist(), dtype="U"))
    out = []
    for r in d.itertuples():
        ks = terms.match(r.name1)
        via = "name1"
        if not ks and r.name2:
            ks = terms.match(r.name2)
            via = "name2"
        for k in ks:
            out.append(dict(name=r.name1, name2=r.name2, term=k, term_label=terms.TERMS[k][0], group=terms.TERMS[k][1],
                            matched_on=via, type=r.type, local_type=r.local_type, lat=r.lat, lon=r.lon, x=r.x, y=r.y,
                            area=r.area, country=r.country))
    m = pd.DataFrame(out)
    m.to_csv(os.path.join(ROOT, "work", "matches_raw.csv"), index=False)
    print("OS features", len(d), "matches", len(m))
    print(m.term.value_counts())


if __name__ == "__main__":
    main()
