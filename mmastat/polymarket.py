"""Polymarket as a second price source — and a structurally different one.

Why bother when The Odds API already works: **a prediction market has almost no
vig.** Sportsbooks quote a two-way overround around 3.7% on the moneyline and
22% on six-way method markets, which is why chasing obscure props there is a
trap — the margin is exactly why nobody bothers to correct them. Polymarket is
peer-to-peer with a small taker fee, so the bar an edge must clear drops from
several percent to well under one.

That matters here specifically. The residual model's measured advantage is
+0.0035 log loss, far too small to beat a bookmaker's margin. Against a
near-zero-fee venue it is at least the right order of magnitude to be worth
measuring. This module exists to find out.

The catch, and it is a real one: **liquidity, not price, is the constraint.**
A market quoting 0.62 with a 9-cent spread and $150 of depth is not a 0.62
price, it is a wish. So this captures the bid, the ask, the spread and the
book depth — never just a midpoint. The spread is this venue's equivalent of
vig and has to be logged alongside the number, or the comparison is dishonest.

Both endpoints used here are documented as public and unauthenticated:
  Gamma  https://gamma-api.polymarket.com   events and markets
  CLOB   https://clob.polymarket.com        orderbook, prices, spreads
"""
import json
import re
import unicodedata

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
UA = "Cornerman/1.0 (UFC analysis; contact via repo issues)"

# markets whose question matches these are props rather than a winner market
PROP_PATTERNS = [
    ("distance", re.compile(r"go the distance|goes the distance|by decision", re.I)),
    ("ko", re.compile(r"\bby (ko|tko|knockout)\b", re.I)),
    ("submission", re.compile(r"by submission", re.I)),
    ("round", re.compile(r"in round \d|round \d\.5|over .*rounds", re.I)),
]


def _nm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


def _get(url, params=None, timeout=30):
    import requests
    r = requests.get(url, params=params or {}, timeout=timeout,
                     headers={"User-Agent": UA})
    r.raise_for_status()
    return r.json()


def fetch_events(limit=100):
    """Open UFC events. tag_slug is documented; the fallback keyword scan
    covers the case where Polymarket retags."""
    try:
        ev = _get(f"{GAMMA}/events", {"active": "true", "closed": "false",
                                      "tag_slug": "ufc", "limit": limit})
        if ev:
            return ev
    except Exception:
        pass
    ev = _get(f"{GAMMA}/events", {"active": "true", "closed": "false",
                                  "limit": limit})
    return [e for e in ev if re.search(r"\bufc\b|\bmma\b", str(e.get("title", "")), re.I)]


def classify(question):
    for kind, pat in PROP_PATTERNS:
        if pat.search(str(question or "")):
            return kind
    return "winner"


def parse_events(events):
    """Flatten Gamma events into rows we can match against a card.

    Gamma returns outcomes and outcomePrices as JSON-encoded strings on each
    market, which is easy to mishandle — they are parsed here rather than at
    the call site.
    """
    out = []
    for e in events:
        for m in e.get("markets", []) or []:
            q = m.get("question") or m.get("groupItemTitle") or ""
            outcomes = m.get("outcomes")
            prices = m.get("outcomePrices")
            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                except Exception:
                    outcomes = []
            if isinstance(prices, str):
                try:
                    prices = json.loads(prices)
                except Exception:
                    prices = []
            toks = m.get("clobTokenIds")
            if isinstance(toks, str):
                try:
                    toks = json.loads(toks)
                except Exception:
                    toks = []
            out.append(dict(
                event=e.get("title"), slug=m.get("slug"), question=q,
                closed=bool(m.get("closed") or e.get("closed")),
                resolved=bool(m.get("umaResolutionStatus") == "resolved"
                              or m.get("resolvedBy")),
                kind=classify(q),
                outcomes=list(outcomes or []),
                prices=[float(p) for p in (prices or []) if p not in (None, "")],
                token_ids=list(toks or []),
                liquidity=float(m.get("liquidityNum") or m.get("liquidity") or 0) or None,
                volume=float(m.get("volumeNum") or m.get("volume") or 0) or None,
                end_date=e.get("endDate")))
    return out


