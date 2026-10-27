"""Step 2. Distance from every term-named feature to the nearest recorded battle, against a matched baseline.

Baseline: for each named feature, a random OS Open Names feature of the SAME local type (Hill Or Mountain,
Woodland Or Forest, Village...) in the SAME 50 km grid square of the British National Grid. If that pool has
fewer than 20 features, the 100 km square is used, then the whole country (England, Scotland or Wales).
Repeated N_SIM times, this gives N_SIM matched "fake" sets of names per term, which carry the same mix of
feature types and the same geography as the real ones. The question is whether the real names sit closer to
recorded battles than these matched sets do.

Outputs:
  data/named_features.csv     matches with nearest battle, distance and baseline stratum
  data/term_results.csv       one row per term (and pooled groups): observed and baseline statistics
  data/results.json           every number used in the page, paper, blog and collage
  work/site.json              compact data for the page

Usage: python3 code/02_analyse.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import terms  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_SIM = 2000
MIN_POOL = 20
CUTS = [1, 2, 5, 10]          # km thresholds reported
GRID = list(range(0, 41))     # km, for the cumulative curves
LATEST_YEAR = 1900            # events after this are left out (Blitz, embassy siege)
TOWN_BANDS = [2, 5, 10]
NAMECHECK_KM = 15            # km, see the namecheck_ok battle set       # km bands of distance to the nearest OS Town or City, for the stricter baseline
rng = np.random.default_rng(20261027)


def stats(dk):
    """dk: distances in km, shape (n,) or (n, sims). Returns dict of arrays."""
    out = {"median": np.median(dk, axis=0), "mean": np.mean(dk, axis=0)}
    for c in CUTS:
        out[f"within_{c}"] = np.mean(dk <= c, axis=0)
    return out


def main():
    b = pd.read_csv(os.path.join(ROOT, "data", "battles_gb.csv"))
    b_all = b.copy()
    b["flag"] = b.flag.fillna("")
    n_flagged = int((b.flag != "").sum())
    b = b[~(b.year > LATEST_YEAR) & (b.flag == "")].copy()
    bc = json.load(open(os.path.join(ROOT, "work", "battle_counts.json")))
    A = np.load(os.path.join(ROOT, "work", "all_features.npz"), allow_pickle=False)
    ax, ay, alt, acountry = A["x"].astype(float), A["y"].astype(float), A["lt"], A["country"]
    m = pd.read_csv(os.path.join(ROOT, "work", "matches_raw.csv"), keep_default_na=False)

    def battle_sets():
        return {
            "main": b,
            "battles_only": b[b.kind == "battle"],
            "pre1700": b[b.year < 1700],
            "dated_1066_1746": b[(b.year >= 1066) & (b.year <= 1746)],
            # leave out the 16 or so battles whose Wikidata point is more than 15 km from any OS place of the name in
            # their label (mostly homonyms, but some may be misplaced points)
            "namecheck_ok": b[~(b.namecheck_km > NAMECHECK_KM)],
        }
    BS = battle_sets()
    trees = {k: cKDTree(v[["x", "y"]].values) for k, v in BS.items()}

    # nearest-battle distance for every OS feature, per battle set (km)
    allxy = np.column_stack([ax, ay])
    dist_all = {k: t.query(allxy)[0] / 1000 for k, t in trees.items()}
    d_main, i_main = trees["main"].query(m[["x", "y"]].values)
    m["nearest_battle"] = b.name.values[i_main]
    m["nearest_battle_qid"] = b.qid.values[i_main]
    m["nearest_battle_year"] = b.year.values[i_main]
    m["dist_km"] = np.round(d_main / 1000, 2)
    # circularity check: is the feature's own name (or its first word, for multi-word names) part of the battle's label?
    def named_after(name, battle):
        nm, bl = name.lower(), battle.lower()
        first = nm.split()[0] if nm.split() else nm
        return nm in bl or (len(first) > 4 and first in bl and first not in ("upper", "lower", "great", "little", "north", "south", "east", "west"))
    m["name_in_battle_label"] = [named_after(a, c) for a, c in zip(m.name, m.nearest_battle)]

    # strata: (local type, 50 km square) with fallbacks
    def keys(x, y, lt, country, size):
        if size == 0:
            return np.char.add(np.char.add(lt.astype(str), "|"), country.astype(str))
        return np.array([f"{a}|{int(xx // size)}_{int(yy // size)}" for a, xx, yy in zip(lt, x, y)])
    pools = {}
    for size in (50000, 100000, 0):
        k = keys(ax, ay, alt, acountry, size)
        s = pd.Series(np.arange(len(k))).groupby(k).apply(lambda v: v.values)
        pools[size] = s.to_dict()
    def stratum(r):
        for size in (50000, 100000, 0):
            kk = f"{r.local_type}|{r.country}" if size == 0 else f"{r.local_type}|{int(r.x // size)}_{int(r.y // size)}"
            p = pools[size].get(kk)
            if p is not None and len(p) >= MIN_POOL:
                return size, kk
        return 0, f"{r.local_type}|{r.country}"
    st = [stratum(r) for r in m.itertuples()]
    m["stratum_km"] = [s[0] // 1000 if s[0] else "country" for s in st]
    m["stratum"] = [s[1] for s in st]

    # one matched draw matrix per feature row (reused across battle sets so that sensitivity runs are paired)
    draws = np.empty((len(m), N_SIM), dtype=np.int64)
    for i, (size, kk) in enumerate(st):
        p = pools[size][kk]
        draws[i] = p[rng.integers(0, len(p), N_SIM)]

    # second, stricter baseline: also match on distance to the nearest town or city (OS local types Town, City),
    # in bands, to test whether any closeness is simply closeness to old centres of population
    towns = allxy[np.isin(alt, ["Town", "City"])]
    tdist = cKDTree(towns).query(allxy)[0] / 1000
    band = np.digitize(tdist, TOWN_BANDS)
    mt_d = cKDTree(towns).query(m[["x", "y"]].values)[0] / 1000
    m["town_km"] = np.round(mt_d, 2)
    mband = np.digitize(mt_d, TOWN_BANDS)
    tpools = {}
    for size in (50000, 100000):
        kk = np.array([f"{a}|{int(xx // size)}_{int(yy // size)}|{bb}" for a, xx, yy, bb in zip(alt, ax, ay, band)])
        tpools[size] = pd.Series(np.arange(len(kk))).groupby(kk).apply(lambda v: v.values).to_dict()
    draws_town = np.empty_like(draws)
    tfall = []
    for i, r in enumerate(m.itertuples()):
        p = None
        for size in (50000, 100000):
            q = tpools[size].get(f"{r.local_type}|{int(r.x // size)}_{int(r.y // size)}|{mband[i]}")
            if q is not None and len(q) >= MIN_POOL:
                p = q; tfall.append(size // 1000); break
        if p is None:
            size, kk = st[i]; p = pools[size][kk]; tfall.append("no_band")
        draws_town[i] = p[rng.integers(0, len(p), N_SIM)]

    groups = [(k, terms.TERMS[k][0], m.term == k) for k in terms.ORDER]
    viol = m[m.group == "violence"].drop_duplicates(["x", "y", "name"]).index
    exe = m[m.group == "execution"].drop_duplicates(["x", "y", "name"]).index
    viol_nk = m[(m.group == "violence") & (m.term != "kill")].drop_duplicates(["x", "y", "name"]).index
    groups += [("all_violence", "All violence words", m.index.isin(viol)),
               ("violence_no_kill", "Violence words without Kill", m.index.isin(viol_nk)),
               ("all_execution", "All execution words", m.index.isin(exe))]

    rows, curves, sens = [], {}, {}
    for key, label, mask in groups:
        idx = np.where(mask)[0]
        for bs in list(BS) + ["main_town_matched"]:
            tb = "main" if bs == "main_town_matched" else bs
            dd = trees[tb].query(m.loc[idx, ["x", "y"]].values)[0] / 1000
            null = dist_all[tb][(draws_town if bs == "main_town_matched" else draws)[idx]]          # (n, N_SIM)
            so, sn = stats(dd), stats(null)
            rec = dict(term=key, label=label, battle_set=bs, n=int(len(idx)),
                       n_types=int(m.loc[idx, "local_type"].nunique()))
            for s in so:
                o, nul = float(so[s]), sn[s]
                rec[f"obs_{s}"] = o
                rec[f"base_{s}"] = float(np.mean(nul))
                rec[f"base_{s}_lo"] = float(np.quantile(nul, .025))
                rec[f"base_{s}_hi"] = float(np.quantile(nul, .975))
                if s in ("median", "mean"):
                    rec[f"p_{s}"] = float((1 + np.sum(nul <= o)) / (1 + N_SIM))     # closer than baseline
                else:
                    rec[f"p_{s}"] = float((1 + np.sum(nul >= o)) / (1 + N_SIM))
            rec["ratio_within_5"] = rec["obs_within_5"] / rec["base_within_5"] if rec["base_within_5"] else None
            rec["ratio_median"] = rec["obs_median"] / rec["base_median"]
            rows.append(rec)
            if bs == "main":
                g = np.array(GRID, float)
                oc = [(dd <= x).mean() for x in g]
                nc = np.stack([(null <= x).mean(axis=0) for x in g])
                curves[key] = dict(obs=[round(v, 4) for v in oc], base=[round(float(v), 4) for v in nc.mean(1)],
                                   lo=[round(float(v), 4) for v in np.quantile(nc, .05, axis=1)],
                                   hi=[round(float(v), 4) for v in np.quantile(nc, .95, axis=1)])
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(ROOT, "data", "term_results.csv"), index=False, float_format="%.4f")

    # strata fallbacks
    m.to_csv(os.path.join(ROOT, "data", "named_features.csv"), index=False,
             columns=["name", "name2", "term", "term_label", "group", "matched_on", "type", "local_type", "lat", "lon", "x", "y",
                      "area", "country", "nearest_battle", "nearest_battle_qid", "nearest_battle_year", "dist_km", "name_in_battle_label", "town_km", "stratum_km", "stratum"])

    # ---------------- results.json ----------------
    R = {}
    R["n_os_features"] = int(len(ax))
    R["n_matches"] = int(len(m))
    R["n_matched_features"] = int(m.drop_duplicates(["x", "y", "name"]).shape[0])
    R["n_sim"] = N_SIM
    R["min_pool"] = MIN_POOL
    R["latest_year"] = LATEST_YEAR
    R["battles"] = dict(
        n_bbox_items=bc["n_bbox_items"], n_offland=bc["n_offland"], n_on_land_all=int(len(b_all)),
        n_after_cutoff=int((b_all.year > LATEST_YEAR).sum()), n_main=int(len(b)),
        n_battle=int((b.kind == "battle").sum()), n_siege=int((b.kind == "siege").sum()),
        n_undated=int(b.year.isna().sum()), n_pre1066=int((b.year < 1066).sum()),
        n_1066_1499=int(((b.year >= 1066) & (b.year < 1500)).sum()), n_1500_1699=int(((b.year >= 1500) & (b.year < 1700)).sum()),
        n_1700_1900=int(((b.year >= 1700) & (b.year <= 1900)).sum()),
        n_multi_point=int((b.n_points > 1).sum()), n_flagged=n_flagged,
        namecheck_n=int(b.namecheck_km.notna().sum()), namecheck_within_5=int((b.namecheck_km <= 5).sum()),
        namecheck_within_10=int((b.namecheck_km <= 10).sum()), namecheck_over_25=int((b.namecheck_km > 25).sum()),
        n_pre1700=int(len(BS["pre1700"])), n_battles_only=int(len(BS["battles_only"])), n_1066_1746=int(len(BS["dated_1066_1746"])),
        by_country={})
    # battles by country via nearest OS feature
    t_all = cKDTree(allxy)
    _, ni = t_all.query(b[["x", "y"]].values)
    bcountry = acountry[ni]
    R["battles"]["by_country"] = {c: int((bcountry == c).sum()) for c in ("England", "Scotland", "Wales")}
    R["battles"]["os_share_by_country"] = {c: float((acountry == c).mean()) for c in ("England", "Scotland", "Wales")}
    R["all_features_median_km"] = float(np.median(dist_all["main"]))
    R["all_features_within_5"] = float(np.mean(dist_all["main"] <= 5))
    R["all_features_within_2"] = float(np.mean(dist_all["main"] <= 2))
    R["town_bands"] = TOWN_BANDS
    R["town_strata"] = {str(k): int(v) for k, v in pd.Series(tfall).astype(str).value_counts().items()}
    R["n_towns"] = int(len(towns))
    R["strata"] = {str(k): int(v) for k, v in m.stratum_km.astype(str).value_counts().items()}
    R["terms"] = {}
    for key, label, mask in groups:
        sub = m[mask]
        rec = T[(T.term == key) & (T.battle_set == "main")].iloc[0].to_dict()
        rec = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rec.items() if k not in ("term", "battle_set")}
        rec["sens"] = {bs: dict(obs_median=round(float(r.obs_median), 2), base_median=round(float(r.base_median), 2),
                                p_median=round(float(r.p_median), 4), obs_within_5=round(float(r.obs_within_5), 4),
                                base_within_5=round(float(r.base_within_5), 4), p_within_5=round(float(r.p_within_5), 4),
                                obs_within_2=round(float(r.obs_within_2), 4), base_within_2=round(float(r.base_within_2), 4),
                                p_within_2=round(float(r.p_within_2), 4))
                       for r in T[(T.term == key)].itertuples() for bs in [r.battle_set]}
        rec["types"] = {k: int(v) for k, v in sub.local_type.value_counts().items()}
        rec["country"] = {k: int(v) for k, v in sub.country.value_counts().items()}
        rec["curve"] = curves[key]
        rec["n_within_1"] = int((sub.dist_km <= 1).sum())
        rec["n_within_2"] = int((sub.dist_km <= 2).sum())
        rec["n_within_5"] = int((sub.dist_km <= 5).sum())
        # expected counts under the matched baseline
        rec["exp_within_2"] = round(rec["n"] * rec["base_within_2"], 1)
        rec["exp_within_5"] = round(rec["n"] * rec["base_within_5"], 1)
        rec["ratio_within_2"] = round(rec["obs_within_2"] / rec["base_within_2"], 2) if rec["base_within_2"] else None
        rec["ratio_within_5"] = round(rec["obs_within_5"] / rec["base_within_5"], 2) if rec["base_within_5"] else None
        if key in terms.TERMS:
            rec["group"] = terms.TERMS[key][1]
            rec["regex"] = terms.TERMS[key][2]
            rec["exclude"] = terms.TERMS[key][3]
            ex = sub.sort_values("dist_km")
            rec["closest"] = [dict(name=r.name, type=r.local_type, area=r.area, battle=r.nearest_battle,
                                   year=None if pd.isna(r.nearest_battle_year) else int(r.nearest_battle_year), km=round(float(r.dist_km), 1))
                              for r in ex.head(10).itertuples()]
        R["terms"][key] = rec
    # named features within 2 km of a recorded battle, all terms
    near = m[m.dist_km <= 2].sort_values("dist_km")
    R["near2"] = [dict(name=r.name, term=r.term_label, type=r.local_type, area=r.area, battle=r.nearest_battle,
                       year=None if pd.isna(r.nearest_battle_year) else int(r.nearest_battle_year), km=float(r.dist_km))
                  for r in near.itertuples()]
    R["n_near2"] = int(len(near.drop_duplicates(["x", "y", "name"])))
    R["n_near2_named_after"] = int(near.name_in_battle_label.sum())
    R["near2_named_after"] = near[near.name_in_battle_label][["name", "nearest_battle"]].values.tolist()
    R["n_near5"] = int((m.dist_km <= 5).sum())
    R["battles"]["namecheck_far_n"] = int((b.namecheck_km > NAMECHECK_KM).sum())
    R["battles"]["namecheck_km"] = NAMECHECK_KM
    R["battles"]["namecheck_median_km"] = float(b.namecheck_km.median())
    R["battles"]["n_namecheck_ok"] = int(len(BS["namecheck_ok"]))
    tm = T[(T.battle_set == "main") & T.term.isin(terms.ORDER)]
    R["n_terms"] = len(terms.ORDER)
    R["n_terms_closer_median"] = int((tm.obs_median < tm.base_median).sum())
    R["n_terms_p05_median"] = int((tm.p_median < .05).sum())
    R["n_terms_p05_within5"] = int((tm.p_within_5 < .05).sum())
    R["n_terms_higher_within5"] = int((tm.obs_within_5 > tm.base_within_5).sum())
    R["n_terms_p05_within2"] = int((tm.p_within_2 < .05).sum())
    R["n_terms_bonf_within2"] = int((tm.p_within_2 < .05 / len(terms.ORDER)).sum())
    R["share_far_10"] = float((m.dist_km > 10).mean())
    R["n_far_10"] = int((m.dist_km > 10).sum())
    R["share_near2"] = float((m.dist_km <= 2).mean())
    R["share_near5"] = float((m.dist_km <= 5).mean())
    R["bonferroni_alpha"] = round(.05 / len(terms.ORDER), 4)
    R["n_terms_bonf_within5"] = int((tm.p_within_5 < .05 / len(terms.ORDER)).sum())
    R["n_terms_bonf_median"] = int((tm.p_median < .05 / len(terms.ORDER)).sum())
    # battles with any term-named feature within 2 km, and how many battles would by chance
    bt = b[["x", "y"]].values
    mt = cKDTree(m.drop_duplicates(["x", "y", "name"])[["x", "y"]].values)
    R["battles_with_name_2km"] = int(sum(len(v) > 0 for v in mt.query_ball_point(bt, 2000)))
    # chance: same count of matched draws (one sim set) - average over 200 sims
    uniq = m.drop_duplicates(["x", "y", "name"]).index.values
    cnt = []
    bt_tree = cKDTree(bt)
    for s in range(200):
        pts = allxy[draws[uniq, s]]
        dd, _ = bt_tree.query(pts)
        hit = set()
        for j, lst in enumerate(cKDTree(pts).query_ball_point(bt, 2000)):
            if lst:
                hit.add(j)
        cnt.append(len(hit))
    R["battles_with_name_2km_base"] = float(np.mean(cnt))
    R["battles_with_name_2km_base_lo"] = float(np.quantile(cnt, .025))
    R["battles_with_name_2km_base_hi"] = float(np.quantile(cnt, .975))

    # the Slaughters and Warcop: sources for what the name means (quoted from Wikipedia, not my own claims)
    sl = m[m.name.isin(["Upper Slaughter", "Lower Slaughter"])]
    R["slaughters"] = [dict(name=r.name, type=r.local_type, nearest_battle=r.nearest_battle,
                            year=None if pd.isna(r.nearest_battle_year) else int(r.nearest_battle_year), km=float(r.dist_km)) for r in sl.itertuples()]
    R["etymology_sources"] = {
        "Upper Slaughter": {"quote": "The name of the village derives from the Old English word \"slohtre\" meaning \"wet land\".",
                            "url": "https://en.wikipedia.org/wiki/Upper_Slaughter", "accessed": "2026-10-26"},
        "Lower Slaughter": {"quote": "The name of the village is derived from the Old English term \"slough\" meaning \"wet land\".",
                            "url": "https://en.wikipedia.org/wiki/Lower_Slaughter", "accessed": "2026-10-26"},
        "Warcop": {"quote": "The name Warcop means 'hill with a cairn', and was spelt Warthecopp and otherwise in the 13th century and earlier.",
                   "url": "https://en.wikipedia.org/wiki/Warcop", "accessed": "2026-10-26"},
        "Battle": {"quote": "Battle contains the site of, and is named after, the Battle of Hastings",
                   "url": "https://en.wikipedia.org/wiki/Battle,_East_Sussex", "accessed": "2026-10-26"},
        "Battlefield": {"quote": "It was roughly here that the Battle of Shrewsbury of 1403 took place.",
                        "url": "https://en.wikipedia.org/wiki/Battlefield,_Shropshire", "accessed": "2026-10-26"},
    }
    json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, default=float)

    # ---------------- compact site data ----------------
    site = dict(
        pts=[[round(r.lat, 4), round(r.lon, 4), terms.ORDER.index(r.term), r.name, r.local_type, r.area, r.nearest_battle,
              round(float(r.dist_km), 1)] for r in m.itertuples()],
        battles=[[round(r.lat, 4), round(r.lon, 4), r.name, None if pd.isna(r.year) else int(r.year), r.kind, r.enwiki if isinstance(r.enwiki, str) else ""]
                 for r in b.itertuples()],
        terms=[[k, terms.TERMS[k][0], terms.TERMS[k][1]] for k in terms.ORDER],
        grid=GRID,
    )
    json.dump(site, open(os.path.join(ROOT, "work", "site.json"), "w"), separators=(",", ":"))
    print(T[T.battle_set == "main"][["term", "n", "obs_median", "base_median", "base_median_lo", "base_median_hi", "p_median",
                                     "obs_within_5", "base_within_5", "p_within_5"]].round(3).to_string())
    print(T[T.battle_set == "main_town_matched"][["term", "n", "obs_median", "base_median", "p_median", "obs_within_5", "base_within_5", "p_within_5"]].round(3).to_string())
    print(T[T.term.isin(["all_violence", "all_execution", "battle", "blood"])][["term", "battle_set", "obs_median", "base_median", "p_median", "obs_within_5", "base_within_5", "p_within_5"]].round(3).to_string())
    print("near2", R["n_near2"], "battles with name 2km", R["battles_with_name_2km"], R["battles_with_name_2km_base"])


if __name__ == "__main__":
    main()
