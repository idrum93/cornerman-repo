"""Four checks. The first is the one that matters.

Temporal leakage is the failure mode that produces beautiful backtests and
worthless models, and it is silent — nothing crashes, the numbers just get
better. So we test for it structurally rather than trusting the code to be
correct by inspection.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from .features import build, FEATURE_NAMES
from .synth import make_corpus

OK, BAD = "PASS", "FAIL"


def test_no_leakage(fights, fighters, n_probe=6, seed=1):
    """Rebuild each probe fight's features from a corpus TRUNCATED at that
    fight. If any feature depends on later fights, the two disagree."""
    full, _ = build(fights, fighters)
    fights_sorted = fights.sort_values(["date", "fight_id"], kind="mergesort").reset_index(drop=True)
    rng = np.random.default_rng(seed)
    probes = rng.choice(np.arange(int(len(fights_sorted) * 0.55), len(fights_sorted)),
                        size=n_probe, replace=False)
    worst = 0.0
    for k in probes:
        fid = fights_sorted.fight_id.iloc[k]
        trunc, _ = build(fights_sorted.iloc[: k + 1], fighters)
        a = full[(full.fight_id == fid) & (full.orient == 0)][FEATURE_NAMES]
        b = trunc[(trunc.fight_id == fid) & (trunc.orient == 0)][FEATURE_NAMES]
        if len(a) == 0 or len(b) == 0:
            continue
        worst = max(worst, float(np.abs(a.values - b.values).max()))
    return worst < 1e-9, f"max feature drift vs truncated rebuild = {worst:.2e}"


def test_antisymmetry(X):
    """f(A,B) must equal -f(B,A) for every feature, or the model can learn
    a corner bias that will not exist at prediction time."""
    f0 = X[X.orient == 0].sort_values("fight_id")[FEATURE_NAMES].values
    f1 = X[X.orient == 1].sort_values("fight_id")[FEATURE_NAMES].values
    err = float(np.abs(f0 + f1).max())
    return err < 1e-9, f"max |f(A,B) + f(B,A)| = {err:.2e}"


def _fit_auc(d, cols, seed=None):
    if seed is not None:
        d = d.copy()
        d["y"] = np.random.default_rng(seed).permutation(d.y.values)
    cut = d.date.quantile(0.8)
    tr, te = d[d.date <= cut], d[d.date > cut]
    sc = StandardScaler().fit(tr[cols])
    m = LogisticRegression(max_iter=2000, fit_intercept=False)
    m.fit(sc.transform(tr[cols]), tr.y)
    return roc_auc_score(te.y, m.predict_proba(sc.transform(te[cols]))[:, 1])


def test_null_model(X, n_seeds=10):
    """Shuffled labels must score ~0.50 AUC. A single draw is far too noisy to
    judge this on — one test block is a few hundred rows, so the per-seed sd is
    ~0.035. Average over seeds and test the mean."""
    d = X[X.min_prior >= 2]
    aucs = np.array([_fit_auc(d, FEATURE_NAMES, seed=s) for s in range(n_seeds)])
    se = aucs.std(ddof=1) / np.sqrt(n_seeds)
    ok = abs(aucs.mean() - 0.5) < max(0.02, 3 * se)
    return ok, (f"shuffled-label AUC = {aucs.mean():.4f} +/- {se:.4f} "
                f"over {n_seeds} seeds (want ~0.500)")


def test_leak_detector_has_power(fights, fighters, X):
    """Positive control: inject a feature computed FROM the fight itself.
    If the eval doesn't light up here, it can't be trusted to catch real
    leakage either."""
    d = X[X.min_prior >= 2].copy()
    stats = fights.set_index("fight_id")
    ss_diff = (stats.r_ss_landed - stats.b_ss_landed).to_dict()
    sign = np.where(d.orient.values == 0, 1.0, -1.0)
    d["LEAK_ss_landed_this_fight"] = d.fight_id.map(ss_diff).values * sign

    clean = _fit_auc(d, FEATURE_NAMES)
    leaked = _fit_auc(d, FEATURE_NAMES + ["LEAK_ss_landed_this_fight"])
    lift = leaked - clean
    return lift > 0.05, (f"clean AUC {clean:.4f} -> leaked AUC {leaked:.4f} "
                         f"(lift +{lift:.4f}, want >+0.05)")


def test_settle_respects_dates(fights):
    """A rematch must not be settled with the earlier fight's result.

    On the first live capture, settle() matched only on the fighter pair and
    resolved a Van vs Pantoja rematch using their 2025-12-06 first meeting —
    marking the fight decided before it happened. 424 fights in the corpus are
    rematches, so this was systematic, not a one-off.
    """
    import json
    import tempfile
    from .upcoming import _key
    from . import ledger

    if "bout" not in fights.columns:
        # the synthetic corpus has no bout strings; CI exercises this against
        # real data via `python -m mmastat.tests` after a corpus refresh
        return True, "skipped (synthetic corpus has no bout names)"
    parts = fights.bout.str.split(" vs. ", n=1, expand=True)
    seen, rematch = {}, None
    for r_, b_, dt in zip(parts[0], parts[1], fights.date):
        k = frozenset((_key(r_), _key(b_)))
        if k in seen:
            rematch = (r_, b_, seen[k], dt)
            break
        seen[k] = dt
    if rematch is None:
        return True, "no rematch found in corpus to test against"
    a, b, first_dt, second_dt = rematch
    # a capture dated a year AFTER the second meeting must not settle
    future = (pd.Timestamp(second_dt) + pd.Timedelta(days=365)).date().isoformat()
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        fh.write(json.dumps({"captured_utc": "x", "event": "future",
                             "event_date": future, "fighter": a, "opponent": b,
                             "p_market_devig": .5, "implied_with_vig": .52,
                             "p_model": .55, "edge": .03, "books": 5,
                             "bet": True, "settled": False}) + "\n")
        tmp = fh.name
    ledger.settle(fights, path=tmp, verbose=False)
    got = ledger.read(tmp)
    ok = not bool(got.settled.iloc[0])
    return ok, (f"a bout dated {future} between two fighters who last met "
                f"{pd.Timestamp(second_dt).date()} was "
                f"{'correctly left open' if ok else 'WRONGLY SETTLED'}")


def run_all(fights=None, fighters=None):
    if fights is None:
        fights, fighters, _ = make_corpus(n_fighters=520, n_events=320)
    X, _ = build(fights, fighters)
    checks = [
        ("no temporal leakage", test_no_leakage(fights, fighters)),
        ("antisymmetric features", test_antisymmetry(X)),
        ("null model is chance", test_null_model(X)),
        ("leak detector has power", test_leak_detector_has_power(fights, fighters, X)),
        ("settle respects dates", test_settle_respects_dates(fights)),
    ]
    print(f"{'CHECK':<28} {'RESULT':<6}  DETAIL")
    print("-" * 78)
    allok = True
    for name, (ok, detail) in checks:
        allok &= ok
        print(f"{name:<28} {(OK if ok else BAD):<6}  {detail}")
    print("-" * 78)
    print("ALL CHECKS PASSED" if allok else "SOMETHING IS WRONG — do not trust downstream numbers")
    return allok


if __name__ == "__main__":
    run_all()
