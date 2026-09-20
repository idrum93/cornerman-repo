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

LEDGER = "data/ledger/odds_log.jsonl"
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


def append(rows, path=LEDGER):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return len(rows)


KEY = ["captured_utc", "event_date", "fighter", "opponent"]


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
        seen[tuple(str(r.get(k)) for k in KEY)] = r
    return list(seen.values())


def read(path=LEDGER):
    if not os.path.exists(path):
        return pd.DataFrame()
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    return pd.DataFrame(dedupe(rows))


def _rewrite(path=LEDGER):
    """Rewrite the file deduplicated, preserving order of first appearance."""
    if not os.path.exists(path):
        return 0
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    clean = dedupe(rows)
    Path(path).write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in clean) + "\n",
        encoding="utf-8")
    return len(rows) - len(clean)


def capture(fights, fighters, card_path="data/upcoming.txt", path=LEDGER,
            verbose=True):
    """Log every priced bout on the upcoming card, at this moment."""
    from .odds_live import fetch_moneylines
    from .upcoming import parse_card, resolve, _states_after, _key
    from .features import elo_eff, make_features

    rule = load_rule()
    book = fetch_moneylines()
    if not book:
        if verbose:
            print("no live odds (set ODDS_API_KEY) - nothing captured")
        return 0

    meta, bouts = parse_card(card_path)
    states = _states_after(fights, fighters)
    names = sorted({n for b in bouts for n in b[:2]})
    ids, _ = resolve(names, fighters)
    as_of = pd.Timestamp(meta.get("date") or fights.date.max())

    rows, ts = [], _now()
    for na, nb, n_rounds, _segment in bouts:
        hit = book.get(frozenset((_key(na), _key(nb))))
        if hit is None or na not in ids or nb not in ids:
            continue
        A, B = states[ids[na]], states[ids[nb]]
        if min(A.n_fights, B.n_fights) < 2:
            continue
        sa, sb = A.snapshot(as_of), B.snapshot(as_of)
        sa["elo"], sb["elo"] = elo_eff(A, as_of), elo_eff(B, as_of)
        fv = make_features(sa, sb)

        src, p_mkt_devig, nbooks = hit
        p_mkt = p_mkt_devig if src == _key(na) else 1 - p_mkt_devig
        # price actually payable: add back half the typical two-way margin
        vig = 0.037
        for side, name, opp, pm in (("a", na, nb, p_mkt), ("b", nb, na, 1 - p_mkt)):
            f = fv if side == "a" else {k: -v for k, v in fv.items()}
            p_model = rule_probability(f, pm, rule)
            implied = pm * (1 + vig / 2)
            rows.append(dict(
                captured_utc=ts, event=meta.get("event"), event_date=meta.get("date"),
                fighter=name, opponent=opp, side=side,
                p_market_devig=round(pm, 5), implied_with_vig=round(implied, 5),
                p_model=round(p_model, 5), edge=round(p_model - implied, 5),
                books=nbooks, bet=bool(fires(p_model, implied, rule)),
                rule_frozen_on=rule.get("frozen_on"), settled=False))
    existing = read(path)
    if not existing.empty:
        have = {tuple(str(r[k]) for k in KEY) for _, r in existing[KEY].iterrows()}
        rows = [r for r in rows if tuple(str(r.get(k)) for k in KEY) not in have]
    n = append(rows, path)
    _rewrite(path)                      # collapse any duplicates a merge left
    if verbose:
        b = sum(1 for r in rows if r["bet"])
        print(f"captured {n} fighter-prices for {meta.get('event')}; "
              f"{b} trigger the pre-registered bet")
    return n


def settle(fights, path=LEDGER, date_tol_days=4, verbose=True):
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
    L = read(path)
    if L.empty:
        if verbose:
            print("ledger is empty")
        return 0

    parts = fights.bout.str.split(" vs. ", n=1, expand=True)
    by_pair = {}
    for r_, b_, w, dt in zip(parts[0], parts[1], fights.winner, fights.date):
        by_pair.setdefault(frozenset((_key(r_), _key(b_))), []).append((dt, _key(r_), w))

    out, n, fixed = [], 0, 0
    for _, row in L.iterrows():
        d = row.to_dict()
        was = bool(d.get("settled"))
        d["settled"], d.pop("won", None), d.pop("void", None)
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
    Path(path).write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in out) + "\n", encoding="utf-8")
    if verbose:
        print(f"settled {n} rows" + (f"; un-settled {fixed} wrongly matched" if fixed else ""))
    return n


def report(path=LEDGER, vig=0.037):
    """Where the forward test stands. CLV first — it converges long before ROI."""
    L = read(path)
    if L.empty:
        return {"status": "ledger empty"}
    # one row per fighter-price: the LAST capture before the fight is the close
    L = L.sort_values("captured_utc")
    close = L.groupby(["event_date", "fighter", "opponent"], as_index=False).last()
    first = L.groupby(["event_date", "fighter", "opponent"], as_index=False).first()
    clv = (close.p_market_devig.values - first.p_market_devig.values)

    bets = close[(close.bet == True) & (close.get("settled") == True)]  # noqa: E712
    out = {
        "captured_prices": int(len(close)),
        "bets_triggered": int((close.bet == True).sum()),  # noqa: E712
        "bets_settled": int(len(bets)),
        "bets_needed": max(0, 300 - int(len(bets))),
        "clv_mean_pp": round(float(np.nanmean(clv) * 100), 3) if len(clv) else None,
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
        capture(f, p)
    elif cmd == "settle":
        settle(f)
    print(json.dumps(report(), indent=1))
