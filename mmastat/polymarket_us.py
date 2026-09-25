"""Polymarket US — the CFTC-regulated exchange, read through its public gateway.

A separate venue from global Polymarket, not a regional skin: its own order
book, its own slugs for the same bout (ufc-ala1-joh9-2026-09-26 globally is
ufc-johcas-alaten-2026-09-26 here). It is captured and stored separately for
the same reason the sportsbook and Polymarket have never been pooled — two
books that disagree are two facts, and averaging them loses both.

Public API, no key: https://gateway.polymarket.us

    GET /v2/leagues/ufc/events        events, each with its markets

Each market carries `sportsMarketType` (MONEYLINE / TOTAL / PROP / FUTURE),
which is a stated type rather than a guess from the question text — the global
reader has to infer this and gets it wrong often enough to matter. Events also
carry a `ufcState` block with weight class, card segment and scheduled rounds.

The price shapes are read defensively. The schema marks `outcomes` and
`outcomePrices` deprecated in favour of `marketSides`, so both are handled and
the first live run reports which shape actually arrived.
"""
import json
import re
import time
import unicodedata
from collections import Counter

GATEWAY = "https://gateway.polymarket.us"
SITE = "https://polymarket.us"
UA = "CornermanBot/1.0 (https://github.com/idrum93/cornerman-repo; research)"
RESOLVED_EPS = 0.02
PAUSE = 0.4

TYPE_MAP = {"SPORTS_MARKET_TYPE_MONEYLINE": "winner",
            "SPORTS_MARKET_TYPE_TOTAL": "total",
            "SPORTS_MARKET_TYPE_PROP": "prop",
            "SPORTS_MARKET_TYPE_SPREAD": "spread",
            "SPORTS_MARKET_TYPE_FUTURE": "future"}


def market_url(slug):
    slug = str(slug or "")
    return f"{SITE}/sports/ufc/{slug}" if slug.startswith("ufc-") else f"{SITE}/event/{slug}"


SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv)\b", re.I)


def _nm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z ]", " ", s.lower())
    s = SUFFIX.sub(" ", s)                 # "R. Rosas Jr." -> "r rosas"
    return re.sub(r"\s+", " ", s).strip()


def _surname(n):
    """Last real token: initials and suffixes are not surnames."""
    toks = [t for t in _nm(n).split() if len(t) > 1]
    return toks[-1] if toks else ""


def _get(path, params=None, tries=3):
    import requests
    for k in range(tries):
        r = requests.get(GATEWAY + path, params=params or {}, timeout=45,
                         headers={"User-Agent": UA, "Accept": "application/json"})
        if r.status_code in (429, 500, 502, 503):
            time.sleep(2 * (k + 1))
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()
    raise RuntimeError(f"polymarket us gateway kept failing on {path}")


def fetch_events(limit=100, pages=4):
    out = []
    for p in range(pages):
        j = _get("/v2/leagues/ufc/events", {"limit": limit, "offset": p * limit,
                                            "type": "sport"})
        ev = j.get("events") or []
        out += ev
        if len(ev) < limit:
            break
    return out


def _sides(m):
    """[(name, price)] for a market, from whichever shape the payload uses."""
    out = []
    for s in m.get("marketSides") or []:
        name = s.get("description") or s.get("identifier") or ""
        px = s.get("price")
        if px is None and isinstance(s.get("quote"), dict):
            px = s["quote"].get("value")
        try:
            px = float(px)
        except (TypeError, ValueError):
            continue
        if name:
            out.append((str(name), px))
    if out:
        return out, "marketSides"
    try:                                   # deprecated, still sometimes present
        names = json.loads(m.get("outcomes") or "[]")
        prices = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
        if len(names) == len(prices) and names:
            return list(zip(names, prices)), "outcomePrices"
    except Exception:
        pass
    return [], "none"


def _quote(m):
    def val(x):
        try:
            return float(x.get("value")) if isinstance(x, dict) else None
        except (TypeError, ValueError):
            return None
    bid, ask = val(m.get("bestBidQuote")), val(m.get("bestAskQuote"))
    if bid is None or ask is None or not (0 < bid <= ask < 1):
        return {}
    return {"bid": bid, "ask": ask, "spread": round(ask - bid, 4),
            "mid": round((bid + ask) / 2, 5)}


