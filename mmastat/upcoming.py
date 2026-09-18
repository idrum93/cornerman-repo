"""Turn an upcoming fight card into predictions.

On retrieval. There is no reliable free machine-readable feed of upcoming UFC
cards. UFCStats' own upcoming page sits behind a JavaScript interstitial (a
plain request returns "Checking your browser..."), the Kaggle `upcoming.csv`
turned out to be a frozen snapshot months out of date, and every other listing
is a news site whose HTML changes without notice. A scraper built on any of
those is a thing that breaks silently and leaves you showing stale fights.

So the input here is a plain text file you edit by hand, `data/upcoming.txt`:

    # UFC 331 | 2026-09-19 | Crypto.com Arena, Los Angeles
    Joshua Van vs. Alexandre Pantoja
    Arman Tsarukyan vs. Mauricio Ruffy
    ...

Thirteen lines copied off any fight card takes a minute, needs no terminal, and
cannot break. `fetch_ufcstats_upcoming()` is provided for when you want to
automate it, but it is unverified from this environment and the manual path is
the one that will still work next year.

Name resolution is the real problem, not retrieval. Newcomers have no history
(Patricio Pitbull's UFC debut has no UFCStats record however famous he is), and
spellings drift between sources. Unresolved and insufficient-history fighters
are reported explicitly rather than silently defaulted to league averages,
because a confident-looking 50/50 on a debut is worse than saying "no read".
"""
import difflib
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from .features import (PANEL_OWN, WIN_FEATURES, _init_states, build,
                       elo_eff, make_features)
from .projections import FEATS as PROJ_FEATS, RANGE_TARGETS, EVENT_TARGETS

MIN_PRIOR = 2


