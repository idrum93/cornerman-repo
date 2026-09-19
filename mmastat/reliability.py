"""Plain-language track record, measured on held-out fights.

AUC is the right metric for us and the wrong one for a reader. It answers
"pick one fight where a takedown happened and one where it didn't — how often
does the model rate the first higher?", which is a real property but not one
anyone should have to decode on a fight card.

The fix is NOT to invent a simpler score. A composite "confidence index" would
be a number we made up, and inventing a metric to make a model look
comprehensible is how sites end up overstating what they know.

Instead this reports what actually happened on fights the model never saw:

    "When this said a takedown was likely, one landed 78% of the time (112 fights)."

That is checkable, it is the question a reader is actually asking, and it
cannot flatter the model, because it is just counting. The underlying AUC and
Brier figures stay in the payload for anyone who wants them.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .features import build, WIN_FEATURES
from .projections import FEATS as PROJ_FEATS


def _record(y, p, hi=0.60, lo=0.40):
    """How often the event happened when the model leaned each way."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    out = {}
    m = p >= hi
    if m.sum() >= 20:
        out["said_likely"] = {"n": int(m.sum()), "happened": round(float(y[m].mean()), 3),
                              "avg_said": round(float(p[m].mean()), 3)}
    m = p <= lo
    if m.sum() >= 20:
        out["said_unlikely"] = {"n": int(m.sum()), "happened": round(float(y[m].mean()), 3),
                                "avg_said": round(float(p[m].mean()), 3)}
    try:
        out["auc"] = round(float(roc_auc_score(y, p)), 3)
    except ValueError:
        pass
    return out


def build_record(fights, fighters, min_date="2012-01-01", test_frac=0.20):
    """Everything the site quotes about its own reliability, computed fresh."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import HistGradientBoostingClassifier
    from .features import build_panel
    from .projections import fit_range, predict_range, RANGE_TARGETS, EVENT_TARGETS

    rec = {}

    # ---- who wins
    X, _ = build(fights, fighters)
    d = X[(X.min_prior >= 2) & (X.date >= pd.Timestamp(min_date))].sort_values("date")
    cut = d.date.quantile(1 - test_frac)
    tr, te = d[d.date <= cut], d[d.date > cut]
    ev = te[te.orient == 0]
    sc = StandardScaler().fit(tr[WIN_FEATURES])
    m = LogisticRegression(max_iter=4000, C=0.5, fit_intercept=False).fit(
        sc.transform(tr[WIN_FEATURES]), tr.y)
    p = m.predict_proba(sc.transform(ev[WIN_FEATURES]))[:, 1]
    y = ev.y.values
    rec["winner"] = {
        "n_tested": int(len(y)),
        "accuracy": round(float(((p > 0.5) == (y == 1)).mean()), 3),
        "tested_from": str(ev.date.min().date()),
        "tested_to": str(ev.date.max().date()),
        "bands": [],
    }
    for lo, hi in ((0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 1.01)):
        m2 = (np.maximum(p, 1 - p) >= lo) & (np.maximum(p, 1 - p) < hi)
        if m2.sum() < 15:
            continue
        won = ((p > 0.5) == (y == 1))[m2].mean()
        rec["winner"]["bands"].append(
            {"said": f"{int(lo*100)}-{int(hi*100) if hi<=1 else 100}%",
             "n": int(m2.sum()), "right": round(float(won), 3)})

    # ---- takedown / knockdown
    P = build_panel(fights, fighters)
    P = P[P.date >= pd.Timestamp(min_date)].sort_values("date")
    pcut = P.date.quantile(1 - test_frac)
    ptr, pte = P[P.date <= pcut], P[P.date > pcut]
    for t, (label, _base) in EVENT_TARGETS.items():
        ytr = (ptr[t] > 0).astype(int)
        clf = HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
            min_samples_leaf=40, l2_regularization=1.0,
            random_state=7).fit(ptr[PROJ_FEATS], ytr)
        pr = clf.predict_proba(pte[PROJ_FEATS])[:, 1]
        rec[label] = _record((pte[t] > 0).astype(int).values, pr)

    # ---- output ranges: does an 80% range cover 80%?
    vcut = ptr.date.quantile(0.85)
    fitp, valp = ptr[ptr.date <= vcut], ptr[ptr.date > vcut]
    rec["ranges"] = {}
    for t, (label, unit, _b, _s, two_sided) in RANGE_TARGETS.items():
        models, k = fit_range(fitp, valp, t, two_sided)
        lo, mid, hi = predict_range(models, k, pte, two_sided)
        yv = pte[t].values
        rec["ranges"][label] = {
            "claimed": 0.80,
            "actual": round(float(((yv >= lo) & (yv <= hi)).mean()), 3),
            "n": int(len(yv))}
    return rec


def phrase(rec, key):
    """One sentence a reader can check, for the site."""
    r = rec.get(key) or {}
    s = r.get("said_likely")
    if not s:
        return None
    return (f"When this called a {key} likely, one happened "
            f"{round(s['happened']*100)}% of the time ({s['n']} fights).")


if __name__ == "__main__":
    import json
    from .loaders import load
    f, p, _ = load(verbose=False)
    print(json.dumps(build_record(f, p), indent=1))
