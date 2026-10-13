"""Single chronological pass over the fight corpus.

THE INVARIANT: inside the loop, `snapshot -> emit -> update` runs in that order
and nothing else touches state. Every feature row for fight N is therefore a
function of fights 1..N-1 only. tests.py asserts this independently.

Each fight is emitted TWICE, once in each orientation, sharing a fight_id so
folds can group them. Every feature is antisymmetric, so combined with
fit_intercept=False the model satisfies P(A beats B) = 1 - P(B beats A) exactly.
"""
import math

import numpy as np
import pandas as pd

from .config import ELO_START, ELO_K, ELO_METHOD_MULT, ELO_REGRESS_PER_YEAR
from .state import FighterState

# Plain differentials: feature = A's value minus B's value.
DIFF_KEYS = [
    "elo", "win_pct", "log_exp", "opp_elo",
    "adj_slpm", "sapm", "str_acc", "str_def",
    "adj_td15", "td_acc", "td_def", "sub15", "ctrl_share",
    "finish_rate", "ko_loss_rate",
    "reach", "height", "age", "log_layoff", "southpaw",
    "kd15", "kd_against15", "body_share", "leg_share",
    "clinch_share", "ground_share",
]

# The fortitude cluster. Held separate from DIFF_KEYS so it can be tested as a
# pre-registered family (PREREGISTRATION.md, addendum 4) rather than quietly
# folded into the win model.
FORTITUDE_KEYS = ["late_acc_delta", "late_volume_ret", "ctrl_retention",
                  "induced_decay", "deep_experience", "kd_recovery"]
FORTITUDE_FEATURES = [f"d_{k}" for k in FORTITUDE_KEYS]

FEATURE_NAMES = ([f"d_{k}" for k in DIFF_KEYS]
                 + ["grapple_edge", "ko_edge", "sub_edge",
                    "power_edge", "position_edge"])

# Pruned set. Each removal below is a feature whose signal is already carried by
# an interaction term or a better-adjusted twin (r > 0.85 with something kept).
# On synthetic data this matches the full set's accuracy while cutting the design
# matrix condition number from ~42 to ~10, which is what stops coefficient signs
# from flipping. Prefer this one for anything you intend to interpret.
DROPPED = {
    "d_adj_td15": "carried by grapple_edge",
    "d_sub15": "carried by sub_edge",
    "d_win_pct": "carried by d_elo, which is opponent-adjusted",
    "d_td_acc": "carried by grapple_edge",
    "d_ctrl_share": "carried by grapple_edge",
    "d_height": "carried by d_reach",
    "d_southpaw": "no measurable effect",
    "d_td_def": "carried by grapple_edge",
    "d_finish_rate": "carried by ko_edge",
}
DROPPED.update({k: "fortitude cluster, tested separately" for k in FORTITUDE_FEATURES})
CORE_FEATURES = [f for f in FEATURE_NAMES if f not in DROPPED]

# The win model deliberately EXCLUDES the style features. Adding the eight
# target/position/knockdown differentials changed held-out log loss by
# -0.0009, 95% CI [-0.0041, +0.0022], P(better) = 0.293 — no detectable effect
# on predicting who wins. They stay in the codebase because they demonstrably
# do help predict OUTPUT (see projections.py: strike-volume ranking Spearman
# 0.441 vs 0.283 for a career average; takedown probability AUC 0.742), and
# because the explanation panel displays them. Keeping them out of the win
# model is the disciplined call, not an oversight: see PREREGISTRATION.md for
# the targeted second attempt via interaction terms.
STYLE_FEATURES = [f for f in CORE_FEATURES
                  if any(k in f for k in ("kd", "_share", "power_edge",
                                          "position_edge"))]
WIN_FEATURES = [f for f in CORE_FEATURES if f not in STYLE_FEATURES]


def elo_eff(st, d):
    """Rating decayed toward the mean by time since last appearance."""
    yrs = st.layoff_days(d) / 365.25
    return ELO_START + (st.elo - ELO_START) * math.exp(-ELO_REGRESS_PER_YEAR * yrs)