def _key(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", "", re.sub(r"\s+", " ", s).strip().lower())


def parse_card(path):
    """Returns (meta dict, list of (name_a, name_b))."""
    meta, bouts = {}, []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            parts = [p.strip() for p in line.lstrip("#").split("|")]
            for k, v in zip(("event", "date", "venue"), parts):
                meta[k] = v
            continue
        rounds = 3
        if "|" in line:                      # "A vs. B | 5" marks a 5-rounder
            line, tail = line.rsplit("|", 1)
            if tail.strip().startswith("5"):
                rounds = 5
        m = re.split(r"\s+vs\.?\s+", line, maxsplit=1, flags=re.I)
        if len(m) == 2:
            bouts.append((m[0].strip(), m[1].strip(), rounds))
    return meta, bouts


def _alias_table(fighters):
    """Every string a source might plausibly use for a fighter.

    Three real failure modes this fixes, all observed on a live card:
      - nickname for surname: "Patricio Pitbull" is UFCStats' "Patricio Freire"
      - spacing: "Joo Sang Yoo" is stored as "JooSang Yoo"
      - accents: handled upstream in _key via NFKD stripping
    """
    table = {}

    def add(s, fid):
        k = _key(s)
        if not k or len(k) < 4:
            return
        table.setdefault(k, fid)
        table.setdefault(k.replace(" ", ""), fid)   # spacing-insensitive

    nicks = fighters.nickname if "nickname" in fighters.columns else [""] * len(fighters)
    for name, nick, fid in zip(fighters.name, nicks, fighters.fighter_id):
        add(name, fid)
        parts = str(name).split()
        nick = str(nick or "").strip()
        if nick and parts:
            add(f"{parts[0]} {nick}", fid)          # first name + nickname
            add(f"{nick} {parts[-1]}", fid)         # nickname + surname
    return table


def load_aliases(path="data/aliases.txt"):
    """Manual name overrides, one per line: `Card name = UFCStats name`.

    Needed because some cases are genuinely unresolvable automatically and
    dangerous to guess. Live example: news sources list "Patricio Pitbull",
    UFCStats stores "Patricio Freire", and his BROTHER "Patricky Freire" is the
    one actually carrying the nickname "Pitbull" in the details file. Fuzzy
    matching resolves that to the wrong man. Refusing and letting you state the
    mapping is the safe behaviour.
    """
    out = {}
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            a, b = line.split("=", 1)
            out[_key(a)] = _key(b)
    except FileNotFoundError:
        pass
    return out


def resolve(names, fighters, cutoff=0.88, alias_path="data/aliases.txt"):
    """Map display names onto fighter_ids. Exact normalised match, then the
    alias forms, then a close-match; anything below `cutoff` is returned as
    unresolved rather than guessed at."""
    table = _alias_table(fighters)
    manual = load_aliases(alias_path)
    keys = list(table)
    out, unresolved = {}, []
    for n in names:
        k = manual.get(_key(n), _key(n))
        if k in table:
            out[n] = table[k]
            continue
        if k.replace(" ", "") in table:
            out[n] = table[k.replace(" ", "")]
            continue
        near = difflib.get_close_matches(k, keys, n=1, cutoff=cutoff)
        if near:
            out[n] = table[near[0]]
        else:
            unresolved.append(n)
    return out, unresolved


def _states_after(fights, fighters):
    """Replay the whole corpus and return each fighter's state as it stands
    after their last recorded bout. Uses the same _apply() the training walk
    uses, so an upcoming-fight snapshot is built exactly like a historical
    one."""
    from .features import _apply
    states = _init_states(fighters)
    for f in fights.sort_values(["date", "fight_id"], kind="mergesort").itertuples():
        A, B = states[f.r_id], states[f.b_id]
        sa, sb = A.snapshot(f.date), B.snapshot(f.date)
        sa["elo"], sb["elo"] = elo_eff(A, f.date), elo_eff(B, f.date)
        _apply(f, A, B, sa, sb)
    return states


def predict_card(path, fights, fighters, verbose=True):
    from .projections import fit_range, predict_range
    from .props import symmetric_features, prop_targets, BINARY
    from sklearn.ensemble import HistGradientBoostingClassifier

    meta, bouts = parse_card(path)
    as_of = pd.Timestamp(meta.get("date") or fights.date.max())
    states = _states_after(fights, fighters)

    names = sorted({n for b in bouts for n in b[:2]})
    ids, unresolved = resolve(names, fighters)

    # --- win model, trained on everything available
    X, _ = build(fights, fighters)
    d = X[(X.min_prior >= MIN_PRIOR) & (X.date >= pd.Timestamp("2012-01-01"))]
    sc = StandardScaler().fit(d[WIN_FEATURES])
    win = LogisticRegression(max_iter=4000, C=0.5, fit_intercept=False).fit(
        sc.transform(d[WIN_FEATURES]), d.y)

    # --- projection + prop models
    from .features import build_panel
    P = build_panel(fights, fighters)
    P = P[P.date >= pd.Timestamp("2012-01-01")].sort_values("date")
    vcut = P.date.quantile(0.85)
    ptr, pval = P[P.date <= vcut], P[P.date > vcut]
    rng_models = {t: fit_range(ptr, pval, t, two_sided=cfg[4])
                  for t, cfg in RANGE_TARGETS.items()}
    evt_models = {}
    for t in EVENT_TARGETS:
        evt_models[t] = HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
            min_samples_leaf=40, l2_regularization=1.0,
            random_state=7).fit(P[PROJ_FEATS], (P[t] > 0).astype(int))

    # --- competing-risks model for method and round, fitted once
    from .survival import (expand as sv_expand, fit as sv_fit, CLASSES,
                           calibrate_hazards, distribution, INTERVAL)
    from .features import WIN_FEATURES as WF
    sv_tr, sv_feats = sv_expand(fights, fighters, full=False)
    sv_pr, _ = sv_expand(fights, fighters, full=True)
    _vc = sv_tr.date.quantile(0.85)
    sv_model, sv_cols = sv_fit(sv_tr[sv_tr.date <= _vc], sv_feats)
    sv_cal = calibrate_hazards(sv_model, sv_cols, sv_pr[sv_pr.date > _vc],
                               fights.set_index("fight_id"))
    sum_keys = [c for c in sv_feats if c.startswith("sum_")]

    def method_round(sa, sb, n_rounds):
        row = {f"d_{k.replace('d_', '')}": 0.0 for k in []}
        fv = make_features(sa, sb)
        base = {c: fv[c] for c in WF}
        base.update({f"sum_{k}": sa[k] + sb[k] for k in PANEL_OWN
                     if f"sum_{k}" in sum_keys})
        n = int(n_rounds * 5)
        grid = pd.DataFrame([{**base, "t": t, "rnd": min(5, (t - 1) // 5 + 1)}
                             for t in range(1, n + 1)])
        H = sv_model.predict_proba(grid[sv_cols])
        H = H.copy()
        H[:, 1:3] *= sv_cal[0]
        H[:, 3:5] *= sv_cal[1]
        H[:, 0] = np.maximum(H[:, 0], 1e-9)
        H /= H.sum(axis=1, keepdims=True)
        surv = 1.0
        out = {k: 0.0 for k in CLASSES[1:]}
        by_r = {}
        for i in range(len(H)):
            r = int(grid.rnd.iloc[i])
            stop = 0.0
            for j, k in enumerate(CLASSES[1:], start=1):
                v = surv * H[i, j]
                out[k] += v
                stop += v
            by_r[r] = by_r.get(r, 0.0) + stop
            surv *= H[i, 0]
        out["decision"] = surv
        return out, by_r

    rows, skipped = [], []
    for na, nb, n_rounds in bouts:
        if na not in ids or nb not in ids:
            skipped.append((na, nb, "name not in UFCStats corpus"))
            continue
        A, B = states[ids[na]], states[ids[nb]]
        if min(A.n_fights, B.n_fights) < MIN_PRIOR:
            skipped.append((na, nb,
                            f"insufficient history ({A.n_fights} / {B.n_fights} prior bouts)"))
            continue
        sa, sb = A.snapshot(as_of), B.snapshot(as_of)
        sa["elo"], sb["elo"] = elo_eff(A, as_of), elo_eff(B, as_of)

        fv = make_features(sa, sb)
        x = pd.DataFrame([fv])[WIN_FEATURES]
        p_a = float(win.predict_proba(sc.transform(x))[0, 1])

        r = dict(bout=f"{na} vs. {nb}", a=na, b=nb, rounds=n_rounds,
                 p_a=round(p_a, 4), p_b=round(1 - p_a, 4))
        try:
            dist, by_r = method_round(sa, sb, n_rounds)
            r["m_a_ko"] = round(dist["a_ko"], 4)
            r["m_b_ko"] = round(dist["b_ko"], 4)
            r["m_a_sub"] = round(dist["a_sub"], 4)
            r["m_b_sub"] = round(dist["b_sub"], 4)
            r["m_decision"] = round(dist["decision"], 4)
            r["p_finish"] = round(1 - dist["decision"], 4)
            for rr in range(1, n_rounds + 1):
                r[f"p_end_r{rr}"] = round(by_r.get(rr, 0.0), 4)
        except Exception as e:
            r["method_error"] = str(e)[:80]
        for who, me, op in (("a", sa, sb), ("b", sb, sa)):
            row = {f"own_{k}": me[k] for k in PANEL_OWN}
            row.update({f"opp_{k}": op[k] for k in PANEL_OWN})
            xx = pd.DataFrame([row])[PROJ_FEATS]
            for t, (models, k) in rng_models.items():
                lo, mid, hi = predict_range(models, k, xx, RANGE_TARGETS[t][4])
                nm = "ctrl" if t == "y_ctrl_pm" else "slpm"
                r[f"{who}_{nm}_lo"] = round(float(lo[0]), 2)
                r[f"{who}_{nm}_mid"] = round(float(mid[0]), 2)
                r[f"{who}_{nm}_hi"] = round(float(hi[0]), 2)
            for t, (lab, _) in EVENT_TARGETS.items():
                r[f"{who}_p_{lab}"] = round(
                    float(evt_models[t].predict_proba(xx)[0, 1]), 3)
        rows.append(r)

    out = pd.DataFrame(rows)
    if verbose:
        print(f"{meta.get('event','(card)')} | {meta.get('date','')} | "
              f"{meta.get('venue','')}")
        print(f"{len(bouts)} bouts parsed, {len(out)} predicted, {len(skipped)} skipped\n")
        if len(out):
            cc = [c for c in ["bout", "p_a", "p_b", "p_finish", "m_decision",
                              "a_p_takedown", "b_p_takedown"]
                  if c in out.columns]
            show = out[cc].copy()
            for c in ("p_a", "p_b", "p_finish", "m_decision"):
                if c in show:
                    show[c] = (show[c] * 100).round(1)
            print(show.to_string(index=False))
        if skipped:
            print("\nNO READ (reported, not guessed):")
            for na, nb, why in skipped:
                print(f"  {na} vs. {nb}  --  {why}")
        if unresolved:
            print("\nunmatched names:", ", ".join(unresolved))
    return out, skipped, unresolved


def fetch_ufcstats_upcoming(url="http://ufcstats.com/statistics/events/upcoming"):
    """UNVERIFIED. UFCStats served a JavaScript interstitial when tested from a
    datacenter IP; it may work from a residential connection. Returns a list of
    (name_a, name_b) or raises. Prefer the manual text file."""
    import requests
    from bs4 import BeautifulSoup
    html = requests.get(url, timeout=20, headers={
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/127.0 Safari/537.36")}).text
    if "Checking your browser" in html or "requires JavaScript" in html:
        raise RuntimeError("UFCStats served a bot-check page; use data/upcoming.txt")
    soup = BeautifulSoup(html, "html.parser")
    ev = soup.select_one("a.b-link")
    if ev is None:
        raise RuntimeError("could not find an upcoming event link")
    page = requests.get(ev["href"], timeout=20).text
    s2 = BeautifulSoup(page, "html.parser")
    bouts = []
    for row in s2.select("tr.b-fight-details__table-row"):
        ps = [a.get_text(strip=True) for a in row.select("a.b-link")]
        if len(ps) >= 2:
            bouts.append((ps[0], ps[1]))
    return bouts


def write_json(out, skipped, unresolved, path="site/predictions.json",
               card_path="data/upcoming.txt"):
    """Emit what the frontend reads. Skipped bouts are included with their
    reason so the site can render "no read" rather than omitting them
    silently — a card with three fights quietly missing looks broken."""
    import json
    from pathlib import Path
    meta, _ = parse_card(card_path)
    payload = {
        "event": meta.get("event"), "date": meta.get("date"),
        "venue": meta.get("venue"),
        "generated_utc": pd.Timestamp.now('UTC').isoformat(),
        "bouts": out.to_dict(orient="records"),
        "no_read": [{"a": a, "b": b, "reason": why} for a, b, why in skipped],
        "unresolved_names": unresolved,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys
    from .loaders import load
    f, p, _ = load(verbose=False)
    out, skipped, unresolved = predict_card("data/upcoming.txt", f, p)
    if "--json" in sys.argv:
        print("\nwrote", write_json(out, skipped, unresolved))