def parse(events):
    """Flatten to rows: one per market, with its stated type and prices."""
    rows = []
    for e in events:
        st = ((e.get("eventState") or {}).get("ufcState")) or {}
        for m in e.get("markets") or []:
            if m.get("closed") or m.get("archived") or m.get("hidden"):
                continue
            sides, shape = _sides(m)
            rows.append({
                "event_slug": e.get("slug"), "event_title": e.get("title"),
                "start": e.get("startDate") or e.get("eventDate"),
                "weight_class": st.get("weightClass"), "segment": st.get("cardSegment"),
                "rounds": st.get("rounds"),
                "slug": m.get("slug") or e.get("slug"),
                "question": m.get("question") or m.get("title") or "",
                "kind": TYPE_MAP.get(m.get("sportsMarketType") or "", "other"),
                "line": m.get("line"), "volume": m.get("volume"),
                "sides": sides, "shape": shape, "book": _quote(m)})
    return rows


def moneylines(rows, max_spread=0.06, min_volume=200.0, require_book=True):
    """{frozenset(name_a, name_b): (name_a, P(a), meta)} — same shape the global
    reader returns, so the ledger treats both venues identically.

    Gates fail closed, as everywhere else: no book means no row. Depth is not
    in this payload, so lifetime volume stands in for it; that is a weaker
    filter than the global reader's order-book depth and is recorded as such.
    """
    out = {}
    for r in rows:
        if r["kind"] != "winner" or len(r["sides"]) != 2:
            continue
        (na, pa), (nb, pb) = r["sides"]
        a, b = _nm(na), _nm(nb)
        if not a or not b or a == b:
            continue
        tot = pa + pb
        if tot <= 0:
            continue
        p = pa / tot
        bk = r["book"]
        if require_book:
            if not bk:
                continue
            if bk["spread"] > max_spread:
                continue
            if (r["volume"] or 0) < min_volume:
                continue
            p = bk["mid"]
        if not (RESOLVED_EPS < p < 1 - RESOLVED_EPS):
            continue
        meta = {"slug": r["slug"], "venue": "polymarket_us", "volume": r["volume"],
                "weight_class": r["weight_class"], "segment": r["segment"], **bk}
        out[frozenset((a, b))] = (a, round(p, 5), meta)
    return _with_variants(out)


def _with_variants(out):
    """Surname and spacing keys, so a bout still matches when the two sources
    spell a name differently. Ambiguous keys are dropped, never guessed."""
    extra = {}
    for k in list(out):
        for v in (frozenset(n.split()[-1] for n in k if n.split()),
                  frozenset(n.replace(" ", "") for n in k)):
            if len(v) == 2:
                extra.setdefault(v, []).append(k)
    for v, ks in extra.items():
        if len(ks) == 1 and v not in out:
            out[v] = out[ks[0]]
    return out


ROUND_RE = re.compile(r"\bround\s*([1-5])\b", re.I)
DIST_RE = re.compile(r"go(es)? the distance|go to (a )?decision|by decision|"
                     r"decision\b.*\bwin|fight to go the distance", re.I)
ITD_RE = re.compile(r"inside the distance", re.I)
KO_RE = re.compile(r"\bko\b|knockout|tko", re.I)
SUB_RE = re.compile(r"submission|tap", re.I)


