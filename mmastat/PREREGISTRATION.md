# Pre-registration: style-matchup interactions

**Written before any of these were fitted. Committed on 2026-09-17.**

The purpose of this file is to make it impossible to fool ourselves later. With
~7,000 usable fights and a few dozen candidate interactions, testing them all
and reporting the winners would guarantee a "finding" whether or not one exists.
Twenty independent tests at p<0.05 produce one false positive by construction.
That is exactly how people come to believe southpaws have an edge over
wrestlers.

So: the hypotheses below are fixed in advance, with directions stated. Anything
not on this list is exploratory and must be labelled as such wherever it
appears, including in the UI.

## Holdout

**252 fights, 2026-04-04 to 2026-09-12.** These sit after the betting-odds file
ends, have never been used for fitting, tuning, feature selection, or any
decision in this project. They are spent once. Do not look at them until the
confirmatory tests below are specified and the model is frozen.

Primary fitting/validation uses fights from 2012-01-01 to 2026-03-28.

## Multiplicity correction

Nine hypotheses. Benjamini-Hochberg at FDR 0.10 across the whole family. A
hypothesis counts as supported only if it survives correction AND the effect
has the pre-stated sign AND it replicates on the holdout.

## Hypotheses

Each is a single interaction term added to the frozen 14-feature win model. The
test is on the interaction coefficient, not on model accuracy.

| # | interaction | predicted sign | rationale |
|---|---|---|---|
| H1 | leg_share x opponent stance mismatch | positive | open stance exposes the lead leg |
| H2 | leg_share x opponent td_def | positive | kicking is riskier against a wrestler who can catch it |
| H3 | (clinch_share + ground_share) x opponent td_def | negative | position-dependent offense needs the takedown to land |
| H4 | body_share x opponent late-round output decay | positive | body work is the classic pace-breaker |
| H5 | kd15 x opponent kd_against15 | positive | power vs chin, already in as `power_edge` |
| H6 | reach differential x own dist_share | positive | reach should pay off only for fighters who fight at range |
| H7 | reach differential x opponent clinch_share | negative | a clinch fighter neutralises reach |
| H8 | td15 x opponent ground_share | negative | taking down a dangerous bottom player is a poor plan |
| H9 | age differential x own pace (ss_att per min) | negative | high-output styles should age worse |

## Pre-stated expectations

Most of these will fail. H5 is already in the model as `power_edge` and carried
a small positive coefficient (+0.09), so it is the most likely to survive. H6
and H7 are the most interesting if true, because reach currently enters the
model as a flat effect and it almost certainly is not one.

Note the prior: adding eight style features to the win model produced a log
loss change of **-0.0009, 95% CI [-0.0041, +0.0022], P(better) = 0.293** — no
detectable effect. Style data did not help predict *who wins*. These
interactions are a more targeted second attempt, and the honest base rate for
that kind of second attempt is low.

## What a null result means

That the style data belongs in the projections and the explanation panel, where
it already demonstrably works (strike-volume ranking Spearman 0.441 vs 0.283 for
a career average; takedown-probability AUC 0.742), and not in the win
probability. That is a perfectly good outcome and must be reported as clearly
as a positive one.

## Prohibited

- Adding hypotheses after seeing results, then presenting them as confirmatory
- Reporting the best of several specifications of the same hypothesis
- Re-using the 252-fight holdout after a failed test
- Dropping a hypothesis from the family to improve the correction for others
- Any "directionally encouraging" language for a result that failed correction

---

# Addendum: market-residual hypotheses

**Added 2026-09-17, after the residual model was fitted but before any of the
rules below were tested on data that could confirm them.**

## What was found

`residual.py` puts `logit(p_market)` in as a fixed offset, so each coefficient
answers "given the price, what does this feature still tell you?". Fitted on
2012 to 2024, walk-forward validated over six disjoint test blocks:

- Log loss beat the closing line in **6 of 6 folds** (sign test p ≈ 0.03).
  Pooled over 2,034 fights: 0.6080 vs 0.6114, gain **+0.0035, 95% CI
  [-0.0010, +0.0079], P(better) = 0.934**. Consistent direction; the interval
  still crosses zero.
- Eight of 22 coefficients had bootstrap CIs excluding zero — but that
  bootstrap is **in-sample**, on the training data, and the features are
  correlated. It does not establish out-of-sample edge.
