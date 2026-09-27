"""Does a record source cover the fighters we actually need?

PREREGISTRATION addendum 36, step 1. The gate before any model work: a source
is useless here if it misses precisely the fighters it is needed for. This
answers one question and stops.

    python -m mmastat.record_probe              both sources, last 12 months
    python -m mmastat.record_probe --months 24
    python -m mmastat.record_probe --source espn

The bar is 70% coverage of thin fighters (3 or fewer prior UFC bouts) WITH a
method split. A record that gives W-L but not how those wins came is no use
for the finish and method targets this was registered for, so it counts as a
miss, not a partial hit.

Nothing here writes to the model or the site. It prints a number.
"""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request

import pandas as pd

UA = {"User-Agent": "cornerman-record-probe/1.0 (research; contact via repo)"}
TIMEOUT = 12

# ESPN's core API is undocumented, so the path is probed rather than assumed —
# the same approach that found the Polymarket US event endpoint after seven
# candidates. Whichever works first is reported, so the next version can
# hard-code it.
ESPN_SEARCH = [
    "https://site.web.api.espn.com/apis/search/v2?region=us&lang=en&limit=5&query={q}",
    "https://site.web.api.espn.com/apis/common/v3/search?query={q}&limit=5&sport=mma",
]
# The fighter history page (espn.com/mma/fighter/history/_/id/<id>) is the real
# prize: one row per bout with a method, not a "12-3" summary. If those rows
# reach back before a fighter's UFC debut, a pre-UFC record can be built with
# methods and rounds intact, which is what addendum 36 needs. "eventlog" is
# ESPN's core-API name for an athlete's bouts.
ESPN_HISTORY = [
    "https://sports.core.api.espn.com/v2/sports/mma/athletes/{id}/eventlog",
    "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/athletes/{id}/eventlog",
    "https://site.web.api.espn.com/apis/common/v3/sports/mma/ufc/athletes/{id}/history",
    "https://site.web.api.espn.com/apis/common/v3/sports/mma/athletes/{id}/history",
    "https://site.api.espn.com/apis/site/v2/sports/mma/athletes/{id}/history",
]
ESPN_ATHLETE = [
    "https://sports.core.api.espn.com/v2/sports/mma/athletes/{id}",
    "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/athletes/{id}",
    "https://site.web.api.espn.com/apis/common/v3/sports/mma/ufc/athletes/{id}",
]
_WORKED = {}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _methods_from_text(txt):
    """A record is only useful here if it says HOW the wins came."""
    t = (txt or "").lower()
    got = {
        "ko": bool(re.search(r"\b(ko|tko|knockout)\b", t)),
        "sub": bool(re.search(r"\bsubmission[s]?\b", t)),
        "dec": bool(re.search(r"\bdecision[s]?\b", t)),
    }
    return got if sum(got.values()) >= 2 else None


def espn_history(aid, verbose=False):
    """Bouts on a fighter's ESPN history, and how many name a method.

    Returns (n_bouts, n_with_method, endpoint) — counting rows, because a
    debutant's rows are all pre-UFC by definition and a row with a method is
    the unit addendum 36 actually needs.
    """
    for tmpl in ([_WORKED["espn_history"]] if "espn_history" in _WORKED else ESPN_HISTORY):
        try:
            j = _get(tmpl.format(id=aid))
        except Exception as e:
            if verbose:
                print(f"      history {tmpl.split('/athletes')[0][-38:]} -> {str(e)[:34]}")
            continue
        blob = json.dumps(j)
        # count bout-like rows however the payload is shaped
        n = max(len(re.findall(r'"(?:competitionId|eventId|gameId)"', blob)),
                blob.count('"opponent"'), blob.count('"competition"'))
        meth = len(re.findall(r'\b(?:KO/TKO|TKO|KO|Submission|Decision|SUB|DEC)\b', blob))
        if n:
            _WORKED["espn_history"] = tmpl
            return n, meth, tmpl
    return 0, 0, "no history endpoint answered"


def espn_record(name, verbose=False):
    """Return (found_record, has_method_split, note)."""
    aid = None
    for tmpl in ([_WORKED["espn_search"]] if "espn_search" in _WORKED else ESPN_SEARCH):
        try:
            j = _get(tmpl.format(q=urllib.parse.quote(name)))
        except Exception as e:
            if verbose:
                print(f"      search {tmpl.split('?')[0]} -> {str(e)[:40]}")
            continue
        blob = json.dumps(j)
        m = re.search(r"/athletes/(\d+)", blob)
        if m:
            aid, _WORKED["espn_search"] = m.group(1), tmpl
            break
    if not aid:
        return False, False, "no athlete id"
    # the history first: rows with methods beat any summary string
    nb, nm2, ep = espn_history(aid, verbose=verbose)
    if nb:
        return True, nm2 >= 2, f"athlete {aid}, {nb} bouts on history ({ep.split('/athletes')[0][-26:]})"
    for tmpl in ([_WORKED["espn_athlete"]] if "espn_athlete" in _WORKED else ESPN_ATHLETE):
        try:
            j = _get(tmpl.format(id=aid))
        except Exception:
            continue
        _WORKED["espn_athlete"] = tmpl
        blob = json.dumps(j)
        # a W-L-D anywhere in the payload counts as a record
        rec = re.search(r"\b(\d{1,3})-(\d{1,3})(-\d{1,2})?\b", blob)
        return bool(rec), bool(_methods_from_text(blob)), f"athlete {aid}"
    return False, False, f"athlete {aid}, no endpoint answered"


