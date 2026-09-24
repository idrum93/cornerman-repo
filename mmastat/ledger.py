"""Forward odds capture: the only remaining way to test the residual rule.

The problem this solves. Every result in this project is retrospective, and the
one finding that ever pointed the right way — the market-residual model,
better in 6 of 6 walk-forward folds — cannot be confirmed retrospectively. The
252-fight holdout has no prices. Re-scoring old fights against old odds is
re-reading data the rule was built on. The only honest test is to write the
prediction down before the fight and check it afterwards.

So this is an append-only log. Three commands:

    capture   fetch live lines, compute the frozen rule's number, append a row
    settle    match logged rows to finished fights, record the outcome
    report    bets, ROI, CLV, and progress toward the 300-bet threshold

Three rules that keep it honest, all enforced in code rather than by intention:

  FROZEN COEFFICIENTS. The rule's weights live in residual_model.json and are
  applied, never refitted. Refitting on each capture would quietly turn the
  forward test back into a retrospective one.

  APPEND ONLY. Rows are never rewritten, only settled. A ledger you can edit
  is a ledger you will edit.

  CLOSING LINE = LAST SNAPSHOT. Capture runs repeatedly; the row nearest the
  event is the closing price. Closing line value converges far faster than ROI
  (~300 bets for ROI, a few dozen for CLV), so CLV is the metric that will
  tell you something first.
"""
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

LEDGER_DIR = "data/ledger"
LEGACY = "data/ledger/odds_log.jsonl"
LEDGER = LEGACY          # kept for call sites that pass an explicit path


def month_file(when=None, directory=LEDGER_DIR):
    """Ledger rows go in a per-month file, e.g. data/ledger/2026-09.jsonl.

    Not for size — a year of capture is under 2 MB. For CHURN. settle()
    rewrites the whole ledger each run, so with one big file every one of the
    ~1,460 commits a year stores a fresh blob of an ever-growing file. With
    monthly files, a month's file stops changing the day the month ends and
    costs nothing thereafter. Cheap now, and it removes the only part of this
    that would eventually need object storage.
    """
    ts = pd.Timestamp(when) if when is not None else pd.Timestamp.now(tz="UTC")
    return os.path.join(directory, f"{ts.year:04d}-{ts.month:02d}.jsonl")


def ledger_files(directory=LEDGER_DIR):
    """Every ledger shard, oldest first. The legacy single file is included so
    existing rows are never orphaned by the switch."""
    import glob
    files = sorted(glob.glob(os.path.join(directory, "[0-9][0-9][0-9][0-9]-[0-9][0-9].jsonl")))
    if os.path.exists(LEGACY):
        files = [LEGACY] + files
    return files
MODEL = os.path.join(os.path.dirname(__file__), "residual_model.json")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_rule(path=MODEL):
    with open(path) as fh:
        return json.load(fh)


def rule_probability(feat_row, p_market, rule):
    """P(win) = sigmoid(logit(market) + x.beta), with x standardised by the
    frozen scaler. feat_row is a dict of the five feature values."""
    x = np.array([float(feat_row[k]) for k in rule["features"]])
    z = (x - np.array(rule["mean"])) / np.array(rule["scale"])
    pm = min(max(float(p_market), 1e-6), 1 - 1e-6)
    logit = math.log(pm / (1 - pm)) + float(z @ np.array(rule["coef"]))
    return 1.0 / (1.0 + math.exp(-logit))


def fires(p_model, implied_with_vig, rule):
    """Does the pre-registered bet trigger? Favourites only, edge over the
    price you would actually pay (vig included), not the devigged estimate."""
    r = rule["rule"]
    if r.get("favourites_only") and implied_with_vig < r["min_implied"]:
        return False
    return (p_model - implied_with_vig) > r["min_edge"]


def append(rows, path=None):
    """Append each row to the shard for its own capture month."""
    if not rows:
        return 0
    by_file = {}
    for r in rows:
        f = path or month_file(r.get("captured_utc"))
        by_file.setdefault(f, []).append(r)
    n = 0
    for f, rs in by_file.items():
        Path(f).parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a", encoding="utf-8") as fh:
            for r in rs:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        n += len(rs)
    return n