def book_quality(token_id):
    """Bid, ask, spread and depth for one outcome token. Without this a
    midpoint is meaningless — spread is the prediction-market analogue of
    vig, and depth decides whether the price is reachable at all."""
    try:
        b = _get(f"{CLOB}/book", {"token_id": token_id})
    except Exception:
        return {}
    bids = b.get("bids") or []
    asks = b.get("asks") or []
    best_bid = max((float(x["price"]) for x in bids), default=None)
    best_ask = min((float(x["price"]) for x in asks), default=None)
    depth = sum(float(x.get("size", 0)) * float(x.get("price", 0))
                for x in bids + asks)
    return {"bid": best_bid, "ask": best_ask,
            "spread": (best_ask - best_bid) if (best_bid and best_ask) else None,
            "mid": ((best_bid + best_ask) / 2) if (best_bid and best_ask) else None,
            "depth_usd": round(depth, 2)}


# A market at 0.99 or 0.01 is not a confident market, it is a decided one.
# Polymarket leaves fights listed until they resolve, so a capture run after
# the bell reads 1.0 / 0.0 — which would enter the ledger as a "prediction"
# the model got exactly right. That happened on the first live Polymarket
# capture: eight rows at certainty, hours after the fights ended.
RESOLVED_EPS = 0.02


def moneylines(rows, with_book=True, max_spread=0.06, min_depth=250.0,
               require_book=True):
    """{frozenset(name_a, name_b): (name_a, P(a), meta)} for winner markets.

    Every gate here FAILS CLOSED. The first version skipped its liquidity
    checks whenever the orderbook call returned nothing, so a market with no
    book data sailed through — which is exactly the case where you know least
    about whether the price is real. Missing evidence is now a rejection, not
    a pass.
    """
    out = {}
    for r in rows:
        if r["kind"] != "winner" or len(r["outcomes"]) != 2 or len(r["prices"]) != 2:
            continue
        if r.get("closed") or r.get("resolved"):
            continue
        a, b = _nm(r["outcomes"][0]), _nm(r["outcomes"][1])
        if not a or not b or a == b:
            continue
        pa, pb = r["prices"][0], r["prices"][1]
        tot = pa + pb
        if tot <= 0:
            continue
        if min(pa, pb) <= RESOLVED_EPS or max(pa, pb) >= 1 - RESOLVED_EPS:
            continue                      # decided, not predicted
        meta = {"liquidity": r["liquidity"], "volume": r["volume"],
                "slug": r["slug"], "venue": "polymarket"}
        if with_book:
            q = book_quality(r["token_ids"][0]) if r["token_ids"] else {}
            meta.update(q)
            if q.get("spread") is None or q.get("depth_usd") is None:
                if require_book:
                    continue              # no book, no row
            else:
                if q["spread"] > max_spread or q["depth_usd"] < min_depth:
                    continue
                if q.get("mid") is None or not (RESOLVED_EPS < q["mid"] < 1 - RESOLVED_EPS):
                    continue
                pa, pb, tot = q["mid"], 1 - q["mid"], 1.0
        out[frozenset((a, b))] = (a, pa / tot, meta)
    return out


ROUND_RE = re.compile(r"\bround\s*([1-5])\b", re.I)
DIST_YES = re.compile(r"go(es)? the distance|go to (a )?decision", re.I)
DIST_NO = re.compile(r"inside the distance|end early|finish", re.I)


