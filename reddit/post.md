# Reddit post: Bloody Place Names

## Title

[OC] Britain's map has 756 grim place names (Battle, Bloody Meadow, Slaughter, Gallows Hill...). Only 42 lie within 2 km of a recorded battle, and only "Battle" names beat chance clearly

## Body

I searched every named hill, wood, valley, water and settlement in OS Open Names for twelve grim words and measured each name's distance to the nearest of 507 battles and sieges in Wikidata. To make it fair, I compared each name with 2,000 random ordinary names of the same type from the same 50 km square.

Names with "Battle" really do cluster at battlefields: 11 of 58 within 2 km, against 2.3 expected. "Bloody" shows a weaker pull. Gallows names sit near battles mostly because both sit near towns. Kill, Dead Man, Murder and Slaughter show nothing beyond chance, and Upper and Lower Slaughter, 4.9 km from the Battle of Stow, get their name from an Old English word for wet land.

Caveat: Wikidata misses many fights, and OS Open Names leaves out field names.

Interactive map: https://tristan-hotham.github.io/bloody-place-names/

## Source comment

Source: OS Open Names (Ordnance Survey; contains OS data © Crown copyright and database right 2026; Open Government Licence v3.0) for the place names; Wikidata (CC0) for battles and sieges with coordinates, up to 1900; Wikipedia articles on Upper Slaughter and Lower Slaughter for the name origins.

Tools: Python (pandas, NumPy, SciPy, Shapely, pyproj, matplotlib).

Interactive version: https://tristan-hotham.github.io/bloody-place-names/
Blog post: https://blog.tristanhotham.com/2026/10/27/bloody-place-names/
Paper: https://doi.org/10.5281/zenodo.23677165