KEY = ["captured_utc", "venue", "event_date", "fighter", "opponent"]


def dedupe(rows):
    """One row per (capture time, bout, fighter), last write wins.

    An append-only log committed by a scheduled job will eventually get
    duplicated: a rebase replays a local rewrite on top of a remote that
    already has it, and both copies survive. That happened on the second live
    capture — the 13:56 Van/Pantoja rows appeared twice, once with the old bad
    settlement and once corrected. Duplicates would double-count in both CLV
    and ROI, so the file is deduplicated on every write. The capture fields
    are identical across copies by construction, so keeping the last is safe.
    """
    seen = {}
    for r in rows:
        k = tuple(str(r.get(k2)) for k2 in KEY)
        if k in seen and seen[k].get("opening") and not r.get("opening"):
            # Last-write-wins must never erase an opening marker: that flag
            # records the first time a bout was seen, and a merge or a
            # same-second recapture could otherwise silently turn it off.
            r = dict(r, opening=True)
        seen[k] = r
    return list(seen.values())


# Fields added after the ledger was already running, with the value that rows
# written before them are known to have had. An append-only log keeps every
# historical schema forever, so every consumer must tolerate the oldest one:
# adding `venue` to the dedupe key broke capture outright with
# KeyError: ['venue'] not in index, because the first 48 rows predate it.
BACKFILL = {"venue": "sportsbook", "spread": None, "depth_usd": None,
            "books": None, "settled": False}


def migrate(rows):
    """Give every row today's schema, so old and new rows compare equal."""
    out = []
    for r in rows:
        d = dict(r)
        for k, v in BACKFILL.items():
            d.setdefault(k, v)
            if d.get(k) is None and k == "venue":
                d[k] = "sportsbook"
        out.append(d)
    return out


