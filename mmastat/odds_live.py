"""Live moneyline prices from The Odds API, for the automated refresh.

Why this and not the Kaggle feed: that file has no public raw URL, so a CI job
cannot fetch it. The Odds API has a perpetual free tier (500 requests/month;
one call a day uses about 30), returns JSON over a plain URL, and covers MMA.

What it does NOT provide, and nobody free does: **method, round or any other
prop prices for MMA.** The Odds API's own documentation says it covers fight
winner odds only. So the site prices its own props from the hazard model and
shows a market marker on the moneyline alone. That asymmetry is honest — a
model number and a market number side by side is a comparison; a model number
alone is a projection, and the site should not imply otherwise.

Set ODDS_API_KEY in the environment. In GitHub Actions:
Settings -> Secrets and variables -> Actions -> New repository secret.
Absent key means absent panel, never a stale price.
"""
import os
import re
import unicodedata

BASE = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds"


def _nm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


def fetch_moneylines(api_key=None, regions="us,uk,eu", timeout=30):
    """{frozenset(name_a, name_b): (name_a, devigged P(a), n_books)}.

    Consensus is the MEDIAN across books, not the best price. Best-available is
    what a bettor would take, but it is the wrong number to compare a model
    against — it mixes book disagreement into what is supposed to be the
    market's estimate.
    """
    import requests
    key = api_key or os.environ.get("ODDS_API_KEY")
    if not key:
        return {}
    r = requests.get(BASE, timeout=timeout, params={
        "regions": regions, "markets": "h2h",
        "oddsFormat": "decimal", "apiKey": key})
    if r.status_code == 401:
        raise RuntimeError("ODDS_API_KEY rejected by The Odds API (401)")
    if r.status_code == 429:
        raise RuntimeError("The Odds API monthly quota exhausted (429)")
    r.raise_for_status()

    out = {}
    for ev in r.json():
        quotes = {}
        for bk in ev.get("bookmakers", []):
            for mkt in bk.get("markets", []):
                if mkt.get("key") != "h2h":
                    continue
                o = mkt.get("outcomes", [])
                if len(o) != 2:
                    continue
                for side in o:
                    quotes.setdefault(_nm(side["name"]), []).append(float(side["price"]))
        if len(quotes) != 2:
            continue
        (k1, p1), (k2, p2) = quotes.items()
        med = lambda v: sorted(v)[len(v) // 2]
        i1, i2 = 1.0 / med(p1), 1.0 / med(p2)
        out[frozenset((k1, k2))] = (k1, i1 / (i1 + i2), max(len(p1), len(p2)))
    return out


def remaining_quota(api_key=None):
    """The API reports quota in response headers; useful in a CI log."""
    import requests
    key = api_key or os.environ.get("ODDS_API_KEY")
    if not key:
        return None
    r = requests.get(BASE, timeout=20, params={
        "regions": "us", "markets": "h2h", "apiKey": key})
    return {"used": r.headers.get("x-requests-used"),
            "remaining": r.headers.get("x-requests-remaining")}