def map_props(rows, bouts, min_depth=150.0, max_spread=0.10, with_book=True):
    """Match Polymarket prop questions to the market keys the scorecard grades.

    A question names the fighters ("Will Tsarukyan win by submission?"), so the
    bout and the side are recovered by matching those names against the card.
    Anything that cannot be matched to a bout AND a known market is skipped
    rather than guessed at — a mis-assigned prop would be graded against the
    wrong claim, which is worse than having no price.

    Keys match mmastat.scorecard so settlement is the same code path:
    decision, inside_distance, ko_a, ko_b, sub_a, sub_b, end_r1..end_r5.
    """
    byname = {}
    for bt in bouts:
        a, b = bt[0], bt[1]
        byname[(_nm(a), _nm(b))] = (a, b)
    out = []
    for r in rows:
        if r["kind"] == "winner" or len(r["outcomes"]) != 2 or len(r["prices"]) != 2:
            continue
        q = _nm(r["question"])
        hit = None
        for (ka, kb), (a, b) in byname.items():
            la, lb = ka.split()[-1], kb.split()[-1]
            if la in q and lb in q:
                hit = (a, b, None); break
            if la in q:
                hit = (a, b, "a"); break
            if lb in q:
                hit = (a, b, "b"); break
        if not hit:
            continue
        a, b, side = hit
        key = None
        m = ROUND_RE.search(r["question"])
        if m:
            key = f"end_r{m.group(1)}"
        elif r["kind"] == "distance" or DIST_YES.search(r["question"]):
            key = "decision" if DIST_YES.search(r["question"]) else "inside_distance"
        elif r["kind"] == "ko" and side:
            key = "ko_" + side
        elif r["kind"] == "submission" and side:
            key = "sub_" + side
        if not key:
            continue
        yes = next((i for i, o in enumerate(r["outcomes"]) if _nm(o).startswith("yes")), None)
        if yes is None:
            continue
        tot = sum(r["prices"])
        if tot <= 0:
            continue
        p = r["prices"][yes] / tot
        meta = {"slug": r["slug"], "question": r["question"], "liquidity": r["liquidity"]}
        if with_book and r["token_ids"]:
            bk = book_quality(r["token_ids"][yes])
            meta.update(bk)
            if bk.get("spread") is None or bk.get("depth_usd") is None:
                continue                      # fail closed, as for winners
            if bk["spread"] > max_spread or bk["depth_usd"] < min_depth:
                continue
            if bk.get("mid") and RESOLVED_EPS < bk["mid"] < 1 - RESOLVED_EPS:
                p = bk["mid"]
        if not (RESOLVED_EPS < p < 1 - RESOLVED_EPS):
            continue                          # decided, not predicted
        out.append({"bout": f"{a} vs. {b}", "a": a, "b": b, "market": key,
                    "p_market": round(p, 5), "meta": meta})
    return out


EVENT_URL = "https://polymarket.com/event/"


def unmatched(rows, bouts):
    """UFC markets Polymarket quotes that the model does not price.

    Listed, with links, and never given a number. The site's rule is that a
    market either carries a projection we can check or it carries nothing —
    but staying silent about markets that exist would hide what is on offer.
    """
    # classify() defaults to "winner" for anything it does not recognise, so a
    # market is only treated as placed if it actually matched — either a prop
    # we mapped, or a two-name market whose pair is on this card. Otherwise
    # event-level markets ("will there be a new champion") were silently
    # swallowed as winner markets and never listed.
    pairs = {frozenset((_nm(bt[0]), _nm(bt[1]))) for bt in bouts}
    placed = {x["meta"].get("slug") for x in map_props(rows, bouts, with_book=False)}
    for r in rows:
        o = [_nm(x) for x in r["outcomes"]]
        if len(o) == 2 and frozenset(o) in pairs:
            placed.add(r["slug"])
    out = []
    for r in rows:
        if r["slug"] in placed or not r.get("question"):
            continue
        out.append({"question": r["question"], "slug": r["slug"],
                    "kind": r["kind"], "liquidity": r["liquidity"]})
    return out


def props(rows):
    """Non-winner markets, grouped by kind. Sportsbooks price MMA props at a
    22% overround; if Polymarket lists any at all they are worth far more as
    a comparison point than a book's would be."""
    keep = {}
    for r in rows:
        if r["kind"] == "winner":
            continue
        keep.setdefault(r["kind"], []).append(r)
    return keep


def fetch_all(with_book=True):
    rows = parse_events(fetch_events())
    return moneylines(rows, with_book=with_book), props(rows), rows