def make_features(sa, sb):
    f = {f"d_{k}": sa[k] - sb[k] for k in DIFF_KEYS + FORTITUDE_KEYS}
    # Interactions: offense discounted by the specific defense in front of it.
    f["grapple_edge"] = (sa["adj_td15"] * (1 - sb["td_def"])
                         - sb["adj_td15"] * (1 - sa["td_def"]))
    f["ko_edge"] = (sa["adj_slpm"] * sb["ko_loss_rate"]
                    - sb["adj_slpm"] * sa["ko_loss_rate"])
    f["sub_edge"] = (sa["sub15"] * (1 - sb["td_def"])
                     - sb["sub15"] * (1 - sa["td_def"]))
    # Power vs chin, measured in knockdowns rather than career method mix.
    f["power_edge"] = (sa["kd15"] * sb["kd_against15"]
                       - sb["kd15"] * sa["kd_against15"])
    # A clinch- or ground-heavy striker needs to get there first; weight their
    # positional preference by whether the opponent can be taken down.
    f["position_edge"] = ((sa["clinch_share"] + sa["ground_share"]) * (1 - sb["td_def"])
                          - (sb["clinch_share"] + sb["ground_share"]) * (1 - sa["td_def"]))
    return f


def length_test(fights, fighters, min_date="2012-01-01", n_boot=400, seed=7):
    """Does height change what a reach edge is worth? Registered, not adopted.

    THE PROPOSAL, in the proposer's words: a fighter two inches shorter with one
    inch longer arms may cancel the taller man's advantage - a way to measure the
    SEVERITY of a reach discrepancy rather than its raw size. `d_reach` alone
    cannot express that, and the observation is correct.

    IT SPLITS INTO TWO HYPOTHESES, and they are not the same question.

    H1, NET LENGTH. Height offsets reach additively, so the quantity that matters
    is the ape index, reach minus height, differenced between corners. Note the
    algebra, because it was initially got wrong here:

        d_ape = (ra - ha) - (rb - hb) = d_reach - d_height

    so span{d_reach, d_ape} == span{d_reach, d_height}, rank 2 either way. Adding
    the ape index to a model that already carries d_reach is THE SAME MODEL as
    adding d_height back, reparameterised. It is not a new degree of freedom and
    it is not orthogonal to d_reach (r is about 0.6, not 0). What the
    reparameterisation does buy is conditioning - 3.2 against 2.5 on simulated
    anthropometry - which is interpretability, not information.

    That makes H1 worth testing anyway, for a reason unrelated to the proposal:
    `d_height` was dropped by a CORRELATION RULE (r > 0.85 with something kept),
    never by a held-out comparison. Nobody has measured whether it adds anything.

    H2, SEVERITY. The VALUE of a reach edge depends on the height context - an
    inch of reach on a shorter man is not worth an inch on a taller one. That is
    an interaction, d_reach x d_height, and it IS a new direction: rank 3 against
    the pair. This is the hypothesis the proposal actually describes, and the
    only one of the two that can tell the tool something d_height could not.

    THE DATA LIMIT, which is the finding that matters most. `loaders.py` imputes
    reach from height for about 26% of fighters as reach = a + b * height. For
    every one of them the ape index is EXACTLY the regression line - zero
    residual by construction - and the interaction is a deterministic function of
    height alone. Both arms would be partly fitting "was this reach imputed".
    Restricted, therefore, to bouts where BOTH corners carry a measured reach.

    PROTOCOL, fixed before any number exists. Time-ordered split, no shuffling.
    Three arms on identical rows: WIN_FEATURES; + d_ape (H1); + d_ape and the
    centred interaction (H2). Held-out log loss, bootstrap 95% interval and
    P(better) - the protocol that rejected the style features at -0.0009,
    95% CI [-0.0041, +0.0022], P(better) = 0.293.

    DECISION RULE, also fixed in advance: adopt an arm only if its interval
    excludes zero AND P(better) >= 0.95 AND it survives a re-run on a later
    corpus. Otherwise record and leave the frozen fourteen alone. The prior is
    against: reach effects in MMA are small, an interaction on a small effect is
    smaller, and a result that merely leans is what noise looks like here.
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import log_loss

    if "reach_imputed" not in fighters.columns:
        return {"error": "fighters table carries no reach_imputed flag; the test "
                         "cannot separate measured reach from imputed"}
    real = set(fighters.loc[~fighters.reach_imputed, "fighter_id"])

    X, y, dates = [], [], []
    for f, sa, sb, n_prior in walk(fights, fighters):
        if min(n_prior) < 2 or f.winner not in ("r", "b"):
            continue
        if pd.Timestamp(f.date) < pd.Timestamp(min_date):
            continue
        if f.r_id not in real or f.b_id not in real:
            continue
        row = make_features(sa, sb)
        row["d_ape"] = (sa["reach"] - sa["height"]) - (sb["reach"] - sb["height"])
        row["_dr"] = sa["reach"] - sb["reach"]
        row["_dh"] = sa["height"] - sb["height"]
        X.append(row)
        y.append(1 if f.winner == "r" else 0)
        dates.append(f.date)

    if len(X) < 800:
        return {"error": f"only {len(X)} bouts with measured reach on both sides; "
                         "too few to separate a residual effect from noise",
                "n": len(X)}

    d = pd.DataFrame(X)
    d["_y"], d["_date"] = y, pd.to_datetime(dates)
    d = d.sort_values("_date")
    # Centred before multiplying, or the interaction proxies the main effects.
    d["d_rxh"] = (d._dr - d._dr.mean()) * (d._dh - d._dh.mean())
    cut = int(len(d) * 0.80)
    tr, te = d.iloc[:cut], d.iloc[cut:]
    yv = te._y.to_numpy()

    def fit_score(cols):
        sc = StandardScaler().fit(tr[cols])
        m = LogisticRegression(max_iter=2000, fit_intercept=False)
        m.fit(sc.transform(tr[cols]), tr._y)
        return m.predict_proba(sc.transform(te[cols]))[:, 1]

    base_cols = [c for c in WIN_FEATURES if c in d.columns]
    preds = {"base": fit_score(base_cols),
             "h1_net_length": fit_score(base_cols + ["d_ape"]),
             "h2_severity": fit_score(base_cols + ["d_ape", "d_rxh"])}

    rng = np.random.default_rng(seed)
    boots = [rng.integers(0, len(yv), len(yv)) for _ in range(n_boot)]
    out = {"n_bouts": int(len(d)), "n_test": int(len(te)),
           "base_logloss": round(float(log_loss(yv, preds["base"])), 5),
           "arms": {}}
    for name in ("h1_net_length", "h2_severity"):
        diffs = np.asarray([log_loss(yv[i], preds[name][i]) - log_loss(yv[i], preds["base"][i])
                            for i in boots if len(set(yv[i])) > 1])
        lo, hi = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
        pb = float((diffs < 0).mean())
        out["arms"][name] = {
            "logloss": round(float(log_loss(yv, preds[name])), 5),
            # negative delta = it helped
            "delta": round(float(log_loss(yv, preds[name]) - log_loss(yv, preds["base"])), 5),
            "ci95": [round(lo, 5), round(hi, 5)], "p_better": round(pb, 3),
            "adopt": bool(hi < 0 and pb >= 0.95),
        }
    out["note"] = ("h1 is algebraically the same model as restoring d_height; only h2 "
                   "is a new degree of freedom. adopt=True still requires a re-run on a "
                   "later corpus before the frozen feature set is touched.")
    return out


def _init_states(fighters):
    st = {}
    for r in fighters.itertuples():
        st[r.fighter_id] = FighterState(
            fid=r.fighter_id,
            dob=r.dob,
            height_in=float(r.height_in),
            reach_in=float(r.reach_in),
            stance=r.stance,
        )
    return st


def walk(fights: pd.DataFrame, fighters: pd.DataFrame):
    """Generator over the corpus in chronological order.

    Yields (fight_row, snapshot_A, snapshot_B, states) BEFORE that fight has
    been applied to either fighter, then advances state when the consumer asks
    for the next item. Every consumer therefore inherits the same
    snapshot-before-update guarantee, so there is exactly one place where
    temporal leakage could be introduced instead of one per model.
    """
    states = _init_states(fighters)
    for f in fights.sort_values(["date", "fight_id"], kind="mergesort").itertuples():
        A, B = states[f.r_id], states[f.b_id]
        d = f.date
        sa, sb = A.snapshot(d), B.snapshot(d)
        sa["elo"], sb["elo"] = elo_eff(A, d), elo_eff(B, d)
        n_prior = (A.n_fights, B.n_fights)

        yield f, sa, sb, n_prior

        _apply(f, A, B, sa, sb)


def _apply(f, A, B, sa, sb):
    """Advance both fighters by one fight. Called only after the snapshot has
    been handed out."""
    minutes = f.total_sec / 60.0
    if f.winner == "r":
        res_a, res_b, score = "W", "L", 1.0
    elif f.winner == "b":
        res_a, res_b, score = "L", "W", 0.0
    else:
        res_a, res_b, score = "D", "D", 0.5

    exp_a = 1.0 / (1.0 + 10 ** ((sb["elo"] - sa["elo"]) / 400.0))
    k = ELO_K * ELO_METHOD_MULT.get(f.method, 1.0)
    delta = k * (score - exp_a)
    A.elo += delta
    B.elo -= delta

    BRK = ("head_landed", "body_landed", "leg_landed",
           "dist_landed", "clinch_landed", "ground_landed",
           "r1_ss_landed", "r1_ss_att", "late_ss_landed", "late_ss_att",
           "r1_ctrl_sec", "late_ctrl_sec", "deep_rounds")
    REN = {"r1_ss_landed": "r1_landed", "r1_ss_att": "r1_att",
           "late_ss_landed": "late_landed", "late_ss_att": "late_att",
           "r1_ctrl_sec": "r1_ctrl", "late_ctrl_sec": "late_ctrl"}
    xa = {REN.get(k2, k2): getattr(f, "r_" + k2, 0.0) for k2 in BRK}
    xa["kd"], xa["kd_against"] = getattr(f, "r_kd", 0.0), getattr(f, "b_kd", 0.0)
    # the OPPONENT's round-1 and late output is what measures induced decay
    xa["opp_r1_att"] = getattr(f, "b_r1_ss_att", 0.0)
    xa["opp_late_att"] = getattr(f, "b_late_ss_att", 0.0)
    xb = {REN.get(k2, k2): getattr(f, "b_" + k2, 0.0) for k2 in BRK}
    xb["kd"], xb["kd_against"] = getattr(f, "b_kd", 0.0), getattr(f, "r_kd", 0.0)
    xb["opp_r1_att"] = getattr(f, "r_r1_ss_att", 0.0)
    xb["opp_late_att"] = getattr(f, "r_late_ss_att", 0.0)

    common = dict(date=f.date, minutes=minutes, method=f.method)
    A.update(**common, **xa, result=res_a, opp_snapshot=sb,
             ss_landed=f.r_ss_landed, ss_att=f.r_ss_att,
             ss_absorbed=f.b_ss_landed, ss_faced=f.b_ss_att,
             td_landed=f.r_td_landed, td_att=f.r_td_att,
             td_conceded=f.b_td_landed, td_faced=f.b_td_att,
             sub_att=f.r_sub_att, ctrl_sec=f.r_ctrl_sec)
    B.update(**common, **xb, result=res_b, opp_snapshot=sa,
             ss_landed=f.b_ss_landed, ss_att=f.b_ss_att,
             ss_absorbed=f.r_ss_landed, ss_faced=f.r_ss_att,
             td_landed=f.b_td_landed, td_att=f.b_td_att,
             td_conceded=f.r_td_landed, td_faced=f.r_td_att,
             sub_att=f.b_sub_att, ctrl_sec=f.b_ctrl_sec)


PANEL_OWN = ["adj_slpm", "sapm", "str_acc", "str_def", "adj_td15", "td_acc",
             "td_def", "sub15", "ctrl_share", "elo", "opp_elo", "age",
             "log_exp", "log_layoff", "reach", "height", "southpaw",
             "kd15", "kd_against15", "body_share", "leg_share",
             "clinch_share", "ground_share"]


def build_panel(fights: pd.DataFrame, fighters: pd.DataFrame) -> pd.DataFrame:
    """One row per fighter per fight, carrying absolute pre-fight LEVELS for
    both sides plus that fighter's realised output. Differentials predict who
    wins; levels are what you need to predict how much someone does."""
    rows = []
    for f, sa, sb, n_prior in walk(fights, fighters):
        if min(n_prior) < 2 or f.total_sec <= 0:
            continue
        mins = f.total_sec / 60.0
        for me, op, pre in ((sa, sb, "r"), (sb, sa, "b")):
            r = {"fight_id": f.fight_id, "date": f.date, "minutes": mins,
                 "y_slpm": getattr(f, pre + "_ss_landed") / mins,
                 "y_td15": getattr(f, pre + "_td_landed") / mins * 15.0,
                 "y_ctrl_pm": getattr(f, pre + "_ctrl_sec") / mins,
                 "y_kd15": getattr(f, pre + "_kd") / mins * 15.0}
            r.update({f"own_{k}": me[k] for k in PANEL_OWN})
            r.update({f"opp_{k}": op[k] for k in PANEL_OWN})
            rows.append(r)
    return pd.DataFrame(rows)


def build(fights: pd.DataFrame, fighters: pd.DataFrame):
    """Mirrored feature rows for the win model.

    Expressed through walk() so there is exactly ONE update path in the
    codebase. It previously had its own inline copy, which silently went stale
    when the fortitude accumulators were added — build() kept passing the old
    field list while build_panel() passed the new one, and the resulting
    features were constant. Two copies of this loop is the bug, not a style
    preference.
    """
    states = _init_states(fighters)
    rows = []
    for f, sa, sb, n_prior, states in _walk_with_states(fights, fighters, states):
        if f.winner not in ("r", "b"):
            continue
        base = dict(fight_id=f.fight_id, date=f.date, method=f.method,
                    min_prior=min(n_prior))
        fwd, rev = make_features(sa, sb), make_features(sb, sa)
        y = 1 if f.winner == "r" else 0
        rows.append({**base, "orient": 0, "a_id": f.r_id, "b_id": f.b_id,
                     "y": y, **fwd})
        rows.append({**base, "orient": 1, "a_id": f.b_id, "b_id": f.r_id,
                     "y": 1 - y, **rev})
    return pd.DataFrame(rows), states


def _walk_with_states(fights, fighters, states):
    """walk(), but yielding the state dict too so build() can return it."""
    for f in fights.sort_values(["date", "fight_id"], kind="mergesort").itertuples():
        A, B = states[f.r_id], states[f.b_id]
        d = f.date
        sa, sb = A.snapshot(d), B.snapshot(d)
        sa["elo"], sb["elo"] = elo_eff(A, d), elo_eff(B, d)
        n_prior = (A.n_fights, B.n_fights)
        yield f, sa, sb, n_prior, states
        _apply(f, A, B, sa, sb)


def current_snapshot(states, fid, on_date):
    """Feature vector for an upcoming (unfought) bout."""
    st = states[fid]
    s = st.snapshot(on_date)
    s["elo"] = elo_eff(st, on_date)
    return s
