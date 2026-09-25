"""Fight and Performance of the Night labels, from Wikipedia event articles.

For PREREGISTRATION addendum 24. The UFC's bonus awards are announced at the
post-fight press conference and recorded in each event article's "Bonus
awards" section; nothing in the UFCStats corpus carries them.

Reuses the MediaWiki plumbing from wiki_records: batched content requests,
polite pacing, a resumable time budget, and the same refusal to guess. An
event whose section cannot be parsed is recorded as such rather than left
looking like a card with no bonuses — "we could not read it" and "none were
awarded" are different facts, and conflating them would quietly bias the
labels toward cards that happen to be well written up.

Collected from February 2014, when Performance of the Night replaced Knockout
and Submission of the Night, so the label set is one consistent scheme.
"""
import json
import re
import time
from pathlib import Path

import pandas as pd

from .wiki_records import _get, clean_cell, fetch_pages, search_title

OUT = "data/wiki/bonuses.json"
# Bump when the parser changes: stored labels were produced by the old one and
# are re-read automatically, so a fix reaches the data without anyone
# remembering to pass a flag. Version 1 counted "Fight of the Night: None" as
# a fighter, which put the award rate at 99% instead of about two thirds.
PARSER_VERSION = 5
POTN_ERA = pd.Timestamp("2014-02-01")
HEADING = re.compile(r"bonus award", re.I)
LABELS = {"fotn": re.compile(r"fight of the night", re.I),
          "potn": re.compile(r"performance of the night", re.I)}


def parse_bonuses(wikitext):
    """{'fotn': [names], 'potn': [names]} from the Bonus awards section.

    Returns None if the section is absent, so a missing write-up is never
    mistaken for a card where no bonuses were given.
    """
    secs = re.split(r"^(={2,6})\s*(.*?)\s*\1\s*$", wikitext, flags=re.M)
    body = None
    for i in range(1, len(secs) - 2, 3):
        if HEADING.search(secs[i + 1] or ""):
            body = secs[i + 2]
            break
    if body is None:
        return None
    out = {"fotn": [], "potn": []}
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith(("*", ";", ":")):
            continue
        which = next((k for k, pat in LABELS.items() if pat.search(s)), None)
        if not which:
            continue
        tail = s.split(":", 1)[1] if ":" in s else s
        # "Abel Trujillo ($75,000 each)" split on the comma into two "names".
        # Drop parentheticals and money before any name extraction.
        # "Geoff Neal{{efn|Despite missing weight, Neal was still awarded...}}"
        # — a footnote template rides along with the name and then splits on
        # the comma inside it. Strip templates before anything else.
        tail = re.sub(r"\{\{[^{}]*\}\}", " ", tail)
        tail = re.sub(r"\{\{.*", " ", tail)          # unbalanced, mid-cell
        tail = re.sub(r"\([^)]*\)", " ", tail)
        tail = re.sub(r"\$\s?[\d,]+", " ", tail)
        if re.search(r"\b(none|not awarded|no bonus(es)? (was |were )?awarded|"
                     r"no fight of the night|n/a)\b", tail, re.I):
            continue                       # an explicit "none", not a fighter
        names = [re.sub(r"\{\{.*", "", n).strip() for n in re.findall(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", tail)]
        if not names:                      # some articles do not link the names
            # split on the separators, taking the period with "vs." — the
            # naive \bvs\.?\b left a stray "." glued to the second name
            names = [x.strip(" .") for x in
                     re.split(r"\s+vs\.?\s+|,|\s+and\s+", clean_cell(tail))
                     if len(x.strip(" .")) > 3]
            # a "name" with no space is usually a stray word, not a fighter
            names = [n for n in names if " " in n]
        out[which] += [n.strip() for n in names if n.strip()]
    return out if (out["fotn"] or out["potn"]) else {"fotn": [], "potn": [], "none": True}


def _load(path=OUT):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "events": {}}


def _save(store, path=OUT):
    store["updated_utc"] = pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(store, sort_keys=True, indent=1), encoding="utf-8")