def wiki_record(name, verbose=False):
    url = ("https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
           "&explaintext=1&redirects=1&format=json&titles=" + urllib.parse.quote(name))
    try:
        j = _get(url)
    except Exception as e:
        return False, False, str(e)[:40]
    pages = (j.get("query") or {}).get("pages") or {}
    for _, pg in pages.items():
        if "missing" in pg:
            return False, False, "no article"
        txt = pg.get("extract") or ""
        rec = re.search(r"\b(\d{1,3})-(\d{1,3})(-\d{1,2})?\b", txt)
        return bool(rec), bool(_methods_from_text(txt)), "article found"
    return False, False, "no page"


def thin_fighters(fights, months=12, max_prior=3):
    """Fighters who appeared recently with few or no prior UFC bouts."""
    f = fights.sort_values("date")
    cutoff = pd.Timestamp(f.date.max()) - pd.DateOffset(months=months)
    prior, out = {}, []
    for r in f.itertuples():
        parts = [x.strip() for x in str(r.bout).split(" vs. ")]
        if len(parts) != 2:
            continue
        for nm, fid in ((parts[0], r.r_id), (parts[1], r.b_id)):
            n = prior.get(fid, 0)
            if r.date >= cutoff and n <= max_prior:
                out.append((nm, n))
        for fid in (r.r_id, r.b_id):
            prior[fid] = prior.get(fid, 0) + 1
    seen, uniq = set(), []
    for nm, n in out:
        if nm.lower() not in seen:
            seen.add(nm.lower())
            uniq.append((nm, n))
    return uniq


ESPN_LEAGUES = [
    "https://sports.core.api.espn.com/v2/sports/mma/leagues?limit=100",
    "https://site.api.espn.com/apis/site/v2/sports/mma/leagues",
]


def espn_leagues(verbose=True):
    """Which promotions does ESPN carry?

    This decides the approach before any endpoint does. A UFC debutant's
    earlier fights only exist in ESPN's data if ESPN covered the promotion he
    fought for. If the list is UFC, PFL and Bellator, then most debutants came
    from regional shows ESPN never recorded, and no athlete endpoint will
    invent them — the coverage bar fails for a reason no amount of probing
    fixes. If Contender Series or the regional feeders are there, a pre-UFC
    record can be assembled from fights rather than scraped from a summary,
    which is the better source anyway.
    """
    for url in ESPN_LEAGUES:
        try:
            j = _get(url)
        except Exception as e:
            if verbose:
                print(f"  leagues {url.split('?')[0]} -> {str(e)[:44]}")
            continue
        blob = json.dumps(j)
        names = sorted(set(re.findall(r'"(?:name|shortName|displayName)"\s*:\s*"([^"]{3,44})"', blob)))
        refs = len(re.findall(r'/leagues/([a-z0-9_-]+)', blob))
        if verbose:
            print(f"  leagues endpoint: {url}")
            print(f"    {len(names)} names, {refs} league references")
            for n in names[:25]:
                print(f"      {n}")
        return names
    if verbose:
        print("  no leagues endpoint answered — cannot tell what ESPN covers")
    return []


def run(source="both", months=12, limit=60, verbose=True):
    from .loaders import load
    fights, _p, _ = load(verbose=False)
    people = thin_fighters(fights, months=months)[:limit]
    if verbose:
        print(f"probing {len(people)} fighters with 3 or fewer prior UFC bouts, "
              f"from the last {months} months")
        print("  bar: 70% with a record AND a method split (addendum 36)")
        print()
    if source in ("both", "espn"):
        if verbose:
            print("WHICH PROMOTIONS DOES ESPN CARRY? (this decides the approach)")
        espn_leagues(verbose=verbose)
        if verbose:
            print()
    srcs = {"espn": espn_record, "wiki": wiki_record}
    if source != "both":
        srcs = {source: srcs[source]}
    out = {}
    for key, fn in srcs.items():
        hit = split = 0
        for nm, n in people:
            try:
                got, meth, note = fn(nm, verbose=verbose and hit + split == 0)
            except Exception as e:
                got, meth, note = False, False, str(e)[:40]
            hit += int(got)
            split += int(got and meth)
            if verbose and not got:
                print(f"    miss: {nm} ({n} prior) — {note}")
            time.sleep(0.2)
        n = max(len(people), 1)
        out[key] = {"n": len(people), "record": hit / n, "with_methods": split / n,
                    "endpoint": _WORKED.get("espn_athlete") if key == "espn" else "wikipedia api"}
        if verbose:
            print()
            print(f"  {key}: record for {100*hit/n:.0f}%, with a method split "
                  f"{100*split/n:.0f}%  -> {'CLEARS' if split/n >= 0.70 else 'BELOW'} the 70% bar")
            if key == "espn":
                print(f"    endpoints that answered: {_WORKED.get('espn_search','-')} | "
                      f"{_WORKED.get('espn_athlete','-')}")
            print()
    if verbose:
        best = max(out.items(), key=lambda kv: kv[1]["with_methods"])
        if best[1]["with_methods"] >= 0.70:
            print(f"VERDICT: {best[0]} clears the bar. Step 2 of addendum 36 can proceed.")
        else:
            print("VERDICT: neither source clears 70%. Addendum 36 says stop here — a record "
                  "present for the known fighters and missing for the obscure ones adds "
                  "signal where it is least needed.")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="both", choices=["both", "espn", "wiki"])
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--limit", type=int, default=60)
    a = ap.parse_args()
    run(source=a.source, months=a.months, limit=a.limit)