def map_props(rows, bouts, max_spread=0.10, min_volume=100.0):
    """Props matched to the market keys mmastat.scorecard grades.

    Unlike the global reader, the market type is stated rather than inferred,
    so only markets the exchange itself calls a prop or a total are considered.
    Anything that cannot be placed on a bout AND a known market is skipped.
    """
    byname = {}
    for bt in bouts:
        a, b = bt[0], bt[1]
        byname[(_nm(a), _nm(b))] = (a, b)
    # Every market here belongs to an event, and a UFC event IS one bout, so a
    # prop whose question never names a fighter ("Will the fight end in round
    # 1?") can still be placed through its event. The global feed has no such
    # handle, which is why those props were being dropped.
    by_event = {}
    for r in rows:
        if r["kind"] != "winner" or len(r["sides"]) != 2:
            continue
        variants = [frozenset(_nm(n) for n, _ in r["sides"]),
                    frozenset(_surname(n) for n, _ in r["sides"]),
                    frozenset(_nm(n).replace(" ", "") for n, _ in r["sides"])]
        for (ka, kb), (a, b) in byname.items():
            cand = [frozenset((ka, kb)), frozenset((_surname(ka), _surname(kb))),
                    frozenset((ka.replace(" ", ""), kb.replace(" ", "")))]
            if any(v == c for v in variants for c in cand):
                by_event[r["event_slug"]] = (a, b)
                break
    out = []
    for r in rows:
        if r["kind"] not in ("prop", "total") or len(r["sides"]) != 2:
            continue
        q = _nm(r["question"])
        hit = None
        if r.get("event_slug") in by_event:
            a0, b0 = by_event[r["event_slug"]]
            la, lb = _surname(a0), _surname(b0)
            hit = (a0, b0, "a" if (la in q and lb not in q) else
                   ("b" if (lb in q and la not in q) else None))
        for (ka, kb), (a, b) in byname.items():
            la, lb = _surname(ka), _surname(kb)
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
        # "Fight ends before Round 4 begins" — a cumulative round contract
        mb = re.search(r"ends? before round\s*([2-5])", r["question"], re.I)
        if mb:
            key = f"ends_before_r{mb.group(1)}"
        # "Method of Finish": one contract per method, no fighter named
        elif side is None and re.fullmatch(r"\s*decision\s*", r["question"], re.I):
            key = "method_dec"
        elif side is None and KO_RE.search(r["question"]) and not re.search(r"\bby\b", r["question"], re.I):
            key = "method_ko"
        elif side is None and SUB_RE.search(r["question"]) and not re.search(r"\bby\b", r["question"], re.I):
            key = "method_sub"
        # "R. Rosas Jr. by Submission" — fighter and method together
        elif side and re.search(r"\bby\b", r["question"], re.I):
            if SUB_RE.search(r["question"]):
                key = "sub_" + side
            elif KO_RE.search(r["question"]):
                key = "ko_" + side
            elif re.search(r"decision", r["question"], re.I):
                key = "dec_" + side
        if not key and r["kind"] == "total" and r.get("line") is not None:
            # "Over 1.5 rounds" arrives as a TOTAL with line=1.5, not as text
            key = "total_over_" + str(r["line"]).replace(".", "_").rstrip("_0") \
                if float(r["line"]) % 1 else None
            if key:
                yes_is_over = any("over" in _nm(n) for n, _ in r["sides"])
                if not yes_is_over:
                    key = None
        if not key:
            # older phrasings, only reached when nothing above matched — this
            # chain used to run unguarded and overwrite every key set above,
            # turning "Rosas by Decision" into the fight-level decision market
            m = ROUND_RE.search(r["question"])
            if m:
                key = f"end_r{m.group(1)}"
            elif DIST_RE.search(r["question"]):
                key = "decision"
            elif ITD_RE.search(r["question"]):
                key = "inside_distance"
            elif KO_RE.search(r["question"]) and side:
                key = "ko_" + side
            elif SUB_RE.search(r["question"]) and side:
                key = "sub_" + side
        if not key:
            continue
        yes = next((i for i, (n, _) in enumerate(r["sides"])
                    if _nm(n).startswith("yes") or _nm(n).startswith("over")), 0)
        tot = sum(p for _, p in r["sides"])
        if tot <= 0:
            continue
        p = r["sides"][yes][1] / tot
        bk = r["book"]
        if bk:
            if bk["spread"] > max_spread:
                continue
            p = bk["mid"] if yes == 0 else 1 - bk["mid"]
        if (r["volume"] or 0) < min_volume:
            continue
        if not (RESOLVED_EPS < p < 1 - RESOLVED_EPS):
            continue
        out.append({"bout": f"{a} vs. {b}", "a": a, "b": b, "market": key,
                    "p_market": round(p, 5),
                    "meta": {"slug": r["slug"], "question": r["question"],
                             "venue": "polymarket_us", "volume": r["volume"], **bk}})
    return out


def describe(rows):
    """What the gateway actually returned — printed on the first live run,
    because the price shape and the market mix are the two things the docs
    cannot tell us."""
    per_event = Counter(r["event_slug"] for r in rows)
    return {"markets": len(rows), "events": len(per_event),
            "markets_per_event_max": max(per_event.values()) if per_event else 0,
            "kinds": dict(Counter(r["kind"] for r in rows)),
            "shapes": dict(Counter(r["shape"] for r in rows)),
            "with_book": sum(1 for r in rows if r["book"])}