def event_titles(name):
    """Candidate Wikipedia titles for a corpus event name.

    "UFC 331: Van vs. Pantoja" lives at "UFC 331"; Fight Nights keep their
    full subtitle. Try the short form first, then the whole thing.
    """
    n = str(name).strip()
    cands = []
    m = re.match(r"^(UFC\s+\d+)", n, re.I)
    if m:
        cands.append(m.group(1))
    cands.append(n)
    cands.append(n.replace(" vs ", " vs. "))
    seen, out = set(), []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def collect(fights, budget_min=20, path=OUT, verbose=True):
    t0 = time.time()
    store = _load(path)
    if store.get("parser") != PARSER_VERSION:
        n = len(store.get("events", {}))
        store = {"version": 1, "parser": PARSER_VERSION, "events": {}}
        if verbose and n:
            print(f"bonuses: parser updated, re-reading all {n} stored events")
    store["parser"] = PARSER_VERSION
    ev = store["events"]
    events = (fights[fights.date >= POTN_ERA][["event", "date"]]
              .drop_duplicates("event").sort_values("date", ascending=False))
    todo = [(r.event, r.date) for r in events.itertuples() if r.event not in ev]
    done = 0
    for name, date in todo:
        if (time.time() - t0) > budget_min * 60:
            break
        rec = {"date": str(pd.Timestamp(date).date()), "status": "missing"}
        try:
            for title in event_titles(name):
                got = fetch_pages([title]).get(title)
                if not got or not got[1]:
                    continue
                b = parse_bonuses(got[1])
                if b is not None:
                    rec = {"date": rec["date"], "status": "ok", "title": got[0],
                           "fotn": b.get("fotn", []), "potn": b.get("potn", []),
                           "none_awarded": bool(b.get("none"))}
                    break
                rec["status"] = "no_section"
            if rec["status"] != "ok":
                t = search_title(name)
                if t:
                    got = fetch_pages([t]).get(t)
                    b = parse_bonuses(got[1]) if got and got[1] else None
                    if b is not None:
                        rec = {"date": rec["date"], "status": "ok", "title": got[0],
                               "fotn": b.get("fotn", []), "potn": b.get("potn", []),
                               "none_awarded": bool(b.get("none"))}
        except Exception as e:
            if verbose:
                print(f"  pausing: {e}")
            break
        ev[name] = rec
        done += 1
        if done % 20 == 0:
            _save(store, path)
    _save(store, path)
    if verbose:
        report(store, remaining=max(0, len(todo) - done), elapsed=time.time() - t0)
    return store


def report(store, remaining=0, elapsed=0):
    from collections import Counter
    ev = store["events"]
    c = Counter(v["status"] for v in ev.values())
    ok = [v for v in ev.values() if v["status"] == "ok"]
    with_fotn = [v for v in ok if v.get("fotn")]
    print(f"bonuses: {len(ev)} events read in {elapsed/60:.1f} min, {remaining} queued")
    print("  " + "  ".join(f"{k} {v}" for k, v in sorted(c.items())))
    if ok:
        print(f"  {len(with_fotn)} of {len(ok)} readable events awarded a Fight of the Night "
              f"({100*len(with_fotn)/len(ok):.0f}%; about two thirds is expected)")
        pot = sum(len(v.get("potn", [])) for v in ok)
        print(f"  {pot} Performance of the Night awards recorded")


def repair(fights, store=None, path=OUT, verbose=True):
    """Complete one-sided Fight of the Night entries from the corpus.

    Some articles name only one fighter on that line. The partner is not a
    guess: a Fight of the Night is a bout, and the corpus knows which bout that
    fighter had on that card. Anything ambiguous is left alone and stays
    visible as an odd count.
    """
    from .upcoming import _key
    store = store or _load(path)
    card = {}
    for r in fights.itertuples():
        parts = str(r.bout).split(" vs. ")
        if len(parts) == 2:
            card.setdefault(r.event, []).append((parts[0].strip(), parts[1].strip()))
    fixed = 0
    for ev, v in store.get("events", {}).items():
        names = v.get("fotn") or []
        if v.get("status") != "ok" or not names or len(names) % 2 == 0:
            continue
        bouts = card.get(ev) or []
        out = []
        for n in names:
            out.append(n)
            hits = [bt for bt in bouts if _key(n) in (_key(bt[0]), _key(bt[1]))]
            if len(hits) == 1:
                other = hits[0][1] if _key(n) == _key(hits[0][0]) else hits[0][0]
                if _key(other) not in {_key(x) for x in names}:
                    out.append(other)
        if len(out) != len(names) and len(out) % 2 == 0:
            v["fotn"] = out
            fixed += 1
    if fixed:
        _save(store, path)
        if verbose:
            print(f"bonuses: completed {fixed} one-sided Fight of the Night entries from the corpus")
    return fixed


