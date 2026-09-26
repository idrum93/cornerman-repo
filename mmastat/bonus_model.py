"""Fight of the Night picks — PREREGISTRATION addendum 24.

Ranks the bouts on a card by how likely each is to win Fight of the Night, and
measures that against the three baselines fixed before any label was collected:

    B1  always pick the main event
    B2  always pick the bout with the highest chance of a finish
    B3  always pick the bout containing the fighter with the most prior bonuses

The pick goes on the site only if it beats all three on held-out cards. Random
is not the bar: main events win bonuses far above their share, for reasons that
have nothing to do with how good the fight is.

Per the amendment, the model is reported twice — with and without prior-bonus
counts — because a model that only clears the baselines once bonus history is
included has learned which fighters the UFC favours, not which fights are good.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .bonuses import OUT as BONUS_FILE, POTN_ERA
from .features import walk
from .projections import finish_row, FINISH_INPUTS
from .upcoming import _key

BASE_FEATURES = ["close", "pace_sum", "kd_sum", "sub_sum", "five", "p_finish",
                 "order", "card_n"]
BONUS_FEATURES = ["prior_bonus", "prior_bonus_rate"]


def _labels(path=BONUS_FILE):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for ev, v in d.get("events", {}).items():
        if v.get("status") == "ok":
            out[ev] = {"fotn": [_key(x) for x in v.get("fotn", [])],
                       "potn": [_key(x) for x in v.get("potn", [])],
                       "date": v.get("date")}
    return out


def features(fights, fighters, labels, min_date=POTN_ERA):
    """One row per bout, with pre-fight quantities only.

    Prior bonus counts are accumulated in card order through the walk, so a
    bout never sees the bonuses awarded on its own card or any later one.
    """
    f = fights.reset_index(drop=True).copy()
    f["ord"] = f.groupby("event").cumcount()
    f["card_n"] = f.event.map(f.event.value_counts())
    won, fought = {}, {}
    rows = []
    for fight, sa, sb, npri in walk(f, fighters):
        if min(npri) < 2 or fight.date < pd.Timestamp(min_date):
            continue
        ev = fight.event
        if ev not in labels:
            continue
        a, b = [x.strip() for x in str(fight.bout).split(" vs. ")[:2]]
        ka, kb = _key(a), _key(b)
        nr = 5 if fight.sched_sec >= 1500 else 3
        fr = finish_row(sa, sb, nr, fight.weight_class)
        pa = 1.0 / (1.0 + np.exp(-(sa["elo"] - sb["elo"]) / 173.0))   # a cheap, stable closeness read
        pri = won.get(ka, 0) + won.get(kb, 0)
        n_f = max(fought.get(ka, 0) + fought.get(kb, 0), 1)
        rows.append(dict(fight_id=fight.fight_id, event=ev, date=fight.date, a=a, b=b,
                         order=fight.ord, card_n=fight.card_n,
                         close=1 - 2 * abs(pa - 0.5),
                         itd=int(fight.method != "DEC"),
                         pace_sum=sa["adj_slpm"] + sb["adj_slpm"],
                         kd_sum=sa["kd15"] + sb["kd15"],
                         sub_sum=sa["sub15"] + sb["sub15"],
                         prior_bonus=pri, prior_bonus_rate=pri / n_f,
                         y=int(ka in labels[ev]["fotn"] or kb in labels[ev]["fotn"]),
                         potn_keys=tuple(labels[ev]["potn"]),
                         prior_a=won.get(ka, 0), prior_b=won.get(kb, 0),
                         # per-fighter finishing threat, for the POTN baseline:
                         # his own knockdown and submission rates, not half the
                         # fight-level finish probability, which was a placeholder
                         fin_a=sa["kd15"] + sa["sub15"], fin_b=sb["kd15"] + sb["sub15"],
                         **{k: v for k, v in fr.items()}))
        # accumulate after the bout, never before
        for k in (ka, kb):
            fought[k] = fought.get(k, 0) + 1
        for k in labels[ev]["fotn"] + labels[ev]["potn"]:
            if k in (ka, kb):
                won[k] = won.get(k, 0) + 1
    return pd.DataFrame(rows)


def _top1(df, score_col):
    """Share of cards whose top-ranked bout actually won Fight of the Night."""
    hit = 0
    cards = [g for _, g in df.groupby("event") if g.y.sum() > 0]
    for g in cards:
        pick = g.sort_values(score_col, ascending=False).iloc[0]
        hit += int(pick.y == 1)
    return hit / max(len(cards), 1), len(cards)


def _top_k(df, score_col, k):
    """Share of a card's actual winners caught by its top k picks."""
    hit = tot = 0
    for _, g in df.groupby("event"):
        if g.y_potn.sum() == 0:
            continue
        picks = set(g.sort_values(score_col, ascending=False).head(k).idx)
        actual = set(g[g.y_potn == 1].idx)
        hit += len(picks & actual)
        tot += min(len(actual), k)
    return hit / max(tot, 1), tot