- Flat-staking at every edge threshold gave positive ROI. Best single cut:
  favourites with >2% edge, n=484, **+7.20%, t = +2.13**. That is one of
  roughly twelve cuts examined, so uncorrected it is p≈0.03 and Bonferroni-
  corrected it is not significant.

The coefficients tell a coherent story, which is why this is worth pursuing
rather than dismissing. The market appears to **overreact to narrative
qualities and underreact to boring ones**:

| feature | beta given the market | reading |
|---|---|---|
| d_age | −0.158 | the line under-penalises age |
| d_sapm | −0.147 | under-penalises getting hit |
| d_kd15 | −0.123 | **over**-values knockdown power |
| d_log_exp | +0.098 | over-penalises veteran status |
| d_log_layoff | +0.068 | over-penalises ring rust |

## The frozen rule

Committed now, no further tuning permitted:

    features : d_age, d_sapm, d_kd15, d_log_exp, d_log_layoff
    model    : OffsetLogit(l2=25.0), offset = logit(devigged closing prob)
    scaler   : StandardScaler fitted on the training window only
    bet when : model_prob - vig_inclusive_implied_prob > 0.02
               AND vig_inclusive_implied_prob >= 0.50   (favourites only)
    stake    : flat, 1 unit
    success  : ROI > +2% over >=300 bets

## Why this cannot be tested on the reserved holdout

The 252-fight holdout (2026-04-04 to 2026-09-12) has **no odds** — the Kaggle
odds file stops at 2026-03-28. A market-edge hypothesis cannot be tested
without prices, so that holdout is useless for this particular question and
remains reserved for the style-interaction hypotheses above.

**The only valid test is forward paper-trading.** Record the closing line and
the model's probability for every fight before it happens, then evaluate after
300+ bets. Anything else is re-reading data the rule was built on.

## Expected outcome