# ---------------------------------------------------------------- validation
def validate(fights, store=None, path=OUT, verbose=True):
    """Check the labels against the corpus, because a parser that reads the
    page is not the same as a parser that reads it correctly.

    The first run reported a Fight of the Night at 99% of events against the
    ~two thirds the award history implies, which is the shape of a parsing
    artifact rather than a finding. Three checks catch it:

      count     a Fight of the Night has exactly two recipients
      identity  every name must be a fighter who actually fought on that card
      coverage  how many events were readable at all
    """
    import difflib
    import unicodedata
    from .upcoming import _key, load_aliases

    # The same alias file the card resolver uses: UFCStats calls Ronaldo Souza
    # "Jacare Souza" and Cris Cyborg "Cristiane Justino", so three of the
    # remaining failures were one fighter under two names.
    try:
        alias = {_key(k): _key(v) for k, v in load_aliases().items()}
    except Exception:
        alias = {}

    HARD = str.maketrans({"\u0142": "l", "\u0111": "d", "\u00f8": "o", "\u0131": "i",
                          "\u00e6": "ae", "\u0153": "oe", "\u00df": "ss"})

    def norm(n):
        """Match on spelling variants, not on luck. Wikipedia writes "Ovince
        St. Preux" and "Antônio Rogério"; UFCStats writes "Ovince Saint Preux"
        and "Antonio Rogerio". Neither is wrong, and a name check that counted
        those as failures would understate the labels."""
        # NFKD leaves l-stroke and friends alone, so "Jan Blachowicz" never
        # matched "Jan B\u0142achowicz"
        n = unicodedata.normalize("NFKD", str(n).translate(HARD))
        n = "".join(c for c in n if not unicodedata.combining(c))
        n = re.sub(r"\b(jr|sr|ii|iii|iv)\b", " ", n, flags=re.I)
        n = re.sub(r"\bst\.?\b", "saint", n, flags=re.I)
        k = _key(re.sub(r"[.\-']", " ", n))
        return alias.get(k, k)

    store = store or _load(path)
    ev = store.get("events", {})
    on_card = {}
    for r in fights.itertuples():
        parts = str(r.bout).split(" vs. ")
        if len(parts) == 2:
            on_card.setdefault(r.event, set()).update(norm(x) for x in parts)
    ok = [(k, v) for k, v in ev.items() if v.get("status") == "ok"]
    fotn = [(k, v) for k, v in ok if v.get("fotn")]
    paired = [1 for _, v in fotn if len(v["fotn"]) % 2 == 0]
    bad_names, checked, matched, odd = [], 0, 0, []
    for k, v in fotn:
        if len(v["fotn"]) % 2 and len(odd) < 5:
            odd.append((k, v["fotn"]))
    for k, v in ok:
        card = on_card.get(k)
        if not card:
            continue
        for n in v.get("fotn", []) + v.get("potn", []):
            checked += 1
            nn = norm(n)
            flat = {c.replace(" ", "") for c in card}
            swapped = " ".join(reversed(nn.split()))      # "Yadong Song" / "Song Yadong"
            # transliteration differs more in the given name than the
            # surname ("Aleksei Oleinyk" / "Alexey Oleynik"), so the surname
            # gets its own, tighter fuzzy pass against this card only
            close = (difflib.get_close_matches(nn, list(card), n=1, cutoff=0.85)
                     or difflib.get_close_matches(nn.split()[-1] if nn.split() else nn,
                                                  [c.split()[-1] for c in card if c.split()],
                                                  n=1, cutoff=0.85))
            if nn in card or nn.replace(" ", "") in flat or swapped in card or close:
                matched += 1
            elif len(bad_names) < 8:
                bad_names.append((k, n))
    res = {"events_ok": len(ok), "with_fotn": len(fotn),
           "fotn_paired": sum(paired),
           "names_checked": checked, "names_on_card": matched}
    by_year = {}
    for k, v in ok:
        y = str(v.get("date", ""))[:4]
        if y:
            a, b = by_year.get(y, (0, 0))
            by_year[y] = (a + (1 if v.get("fotn") else 0), b + 1)
    if verbose:
        print("bonus labels, checked against the corpus")
        print(f"  readable events: {len(ok)}")
        print(f"  with a Fight of the Night: {len(fotn)} ({100*len(fotn)/max(len(ok),1):.0f}%)")
        print(f"  with an even number of recipients: {sum(paired)} "
              f"({100*sum(paired)/max(len(fotn),1):.0f}%; some cards award two "
              f"Fight of the Night bonuses, so four names is two fights — an ODD "
              f"count is the mis-parse)")
        if checked:
            print(f"  names that fought on that card: {matched} of {checked} "
                  f"({100*matched/checked:.0f}%)")
        print("  Fight of the Night awarded, by year:")
        line = "    " + "  ".join(f"{y} {100*a/b:.0f}%" for y, (a, b) in sorted(by_year.items()))
        print(line)
        for k, n in odd:
            print(f"    odd number of recipients: {k.strip()!r} -> {n}")
        for k, n in bad_names:
            print(f"    not on the card: {k.strip()!r} -> {n!r}")
    return res


if __name__ == "__main__":
    import sys
    from .loaders import load
    budget = 20
    if "--budget-min" in sys.argv:
        budget = float(sys.argv[sys.argv.index("--budget-min") + 1])
    f, _p, _ = load(verbose=False)
    if "--check" in sys.argv:
        repair(f)
        validate(f)
        raise SystemExit(0)
    if "--recollect" in sys.argv:
        # the parser changed, so stored labels are stale: start over
        _save({"version": 1, "events": {}})
        print("bonuses: cleared stored labels, re-reading every event")
    collect(f, budget_min=budget)
    repair(f)
    validate(f)