def potn(F, tr_cut, verbose=True):
    """Performance of the Night, scored per fighter rather than per bout.

    Two bonuses a card, so the measure is how many of a card's actual winners
    the top two picks catch. Same three baselines, fighter-level: the main
    event, the likeliest finisher, and the most decorated.
    """
    rows = []
    for r in F.itertuples():
        for side, nm, fin, pri in (("a", r.a, r.fin_a, r.prior_a),
                                   ("b", r.b, r.fin_b, r.prior_b)):
            rows.append(dict(event=r.event, date=r.date, idx=f"{r.fight_id}:{side}",
                             name=nm, order=r.order, card_n=r.card_n, five=r.five,
                             p_finish=fin, prior_bonus=pri,
                             pace=r.pace_sum, kd=r.kd_sum, sub=r.sub_sum,
                             y_potn=int(_key(nm) in r.potn_keys)))
    P = pd.DataFrame(rows)
    if P.empty or P.y_potn.sum() == 0:
        return None
    tr, te = P[P.date <= tr_cut].copy(), P[P.date > tr_cut].copy()
    cols = ["p_finish", "order", "card_n", "five", "pace", "kd", "sub"]
    sc = StandardScaler().fit(tr[cols])
    m = LogisticRegression(max_iter=4000, C=0.5).fit(sc.transform(tr[cols]), tr.y_potn)
    te["s_base"] = m.predict_proba(sc.transform(te[cols]))[:, 1]
    sc2 = StandardScaler().fit(tr[cols + ["prior_bonus"]])
    m2 = LogisticRegression(max_iter=4000, C=0.5).fit(sc2.transform(tr[cols + ["prior_bonus"]]), tr.y_potn)
    te["s_full"] = m2.predict_proba(sc2.transform(te[cols + ["prior_bonus"]]))[:, 1]
    te["b1"] = -te["order"]
    te["b2"] = te["p_finish"]
    te["b3"] = te["prior_bonus"]
    res = {k: _top_k(te, c, 2) for k, c in
           (("model, no bonus history", "s_base"), ("model, with bonus history", "s_full"),
            ("B1 main-event fighters", "b1"), ("B2 likeliest finisher", "b2"),
            ("B3 most prior bonuses", "b3"))}
    if verbose:
        n = res["B1 main-event fighters"][1]
        print()
        print(f"PERFORMANCE OF THE NIGHT, top-2 hit rate over {n} awards on held-out cards")
        for k, (acc, _) in res.items():
            print(f"  {k:<30} {100*acc:5.1f}%")
        beats = res["model, no bonus history"][0] > max(
            res["B1 main-event fighters"][0], res["B2 likeliest finisher"][0],
            res["B3 most prior bonuses"][0])
        print("  VERDICT: " + ("beats every baseline without bonus history"
                               if beats else "does NOT beat all three baselines — not published"))
    return res


def run(fights, fighters, path=BONUS_FILE, verbose=True):
    labels = _labels(path)
    F = features(fights, fighters, labels)
    if F.empty:
        print("bonus model: no labelled bouts — run the collector first")
        return None
    # a finish probability, fitted on the training window only
    cut = F.date.quantile(0.8)
    tr, te = F[F.date <= cut].copy(), F[F.date > cut].copy()
    # B2 needs a real finish probability, fitted on whether training-window
    # fights actually finished — the first version fitted on a placeholder,
    # which would have made the baseline easier to beat than it should be
    fin = LogisticRegression(max_iter=2000)
    sc0 = StandardScaler().fit(tr[FINISH_INPUTS])
    fin.fit(sc0.transform(tr[FINISH_INPUTS]), tr.itd.values)
    for d in (tr, te):
        d["p_finish"] = fin.predict_proba(sc0.transform(d[FINISH_INPUTS]))[:, 1]

    def fit_score(cols, name):
        sc = StandardScaler().fit(tr[cols])
        m = LogisticRegression(max_iter=4000, C=0.5).fit(sc.transform(tr[cols]), tr.y)
        te[name] = m.predict_proba(sc.transform(te[cols]))[:, 1]
        return dict(zip(cols, np.round(m.coef_[0], 3)))

    w_base = fit_score(BASE_FEATURES, "s_base")
    w_full = fit_score(BASE_FEATURES + BONUS_FEATURES, "s_full")
    te["b1"] = -te["order"]                 # the main event is order 0
    te["b2"] = te["p_finish"]
    te["b3"] = te["prior_bonus"]
    res = {k: _top1(te, c) for k, c in
           (("model, no bonus history", "s_base"), ("model, with bonus history", "s_full"),
            ("B1 always the main event", "b1"), ("B2 highest chance of a finish", "b2"),
            ("B3 most prior bonuses", "b3"))}
    n_cards = res["B1 always the main event"][1]
    rand = float(np.mean([1 / len(g) for _, g in te.groupby("event") if g.y.sum() > 0]))
    if verbose:
        print(f"FIGHT OF THE NIGHT, top-1 accuracy on {n_cards} held-out cards")
        for k, (acc, _) in res.items():
            print(f"  {k:<30} {100*acc:5.1f}%")
        print(f"  {'random pick':<30} {100*rand:5.1f}%")
        beats = (res["model, no bonus history"][0] >
                 max(res["B1 always the main event"][0], res["B2 highest chance of a finish"][0],
                     res["B3 most prior bonuses"][0]))
        print()
        print("  VERDICT: " + ("the model beats every baseline without bonus history — "
                               "publishable under addendum 24"
                               if beats else
                               "the model does NOT beat all three baselines — not published"))
        print(f"  weights (no bonus history): {w_base}")
        print(f"  weights (with):             {w_full}")
    potn(pd.concat([tr, te]), cut, verbose=verbose)
    return res


if __name__ == "__main__":
    from .loaders import load
    _f, _p, _ = load(verbose=False)
    run(_f, _p)