Low. An apparent +7% ROI on a retrospective subset of a liquid market is far
more often multiple comparisons than edge, and the effect is concentrated in
exactly the price band where the [favourite-longshot analysis](#) showed the
market is already at break-even. Record the result either way.

## Additional prohibitions for this addendum

- No re-tuning of the threshold, the l2, or the feature list after seeing
  forward results. A changed rule is a new hypothesis with a fresh sample.
- No reporting of ROI on fewer than 300 bets.
- No switching to closing-line-value as the success metric after an ROI
  failure, or vice versa.
- Underdogs are excluded by the rule and stay excluded; their subset returned
  −1.90% and adding them back after the fact would be selection.

---

# Addendum 3: round-shape hypotheses (2026-09-18)

Registered before fitting. The round-by-round data has been in
`ufc_fight_stats.csv` all along — the loader aggregates it to fight totals and
throws the trajectory away. One summary of that trajectory (round 3 output
divided by round 1) was already tested and was null, so these are a second
attempt at the same underlying idea and the prior is correspondingly low.

Registering them matters here specifically because there are dozens of ways to
summarise a three-point curve. Fitting several and reporting the best is how a
null becomes a "finding".

| # | feature | predicted sign | rationale |
|---|---|---|---|
| R1 | first-round output relative to own career R1 rate | positive | fast starters vs slow starters is a real stylistic split |
| R2 | round-to-round variance of significant-strike rate | negative | erratic output implies inconsistency, not adaptability |
| R3 | late-round striking ACCURACY change (R3+ minus R1) | positive | accuracy decay should track fatigue better than volume, which is confounded by the opponent going into a shell |
| R4 | control-time share in R1 vs R3+ | positive | wrestlers who keep controlling late are the ones whose grappling actually holds |
| R5 | opponent's output decay when facing this fighter, career average | positive | a pressure fighter who drags others down is different from one who merely paces himself |

R3 and R5 are the interesting ones. Volume decay failed, and both of these
test whether a better-chosen summary of the same curve carries what volume did
not. R5 in particular is a defensive-pressure measure with no equivalent
anywhere in the current feature set.

Family of five, Benjamini-Hochberg at FDR 0.10, evaluated on the 2012-2026-03
window with the 252-fight holdout still reserved.

## Why the uploaded parquet files are NOT being used

`full_data_silver_plus.parquet` is the same round-level data already present in
`ufc_fight_stats.csv`, reshaped wide. Nothing new.

It also carries `f_1_fighter_SlpM`, `f_1_fighter_Str_Def`, `f_1_fighter_TD_Def`
and similar. Those are **career-aggregate values scraped from the fighter's
current UFCStats profile**, so on a 2015 fight row they describe a career that
includes fights through 2026. Using them as features is textbook temporal
leakage, and it is silent. Anyone building on that dataset should be told.

`ufc_features.parquet` is ~12,000 engineered columns: rolling win/loss/finish/
streak counts over windows of 3 through 10 previous fights, plus `f_1_ranking`
and `f_2_ranking`. Every one of those rolling features is something
`features.walk()` already computes under a tested no-leakage guarantee. Adopting
thousands of unverified equivalents would trade the single property that makes
this project trustworthy for convenience.

Rankings are the one genuinely new item. If pursued, the first check is whether
the rank is as-of-fight-date or the fighter's current rank — the latter is the
same leakage class as above, and `test_no_leakage` would not catch it because
the value arrives pre-computed from outside the walk.

---

# Addendum 4: the fortitude cluster (2026-09-18)

**Written after the features were built and the pipeline validated, before any
model was fitted to them.**

The idea: durability late in a fight may be a dimension markets underweight,
because it is invisible in the headline stats everyone quotes. Volume decay was
already tested alone and was null; this treats late-round resilience as a
cluster rather than a single ratio.

All six are career-to-date, accumulated inside `features.walk()`, and shrink
toward the NULL rather than toward a league mean — a fighter with two deep
rounds on record looks exactly average, which is what you want when the
quantity is a deviation. Round 1 versus rounds 3+; round 2 is excluded from both
sides as transitional.

| # | feature | predicted sign | rationale |
|---|---|---|---|
| F1 | `d_late_acc_delta` | positive | accuracy in rounds 3+ minus round 1. Cleaner than volume: an opponent retreating into a shell looks identical to a fighter tiring, but accuracy is not confounded that way |
| F2 | `d_late_volume_ret` | positive | output retention. Included despite the earlier null so the cluster is complete and the earlier result is re-tested under correction |
| F3 | `d_ctrl_retention` | positive | grapplers who still control late are the ones whose wrestling is real rather than a first-round burst |
| F4 | `d_induced_decay` | **negative** | how much this fighter's OPPONENTS fade. Below 1.0 means people wilt against him. Distinct from pacing himself, and has no equivalent anywhere in the feature set |
| F5 | `d_deep_experience` | positive | career rounds logged past round 2 — "championship rounds" experience, which commentary treats as real and which no stat page reports |
| F6 | `d_kd_recovery` | positive | share of knockdowns absorbed that did not end the fight. Heavily shrunk; most fighters have almost no sample |

## Analysis plan, fixed now

- Window 2012-01-01 to 2026-03-28. The 252-fight holdout stays reserved.
- Each feature added **individually** to the frozen 14-feature win model;
  coefficient sign and bootstrap CI recorded.
- The whole cluster added together, log-loss change bootstrapped against the
  frozen model.
- **Benjamini-Hochberg at FDR 0.10 across all six.** A feature counts only if
  it survives correction AND carries the predicted sign.
- Separately, the cluster is tested on the market residual (`residual.py`),
  since "markets underweight this" is the actual claim and it is a different
  test from "it predicts outcomes".

## Pre-stated expectation

Low, and the reason is specific. Every prior attempt to add information beyond
the core 14 has come back null: style features (−0.0009), margin-aware rating,
pace decay, clustering. Aggregate round-1 accuracy is 0.462 and late accuracy
0.458 — there is no league-wide fade for individual variation to sit inside.

F4 is the one worth watching. It measures something about the opponent rather
than the fighter, which is the only structurally new kind of information in
the cluster.

## Prohibited

- Reporting individual features that fail BH correction as "directionally
  encouraging"
- Dropping F2 or F6 from the family to improve the correction for the others
- Re-specifying a feature (different round split, different shrinkage) and
  re-testing without declaring it a new hypothesis

## Addendum 4: RESULT (2026-09-18)

**Zero of six supported.** Nothing survives Benjamini-Hochberg, and five of the
six carry the *wrong* sign.

| feature | predicted | beta | 95% CI | p | BH threshold | sign correct |
|---|---|---|---|---|---|---|
| `d_kd_recovery` | + | -0.0683 | [-0.143, -0.003] | .045 | .0167 | no |
| `d_late_volume_ret` | + | -0.0487 | [-0.100, +0.007] | .090 | .0333 | no |
| `d_deep_experience` | + | +0.0962 | [-0.017, +0.195] | .105 | .0500 | **yes** |
| `d_ctrl_retention` | + | -0.0439 | [-0.096, +0.015] | .115 | .0667 | no |
| `d_late_acc_delta` | + | -0.0260 | [-0.081, +0.023] | .245 | .0833 | no |
| `d_induced_decay` | - | +0.0277 | [-0.020, +0.079] | .335 | .1000 | no |

Whole cluster added to the frozen model: accuracy **67.42% vs 67.54%**, log loss
**0.6215 vs 0.6199**, gain **-0.0016, 95% CI [-0.0052, +0.0019], P(better) =
0.185**. It makes the model slightly worse.

`d_deep_experience` is the only one with the predicted sign and it does not
clear its threshold (p = .105 against .050). Per the prohibitions above it is
not reported as encouraging, and note its uncorrected p-value would not have
survived either.

`d_kd_recovery` is nominally the strongest and points the *wrong way* — fighters
who have survived knockdowns do slightly worse, not better. That is more
consistent with "having been knocked down is bad news about your chin" than
with recovery being evidence of toughness, and it aligns with `d_ko_loss_rate`
already carrying a negative weight in the frozen model.

**Conclusion: fortitude, as measurable from round-level UFCStats data, does not
predict who wins.** The earlier pace-decay null was not a bad choice of
summary; the underlying dimension appears to be absent. Aggregate round-1
accuracy is 0.462 and late accuracy 0.458, so there was little league-wide fade
for individual variation to live inside.

The features stay in the codebase and out of `WIN_FEATURES`. They are
legitimate descriptive content for the site — "his opponents' output drops 12%
after round two" is a real, checkable sentence about a fighter — but they are
not predictive.

The market-residual half of this plan was not run. With the cluster failing to
predict outcomes at all, testing whether markets underprice it would be testing
whether they underprice noise.

---

# Addendum 6: competing-risks hazard model (2026-09-18)

Built as the one remaining principled structure: a fight ending is a race
between four hazards (each fighter by KO or submission) against the clock, so
one fit should produce method, round and winner coherently instead of three
classifiers that can contradict each other.

**It works structurally and does not beat what it replaced.**

| | coherent hazard | independent classifiers | market |
|---|---|---|---|
| KO/TKO AUC | .6617 | **.6686** | — |
| submission AUC | **.6625** | .6477 | — |
| decision AUC | .6077 | **.6234** | — |
| KO/TKO Brier (market subset) | **.1873** | — | .1922 |
| submission Brier (market subset) | .1319 | — | **.1216** |
| decision Brier (market subset) | .2533 | — | **.2363** |

Who wins: hazard roll-up 65.02% / .7073 AUC versus the direct logistic at
66.01% / .7153. Averaging the two is marginally the best of the three
(66.26%, .7164, log loss .6206), which is a genuine if small ensemble gain.

Calibration after fitting two hazard multipliers on a validation slice:
P(decision) .487 vs .525 actual, P(KO) .307 vs .303, P(sub) .205 vs .172.

**What it buys, which the metrics do not show.** The independent classifiers
sum to a mean of 0.9619 with a range of 0.584 to 1.313 — some fights get a
method distribution summing to 131%. The hazard model sums to 1.000000 by
construction, and produces P(ends in round N) and expected duration as
by-products of the same curve. For a site that displays these numbers, internal
consistency is worth more than a thousandth of Brier.

**A bug worth recording.** The first version rolled the survival curve over
each fight's OBSERVED duration rather than its SCHEDULED duration. A
first-round knockout then had one interval to decay over and came out as the
likeliest decision on the card: P(decision) scored **AUC 0.19**, reliably
backwards. It is the survival analogue of temporal leakage — using the outcome
to decide how far to integrate — and `test_no_leakage` would not catch it
because it lives in the prediction step, not the feature build. `expand()` now
takes an explicit `full` flag with the distinction documented at the call site.

**Conclusion.** Adopt it for the product, not for accuracy. It replaces
`props.py` as the source of method and round numbers on the site because those
numbers will be coherent. The win probability stays with the direct logistic,
or the average of the two if the small ensemble gain holds up on more data.
