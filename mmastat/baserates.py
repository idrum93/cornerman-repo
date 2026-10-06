"""Conditional base rates: what happened in past fights that looked like this.

Not a model. Counts. For each registered condition the corpus is split into
quartiles and the outcome rate is reported with n and a 95% interval.

The condition list is FIXED in PREREGISTRATION.md addendum 10 and every entry
is rendered every time, including the ones that come out flat. The risk this
guards against is not false discovery, it is selective display: with a dozen
candidate conditions, showing whichever looks strongest turns a lookup table
into a machine for rendering noise attractively. C5 (combined control share
against inside-the-distance) measured flat and stays in the panel for exactly
that reason — a display that only ever shows strong relationships is
indistinguishable from one that selects them.

Two granularities, because the outcomes live at different levels:
  fighter  one row per fighter per fight  (did HE land a takedown)
  fight    one row per fight              (did IT end inside the distance)
"""
import numpy as np
import pandas as pd

from .features import build_panel

MIN_CELL = 200          # quartiles thinner than this are grayed, never dropped

# (id, label, level, condition column, outcome column, why it is here)
CONDITIONS = [
    ("C1", "Own takedown rate", "fighter", "own_adj_td15", "y_td",
     "the rate is the propensity"),
    ("C2", "Opponent's takedown defense", "fighter", "opp_td_def", "y_td",
     "the thing standing in the way"),
    ("C3", "Own knockdown rate", "fighter", "own_kd15", "y_kd",
     "direct"),
    ("C4", "Combined knockdown rate", "fight", "kd_sum", "itd",
     "two heavy hitters end fights"),
    ("C5", "Combined control share", "fight", "ctrl_sum", "itd",
     "grappling-heavy fights grind out"),
    ("C6", "Reach advantage", "fighter", "reach_diff", "y_td",
     "shooting under a longer fighter"),
    ("C7", "Combined strike volume", "fight", "slpm_sum", "itd",
     "pace as a proxy for damage"),
    ("C8", "Age gap", "fight", "age_gap", "itd",
     "the older fighter as the one who breaks"),
    ("C9", "Combined submission-attempt rate", "fight", "sub_sum", "dec",
     "grapplers hunting finishes"),
    ("C10", "Own clinch + ground share", "fighter", "pos_share", "y_td",
     "position-dependent offense needs the takedown first"),
    # addendum 14: the knockdown question had only one side
    ("C11", "Opponent's knockdowns absorbed", "fighter", "opp_kd_against15", "y_kd",
     "a chin that has gone before goes again"),
    ("C12", "Opponent's strikes absorbed", "fighter", "opp_sapm", "y_kd",
     "a hittable opponent gets hit cleanly more often"),
    # addendum 35. Same-measure by construction, like C1: the share of a
    # fighter's wins that went to decision, against whether THIS fight goes to
    # decision. Context, not a discovery — and not a model feature either
    # (addendum 33: worth nothing on top of average fight time).
    ("C13", "Combined share of bouts going the distance", "fight", "dec_share_sum", "itd",
     "two fighters whose fights go long produce another one"),
]

OUTCOME_LABEL = {"y_td": "lands a takedown", "y_kd": "scores a knockdown",
                 "itd": "ends inside the distance", "dec": "goes the distance"}


def _frames(fights, fighters, min_date="2012-01-01"):
    P = build_panel(fights, fighters)
    P = P[P.date >= pd.Timestamp(min_date)].copy()
    P["y_td"] = (P.y_td15 > 0).astype(int)
    P["y_kd"] = (P.y_kd15 > 0).astype(int)
    P["reach_diff"] = P.own_reach - P.opp_reach
    P["pos_share"] = P.own_clinch_share + P.own_ground_share

    P["side"] = P.groupby("fight_id").cumcount()
    w = P.pivot_table(index="fight_id", columns="side",
                      values=["own_kd15", "own_ctrl_share", "own_adj_slpm",
                              "own_sub15", "own_age"])
    w.columns = [f"{a}{b}" for a, b in w.columns]
    F = fights.set_index("fight_id")
    F = F[F.date >= pd.Timestamp(min_date)].join(w, how="inner")
    F["itd"] = (F.method != "DEC").astype(int)
    F["dec"] = (F.method == "DEC").astype(int)
    F["kd_sum"] = F.own_kd150 + F.own_kd151
    F["ctrl_sum"] = F.own_ctrl_share0 + F.own_ctrl_share1
    F["slpm_sum"] = F.own_adj_slpm0 + F.own_adj_slpm1
    F["sub_sum"] = F.own_sub150 + F.own_sub151
    F["age_gap"] = (F.own_age0 - F.own_age1).abs()

    # addendum 35 (C13). Built from prior bouts only, walking in date order,
    # so the row is leakage-safe the same way every model feature is. Needs two
    # wins on record per corner before a share means anything.
    hist, pair = {}, {}
    for r in fights.sort_values("date").itertuples():
        ha, hb = hist.get(r.r_id), hist.get(r.b_id)
        if ha and hb and ha["w"] >= 3 and hb["w"] >= 3:
            pair[r.fight_id] = (ha["dec"] / ha["w"] + hb["dec"] / hb["w"]) / 2
        for side, fid in (("r", r.r_id), ("b", r.b_id)):
            # Every bout, not only the wins. Measured 2026-09-26: the
            # participation version separates finishes better (AUC .647 against
            # .623, a 35-point quartile spread against 27), because a fighter
            # who gets finished contributes to short fights without ever
            # finishing one. Adding the wins-only version on top is worth
            # nothing (.6605 against .6599).
            h = hist.setdefault(fid, {"w": 0, "dec": 0})
            h["w"] += 1
            h["dec"] += int(r.method == "DEC")
    F["dec_share_sum"] = pd.Series(pair)
    return P, F


