"""The search terms. Each term is a case-insensitive regular expression tested on OS Open Names
name1 and name2 (the Welsh or Gaelic alternative name, where there is one).

A match means only "the name contains these letters". No claim is made here about what any name
means or where it comes from.

Run `python3 code/terms.py` to see the tests pass.
"""
import re

# key: (label, group, regex, exclude regex or None)
TERMS = {
    "battle":    ("Battle",    "violence",  r"battle", None),
    "blood":     ("Blood / Bloody", "violence", r"blood", None),
    "slaughter": ("Slaughter", "violence",  r"slaughter", None),
    "redbank":   ("Red Bank",  "violence",  r"\bred ?banks?\b", None),
    "deadman":   ("Dead Man",  "violence",  r"\bdead ?m[ae]n", None),
    "murder":    ("Murder",    "violence",  r"murder", None),
    "kill":      ("Kill",      "violence",  r"\bkill", None),
    "war":       ("War",       "violence",  r"\bwar\b", r"memorial|man o'? ?f? ?war|great war|prisoner"),
    "soldier":   ("Soldier",   "violence",  r"soldier", None),
    "gallows":   ("Gallows",   "execution", r"gallow", None),
    "gibbet":    ("Gibbet",    "execution", r"gibbet", None),
    "hangman":   ("Hangman",   "execution", r"hangman", None),
}
ORDER = list(TERMS)
_C = {k: (re.compile(v[2], re.I), re.compile(v[3], re.I) if v[3] else None) for k, v in TERMS.items()}


def match(name):
    """Return the list of term keys found in one name."""
    out = []
    for k, (rx, ex) in _C.items():
        if rx.search(name) and not (ex and ex.search(name)):
            out.append(k)
    return out


if __name__ == "__main__":
    tests = {
        "Battle": ["battle"], "Upper Battlefield": ["battle"], "Bloody Meadow": ["blood"],
        "The Slaughters": ["slaughter"], "Red Bank": ["redbank"], "Redbanks": ["redbank"],
        "Deadman's Hill": ["deadman"], "Dead Man's Bay": ["deadman"], "Murder Moss": ["murder"],
        "Killiecrankie": ["kill"], "Kiln Copse": [], "War Down": ["war"], "War Memorial Plantation": [],
        "Man o' War Cove": [], "Man of War": [], "Warren Wood": [], "Warcop": [],
        "Gallows Hill": ["gallows"], "Gallow Hill": ["gallows"], "Gibbet Hill": ["gibbet"],
        "Hangman's Wood": ["hangman"], "Soldiers' Pond": ["soldier"], "Redbridge": [],
    }
    for n, want in tests.items():
        got = match(n)
        assert got == want, (n, got, want)
    print(f"{len(tests)} tests passed")