def _raw(path=None):
    files = [path] if path else ledger_files()
    rows = []
    for f in files:
        if not f or not os.path.exists(f):
            continue
        rows += [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    return rows


def read(path=None):
    rows = _raw(path)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(dedupe(migrate(rows)))
    for k, v in BACKFILL.items():          # guarantee the column exists
        if k not in df.columns:
            df[k] = v
    return df


def prune_resolved(path=None, eps=0.02, verbose=True):
    """Remove rows whose market price is at certainty.

    Append-only is a discipline for PREDICTIONS. A row quoting 1.0 after the
    fight is not a prediction that turned out well, it is corrupt input, and
    leaving it in would hand the model a fabricated perfect record. Removals
    are counted and reported rather than done silently.
    """
    drop = 0
    for f in ([path] if path else ledger_files()):
        if not f or not os.path.exists(f):
            continue
        rows = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        keep = [r for r in rows
                if r.get("p_market_devig") is None
                or eps < float(r["p_market_devig"]) < 1 - eps]
        if len(keep) != len(rows):
            drop += len(rows) - len(keep)
            Path(f).write_text(
                "\n".join(json.dumps(r, sort_keys=True) for r in keep) + "\n",
                encoding="utf-8")
    if drop and verbose:
        print(f"pruned {drop} rows priced at certainty (resolved markets)")
    return drop


def _rewrite(path=None):
    """Deduplicate each shard in place. Only shards that actually change are
    written, so a closed month never produces a new git blob."""
    removed = 0
    for f in ([path] if path else ledger_files()):
        if not f or not os.path.exists(f):
            continue
        raw = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        clean = dedupe(migrate(raw))
        if len(clean) != len(raw):
            Path(f).write_text(
                "\n".join(json.dumps(r, sort_keys=True) for r in clean) + "\n",
                encoding="utf-8")
            removed += len(raw) - len(clean)
    return removed


def capture(fights, fighters, card_path="data/upcoming.txt", path=None,
            verbose=True, venues_only=None):
    """Log every priced bout on the upcoming card, at this moment."""
    from .odds_live import fetch_moneylines
    from .upcoming import parse_card, resolve, _states_after, _key
    from .features import elo_eff, make_features

    rule = load_rule()

    # Two venues, logged separately and never pooled.
    #
    #   sportsbook   The Odds API consensus. Cost is the bookmaker margin, so
    #                the payable price is the devigged probability inflated by
    #                half the two-way overround.
    #   polymarket   peer-to-peer, near-zero fee. There is no vig to add back:
    #                the ASK is literally what you pay. Its cost is the spread,
    #                which is recorded per row.
    #
    # They stay separate because the pre-registered rule was frozen on
    # sportsbook prices. Pooling a second venue into it would widen the
    # population mid-experiment, which is the same error as re-specifying a
    # hypothesis after seeing data. Polymarket rows accumulate as their own
    # test, with their own count toward 300.
    venues = {}
    try:
        sb = fetch_moneylines()
        if sb:
            venues["sportsbook"] = sb
    except Exception as e:
        print(f"note: sportsbook odds unavailable ({e})")
    try:
        from .polymarket import fetch_all
        pm, _props, _rows = fetch_all(with_book=True)
        if pm:
            venues["polymarket"] = pm
    except Exception as e:
        print(f"note: polymarket unavailable ({e})")
    if venues_only:
        venues = {k: v for k, v in venues.items() if k in venues_only}
    if not venues:
        if verbose:
            print("capture: no card-keyed venues to record")
        return 0
    book = venues.get("sportsbook") or {}

    meta, bouts = parse_card(card_path)

    # Hard stop: a capture is a PREDICTION, so it is only meaningful before
    # the event. Polymarket keeps resolved fights listed and quotes them at
    # 1.0/0.0; a run after the bell logged eight of those as if they were
    # forecasts the model nailed. No venue-specific fix is sufficient here —
    # the date is the invariant.
    ev_date = pd.to_datetime(meta.get("date"), errors="coerce")
    if pd.notna(ev_date) and pd.Timestamp.now(tz="UTC").normalize() > \
            ev_date.tz_localize("UTC") + pd.Timedelta(days=1):
        if verbose:
            print(f"card dated {meta.get('date')} is in the past - "
                  f"refusing to capture prices for a finished event")
        return 0

    states = _states_after(fights, fighters)
    names = sorted({n for b in bouts for n in b[:2]})
    ids, _ = resolve(names, fighters)
    as_of = pd.Timestamp(meta.get("date") or fights.date.max())

    rows, ts = [], _now()
    for venue, vbook in venues.items():
        for na, nb, n_rounds, _segment in bouts:
            hit = vbook.get(frozenset((_key(na), _key(nb))))
            if hit is None or na not in ids or nb not in ids:
                continue
            A, B = states[ids[na]], states[ids[nb]]
            if min(A.n_fights, B.n_fights) < 2:
                continue
            sa, sb = A.snapshot(as_of), B.snapshot(as_of)
            sa["elo"], sb["elo"] = elo_eff(A, as_of), elo_eff(B, as_of)
            fv = make_features(sa, sb)

            src, p_raw, extra = hit
            p_mkt = p_raw if src == _key(na) else 1 - p_raw
            meta_x = extra if isinstance(extra, dict) else {"books": extra}
            for side, name, opp, pm in (("a", na, nb, p_mkt), ("b", nb, na, 1 - p_mkt)):
                f = fv if side == "a" else {k: -v for k, v in fv.items()}
                p_model = rule_probability(f, pm, rule)
                if venue == "polymarket":
                    # the ask is the price; no margin to add back
                    sp = meta_x.get("spread")
                    implied = pm + (sp / 2 if sp else 0.0)
                else:
                    implied = pm * (1 + 0.037 / 2)
                rows.append(dict(
                    captured_utc=ts, venue=venue,
                    event=meta.get("event"), event_date=meta.get("date"),
                    fighter=name, opponent=opp, side=side,
                    p_market_devig=round(pm, 5), implied_with_vig=round(implied, 5),
                    p_model=round(p_model, 5), edge=round(p_model - implied, 5),
                    books=meta_x.get("books"), spread=meta_x.get("spread"),
                    depth_usd=meta_x.get("depth_usd"),
                    bet=bool(fires(p_model, implied, rule)),
                    rule_frozen_on=rule.get("frozen_on"), settled=False))
    # Read the raw rows, not a DataFrame view: indexing by column list breaks
    # the moment a key field postdates some of the file.
    prior = []
    if os.path.exists(path):
        prior = migrate([json.loads(l) for l in open(path, encoding="utf-8") if l.strip()])
    have = {tuple(str(r.get(k)) for k in KEY) for r in prior}
    rows = [r for r in rows if tuple(str(r.get(k)) for k in KEY) not in have]
    n = append(rows, path)
    _rewrite(path)                      # collapse any duplicates a merge left
    if verbose:
        from collections import Counter
        per = Counter(r["venue"] for r in rows)
        b = Counter(r["venue"] for r in rows if r["bet"])
        print(f"captured {n} fighter-prices for {meta.get('event')}")
        for v in per:
            print(f"  {v:<12} {per[v]:>3} prices, {b.get(v,0)} trigger the rule")
    return n


def event_date_et(commence):
    """UFCStats dates a card by its local evening; The Odds API gives UTC.
    A Saturday-night card commences around 02:00 UTC Sunday, so the raw UTC
    date is a day late and would never line up with the corpus. Eastern time
    matches the corpus for nearly every card."""
    ts = pd.to_datetime(commence, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.tz_convert("America/New_York").date().isoformat()


# ---- prop markets (Polymarket only; no sportsbook feed quotes these) --------
#
# Kept in their own shards and their own claim space. A prop is a different
# claim from a winner price, graded by a different rule, and mixing them into
# the moneyline ledger would corrupt both the residual test and the
# opening-line test, whose populations are registered as moneyline bouts.
PROP_MODEL_FIELD = {"decision": "m_decision", "inside_distance": "p_finish",
                    "ko_a": "m_a_ko", "ko_b": "m_b_ko",
                    "sub_a": "m_a_sub", "sub_b": "m_b_sub"}


def prop_month_file(when=None, directory=LEDGER_DIR):
    ts = pd.Timestamp(when) if when is not None else pd.Timestamp.now(tz="UTC")
    return os.path.join(directory, f"props-{ts.year:04d}-{ts.month:02d}.jsonl")


def prop_files(directory=LEDGER_DIR):
    import glob
    return sorted(glob.glob(os.path.join(directory, "props-*.jsonl")))


def _model_prob(bout_payload, market):
    if market.startswith("end_r"):
        return bout_payload.get("p_end_r" + market[-1])
    f = PROP_MODEL_FIELD.get(market)
    return bout_payload.get(f) if f else None


def capture_props(card_path="data/upcoming.txt", payload_path="site/predictions.json",
                  verbose=True):
    """Log every prop Polymarket quotes for this card, beside the model's number.

    This is what addendum 9's distance rule has been waiting for: no sportsbook
    feed we can reach quotes method or round markets, and Polymarket may.
    Whether it does is answered by running this, not by arguing about it.
    """
    from .polymarket import fetch_events, parse_events, map_props, unmatched
    from .upcoming import parse_card
    meta, bouts = parse_card(card_path)
    ev_date = pd.to_datetime(meta.get("date"), errors="coerce")
    if pd.isna(ev_date) or pd.Timestamp.now(tz="UTC").normalize() > \
            ev_date.tz_localize("UTC") + pd.Timedelta(days=1):
        if verbose:
            print("props: card already happened, nothing logged")
        return 0
    try:
        payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    except Exception:
        payload = {"bouts": []}
    model = {b["bout"]: b for b in payload.get("bouts", [])}
    try:
        _rows = parse_events(fetch_events())
        found = map_props(_rows, bouts)
        extra = unmatched(_rows, bouts)
    except Exception as e:
        if verbose:
            print(f"props: polymarket unavailable ({e})")
        return 0
    ts = _now()
    rows = []
    for x in found:
        mb = model.get(x["bout"])
        pm_model = _model_prob(mb, x["market"]) if mb else None
        rows.append(dict(captured_utc=ts, venue="polymarket", event=meta.get("event"),
                         event_date=meta.get("date"), bout=x["bout"], a=x["a"], b=x["b"],
                         market=x["market"], p_market=x["p_market"],
                         p_model=pm_model,
                         edge=(round(pm_model - x["p_market"], 5) if pm_model is not None else None),
                         spread=x["meta"].get("spread"), depth_usd=x["meta"].get("depth_usd"),
                         slug=x["meta"].get("slug"),
                         question=x["meta"].get("question"), settled=False))
    # markets on the board that the model does not price: recorded so the site
    # can link them, never scored
    for x in extra:
        rows.append(dict(captured_utc=ts, venue="polymarket", event=meta.get("event"),
                         event_date=meta.get("date"), bout=None, a=None, b=None,
                         market=None, p_market=None, p_model=None, edge=None,
                         slug=x["slug"], question=x["question"], kind=x["kind"],
                         settled=False))
    if rows:
        f = prop_month_file()
        Path(f).parent.mkdir(parents=True, exist_ok=True)
        key = lambda r: (r.get("captured_utc"), r.get("bout"), r.get("market"), r.get("question"))
        have = set()
        for fp in prop_files():
            for line in open(fp, encoding="utf-8"):
                if line.strip():
                    have.add(key(json.loads(line)))
        rows = [r for r in rows if key(r) not in have]
        with open(f, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    if verbose:
        got = sorted({x["market"] for x in found})
        print(f"props: {len(found)} quoted by polymarket ({', '.join(got) if got else 'none'}), "
              f"{len(rows)} new rows")
    return len(rows)


def settle_props(fights, verbose=True):
    """Grade logged props with the same outcome rules the scorecard uses."""
    from .scorecard import _outcome
    from .upcoming import _key
    parts = fights.bout.str.split(" vs. ", n=1, expand=True)
    idx = {}
    for i, (r_, b_) in enumerate(zip(parts[0], parts[1])):
        idx.setdefault(frozenset((_key(r_), _key(b_))), []).append(i)
    n = 0
    for fp in prop_files():
        rows = [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
        out = []
        for r in rows:
            r = dict(r)
            ev = pd.to_datetime(r.get("event_date"), errors="coerce")
            best = None
            for i in idx.get(frozenset((_key(r["a"]), _key(r["b"]))), []):
                row = fights.iloc[i]
                gap = abs((pd.Timestamp(row.date) - ev).days) if pd.notna(ev) else 99
                if gap <= 4 and (best is None or gap < best[0]):
                    best = (gap, row)
            if best and best[1].winner in ("r", "b"):
                red = _key(best[1].bout.split(" vs. ")[0])
                hit = _outcome(r["market"], best[1], _key(r["a"]) == red)
                if hit is not None:
                    r["settled"], r["hit"] = True, bool(hit)
                    n += 1
            out.append(r)
        Path(fp).write_text("\n".join(json.dumps(x, sort_keys=True) for x in out) + "\n",
                            encoding="utf-8")
    if verbose:
        print(f"props: settled {n} rows")
    return n


def report_props():
    """Per market: how the model scored against the price, once settled."""
    rows = []
    for fp in prop_files():
        rows += [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
    if not rows:
        return {"status": "no prop prices captured yet"}
    D = pd.DataFrame(rows)
    D = D.sort_values("captured_utc").groupby(["event_date", "bout", "market"], as_index=False).last()
    out = {"captured": int(len(D)), "markets": {}}
    S = D[(D.get("settled") == True) & D.p_model.notna()]  # noqa: E712
    for mk, g in S.groupby("market"):
        y = g.hit.astype(float).values
        out["markets"][mk] = {
            "n": int(len(g)),
            "model_brier": round(float(np.mean((g.p_model.values - y) ** 2)), 4),
            "market_brier": round(float(np.mean((g.p_market.values - y) ** 2)), 4)}
    return out


def latest_prop_prices(event_date=None):
    """The most recent price per bout and market, for the site to display."""
    rows = []
    for fp in prop_files():
        rows += [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
    out = {}
    for r in sorted(rows, key=lambda x: x.get("captured_utc", "")):
        if event_date and r.get("event_date") != event_date:
            continue
        if not r.get("bout") or not r.get("market"):
            continue
        out.setdefault(r["bout"], {})[r["market"]] = {"p": r["p_market"], "slug": r.get("slug")}
    return out


def unpriced_markets(event_date=None, limit=12):
    """Polymarket UFC markets with no model projection — for listing, not scoring."""
    rows = []
    for fp in prop_files():
        rows += [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
    seen, out = set(), []
    for r in sorted(rows, key=lambda x: x.get("captured_utc", ""), reverse=True):
        if r.get("market") or not r.get("question"):
            continue
        if event_date and r.get("event_date") != event_date:
            continue
        if r["question"] in seen:
            continue
        seen.add(r["question"])
        out.append({"question": r["question"], "slug": r.get("slug"), "kind": r.get("kind")})
    return out[:limit]


def gate(verbose=True, throttle_min=60, near_hours=48, baseline_hours=20):
    """Decide, for free, whether a paid odds call is worth its 3 credits.

    The free events endpoint says what is on the board without costing
    anything, so the paid call is only made when it can add information:

      a NEW bout has appeared      -> its opening price, the thing addendum 13
                                      needs and the easiest to miss
      a bout starts within 48h     -> fight week, where lines actually move
                                      and the closing price is set
      nothing paid in ~a day       -> one baseline point, so a slow mid-week
                                      drift is still recorded eventually

    Anything else is a capture of prices that have not moved, which costs 3
    credits and records nothing new. And a throttle: a second paid call within
    an hour of the first is refused outright, because that is exactly what
    manual testing from the Actions tab was burning.

    Both ends of the line — open and close — are always captured. What is
    given up is resolution in the middle of a quiet week.
    """
    from .odds_live import list_events, read_usage
    u = read_usage()
    now = pd.Timestamp.now(tz="UTC")
    last = pd.to_datetime(u.get("last_paid_utc"), utc=True, errors="coerce")
    since = (now - last).total_seconds() / 3600 if pd.notna(last) else 1e9

    if since * 60 < throttle_min:
        return False, (f"throttled: last paid call {since * 60:.0f} min ago "
                       f"(minimum {throttle_min})")
    try:
        board = list_events()
    except Exception as e:
        return True, f"free event list unavailable ({e}); paying to be safe"
    if not board:
        return False, "no MMA events listed"

    seen = {frozenset((str(r.get("fighter", "")).lower(), str(r.get("opponent", "")).lower()))
            for r in _raw()}
    from .odds_live import _nm
    seen = {frozenset(_nm(x) for x in pair) for pair in seen}
    new = [e for e in board if frozenset((e["k1"], e["k2"])) not in seen]
    starts = [pd.to_datetime(e["commence"], utc=True, errors="coerce") for e in board]
    near = [t for t in starts if pd.notna(t) and now < t <= now + pd.Timedelta(hours=near_hours)]

    if new:
        return True, f"{len(new)} bout(s) not seen before - capturing opening prices"
    if near:
        return True, f"{len(near)} bout(s) start within {near_hours}h - fight week"
    if since >= baseline_hours:
        return True, f"baseline: {since:.0f}h since last paid call"
    return False, (f"skipped: nothing new, nothing within {near_hours}h, "
                   f"last paid {since:.1f}h ago - would record unchanged prices")


def sweep(fights, fighters, path=None, verbose=True):
    """Log EVERY listed bout the model can price, at no extra API cost.

    The point is the opening price. A bout's first appearance in the feed is
    the closest thing to its true open, and the old capture only logged the
    card in data/upcoming.txt — which advances once a day and often lags the
    feed by a week or more. So a card was first captured days after its line
    opened, after the softest price had already been bid away, systematically
    understating the effect addendum 13 is trying to measure.

    Each bout is guarded by its OWN start time, not the card's: a bout that
    has already begun is never priced, which also closes off the resolved-
    market failure at the root rather than filtering it afterwards.
    """
    from .odds_live import fetch_events
    from .upcoming import resolve, _states_after
    from .features import elo_eff, make_features

    rule = load_rule()
    try:
        events = fetch_events()
    except Exception as e:
        if verbose:
            print(f"sweep: odds unavailable ({e})")
        return 0
    if not events:
        if verbose:
            print("sweep: no events (set ODDS_API_KEY)")
        return 0

    now = pd.Timestamp.now(tz="UTC")
    upcoming = [e for e in events
                if pd.to_datetime(e["commence"], utc=True, errors="coerce") > now]
    names = sorted({n for e in upcoming for n in (e["name1"], e["name2"])})
    ids, _ = resolve(names, fighters)
    states = _states_after(fights, fighters)

    prior = {tuple(str(r.get(k)) for k in ("venue", "event_date", "fighter", "opponent"))
             for r in migrate(_raw(path))}
    rows, ts, new_bouts, skipped = [], _now(), 0, 0
    for e in upcoming:
        na, nb = e["name1"], e["name2"]
        if na not in ids or nb not in ids:
            skipped += 1                 # not a UFC fighter we have history for
            continue
        A, B = states[ids[na]], states[ids[nb]]
        if min(A.n_fights, B.n_fights) < 2:
            skipped += 1
            continue
        ed = event_date_et(e["commence"])
        as_of = pd.Timestamp(ed)
        sa, sb = A.snapshot(as_of), B.snapshot(as_of)
        sa["elo"], sb["elo"] = elo_eff(A, as_of), elo_eff(B, as_of)
        fv = make_features(sa, sb)
        p_a = e["p1"] if _nm_key(na) == e["k1"] else 1 - e["p1"]
        first_seen = ("sportsbook", ed, na, nb) not in prior
        new_bouts += first_seen
        for side, name, opp, pm in (("a", na, nb, p_a), ("b", nb, na, 1 - p_a)):
            f = fv if side == "a" else {k: -v for k, v in fv.items()}
            p_model = rule_probability(f, pm, rule)
            implied = pm * (1 + 0.037 / 2)
            rows.append(dict(
                captured_utc=ts, venue="sportsbook", event=None, event_date=ed,
                fighter=name, opponent=opp, side=side,
                p_market_devig=round(pm, 5), implied_with_vig=round(implied, 5),
                p_model=round(p_model, 5), edge=round(p_model - implied, 5),
                books=e["books"], spread=None, depth_usd=None,
                bet=bool(fires(p_model, implied, rule)),
                opening=bool(first_seen),
                rule_frozen_on=rule.get("frozen_on"), settled=False))
    n = append(rows, path)
    if verbose:
        print(f"sweep: {len(upcoming)} upcoming bouts in feed, {n // 2} priced, "
              f"{new_bouts} seen for the first time (opening prices), "
              f"{skipped} skipped (no UFC history)")
    return n


def _nm_key(s):
    from .odds_live import _nm
    return _nm(s)


def settle(fights, path=None, date_tol_days=4, verbose=True):
    """Attach outcomes to finished bouts.

    Matching is on the name pair AND the event date, within a few days. Name
    pair alone is wrong: 424 fights in the corpus are rematches, and on the
    first live capture this settled a Van vs Pantoja rematch using their
    2025-12-06 first meeting — marking tonight's fight decided, hours before
    it happened. Silently resolving a prediction with a different fight's
    result is the worst failure this ledger could have.

    Settlement is RE-DERIVED from the corpus on every run rather than skipped
    once set, so a bad settle heals itself on the next pass. The captured
    prediction fields are never touched; only the outcome fields are.
    """
    from .upcoming import _key
    files = [path] if path else ledger_files()
    if not any(f and os.path.exists(f) for f in files):
        if verbose:
            print("ledger is empty")
        return 0

    parts = fights.bout.str.split(" vs. ", n=1, expand=True)
    by_pair = {}
    for r_, b_, w, dt in zip(parts[0], parts[1], fights.winner, fights.date):
        by_pair.setdefault(frozenset((_key(r_), _key(b_))), []).append((dt, _key(r_), w))

    n, fixed = 0, 0
    for f in files:
        if not f or not os.path.exists(f):
            continue
        out = []
        for d in migrate([json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]):
            was = bool(d.get("settled"))
            d.pop("won", None)
            d.pop("void", None)
            d["settled"] = False
            cands = by_pair.get(frozenset((_key(d["fighter"]), _key(d["opponent"]))), [])
            ev = pd.to_datetime(d.get("event_date"), errors="coerce")
            best = None
            for dt, red, w in cands:
                if pd.isna(ev):
                    continue
                gap = abs((pd.Timestamp(dt) - ev).days)
                if gap <= date_tol_days and (best is None or gap < best[0]):
                    best = (gap, red, w)
            if best is not None:
                _, red, winner = best
                if winner not in ("r", "b"):
                    d["settled"], d["void"] = True, True
                else:
                    d["settled"] = True
                    d["won"] = bool((winner == "r") == (_key(d["fighter"]) == red))
                n += 1
            if was and not d["settled"]:
                fixed += 1
            out.append(d)

        out = dedupe(out)
        new = "\n".join(json.dumps(r, sort_keys=True) for r in out) + "\n"
        if new != Path(f).read_text(encoding="utf-8"):
            Path(f).write_text(new, encoding="utf-8")   # untouched shards stay untouched
    if verbose:
        print(f"settled {n} rows" + (f"; un-settled {fixed} wrongly matched" if fixed else ""))
    return n


def report(path=LEDGER, vig=0.037, venue=None):
    """Where the forward test stands. CLV first — it converges long before ROI."""
    L = read(path)
    if L.empty:
        return {"status": "ledger empty"}
    # one row per fighter-price: the LAST capture before the fight is the close
    if venue:
        L = L[L.venue == venue]
        if L.empty:
            return {"status": f"no rows for venue {venue}"}
    L = L.sort_values("captured_utc")
    gk = ["venue", "event_date", "fighter", "opponent"]
    close = L.groupby(gk, as_index=False).last()
    first = L.groupby(gk, as_index=False).first()
    move = close.p_market_devig.values - first.p_market_devig.values

    # CLV is only defined for the side you BACKED. Averaged over both corners
    # it is identically zero: every point the favourite gains, the underdog
    # loses. The first version did exactly that and reported -0.0 on a card
    # where the lines had genuinely moved almost two points.
    betmask = close.bet.fillna(False).values.astype(bool)
    clv = move[betmask]

    bets = close[(close.bet == True) & (close.get("settled") == True)]  # noqa: E712
    out = {
        "venue": venue or "all",
        "captured_prices": int(len(close)),
        "bets_triggered": int((close.bet == True).sum()),  # noqa: E712
        "bets_settled": int(len(bets)),
        "bets_needed": max(0, 300 - int(len(bets))),
        # movement on the backed side only; positive means the market came to us
        "clv_bets_n": int(betmask.sum()),
        "clv_mean_pp": round(float(np.nanmean(clv) * 100), 3) if len(clv) else None,
        "clv_positive_share": (round(float(np.mean(clv > 0)), 3) if len(clv) else None),
        # sanity: across both corners this must be ~0, and if it is not the
        # two sides of a fight are not being paired correctly
        "all_sides_move_pp": round(float(np.nanmean(move) * 100), 4),
    }
    if len(bets):
        won = bets.get("won")
        dec = 1.0 / bets.implied_with_vig
        pnl = np.where(won.fillna(False), dec - 1.0, -1.0)
        out["win_rate"] = round(float(won.fillna(False).mean()), 4)
        out["roi_pct"] = round(float(pnl.mean() * 100), 3)
        out["roi_se_pct"] = round(float(pnl.std(ddof=1) / np.sqrt(len(pnl)) * 100), 3)
        out["verdict"] = ("too early — need 300 settled bets"
                          if len(bets) < 300 else
                          ("rule SUPPORTED" if out["roi_pct"] > 2.0 else "rule REJECTED"))
    return out


if __name__ == "__main__":
    import sys
    from .loaders import load
    f, p, _ = load(verbose=False)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "capture":
        go, why = gate()
        print(f"gate: {'PAY' if go else 'SKIP'} - {why}")
        if go:
            # The sweep logs every listed bout, including the current card.
            sweep(f, p)
        # Polymarket is free and keyed to the card, so it runs regardless.
        capture(f, p, venues_only=("polymarket",))
        capture_props()
        from .odds_live import read_usage
        u = read_usage()
        if u.get("remaining") is not None:
            print(f"odds api: {u['remaining']} credits remaining this month "
                  f"({u['used']} used)")
    elif cmd == "settle":
        prune_resolved()
        settle(f)
        settle_props(f)
    elif cmd == "prune":
        prune_resolved()
    for v in (None, "sportsbook", "polymarket"):
        r = report(venue=v)
        if r.get("status"):
            continue
        print(json.dumps(r, indent=1))