def build_table(fights, fighters, min_date="2012-01-01", n_q=4):
    """Every registered condition, every quartile, always."""
    P, F = _frames(fights, fighters, min_date)
    out = []
    for cid, label, level, col, outcome, why in CONDITIONS:
        d = P if level == "fighter" else F
        if col not in d.columns or outcome not in d.columns:
            continue
        s = d[col].astype(float)
        try:
            q = pd.qcut(s, n_q, duplicates="drop", labels=False)
        except ValueError:
            continue
        base = float(d[outcome].mean())
        edges = [float(x) for x in np.nanquantile(s, np.linspace(0, 1, n_q + 1))]
        cells = []
        for i in range(int(np.nanmax(q)) + 1):
            m = q == i
            n = int(m.sum())
            if n == 0:
                continue
            r = float(d.loc[m, outcome].mean())
            se = float(np.sqrt(max(r * (1 - r), 1e-9) / n))
            cells.append({"q": i + 1, "n": n, "rate": round(r, 4),
                          "lift": round(r - base, 4), "ci": round(1.96 * se, 4),
                          "thin": n < MIN_CELL,
                          "lo": round(edges[i], 3), "hi": round(edges[i + 1], 3)})
        spread = max(c["rate"] for c in cells) - min(c["rate"] for c in cells)
        out.append({"id": cid, "label": label, "level": level,
                    "outcome": outcome, "outcome_label": OUTCOME_LABEL[outcome],
                    "why": why, "base": round(base, 4), "n": int(len(d)),
                    "spread": round(spread, 4), "edges": edges, "cells": cells})
    return out


