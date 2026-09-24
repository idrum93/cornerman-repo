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
        names = re.findall(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", tail)
        if not names:                      # some articles do not link the names
            # split on the separators, taking the period with "vs." — the
            # naive \bvs\.?\b left a stray "." glued to the second name
            names = [x.strip(" .") for x in
                     re.split(r"\s+vs\.?\s+|,|\s+and\s+", clean_cell(tail))
                     if len(x.strip(" .")) > 3]
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


if __name__ == "__main__":
    import sys
    from .loaders import load
    budget = 20
    if "--budget-min" in sys.argv:
        budget = float(sys.argv[sys.argv.index("--budget-min") + 1])
    f, _p, _ = load(verbose=False)
    collect(f, budget_min=budget)
