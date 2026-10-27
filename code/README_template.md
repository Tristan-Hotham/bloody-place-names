# Bloody Place Names

Britain's map is full of names like Battle, Bloody Meadow, Slaughter, Dead Man's Hill and Gallows Hill. Do they sit near real recorded battles, or are most of them red herrings? This study measures {{n_matched_features|int}} such names on the Ordnance Survey map against {{battles.n_main|int}} battles and sieges located in Wikidata, and against matched ordinary names of the same type in the same region.

**Interactive version:** https://tristan-hotham.github.io/bloody-place-names/

**Paper:** https://doi.org/10.5281/zenodo.23677165

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion studies: [Dale, Down, Fell or Beck](https://tristan-hotham.github.io/dale-down-fell-beck/), [Within Sight](https://tristan-hotham.github.io/within-sight/).

## Headline results

- {{n_matched_features|int}} OS Open Names features contain one of twelve grim words. {{n_near2|int}} of them ({{share_near2|pct1}}) lie within 2 km of a recorded battle or siege, and {{n_far_10|int}} ({{share_far_10|pct0}}) are more than 10 km from any.
- "Battle" names are the clear exception: {{terms.battle.n_within_2|int}} of {{terms.battle.n|int}} lie within 2 km of a recorded battle, against {{terms.battle.exp_within_2|f1}} expected from matched names ({{terms.battle.ratio_within_2|f1}} times as many). Within 5 km: {{terms.battle.obs_within_5|pct0}} against {{terms.battle.base_within_5|pct0}}. This holds in every sensitivity run.
- "Bloody" names show a weaker pull: {{terms.blood.n_within_2|int}} of {{terms.blood.n|int}} within 2 km against {{terms.blood.exp_within_2|f1}} expected (chance {{terms.blood.p_within_2|pct1}}, not significant after correcting for twelve tests).
- Gallows names ({{terms.gallows.n|int}}) also sit nearer battles than matched names ({{terms.gallows.n_within_2|int}} within 2 km against {{terms.gallows.exp_within_2|f1}} expected), but much of this goes away when names are also matched on distance to the nearest town (chance rises to {{terms.gallows.sens.main_town_matched.p_within_2|pct1}}).
- Kill, Dead Man, Murder, Hangman, Gibbet, Soldier, War, Red Bank and Slaughter names show no clear signal at 2 km.
- {{battles_with_name_2km|int}} recorded battles have a grim name within 2 km; matched ordinary names would give about {{battles_with_name_2km_base|f1}} (95% range {{battles_with_name_2km_base_lo|int}} to {{battles_with_name_2km_base_hi|int}}).
- The Slaughter trap: Upper and Lower Slaughter are about {{slaughters.0.km|f1}} km from the Wikidata point for the Battle of Stow-on-the-Wold ({{slaughters.0.year|raw}}), but Wikipedia derives their name from an Old English word meaning "wet land".

## Files

- `index.html`: the interactive page (Leaflet map, charts).
- `header.png`: social card.
- `data/named_features.csv`: one row per OS feature and matched word: name, Welsh or Gaelic alternative, word, OS type and local type, coordinates (WGS84 and British National Grid), area, nearest recorded battle (with Wikidata id and year), distance in km, whether the place name appears in that battle's name, distance to the nearest OS town or city, and the baseline stratum used.
- `data/battles_gb.csv`: the recorded battles and sieges on or within 2 km of GB land: Wikidata id, label, kind, date, coordinates, Wikipedia link, where the coordinate came from, a name check against OS places, and a flag for the one excluded point.
- `data/term_results.csv`: one row per word (and pooled groups) and per battle set: observed and baseline median distance and shares within 1, 2, 5 and 10 km, with 95% baseline ranges and chance values.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage, plus the quotations about the Slaughters, Warcop, Battle and Battlefield with their Wikipedia URLs.
- `code/terms.py`: the twelve search patterns, with tests (`python3 code/terms.py`).
- `code/01_data.py`, `code/02_analyse.py`, `code/03_build_site.py`, `code/04_header.py`: run in that order. `release/` and `reddit/` hold the scripts for the paper, blog figures and collage.

## Method in brief

Names: OS Open Names features of type populated place, landform, landcover and hydrography ({{n_os_features|int}} features), searched case-insensitively for: battle, blood, slaughter, red bank, dead man, murder, kill (word start), war (whole word, excluding memorials and "man of war"), soldier, gallow, gibbet, hangman. A match means only that the name contains these letters; no claim is made about meaning.

Battles: Wikidata items that are battles or sieges with a coordinate on or within 2 km of GB land, dated up to 1900 ({{battles.n_main|int}}: {{battles.n_battle|int}} battles, {{battles.n_siege|int}} sieges). One plainly wrong point (First Battle of St Albans, placed in Essex) is excluded.

Baseline: for each grim name, {{n_sim|int}} random OS names of the same local type from the same 50 km grid square (falling back to 100 km, then country, when fewer than {{min_pool|int}} are available). Chance values are the share of matched sets at least as close as the real names. Sensitivity runs: battles only, before 1700, dated 1066 to 1746, battles passing a name check, and names also matched on distance to the nearest OS town or city.

Caveats: OS Open Names omits field names and most minor names; Wikidata coverage is uneven (some battles are missing, some points are approximate, some sites are disputed) and differs between England, Scotland and Wales; distance is not meaning; twelve words were tested, so one or two may look striking by chance.

## Rerun

Needs Python 3 with pandas, numpy, scipy, shapely and pyproj. Place `osnames_gb.tsv` (an extract of OS Open Names), `_data2/wikidata/battles_world.json` (Wikidata battles extract) and `how-roman-is-your-road/data/counties.geojson` (ONS county boundaries) one folder above this repository, then run the scripts in `code/` in order.

## Sources and licence

- Place names: OS Open Names. Contains OS data © Crown copyright and database right 2026. Open Government Licence v3.0. https://www.ordnancesurvey.co.uk/products/os-open-names
- Battles and sieges: Wikidata, CC0. https://www.wikidata.org/
- Land outline for static maps: county and unitary authority boundaries, Office for National Statistics, OGL v3.0 (contains OS data © Crown copyright and database right).
- Quotations about names: English Wikipedia (CC BY-SA 4.0): Upper Slaughter, Lower Slaughter, Warcop, Battle, East Sussex, Battlefield, Shropshire.
- Base map tiles on the page: Esri. Map library: Leaflet.

The derived data and the text are released under CC BY 4.0. Code is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) *Bloody Place Names: do Britain's battle names mark real battles?* Data study and paper. Zenodo. https://doi.org/10.5281/zenodo.23677165

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