def band_for(value, table_entry):
    """Which quartile a given fight or fighter falls in, 1-indexed."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    e = table_entry["edges"]
    for i in range(len(e) - 1):
        if value <= e[i + 1] or i == len(e) - 2:
            return i + 1
    return None


DIVISION_ORDER = ["Flyweight", "Bantamweight", "Featherweight", "Lightweight",
                  "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight",
                  "Women's Strawweight", "Women's Flyweight", "Women's Bantamweight"]


def divisions(fights, min_date="2012-01-01"):
    """What happens in each division (PREREGISTRATION addendum 16, test 1).
    Descriptive counts: finishes and knockdowns rise with weight, takedowns
    fall, and pace barely moves at all."""
    import re
    F = fights[(fights.date >= pd.Timestamp(min_date))
               & fights.method.isin(["KO/TKO", "SUB", "DEC"])].copy()
    def name(wc):
        s = re.sub(r"\b(UFC|Interim|Title|Bout|Tournament|Championship)\b", "", str(wc), flags=re.I)
        s = re.sub(r"\s+", " ", s).strip()
        return s if s in DIVISION_ORDER else None
    F["div"] = F.weight_class.map(name)
    F = F[F["div"].notna()]
    mins = (F.total_sec / 60).replace(0, np.nan)
    out = []
    for d in DIVISION_ORDER:
        G = F[F["div"] == d]
        if len(G) < 50:
            continue
        # Only quantities a book actually sells. "Any knockdown" and "any
        # takedown" are nobody's contract, and strikes per minute is a rate no
        # market quotes — the market sells a fighter's TOTAL, so that is what
        # this reports.
        out.append({"division": d, "n": int(len(G)),
                    "distance": round(float((G.method == "DEC").mean()), 3),
                    "ko": round(float((G.method == "KO/TKO").mean()), 3),
                    "sub": round(float((G.method == "SUB").mean()), 3),
                    "strikes": round(float(((G.r_ss_landed + G.b_ss_landed) / 2).median()), 1),
                    "takedowns": round(float(((G.r_td_landed + G.b_td_landed) / 2).mean()), 2),
                    "finish": round(float((G.method != "DEC").mean()), 3)})
    return out


def market_bases(fights, min_date="2012-01-01"):
    """How often each market comes in, across all fights. The site ranks which
    props to surface by how far a projection sits from these — a prop is worth
    showing because it is unusual, not because the number is large. "Over 1.5
    rounds" is near-certain in every fight; saying so on every tile is noise."""
    F = fights[(fights.date >= pd.Timestamp(min_date))
               & fights.method.isin(["KO/TKO", "SUB", "DEC"])]
    out = {"td": float(np.r_[(F.r_td_landed > 0).values, (F.b_td_landed > 0).values].mean()),
           "kd": float(np.r_[(F.r_kd > 0).values, (F.b_kd > 0).values].mean()),
           "itd": float((F.method != "DEC").mean()),
           "dec": float((F.method == "DEC").mean()), "totals": {}, "ends_before": {}}
    for sched, nr in ((900, 3), (1500, 5)):
        G = F[F.sched_sec == sched]
        if len(G) < 100:
            continue
        out["totals"][str(nr)] = {f"{line:g}": float((G.total_sec > line * 300).mean())
                                  for line in (1.5, 2.5, 3.5, 4.5) if line < nr}
        # The cumulative round contract the exchange actually quotes: a finish
        # before round n begins, i.e. inside the first n-1 rounds.
        fin = G[G.method != "DEC"]
        out["ends_before"][str(nr)] = {
            str(n): float((fin.total_sec <= (n - 1) * 300).sum() / len(G))
            for n in range(2, nr + 1)}
    return {k: (round(v, 4) if isinstance(v, float) else
                {a: {b: round(c, 4) for b, c in d.items()} for a, d in v.items()})
            for k, v in out.items()}


def decision_curve(fights, min_date="2012-01-01", min_wins=2):
    """Average the pair's career decision share; how often does the fight finish?

    This is the empirical ground under the UFC.com check's length read. The
    check has no model behind it - it averages two career method splits and
    calls the fight long or short - and this curve is the evidence that doing
    so means anything: finish rate falls monotonically from about 70% when both
    fighters finish nearly everything to about 33% when both go to the cards.

    RAW shares, deliberately, not the shrunk `finish_rate` the win model uses.
    Shrinkage pulls every fighter toward the league mean, which is right for a
    model input and wrong for this table: it compresses the whole corpus into
    the middle two buckets and hides the relationship the reader is being shown.
    The check's own read IS shrunk; this curve is the unshrunk picture of why
    the underlying quantity is informative at all.

    Verified against an independently produced version of the same table: all
    six buckets agreed within 1.6 points on 3,325 bouts, r = -0.208.
    """
    F = fights.sort_values(["date", "fight_id"]).copy()
    F["date"] = pd.to_datetime(F.date)
    cut = pd.Timestamp(min_date)
    wins, rows = {}, []
    for r in F.itertuples():
        if r.winner not in ("r", "b"):
            continue
        a, b = r.r_id, r.b_id
        wa, wb = wins.get(a, [0, 0]), wins.get(b, [0, 0])
        if r.date >= cut and wa[0] >= min_wins and wb[0] >= min_wins:
            rows.append(((wa[1] / wa[0] + wb[1] / wb[0]) / 2.0,
                         r.method in ("KO/TKO", "SUB")))
        w = a if r.winner == "r" else b
        c = wins.get(w, [0, 0])
        wins[w] = [c[0] + 1, c[1] + (1 if r.method == "DEC" else 0)]
        for x in (a, b):
            wins.setdefault(x, [0, 0])
    if not rows:
        return None
    d = pd.DataFrame(rows, columns=["avg_dec", "finished"])
    edges = [0, .15, .30, .45, .60, .75, 1.01]
    out = []
    for lo, hi in zip(edges, edges[1:]):
        m = d[(d.avg_dec >= lo) & (d.avg_dec < hi)]
        # A lower floor than MIN_CELL on purpose. MIN_CELL guards the quartile
        # CONDITIONS, where a thin cell can invent a pattern; this is a single
        # rate per bucket, and at n=150 its standard error is under 4 points.
        # The strictest bucket - both fighters finish nearly everything - is the
        # most informative row in the table and the smallest, and dropping it
        # removes the end of the curve that makes the shape legible.
        if len(m) < 150:
            continue
        out.append({"lo": lo, "hi": min(hi, 1.0), "n": int(len(m)),
                    "finish": round(float(m.finished.mean()), 4)})
    return {"buckets": out, "n": int(len(d)),
            "r": round(float(d.avg_dec.corr(d.finished.astype(float))), 4)}


def card_shape(fights, min_date="2012-01-01"):
    """What a whole card usually looks like: its size, and how much of it ends
    early. One row per EVENT, not per fight.

    This is the only readout on the site whose unit is the card rather than the
    bout, which is the point of it. "Round one ends a quarter of all fights" is
    a rate nobody can feel. "Three of tonight's twelve, and almost never none"
    is a number a reader can hold against the card in front of them — and the
    model can be scored on it afterwards, because the projection is just the
    sum of the per-bout first-round probabilities it already publishes.

    Summing them is only legitimate because the count behaves binomially. The
    worry was clustering — a wild card where everyone swings — and if finishes
    did cluster, the real spread would be wider than a sum of independents
    implies and the readout would understate its own error. They do not: the
    per-card variance measured 1.05x what independent bouts give, which is
    nothing beyond chance. `overdispersion` carries that ratio so the
    assumption is re-checked on every build instead of resting on the one time
    somebody measured it.
    """
    F = fights[(fights.date >= pd.Timestamp(min_date))
               & fights.method.isin(["KO/TKO", "SUB", "DEC"])].copy()
    F["is_fin"] = F.method != "DEC"
    F["is_r1"] = F.is_fin & (F.total_sec <= 300)

    g = F.groupby("event").agg(bouts=("method", "size"), r1=("is_r1", "sum"),
                               fin=("is_fin", "sum"))
    # Under six bouts is a truncated record or a one-off show, not the kind of
    # card a reader is holding this up against.
    g = g[g.bouts >= 6]
    if not len(g):
        return None

    cap = 8                      # past here is ~0.4% of cards
    counts = g.r1.clip(upper=cap).value_counts().sort_index()
    dist = [{"k": int(k), "share": round(float(v) / len(g), 4),
             "plus": bool(k == cap)} for k, v in counts.items()]

    p = float(F.is_r1.mean())
    exp_var = float((g.bouts * p * (1 - p)).mean())

    split = {}
    for key, name in (("KO", "KO/TKO"), ("SUB", "SUB")):
        s = F[F.method == name]
        if len(s) < 200:
            continue
        # round index from elapsed time: a finish at 6:10 is round two
        rounds = np.minimum((s.total_sec // 300).astype(int) + 1, 5)
        split[key] = {"n": int(len(s)),
                      "by_round": [round(float((rounds == i).mean()), 4)
                                   for i in range(1, 6)]}

    return {
        "n_cards": int(len(g)), "min_date": min_date,
        "bouts_median": int(g.bouts.median()),
        "bouts_lo": int(g.bouts.quantile(0.25)),
        "bouts_hi": int(g.bouts.quantile(0.75)),
        "r1_mean": round(float(g.r1.mean()), 2), "r1_median": int(g.r1.median()),
        "r1_p10": int(np.percentile(g.r1, 10)),
        "r1_p90": int(np.percentile(g.r1, 90)),
        "r1_none": round(float((g.r1 == 0).mean()), 4),
        "r1_dist": dist,
        "fin_mean": round(float(g.fin.mean()), 2), "fin_median": int(g.fin.median()),
        "r1_share_of_bouts": round(p, 4),
        "overdispersion": round(float(g.r1.var() / exp_var), 2) if exp_var else None,
        "round_split": split,
    }


def write_json(fights, fighters, path="site/baserates.json", verbose=True):
    import json
    from pathlib import Path
    tbl = build_table(fights, fighters)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(
        {"built_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
         "min_cell": MIN_CELL, "conditions": tbl,
         "divisions": divisions(fights),
         "card": card_shape(fights),
         "decision_curve": decision_curve(fights),
         "market_bases": market_bases(fights)}, indent=1), encoding="utf-8")
    if verbose:
        flat = sum(1 for t in tbl if t["spread"] < 0.03)
        print(f"base rates: {len(tbl)} conditions written to {path} "
              f"({flat} flat, kept deliberately)")
    return tbl


if __name__ == "__main__":
    from .loaders import load
    f, p, _ = load(verbose=False)
    for t in write_json(f, p):
        cells = "  ".join(f"Q{c['q']} {c['rate']:.3f}" for c in t["cells"])
        print(f"  {t['id']:<4} {t['label']:<34} base {t['base']:.3f}  {cells}"
              f"   spread {t['spread']:+.3f}")
