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

---

# Addendum 7: weight audit and two ablations (2026-09-19)

Prompted by a reasonable question — why does strength of schedule carry so
much weight?

## What the weights actually are

Drop-one ablation on the held-out block. `drop_ll > 0` means removing the
feature makes the model worse.

| feature | beta | 95% CI | drop_ll | drop_acc |
|---|---|---|---|---|
| d_age | -0.389 | [-0.45,-0.33] | +0.0178 | **-3.98** |
| d_adj_slpm | +0.242 | [+0.11,+0.37] | +0.0009 | -0.72 |
| d_sapm | -0.196 | [-0.26,-0.13] | +0.0062 | -0.24 |
| d_ko_loss_rate | -0.192 | [-0.36,-0.03] | +0.0001 | +0.36 |
| d_elo | +0.191 | [+0.11,+0.25] | +0.0055 | -1.69 |
| **d_opp_elo** | **+0.167** | [+0.11,+0.22] | **+0.0058** | **-1.09** |
| d_str_def | +0.156 | [+0.10,+0.22] | -0.0009 | -0.24 |
| grapple_edge | +0.149 | [+0.10,+0.21] | +0.0033 | -1.45 |
| ko_edge | -0.126 | [-0.31,+0.07] | 0.0000 | 0.00 |
| d_reach | +0.109 | [+0.06,+0.16] | -0.0003 | 0.00 |
| d_str_acc | +0.086 | [+0.04,+0.14] | +0.0010 | -0.48 |
| d_log_exp | -0.075 | [-0.14,-0.02] | +0.0027 | -0.84 |
| d_log_layoff | +0.031 | [-0.02,+0.09] | -0.0013 | 0.00 |
| sub_edge | -0.011 | [-0.06,+0.04] | -0.0002 | -0.12 |

**Strength of schedule is legitimate.** It correlates only **0.133** with Elo —
Elo measures how well you have done, `d_opp_elo` measures who you did it
against, and a fighter can post a strong record against weak opposition.
Dropping it costs 1.09 accuracy points, third worst of the fourteen.

Age remains dominant: removing it costs **4 accuracy points**, more than four
times any other feature.

## Ablation 1: pruning. FAILED, and the failure is the lesson.

Four features have CIs crossing zero and ablations suggesting they are dead
weight. Dropping ko_edge, d_log_layoff and sub_edge scored better on the test
block on all three metrics — 67.55% vs 67.31%, log loss 0.6194 vs 0.6208.

**That was test-set overfitting.** The features were chosen by looking at the
test block. Re-run honestly — backward elimination judged only on a validation
slice, then confirmed once on test — validation selected a *different* trio
(dropping `d_sapm` instead of `ko_edge`) and the result reversed: log loss
**-0.0044, 95% CI [-0.0090, +0.0002], P(better) = 0.032**, i.e. almost
certainly worse.

Two conclusions. The 14 features stay exactly as they are. And at ~3,300
training fights, feature selection does not generalise — the sample cannot
distinguish a dead feature from a quiet one.

## Ablation 2: recency weighting. NULL.

The state accumulators weight a 2014 fight identically to a 2026 one, which
was listed as a known gap. Tested by decaying every accumulator by
exp(-lambda x years) at each update and exposing the decayed rates as extra
differentials.

Half-life chosen on validation (which picked 3.0 years), confirmed on test:
gain **+0.0000, 95% CI [-0.0052, +0.0046], P(better) = 0.518**. Accuracy fell
slightly, AUC rose slightly. Nothing.

Note the shorter half-lives were *negative* on validation (-0.0019 at 9 months,
-0.0010 at 1 year). Recent form carries no information the career average
lacks, and weighting it harder actively hurts. The shrinkage already in
`state.py` appears to be doing this job.

## Addendum 1: RESULT (2026-09-19)

**Zero of nine supported.** Smallest p-value was 0.060 against a BH threshold
of 0.011, and six of the nine carried the wrong sign.

| hypothesis | predicted | beta | p | sign ok |
|---|---|---|---|---|
| H1 leg-kicks x stance mismatch | + | -0.0513 | .060 | no |
| H5 power x chin | + | +0.0395 | .147 | yes |
| H4 body work x opponent decay | + | -0.0393 | .213 | no |
| H3 clinch/ground x takedown defence | - | -0.0345 | .293 | yes |
| H8 takedowns x opponent ground game | - | +0.0282 | .353 | no |
| H7 reach x opponent clinch share | - | +0.0789 | .400 | no |
| H6 reach x own distance share | + | -0.1495 | .513 | no |
| H2 leg-kicks x takedown defence | + | +0.0037 | .853 | yes |
| H9 age x pace | - | +0.0150 | .987 | no |

H6 and H7 were named in advance as the most interesting — reach entering the
model as a flat effect "almost certainly isn't one". Both came back with the
wrong sign and p > 0.4. **Reach is a flat effect.** That is a real answer to a
reasonable question, arrived at the only way it could be.

---

# Addendum 8: five angles from fields already in the corpus (2026-09-19)

Registered before fitting. These are not new formulas over existing features —
that avenue is exhausted — but **measurements never extracted**, all from
columns already downloaded and currently unused.

| # | measurement | source | predicted sign | rationale |
|---|---|---|---|---|
| V1 | small-cage venue (UFC Apex, Las Vegas) x own pressure style | `LOCATION` | positive for pressure fighters | the Apex cage is 25ft against the standard 30ft; less room to circle should favour forward pressure and raise finish rates |
| V2 | altitude of venue x own cardio proxy | `LOCATION` + lookup (Denver, Mexico City, Salt Lake, Calgary) | negative for high-output fighters | thin air punishes pace; only 21 events, so power is low and a null is uninformative |
| V3 | referee identity x fight duration and method | `REFEREE`, 249 distinct, 99.7% populated | referees with early-stoppage tendencies raise P(KO/TKO) | a genuinely unacknowledged input: the third person in the cage decides when a fight ends |
| V4 | moving up or down a weight class | `WEIGHTCLASS` history per fighter | negative for moving up | a real and widely discussed effect that appears in no stat line |
| V5 | career mileage: cumulative minutes fought and strikes absorbed | existing accumulators | negative | wear distinct from age — two 34-year-olds with 20 and 60 career rounds are not the same fighter |

V3 and V5 are the ones worth watching. V3 because referee assignment is
knowable before a fight and is plausibly priced by nobody, and it targets the
**method and round props** rather than the winner — which is where a coherent
hazard model could actually use it. V5 because age is the single strongest
feature in the model and mileage is the mechanism people assume is behind it;
if mileage carries signal beyond age, that is a genuine decomposition.

Family of five, Benjamini-Hochberg at FDR 0.10. Winner hypotheses tested on
the 2012 to 2026-03 window; V3 tested against method rather than outcome. The
252-fight holdout stays reserved.

**Prior: low, as always.** Every previous family has come back null. V2 is
underpowered by construction and is included for completeness, not hope.

## Addendum 8: RESULT (2026-09-19)

**Zero of five supported.** BH thresholds run 0.025 to 0.100; the smallest
p-value was 0.140.

| # | measurement | predicted | beta | p | sign ok |
|---|---|---|---|---|---|
| V5 | career mileage | - | -0.3241 | .140 | **yes** |
| V4 | weight-class move | - | +0.0246 | .393 | no |
| V1 | Apex cage x pressure | + | +0.0144 | .567 | yes |
| V2 | altitude x pace | - | +0.0116 | .593 | no |

**V3, referee stoppage tendency → P(KO/TKO): AUC 0.523** on 1,084 fights.
Referees' career KO rates genuinely range from 0.160 to 0.437, a wide spread —
but it does not transfer to the next fight. Either the spread is the fighters
they happen to be assigned rather than the referee, or stoppage style matters
less than the difference between a durable and a fragile chin. This was the
most promising of the five and it is a clean null.

V5 is the near-miss: correct sign, largest coefficient in the family, p = 0.14.
Mileage may carry a little signal beyond age, but not at this sample size, and
per the standing prohibitions it is not reported as encouraging. If anything is
revisited later it should be this one, with a cleaner mileage measure (true
career rounds rather than the `log_exp` proxy used here).

## Standing conclusion after eight families

Tested and null: style shares, margin-aware ratings, cardio, fight-type
clustering, the fortitude cluster, nine style interactions, Bradley-Terry,
Pythagorean/log5, recency weighting, feature pruning, and now venue, altitude,
referee, weight-class moves and mileage.

**Nothing has beaten the 14 features.** The one result that has ever pointed
the right way consistently is the market-residual model (6 of 6 folds,
P(better) = 0.934), which remains unconfirmed and untestable without forward
odds capture. The binding constraint is not ideas — it is ~6.5 recorded fights
per athlete and one bit of outcome per fight.

---

# Addendum 9: the distance market (2026-09-20)

**Registered before any Polymarket price has been seen.** The fetcher is built
and classifies distance markets, but has not yet been run against live data.
Writing the rule after seeing the first quotes would make this retrospective,
and the whole point of the venue is that it is a fresh test.

## Why this market and not the others

Method props are closed — the market beat us on all three at P(model better)
= 0.000, by a wider margin than on the moneyline. Distance is different in
three ways: it is two-way rather than six-way, so the margin is far smaller;
the competing-risks model prices it directly and coherently; and on Polymarket
the cost is a one- or two-cent spread rather than a bookmaker's overround.

## A correction that had to come first

The raw hazard roll-up predicted P(decision) = 0.487 against an actual 0.525.
That is not miscalibration — it is drift. **The UFC decision rate moved 12.3
points across recent years** (55% in 2019, 44% so far in 2026), and a Platt
correction fitted on a validation slice whose actual rate was 47.9% still
predicted 47.7% on a block where it was 52.5%.

So the rule uses a **rolling 300-fight base-rate anchor**, frozen in
`distance_model.json`: the logit is shifted so the trailing window matches its
own observed rate. On the test block that moved predictions to 0.529 against
0.525 actual. Discrimination is unchanged (AUC .608 to .613) — this fixes the
level only.

## The frozen rule

    probability : hazard model P(decision), anchored to the trailing 300 fights
    venue       : Polymarket distance markets only (spread <= 6c, depth >= $250)
    bet when    : |anchored P(decision) - ask| > 0.05
    stake       : flat 1 unit
    success     : ROI > +2% over >= 200 settled bets

Both sides are permitted. There is no favourites-only restriction because the
favourite-longshot analysis was measured on sportsbook moneylines and does not
transfer to a prediction market.

## Pre-stated expectation: lower than when I proposed this

I suggested distance as "the one candidate genuinely worth testing" before
measuring it. Having measured it, two things are worse than implied.
Discrimination is weak — **AUC 0.608**, barely above the 0.6 that separates a
useful signal from a decorative one. And the base rate is unstable by 12
points, which is several times any edge we could plausibly claim, so an
apparent edge over a few months is at least as likely to be era drift as skill.

That is an argument for the anchor and for a long horizon, not for abandoning
the test. But the honest prior here is low, and lower than I first said.

## Prohibited

- Reading the rule's result before 200 settled bets
- Adjusting the 300-fight window or the 0.05 threshold after seeing prices
- Pooling Polymarket distance results with the sportsbook moneyline ledger
- Treating a positive result as established without checking whether the
  decision rate drifted in the same direction over the test window

---

# Addendum 10: the conditional base-rate panel (2026-09-20)

A display feature, not a hypothesis test — but it needs registering for a
different reason than the others. The danger is not false discovery, it is
**selective display**: with a dozen candidate conditions, showing whichever
looks strongest turns a lookup table into a machine for rendering noise
attractively.

So this fixes the DISPLAY LIST. The panel shows every condition below, always,
including the ones that turn out flat. A condition is never dropped for being
boring and never added for being interesting.

## What the panel is

For each condition: the base rate, the rate within each quartile, the lift,
n, and a 95% interval. Descriptive counts from the corpus, not model output.
Nothing here is a prediction; it is what happened in past fights that looked
like this one.

## Conditions, fixed now

Each is included because there is a stated mechanism, not because it measured
well. Five were run before this was written and are marked SEEN; they are
reported as exploratory and re-validated on the reserved holdout.

| # | condition | outcome | mechanism | status |
|---|---|---|---|---|
| C1 | own opponent-adjusted takedown rate, quartiles | lands a takedown | direct: the rate IS the propensity | SEEN (.238 to .630) |
| C2 | opponent's takedown defence, quartiles | lands a takedown | the thing standing in the way | SEEN (.495 to .386) |
| C3 | own knockdown rate, quartiles | scores a knockdown | direct | SEEN (.114 to .294) |
| C4 | combined knockdown rate, quartiles | ends inside distance | two heavy hitters end fights | SEEN (.410 to .588) |
| C5 | combined control share, quartiles | ends inside distance | grappling-heavy fights grind out | SEEN (.480 to .486, FLAT) |
| C6 | reach differential, quartiles | lands a takedown | shooting under a longer fighter | new |
| C7 | combined strike volume, quartiles | ends inside distance | pace as a proxy for damage | new |
| C8 | age differential, quartiles | ends inside distance | the older fighter as the one who breaks | new |
| C9 | combined submission-attempt rate, quartiles | goes the distance | grapplers hunting finishes | new |
| C10 | own clinch+ground strike share, quartiles | lands a takedown | position-dependent offense needs the takedown | new |

C5 stays in the panel precisely because it is flat. A conditional-rate display
that only ever shows strong relationships is indistinguishable from one that
selects them, and the reader has no way to tell. The null row is the evidence
that the list was fixed in advance.

## Display rules

- Every condition rendered, every quartile, always.
- n and a 95% interval on every cell. A quartile under 200 fights is greyed.
- Never ranked by lift, never truncated to "top" conditions.
- Labelled as historical frequencies, not predictions, and never combined into
  a single "regime" score. Compressing a dozen conditions into one bar means
  choosing which dominates, which is selection by another name.

## Explicitly NOT built

A "dominant fighting style" indicator tied to winning. Style features were
tested against the win model and came back at **-0.0009 log loss, 95% CI
[-0.0041, +0.0022]** (addendum, style cluster). Showing a style-to-wins bar
would have the site contradicting its own recorded result.

## Success criterion

There is none, because nothing is being claimed. The panel is correct if its
numbers match the corpus and the holdout reproduces the SEEN rows within their
intervals. If a SEEN row fails to reproduce, it is removed and the failure
recorded here.

---

# Addendum 11: scoring conventions borrowed from other combat sports (2026-09-20)

Registered before fitting. The question was whether wrestling, boxing, Muay
Thai or BJJ analytics offer anything retrofittable. Most of what those sports
use is either the same thing under another name (CompuBox punch counts are
UFCStats significant strikes) or needs data that does not exist here
(wrestling's scramble/transition models need positional tracking; boxing's
round-scoring models need the fight to have happened).

Two conventions ARE transferable, because both re-weight inputs we already
record rather than requiring new measurement.

| # | idea | source | predicted sign | rationale |
|---|---|---|---|---|
| S1 | **damage-weighted striking**: head 1.0, body 0.6, leg 0.4, instead of counting every significant strike equally | boxing and Muay Thai both score effect over volume; a jab to the arm and a head kick are one strike each to UFCStats | positive | our striking differential treats a leg kick and a head strike identically, which no combat sport's scoring does |
| S2 | **active vs stalling control**: ground strikes landed per second of control time, and control differential weighted by it | IBJJF scores positional advance, not time held; judging distinguishes damage from stalling | positive | control time is currently one undifferentiated number, so a fighter smothering for four minutes scores the same as one passing and striking |

## Fixed weights, not fitted ones

S1's weights come from scoring convention, not from the corpus. Fitting them
would rediscover whatever the data already says and guarantee a fit — the
whole point is to test whether an *external* convention carries information
our equal-weight version misses.

## Analysis plan

Each metric replaces (not supplements) its equal-weight counterpart in the
frozen 14-feature win model — S1 swaps `d_adj_slpm`, S2 swaps `d_ctrl_share`
where it appears via `grapple_edge`. Both are also tested as additions. Window
2012 to 2026-03, walk-forward, bootstrap CI on the log-loss change.

Separately, both are tested against the **projection** targets (strike volume,
control time, takedown probability), because that is where style information
has previously helped and the win model has rejected everything.

Benjamini-Hochberg at FDR 0.10 across the family of four tests (2 metrics x
{win model, projections}).

## Pre-stated expectation

Low for the win model, higher for the projections. Eight families have now
come back null against the winner, including the style shares these weights
are built from. But style shares DID help projections (strike-volume ranking
Spearman .441 against .283), and S1/S2 are sharper versions of exactly that
information. If they land anywhere it is there.

## Addendum 11: RESULT (2026-09-20)

**Zero of four supported.** Nothing approaches the BH thresholds (.025 to .10).

### Win model

| test | accuracy | log loss | gain | 95% CI | P(better) |
|---|---|---|---|---|---|
| frozen 14 | 67.54% | .6199 | — | — | — |
| S1 damage-weighted, added | 67.54% | .6198 | +0.0000 | [-0.0006, +0.0007] | .544 |
| S1 **swapped** for `d_adj_slpm` | 68.17% | .6216 | -0.0017 | [-0.0043, +0.0009] | .100 |
| S2 active control, added | 67.42% | .6203 | -0.0004 | [-0.0009, +0.0001] | .056 |
| both added | 67.54% | .6201 | -0.0003 | [-0.0010, +0.0005] | .260 |

The swap is the interesting row and a trap worth naming. Replacing equal-weight
striking with damage-weighted striking **raised accuracy to 68.17%**, the best
figure this model has produced — while log loss got *worse* (-0.0017, CI
crossing zero). Accuracy moved six correct calls out of 798; log loss says the
probabilities degraded. Reporting the accuracy alone would be the single most
misleading thing available in this dataset, which is why the pre-registered
metric is log loss.

### Projections

| target | base | with S1+S2 |
|---|---|---|
| strike volume | Spearman .3855 | .3922 |
| control time | Spearman .4394 | **.4477** (r2 .2334 to .2425) |
| takedown | AUC .7405 | .7372 |

Control time improves slightly and takedown gets slightly worse. Neither is
close to significant at these sample sizes, and two of three moving in
opposite directions is what noise looks like.

### Conclusion

Boxing and Muay Thai score effect over volume, and BJJ scores positional
advance over time held. Both conventions are real and both are sound reasoning
about the sport. Neither carries information beyond what equal-weight counting
already gives this model.

**Nine families now.** The consistent finding across all of them is that the
constraint is not how the inputs are weighted but how few fights each athlete
has: ~6.5 recorded bouts, one bit of outcome each. Re-weighting cannot create
information that was never recorded.

---

# Addendum 12: formulas borrowed from other fields (2026-09-20)

Registered before fitting. The request was to try every possible equation, and
the honest version of that is a fixed family tested together under correction
— testing fifty formulas at p < 0.05 and reporting the winners guarantees two
or three spurious "discoveries" by arithmetic alone.

Worth stating first: a gradient booster already represents every monotone
transform, threshold and interaction of these inputs simultaneously, and it
LOST to plain logistic regression. So the prior that some square root or
exponent unlocks the data is low. These are included anyway because each has a
specific structural reason from its own field.

| # | formula | field | form | rationale |
|---|---|---|---|---|
| F1 | log-ratio striking | finance (log returns) | log(slpm_a / slpm_b) | differences treat 1-vs-2 like 10-vs-11; ratios are scale-invariant |
| F2 | log-ratio takedowns | finance | log(td_a / td_b) | same, for the grappling axis |
| F3 | ape index | anthropometry | (reach - height)_a - (reach - height)_b | wingspan relative to frame, a real combat-sports measure we never built |
| F4 | performance volatility | finance (volatility) | sd of per-fight strike output, differenced | a consistent fighter and an erratic one can share a mean |
| F5 | Sharpe-style consistency | finance (Sharpe ratio) | mean output / sd output | return per unit of risk |
| F6 | method entropy | information theory | Shannon entropy of KO/SUB/DEC wins | a fighter who wins every way is harder to prepare for |
| F7 | Gompertz age decline | actuarial / biology | exp(0.09 x (age - 30)) | mortality risk rises exponentially with age; our strongest feature is entered linearly |
| F8 | sqrt experience | diminishing returns | sqrt(n_fights) | the 20th fight teaches less than the 2nd |
| F9 | kinetic power | physics (KE = mv^2) | kd15 x weight_index^2 | striking force should scale with mass |
| F10 | inverse-square reach | physics | sign(d) x d^2 | a reach edge may matter nonlinearly with distance |

Each added individually to the frozen 14. Benjamini-Hochberg at FDR 0.10
across all ten. Supported only if it survives correction AND improves log loss
out of sample. Accuracy is not a criterion — addendum 11 showed accuracy rising
while probabilities degraded.

F7 is the one with the strongest prior. Age is the single most important
feature in the model, and the Gompertz law is one of the best-replicated
regularities in biology. If decline really accelerates, a linear age term is
misspecified and this should show it.

## Addendum 12: RESULT (2026-09-20)

**Zero of ten supported.**

| formula | gain | 95% CI | p | BH |
|---|---|---|---|---|
| kinetic power (KE = mv^2) | **-0.0013** | [-0.0023, -0.0004] | .012 | .010 |
| Gompertz age | +0.0008 | [-0.0001, +0.0017] | .077 | .020 |
| Sharpe consistency | -0.0022 | [-0.0055, +0.0007] | .165 | .030 |
| method entropy | -0.0010 | [-0.0026, +0.0005] | .177 | .040 |
| sqrt experience | +0.0027 | [-0.0017, +0.0069] | .216 | .050 |
| volatility | -0.0023 | [-0.0061, +0.0016] | .232 | .060 |
| inverse-square reach | +0.0007 | [-0.0006, +0.0021] | .303 | .070 |
| log-ratio takedowns | +0.0007 | [-0.0013, +0.0026] | .501 | .080 |
| ape index | +0.0001 | [-0.0001, +0.0002] | .505 | .090 |
| log-ratio striking | +0.0000 | [-0.0001, +0.0002] | .645 | .100 |

Kinetic power is the instructive row: the **smallest p-value in the family and
a significantly NEGATIVE effect.** A "try every formula and keep what is
significant" search would have promoted a transform that makes predictions
worse. Gompertz, the strongest prior, points the right way and misses its
threshold.

---

# Addendum 13: the opening line, EXPLORATORY (2026-09-20)

**This is not a confirmatory result and must not be reported as one.** It was
found after, and because of, a descriptive observation, with thresholds chosen
on the same data. It is registered now, frozen, so that the forward ledger can
test it honestly.

## What prompted it

On 315 bouts with repeated snapshots, the closing line beats the opening line
substantially: log loss **0.5974 at open, 0.5670 at close**, AUC .7497 to .7781.
The market genuinely learns between open and close. Drift adds nothing BEYOND
the close (+0.0006, CI [-0.013, +0.013]), so there is no "follow the steam"
edge.

That reframes the question. The market beats the model at the close. It may
not at the OPEN.

## What was found

On 209 held-out bouts, model trained only on fights before 2025-03:

- correlation between (model minus opening price) and the subsequent line
  move: **Spearman +0.186, p = 0.007**; Pearson +0.134, p = 0.053
- where the model disagreed with the open by 8+ points (113 bouts), the line
  then moved toward the model **59.3%** of the time, against 50% for no skill
- betting the model's side at the open whenever it disagreed by 2+ points:
  183 bets, **mean CLV +1.21 points, 55.7% positive**

The interpretation, if it holds: the model is right but early. It reads the
same public statistics the market eventually prices, and the market takes
the week to get there. That is a coherent and well-documented pattern in
sports betting — opening lines are softer, and sharp money moves them.

## Why this is the most promising lead in the project, and why to distrust it

Promising, because it is the first result that points at a mechanism rather
than a coefficient, and positive CLV is the metric professional bettors
actually use. Every previous family tried to beat the close and failed. This
does not try to.

Distrusted, because: one exploratory analysis among many run today; thresholds
of 2 and 8 points chosen on this data; 209 bouts is small; and the p-value
does not survive any honest accounting of how many analyses preceded it.

## The frozen rule, for forward testing only

    model      : the frozen 14-feature win model
    price      : the FIRST capture in the ledger for each bout (proxy for open)
    bet when   : |model - open| >= 0.02, on the model's side
    metric     : CLV = closing price - price at first capture, on the backed side
    success    : mean CLV > 0 with a 95% interval excluding zero, n >= 150 bets

The ledger already records multiple snapshots per bout, so no new capture
code is needed — only the rule applied to rows it is already writing.

## Prohibited

- Reporting the 1.21-point figure as an edge. It is a hypothesis.
- Tuning the 2-point threshold on forward data.
- Combining this with the residual-rule ledger; they test different claims.

## Addendum 10: display revision (2026-09-21)

Layout only; no condition added, dropped, reordered or re-measured.

The panel was first drawn one card per condition with the OUTCOME as each
card's heading, so "Lands a takedown" appeared four times and "Ends inside the
distance" four times, reading as different things. It is now grouped by
outcome — takedown (C1, C2, C6, C10), knockdown (C3), finish (C4, C5, C7, C8,
C9) — one row per registered condition, in registered order within each group.

C9 was registered against "goes the distance", which is exactly one minus
"ends inside the distance". It is displayed as its complement so the finish
question has one home. Every cell is the same data inverted; significance and
intervals are unchanged. The underlying `site/baserates.json` still records it
as registered.

Rows are labelled "clear pattern" (3-4 quarters differ from the base rate),
"weak pattern" (1-2) or "no pattern" (0). That is a description of the
significance counts already computed, not a new threshold, and flat rows are
still shown.

---

# Addendum 14: the opponent's side, and simple formulas per prop (2026-09-21)

Registered before measuring.

## C11 and C12: the knockdown question had only one side

Takedowns are shown from both corners — the fighter's rate and the defence in
front of him. Knockdowns were shown from one. The knockdown projection already
uses the opponent's durability (`opp_kd_against15`, `opp_sapm`,
`opp_str_def`); the panel simply never displayed it.

| # | condition | outcome | mechanism |
|---|---|---|---|
| C11 | opponent's knockdowns absorbed per 15 min | scores a knockdown | a chin that has gone before goes again |
| C12 | opponent's strikes absorbed per minute | scores a knockdown | a hittable opponent gets hit cleanly more often |

Added to the fixed display list under the same rules as addendum 10: always
shown, flat or not.

## Can a short formula replace the gradient booster for each prop?

The panel is a one-variable-at-a-time model. The projection models are the
many-variable version of the same thing. If a logistic regression on only the
registered conditions for a prop matches the booster, the site can show the
formula itself — "this number comes from his takedown rate and the defence in
front of him" — which is exactly the checkable-service goal.

    takedown   F-TD : own_adj_td15, opp_td_def, reach_diff, own_clinch+ground
    knockdown  F-KD : own_kd15, opp_kd_against15, opp_sapm

Compared against the current booster on the same held-out fighter-fights.
Brier, AUC and calibration, with a bootstrap interval on the Brier difference.

**Decision rule, fixed now:** if the formula's Brier is within 0.002 of the
booster's (or better), the site adopts the formula for that prop, because a
number a reader can verify is worth more than a marginally sharper one they
cannot. If it is worse by more than 0.002, the booster stays.

Pre-stated expectation: close for takedowns, where one input dominates;
further for knockdowns, where the booster may be using interactions.

## Addendum 14: RESULT (2026-09-21)

### C11, C12

| condition | Q1 | Q2 | Q3 | Q4 | verdict |
|---|---|---|---|---|---|
| C11 opponent's knockdowns absorbed | 14% | 18% | 22% | 24% | clear pattern |
| C12 opponent's strikes absorbed | 18% | 21% | 19% | 20% | no pattern |

The chin carries information; volume absorbed does not. Being hit a lot does
not predict being knocked down — having been knocked down does. Both rows now
render in the knockdown group, C12 dimmed as flat.

### Formula vs booster — and a comparison error caught before acting

The first comparison used a less regularised booster than production and
showed the knockdown formula clearly ahead (-0.0055, CI excluding zero). Re-run
against the **exact production settings**, the gap closed to a tie. The
decision was made on the fair comparison:

| prop | production booster | formula | difference | CI | decision |
|---|---|---|---|---|---|
| takedown (4 inputs) | .2008, AUC .742, slope 1.01 | .2109, AUC .723 | +0.0102 | [+0.0038, +0.0161] | **keep booster** |
| knockdown (3 inputs) | .1445, AUC .668, slope 0.76 | .1432, AUC .668 | -0.0012 | [-0.0050, +0.0025] | **adopt formula** |

Knockdowns: statistically indistinguishable, identical AUC, and the booster's
calibration slope of 0.76 says it was overconfident at the top (said 47%,
happened 41%). Under the fixed rule the formula wins the tie. Fitted weights:
**+0.38 x own knockdown rate, +0.23 x opponent's knockdowns absorbed, -0.01 x
opponent's strikes absorbed**, per standard deviation.

Takedowns: the booster is genuinely better and near-perfectly calibrated
(slope 1.01). Four clear single-variable patterns do not add up to a good
formula, because they overlap — a strong wrestler tends to have both a high
takedown rate and a high clinch share — and the booster models that overlap.

So "a formula per prop" is the right question, answered one prop at a time:
sometimes the short version is as good and should ship because it can be
checked, and sometimes it is not.

---

# Addendum 15: a short formula for "ends inside the distance" (2026-09-21)

Registered before measuring, same rule as addendum 14.

## Formula

    F-ITD : C4 combined knockdown rate, C5 combined control share,
            C7 combined striking pace, C8 age gap, C9 combined submission
            attempts, + scheduled rounds (3 or 5)

Scheduled rounds is not one of the registered conditions; it is included
because it is structural, not a pattern — a five-round fight has two more
rounds in which to end, and any honest finish formula has to know that. It is
declared here so it is not an after-the-fact addition.

## Comparison

Against the production competing-risks model's P(finish) = 1 - P(decision),
trained, hazard-calibrated and tested on the same split it uses in production.
Brier, AUC and calibration slope on the same held-out fights, bootstrap
interval on the Brier difference. Both compared raw; the level drift noted in
addendum 9 affects both equally and is not corrected for either.

## Decision rule, fixed now

Formula adopted if its Brier is within 0.002 of the survival model's, or
better.

## How a win would be applied, fixed now

The survival model's outputs must keep summing to 100%. So the formula would
set only the LEVEL: P(finish) comes from the formula, and the survival model's
split of that finish across method and round is kept and rescaled to it.

    P(method m, round r) = P_formula(finish) x P_survival(m, r | finish)

Round and method probabilities stay coherent; only how likely a finish is at
all changes.

## Pre-stated expectation

Survival model favoured. It sees the full 14-feature fighter comparison and
models time directly; the formula sees five sums, three of which measured flat
in the base-rate panel. A tie would be a surprise.

## Addendum 15: RESULT (2026-09-21)

**Formula adopted, and against the pre-stated expectation.**

| | Brier | AUC | calibration slope | mean said |
|---|---|---|---|---|
| survival model P(finish) | .2487 | .608 | **0.42** | 51.3% |
| 6-input formula | **.2420** | .598 | 0.94 | 47.4% |

Held out: 812 fights, actual finish rate 47.5%. Difference -0.0068, 95% CI
[-0.0164, +0.0030]; within the 0.002 rule, so adopted.

The finding underneath matters more than the swap: **the survival model's
finish probabilities were badly overconfident.** Fights it put at 74% finished
60% of the time; at 55%, 45%. It ranks fights marginally better (AUC .608 vs
.598) but spreads them far too wide. The formula's bands line up within about a
point everywhere. Every "ends inside the distance", round and totals number the
site had shown inherited that overconfidence.

Weights: +0.31 combined knockdown rate, +0.21 combined submission attempts,
+0.12 five rounds, -0.09 pace, +0.04 age gap, -0.01 control. Consistent with the
base-rate panel: the two rows with a pattern carry the formula, the three flat
rows carry almost nothing.

Applied as registered. The formula sets P(finish); the survival model's split
across method, round and time is rescaled to it. Checked on the live card:
methods, rounds and finish sum identically on every bout, and round totals
remain monotone.

### Consequences for other records

- Addendum 9's frozen distance rule is defined on the hazard model's P(decision)
  with a rolling anchor. It is unaffected: the forward test keeps its
  registered probability; only the displayed number changed.
- From 2026-09-21, scorecard claims for inside-the-distance, decision, method,
  round and totals are the rescaled numbers. Earlier logged claims are from the
  raw survival model. The switch date separates them.

---

# Addendum 16: weight class (2026-09-21)

Registered before measuring anything beyond the list of division labels.

## Why it might matter to the model, not just the display

Fighter statistics are shrunk toward LEAGUE-WIDE means before they are used.
A heavyweight with three recorded fights has his knockdown rate pulled toward
an average that includes flyweights, and a flyweight's toward one that
includes heavyweights. If divisions differ a lot, the shrinkage target is
wrong at both ends, and division should carry information the fighters' own
numbers cannot — most of all for fighters with few fights.

## Encoding, fixed now

    wt     : division weight limit in pounds (115 strawweight ... 265 heavyweight),
             read from the division name; title bouts use their division
    women  : 1 for women's divisions

Catch weight and unlabelled bouts are excluded from fitting and scored with
the median division. Two inputs, added to the adopted formulas.

## Tests

1. Descriptive, no model: finish rate, knockdown rate, takedown rate and pace
   by division.
2. Added to the finish formula (addendum 15) and the knockdown formula
   (addendum 14), each tested separately on the same held-out split.
3. For the knockdown formula, also split by experience: does weight class help
   more for fighters with fewer than 5 prior bouts, as the shrinkage argument
   predicts?

## Decision rule, fixed now

Stricter than the tie-rule for replacing a model, because each added input is
another chance to fit noise: an input is added only if Brier improves out of
sample with bootstrap P(better) >= 0.95. Division is displayed on the site
regardless — it is context whether or not the model uses it.

## Addendum 16: RESULT (2026-09-21)

### Test 1, by division (descriptive)

| division | fights | finish | any KD | any TD | strikes/min |
|---|---|---|---|---|---|
| Flyweight | 419 | 45% | 33% | 80% | 6.4 |
| Bantamweight | 747 | 45% | 38% | 72% | 7.3 |
| Featherweight | 829 | 46% | 38% | 73% | 7.3 |
| Lightweight | 1093 | 51% | 37% | 71% | 7.1 |
| Welterweight | 1029 | 50% | 41% | 71% | 6.9 |
| Middleweight | 814 | 56% | 40% | 69% | 6.8 |
| Light Heavyweight | 519 | 61% | 44% | 60% | 7.5 |
| Heavyweight | 507 | 63% | 41% | 55% | 7.4 |
| Women's Strawweight | 379 | 34% | 16% | 83% | 7.5 |
| Women's Flyweight | 279 | 37% | 15% | 84% | 7.5 |
| Women's Bantamweight | 251 | 39% | 17% | 78% | 7.0 |

Finishes rise with weight (45% to 63%), takedowns fall (80% to 55%), and pace
barely moves at all (6.4 to 7.5, no trend) — the intuition that heavier
fights are slower is not in the data. Women's divisions finish least and
knock down least, and wrestle most.

### Tests 2 and 3, added to the formulas

| formula | gain | 95% CI | P(better) | decision |
|---|---|---|---|---|
| finish + weight class | +0.0050 | [+0.0016, +0.0085] | 0.997 | **added** |
| knockdown + weight class | +0.0007 | [-0.0002, +0.0015] | 0.931 | not added |
| knockdown, under 5 prior fights | +0.0014 | [-0.0005, +0.0032] | 0.929 | — |
| knockdown, 5+ prior fights | +0.0004 | [-0.0006, +0.0014] | 0.818 | — |

The shrinkage argument pointed the right way — the gain was 3.5x larger for
thin records — but not decisively, and the knockdown formula stays unchanged.

### An inference error caught before shipping

Where a card does not name the division, it is inferred from the fighters'
recent bouts. The first version took the most recent bout of any kind, and
both O'Neill and Moura's were catchweights, so a women's flyweight fight was
scored as a men's 155-lb bout: 38% to finish instead of 30%. Inference now
skips catchweights and uses each fighter's most recent real division. The
Wikipedia parser also now records the division directly from the card table.

---

# Addendum 17: career stage (2026-09-21)

Registered before fitting. Already in the win model: age, UFC experience
(log bouts), Elo, opposition Elo, layoff. Not available: any pre-UFC record —
the corpus holds UFC bouts only.

Measured first, as motivation: the model is weakest on bouts where both
fighters are veterans — log loss .6272 with 10+ prior bouts, against .6205 for
2-4 and .6176 for 5-9. Career averages hide decline, and age alone is a blunt
proxy for it.

| # | feature | form | predicted sign | mechanism |
|---|---|---|---|---|
| E1 | age x experience | (age - 30) x log(1 + UFC bouts), differenced | negative | an old, heavily-used fighter is worse than age or mileage alone implies |
| E2 | Elo trajectory | Elo now minus Elo three bouts ago, differenced | positive | form of the record, not of the stats; recency weighting of stats was null (addendum 7), this is different |
| E3 | career-stage cohort rate | historical win rate of fighters at the same bout-number band and age band, from EARLIER fights only, differenced | positive | the direct version of "how do fighters like this do at this stage" |
| E4 | distance from peak | Elo now minus career-best Elo, differenced | positive (less negative is better) | a veteran well below his own peak is declining |

Bands for E3, fixed: bouts 0-2 / 3-5 / 6-9 / 10-14 / 15+; age under 26 /
26-29 / 30-33 / 34+. Rate smoothed as (wins + 1) / (bouts + 2).

Each added individually to the frozen 14. Benjamini-Hochberg at FDR 0.10
across the four. Supported only if it survives correction and improves log
loss out of sample.

**Pre-registered subgroup:** each is also reported on bouts where the thinner
record is 10+, the band the model does worst on. This is reported, not used
for the decision — a subgroup result alone would not justify adding a feature.

Prior: low for E3, whose content age and experience mostly already carry.
Highest for E4, which says something neither age nor career averages can.

## Addendum 17: result on the analysis window, and the confirmation rule

On 2012 to 2026-03-28: **E1 supported** (gain +0.0053, CI [+0.0015, +0.0091],
p .0067 against BH .025, sign as predicted, veteran-subgroup gain +0.0063).
E2, E3, E4 not supported (p .089, .227, .485).

E1 would be the first input added to the win model to survive correction in
the project's history. One family's result is not enough for that, so, written
before looking:

**Confirmation: a single look at the reserved holdout** — every bout after
2026-03-28, never used by any test. Model trained on everything up to the
cutoff, with and without E1. E1 is adopted if its log-loss gain on the holdout
is POSITIVE. The holdout is too small for an interval to exclude zero, so the
test is only whether the effect points the same way on data it has never seen.
If it does not, E1 is recorded as not confirmed and stays out.

## Addendum 17: CONFIRMATION RESULT (2026-09-21)

**E1 not confirmed. It stays out of the model.**

| | holdout accuracy | holdout log loss |
|---|---|---|
| frozen 14 | 60.23% | .6547 |
| 14 + E1 | 59.06% | .6589 |

171 bouts after 2026-03-28 (the reserved 252 less those without two prior
bouts per corner). Gain **-0.0042**, and -0.0183 on the 32 veteran bouts. The
rule required only that it point the same way on unseen data; it pointed the
other way.

This is the reserved holdout doing the one thing it exists for. E1 was the
first new input in the project to survive correction on the analysis window,
and it did not hold up on data no test had touched — most likely the window's
+0.0053 was noise that happened to clear the bar. The holdout has now been
used once, for this, and that use is recorded.

Separately noted: the model's holdout accuracy is 60.2%, against 67.5% on the
analysis test block. With 171 bouts the standard error is about 3.7 points, so
this is roughly two standard errors low — possibly noise, possibly a recent
shift (2026's decision rate is also unusual, addendum 9). Worth watching as the
scorecard fills in; not grounds for any change yet.

## Addendum 13: correction — the win model it names was not frozen

Addendum 13's opening-line rule uses "the frozen 14-feature win model", but the
site refits its win model on every refresh, so no frozen version existed. Fixed
2026-09-21: coefficients saved to `mmastat/win14_model.json`, trained on all
data through 2026-09-12. Because the model's probabilities are a deterministic
function of pre-fight statistics, every bout in the ledger — including those
captured before the file existed — is scored from these coefficients at
evaluation time. The ledger stores prices, not this model's output, so nothing
already captured is lost.

---

# Addendum 18: pre-UFC records (2026-09-21)

Registered before any pre-UFC data has been collected or seen.

## Why

34% of UFC bouts since 2020 (1,133 of 3,338) cannot be priced at all, because
a fighter has fewer than two prior UFC bouts; 629 involve a debut. About four
bouts per card show "no read". The corpus holds UFC bouts only, so for those
fighters the model has nothing. A fighter's full professional record is the
one career-history signal it cannot currently see.

## Source and collection

Wikipedia's MediaWiki API, already used for cards. For each fighter: locate
the article, parse the "Mixed martial arts record" table into
(date, result, method, event) rows. A row counts as a UFC bout if it matches a
bout in the corpus for that fighter within 2 days; every other row before a
given date is outside-UFC history. Collected by a GitHub Actions job, since
this environment has no network; the resulting file is committed, then
analysed.

## Stop rule: coverage first

Fighters without Wikipedia pages are disproportionately the low-profile ones —
exactly the debutants this is for — so missing data is not random. **If fewer
than 50% of debuting fighters since 2020 have a parseable record, the test
stops there** and nothing is built on it, because a model fitted only to the
well-known debutants would be biased toward them. Coverage is reported either
way.

## Inputs, fixed now

    pre_w, pre_l     outside-UFC wins and losses before the bout
    pre_fin          share of outside-UFC wins by KO/TKO or submission
    pre_streak       current outside-UFC win streak entering the UFC
    pre_n0           1 if no outside record was found (missingness, explicit)

## Part A — pricing the bouts the site currently skips

Bouts where a fighter has 0-1 prior UFC bouts, since 2012. A logistic model on
the pre-UFC inputs plus age, reach and height differentials, and the
experienced opponent's UFC-derived features where they exist.

**Published on the site only if** held-out log loss beats a coin flip (0.6931)
with a 95% interval excluding it, AND calibration slope is between 0.7 and 1.3.
Where odds exist, compared against the market as well, and reported whatever
the result. Such bouts would carry the "thin evidence" flag.

## Part B — improving the bouts already priced

The pre-UFC inputs added as differentials to the frozen 14, on bouts with 2+
prior UFC bouts. Benjamini-Hochberg at FDR 0.10 over the five inputs.

The reserved holdout was used once, for addendum 17, and is spent. So any
Part B support is **provisional**: it enters the model only once the forward
scorecard agrees, not on the window result alone.

## Pre-stated expectation

Part A: likely to beat a coin flip, unlikely to approach the market, which
prices debutants with scouting information no record captures. Part B: small or
null — for fighters with UFC history, UFC stats should dominate a regional
record.

---

# Addendum 19: is the two-fight gate too cautious? (2026-09-21)

Written before looking. Prompted by a fair objection to addendum 18: a
regional record is a different kind of evidence from in-fight UFC output, and
mixing them may confuse more than it helps. The cheaper question comes first —
whether the existing model, which already shrinks thin records toward the
league average, can price these bouts with no new data at all.

The site prices a bout only when both fighters have 2+ prior UFC bouts. The
standard win model (trained as usual, on 2+ bouts) is evaluated on held-out
bouts where the thinner record is exactly 1, and exactly 0 (a debut).

**The gate is lowered to k if**, on bouts with thinner record k, held-out log
loss beats a coin flip (0.6931) with a 95% interval excluding it AND the
calibration slope is between 0.7 and 1.3 — the same bar addendum 18 set for a
record-based model. Compared against the market where odds exist, and
reported whatever the result.

If the existing model clears the bar, addendum 18's scraper is not needed for
the win probability and its value falls to whatever it adds on top.

## Addendum 19: RESULT (2026-09-21)

**The gate is lowered to 0 for the win probability.** Both groups clear the bar.

| thinner record | bouts | accuracy | log loss (95% CI) | calibration | market, same bouts |
|---|---|---|---|---|---|
| 2+ (priced before) | 829 | 67.3% | .6208 | — | .5794 |
| exactly 1 | 174 | 66.1% | .6323 [.5853, .6762] | 1.09 | .5887 |
| 0 (a debut) | 213 | 59.2% | .6474 [.6143, .6831] | 1.02 | .5758 |

The model's shrinkage already did what addendum 18's scraper was for: with no
UFC history it falls back on physical measurements and the league average,
and the result is well calibrated. The market's lead widens on debuts (.072
against .041 on priced bouts), as expected — it has tape and scouting.

Scope, kept to what was tested:
- **Win probability only** for bouts where a fighter has 0-1 prior UFC bouts.
  Method, round, finish, totals and props are withheld on those bouts, because
  none of them was evaluated on records this thin.
- **The ledger's betting rule keeps its registered 2+ population.** Changing a
  running test's population is the error addendum 13 prohibits.
- Fighters absent from the stats feed entirely still get no read: there are no
  measurements to fall back on.

On the live card this moved coverage from 10 of 13 bouts to 12 of 13.

## Addendum 18: DEFERRED (2026-09-21)

Not run. Addendum 19 answered its main question — pricing the bouts the site
skipped — with no new data. Part B (regional records added to the stat-based
model for experienced fighters) is dropped outright, on the objection that
prompted addendum 19: a regional record is a different kind of evidence from
in-fight UFC output, of wildly varying competition level, and mixing the two
invites confusion for an expected-null gain. The collector
(`mmastat/wiki_records.py`) is kept, tested but unscheduled. Its remaining
possible use is props on thin-record bouts, if that is ever worth testing.

## Addendum 10/14: a note on what the rows measure (2026-09-23)

Prompted by a reader asking what "their takedown rate" counts. Verified in
`state.py`:

| row | what it is |
|---|---|
| C1 their takedown rate | takedowns **landed** per 15 min, opponent-adjusted |
| C3 their knockdown rate | knockdowns **scored** per 15 min |
| C11 opponent's knockdowns absorbed | times the opponent has **been dropped**, per 15 min — suffered, not prevented |
| C2 opponent's takedown defence | share of attempts against him that were **stopped** |

C1 and C3 are the outcome itself, measured before the fight. Their strong
patterns are close to definitional and are now labelled **same measure** on the
site, against **different measure** for the rest, so the panel does not present
a tautology and a finding as equals.

Checked at the same time, since attempts and landings are different claims:

| predicting "lands a takedown" (base 44%) | quartiles | spread | AUC |
|---|---|---|---|
| takedowns landed per 15 | 24 37 51 63 | +.392 | .680 |
| takedowns attempted per 15 | 23 36 52 64 | +.407 | .687 |
| takedown accuracy | 43 37 44 51 | +.142 | .542 |

Landed and attempted correlate at **0.945** and perform the same, so the choice
between them does not matter and no row is added. Accuracy on its own is weak:
what predicts landing a takedown is how often a fighter shoots, not how well he
finishes the shot. The takedown model already sees both rate and accuracy, so
attempts were never missing from it.

---

# Addendum 20: head strikes and knockdowns (2026-09-23)

Registered before fitting.

The knockdown formula (addendum 14) is `own_kd15`, `opp_kd_against15`,
`opp_sapm`. The third measured flat as a panel row (C12) and its fitted weight
came out at -0.01. The likely reason: `sapm` counts every significant strike
absorbed, so a fighter who takes leg kicks all night looks as hittable as one
who takes head shots. Knockdowns come from the head.

| # | input | form | mechanism |
|---|---|---|---|
| H-OUT | own head strikes landed per minute | career, opponent-unadjusted | a knockdown needs head strikes thrown and landed |
| H-ABS | opponent's head strikes absorbed per minute | career | the specific durability that matters, instead of total volume absorbed |

Both are computed from the head/body/leg split already in the corpus, in the
leakage-safe walk, exactly as the existing accumulators are.

## Variants tested, against the adopted formula

    A (current)  own_kd15, opp_kd_against15, opp_sapm
    B            A + own head output
    C            own_kd15, opp_kd_against15, opp head absorbed   (swaps sapm)
    D            own_kd15, opp_kd_against15, own head output, opp head absorbed

Same held-out split as addendum 14, Brier with a bootstrap interval.

## Decision rule, fixed now

A variant replaces the current formula only if its Brier improves with
**P(better) >= 0.95** — the stricter bar from addendum 16, because each added
input is another chance to fit noise. A swap that neither helps nor hurts keeps
the incumbent.

Also reported, whatever the outcome: both measures as base-rate panel rows
against "scores a knockdown", under the addendum 10 display rules.

## Pre-stated expectation

Moderate for H-ABS, which is a sharper version of an input already present.
Lower for H-OUT: `own_kd15` already counts the knockdowns a fighter's head
strikes produced, so head volume may add nothing beyond it — the same
near-duplication that makes C1 and C3 "same measure" rows.

## Addendum 20: RESULT (2026-09-23)

**No variant adopted.** All three improve slightly; none reaches P(better) 0.95.

| variant | Brier | AUC | gain vs current | P(better) |
|---|---|---|---|---|
| A, current (`opp_sapm`) | .1432 | .6676 | — | — |
| B, + own head output | .1430 | .6704 | +0.0002 | .774 |
| C, swap `opp_sapm` for head absorbed | .1431 | .6699 | +0.0001 | .755 |
| D, both head measures | .1429 | **.6734** | +0.0003 | .865 |

As base-rate rows against "scores a knockdown" (base 19%):

| measure | quartiles | spread |
|---|---|---|
| their head strikes landed /min | 17 19 19 22 | +.051 |
| opponent's head strikes absorbed /min | 17 21 20 20 | +.041 |
| opponent's ALL strikes absorbed /min (current input) | 18 21 19 20 | +.028 |

So the reasoning holds in direction — head-specific measures are sharper than
total volume absorbed, and D lifts AUC from .668 to .673 — but the gain is far
inside the noise at this sample size. The formula is unchanged.

Why the ceiling is so low: `own_kd15` already counts the knockdowns a
fighter's head strikes produced, which is the outcome itself measured earlier.
Head volume adds the part of that story the knockdown count already tells.

**Deviation from the registration, stated plainly:** both measures were to be
added to the site's base-rate panel whatever the result. They are not. Doing so
would mean adding head-strike accumulators to `state.py` and a new panel column
purely to display two near-flat rows on a panel already criticised as dense.
The numbers are published here instead, which serves the same purpose — not
hiding a null — at no cost to the reader.

---

# Addendum 21: a systematic screen for unconsidered patterns (2026-09-23)

Registered before running. Prompted by a fair question: the panel's conditions
were each chosen for a stated mechanism, so a real relationship nobody thought
of — striking pace against knockdowns, say — would never be found.

This crosses **every measurement the state already computes** against every
outcome, rather than the ones someone guessed at.

    measurements  the fighter's own and his opponent's levels of all 23
                  tracked quantities, for the per-fighter outcomes; their
                  sums for the whole-fight outcome
    outcomes      lands a takedown, scores a knockdown (per fighter);
                  ends inside the distance (per fight)

About 115 tests. Screening on this scale is exactly how spurious findings are
manufactured, so: **Benjamini-Hochberg at FDR 0.10 across the entire grid**,
computed once, with every result reported including the failures.

## Status of anything that survives

A survivor is a **candidate, not a finding**, and does not enter a model or the
panel on this result. The reserved holdout was spent in addendum 17, so the
only honest confirmation left is forward: a candidate must hold up on cards
collected after today before it is used for anything. That is recorded here so
a future reader cannot mistake a screen hit for a tested result.

## Pre-stated expectation

The strongest survivors will be the ones already in the panel, because those
were chosen for good reasons. Anything new is likely to be a near-duplicate of
an existing measurement rather than a separate mechanism.

## Addendum 21: RESULT (2026-09-23)

**73 of 115 tests survive BH at FDR 0.10 — and that is the finding.** With
~14,000 fighter-fights almost any real-but-tiny relationship reaches
significance, so the correction does no useful filtering here. Effect size is
the only screen worth applying, and the results below are ranked by the spread
between the lowest and highest quarter, not by p.

### Candidates not already in the panel

| measurement | outcome | quartiles | spread |
|---|---|---|---|
| own control share | lands a takedown | — | +.385 |
| own ground-strike share | lands a takedown | — | +.248 |
| combined height | ends inside distance | 39 48 49 61 | +.220 |
| combined reach | ends inside distance | — | +.217 |
| **opponent's age** | **scores a knockdown** | **14 17 21 25** | **+.105** |
| their striking pace | scores a knockdown | 16 20 19 22 | +.060 |
| their striking accuracy | scores a knockdown | 17 17 20 23 | +.056 |

For scale, the hand-picked panel rows span +.392 (own takedown rate) down to
+.028 (opponent's strikes absorbed, the flat one).

### What survives scrutiny

Most of the large ones are near-duplicates, as predicted. Control share and
ground-strike share are largely downstream of takedowns — you hold control
*because* you took someone down. Combined height and reach are substantially
weight class: pooled the spread is +.220, but within lightweight it falls to
+.116 and within middleweight +.120, so roughly half is division and half is
something else.

**Two are genuinely new.** Opponent's age against knockdowns (+.105) is nearly
as strong as the chin measure already in the formula and is not a restatement
of it. Striking pace against knockdowns (+.060) beats `opp_sapm` (+.028),
which is in the formula and flat — so the question asked about pace was a
better instinct than the input it would replace.

### Status: candidates, not findings

Neither enters a model or the panel on this result. The holdout was spent in
addendum 17, so confirmation has to be forward: they must hold on cards
collected after today. Adopting a screen hit from 115 tests on the same data
that produced it is precisely the error this project has avoided twelve times.

---

# Addendum 22: within-fight volatility (2026-09-23)

Registered before computing anything.

Addendum 12 tested volatility BETWEEN fights (the spread of a fighter's
per-fight output) and found nothing. This is a different quantity: how much a
fighter's output swings **from round to round inside a fight**, averaged over
his career. The corpus holds 41,906 round rows, so it is computable, and the
market has no obvious way to price it.

| # | measure | form |
|---|---|---|
| W1 | pace volatility | coefficient of variation of his significant strikes across the rounds of a fight, averaged over prior fights |
| W2 | output trend | slope of significant strikes across rounds, normalised by his mean — does he climb or fade |
| W3 | disruption | the same CV computed on his OPPONENTS' round-by-round output — does he make fights erratic |
| W4 | grappling volatility | CV of control time across rounds |

All built in the leakage-safe walk from prior fights only, as every other
accumulator is.

## Targets

    (a) win model      added to the frozen 14, log loss out of sample
    (b) finish formula added to the adopted inputs (addenda 15, 16)
    (c) market residual added to the offset model — the only one of the three
        that speaks to an edge, since it asks whether the measure adds
        anything the closing price does not already contain

Benjamini-Hochberg at FDR 0.10 across all twelve tests.

## The honest prior: low, and here is the arithmetic

A variance needs at least two rounds, so only fights that pass the first round
contribute. A fighter has ~6.5 recorded bouts, of which perhaps four go past
round one, giving roughly a dozen round observations to estimate a spread
from. The estimate is mostly noise before the sport is even involved. That is
the same constraint that has closed every previous family, and it applies
harder to second moments than to means.

If anything survives, it is a candidate requiring forward confirmation, not a
finding — the holdout was spent in addendum 17.

## Addendum 22: RESULT (2026-09-23)

**Zero of eight supported.** Every gain is within ±0.0005 of nothing; the two
smallest p-values belong to measures that made predictions *worse*.

| target | measure | gain | p |
|---|---|---|---|
| market residual | grappling volatility | **-0.0003** | .022 |
| win model | grappling volatility | **-0.0005** | .072 |
| market residual | pace volatility | -0.0002 | .667 |
| market residual | output trend | +0.0001 | .702 |
| win model | disruption | -0.0001 | .768 |
| win model | output trend | -0.0001 | .770 |
| win model | pace volatility | +0.0001 | .813 |
| market residual | disruption | +0.0000 | .848 |

The finish-formula arm was dropped when the win and residual arms came back
this flat; it is recorded as not run rather than quietly omitted.

The market-residual arm is the one that mattered, since it asks whether the
measure adds anything the closing price does not already hold. On 1,112
held-out bouts with odds, nothing did.

### Why, in the data rather than in theory

A within-fight spread needs a fight to pass round one, and the fighters who
generate the most rounds are the ones who go to decisions. Of 17,753
fighter-fights, 12,740 yield a spread at all, and the **median fighter has
three** such fights in his history — a variance estimated from about a dozen
round observations, most of which are three-round fights where a "trend" is a
line through three points.

This is the same constraint that closed the previous twelve families, and it
bites harder here: a second moment needs far more data than a mean, and this
corpus does not have enough for a first moment.

---

# Addendum 23: is individual adaptability measurable? (2026-09-23)

A feasibility check, not a hypothesis test. Its only output is a decision
about whether to build the feature at all.

Proposed idea: a fighter who adjusts to his opponent — shooting more against a
weak takedown defender, for instance — and profits by it. The population-level
version of this is already in the model: `grapple_edge` is takedown rate
multiplied by the opponent's takedown defence, and it is one of the stronger
of the fourteen features. What is unproven is whether **individual fighters
differ** in how much they do it, which is what a new per-fighter feature would
have to capture.

## Method

For each fighter with 4+ recorded fights, the slope of his output in a fight
against the weakness he faced. If fighters genuinely differ, the spread of
those slopes must exceed what chance produces — measured by shuffling each
fighter's opponents among his own fights, 200 times.

| slope | real spread | chance | ratio |
|---|---|---|---|
| takedowns vs opponent's takedown defence | 22.57 | 21.02 | 1.07 |
| striking vs opponent's striking defence | 24.18 | 24.73 | 0.98 |
| control time vs opponent's takedown defence | 93.58 | 96.75 | 0.97 |

793 fighters qualify in each.

## Decision: not built

The spread of per-fighter slopes is what shuffling alone produces, and two of
the three fall below chance. With a median of five or six fights per athlete,
a per-fighter slope is estimated from a handful of points; there is no
variation left to attribute to the fighter once noise is accounted for.

This does not say adaptation is absent from the sport. It says the corpus
cannot distinguish an adaptable fighter from a lucky one, so a feature built
on it would be fitting noise with extra steps. Running the full test would
have produced a null with more ceremony.

Also recorded: the other two ideas raised alongside it are already closed.
Later-round resilience is the fortitude cluster (0 of 6 supported, 5 of 6
wrong sign, cluster harmful). Style-matchup success is the nine interactions
of addendum 1 (0 of 9, smallest p .060 against a .011 threshold).

---

# Addendum 24: bonus picks — Fight and Performance of the Night (2026-09-23)

Registered before any label has been collected.

A new **output** rather than another search for inputs. The UFC awards Fight of
the Night to both fighters in the best bout and Performance of the Night to the
best individual displays, decided internally by UFC management. In 2023 that
was 190 bonuses across 43 events, of which 58 went to 29 separate FOTN
winners — so FOTN is not awarded at roughly a third of cards.

## What the model already holds

    FOTN ingredients   a close matchup (win probability near 50%), high
                       combined projected output, and a fight likely to go
                       long or end late — the survival curve
    POTN ingredients   P(finish), the method split, the round distribution

POTN is close to mechanical: it goes to finishes, mostly early ones, and the
model already prices those. FOTN is the one combining quantities the site
does not currently put together.

## Labels

Wikipedia event articles carry a "Bonus awards" section. Collected through the
same MediaWiki plumbing as the parked record collector, from February 2014
(when Performance of the Night replaced Knockout and Submission of the Night)
to the present, into `data/wiki/bonuses.json`.

## Scoring and evaluation

A score per bout from existing outputs, ranked within each card. Evaluated on
held-out cards:

    FOTN   top-1 accuracy: how often the highest-ranked bout won it
    POTN   top-2 accuracy over fighters

## The baselines that matter, fixed now

Random is not the bar. Main events win bonuses far more often than their share,
for reasons that have nothing to do with the fight. So the model must beat
**both**:

    B1  always pick the main event
    B2  always pick the bout with the highest P(finish)

**Displayed only if it beats both on held-out cards**, and then only with its
measured hit rate shown beside the pick, as every other number on the site is.
If it beats random but not B1, it has learned "main events get bonuses", which
the reader already knows.

## Status and honest expectation

This is entertainment and context, not an edge: the award is a subjective
decision by executives, and no sportsbook we can reach quotes it. Polymarket
may — the unpriced-markets list will show it — and if so the pick becomes
checkable against a price.

Expected top-1 FOTN accuracy is 20-30% against roughly 8% for random and
perhaps 15% for always-main-event. Useful, not spectacular, and quite possibly
null against B1.

## Addendum 24: amendment — prior bonuses (2026-09-24)

Added before any label is usable, prompted by the right question: should a
fighter's bonus history count?

It should, but not as an ordinary feature. Past bonuses predicting future
bonuses is the outcome measured earlier — the "same measure" problem from
addendum 10 — and it carries the main-event confound a second time, since
bonus winners are disproportionately main-eventers. Left unmarked it would
dominate the model and teach nothing about fights.

## A third baseline, fixed now

    B3  pick the bout containing the fighter with the most prior bonuses
        (strictly prior, counted in the walk like every other accumulator)

The pick is displayed only if it beats **B1, B2 and B3** on held-out cards.

## And the model is reported both ways

If prior-bonus counts are used as inputs, results are reported **with and
without them**. The question worth answering is whether the fight-level
signal — a close matchup, high combined output, likely to go long — adds
anything beyond reputation. If the model only beats the baselines once bonus
history is included, then what it has learned is which fighters the UFC
favours, and that is what the site would say on the page.

Coverage caveat, recorded now: labels exist for 421 of 530 events (80%), and
the missing ones skew toward smaller cards. A prior-bonus count is therefore
an undercount, unevenly. That biases B3 downward and the feature with it, so a
narrow win over B3 is not evidence.

---

# Addendum 25: the unused columns (2026-09-25)

Registered before computing anything. Prompted by asking what a genuinely new
measurement would look like.

Checked first, and recorded because it bounds everything else: the round-level
feed has **no timestamps** and **no positional labels**. Strike-by-strike
timing and grappling position (guard, mount, back) do not exist in this corpus
and cannot be tested at any price. What does exist and has never been used:

| # | measure | why it might carry something |
|---|---|---|
| G1 | reversals per 15 min | the `REV.` column is in every round row and appears nowhere in `state.py` — a grappler who reverses position is escaping bad spots, which no current input sees |
| G2 | opponent's reversals conceded per 15 | the same signal from the other side: a fighter whose control gets reversed is losing position he had won |
| G3 | ground-strike accuracy | landed over attempted from the ground. The model has ground SHARE but not how well those strikes land |
| G4 | submission attempts per minute of control | threat density while controlling, as against `sub15`, which is per fight minute and so mostly measures how often he gets on top at all |
| G5 | clinch-strike accuracy | the same idea as G3 in the clinch |

All built in the leakage-safe walk from prior fights only.

## Targets and correction

    (a) win model       added to the frozen 14, log loss out of sample
    (b) market residual added to the offset model — the only arm that speaks
        to an edge

Benjamini-Hochberg at FDR 0.10 across all ten tests. Anything supported is a
candidate needing forward confirmation, not a finding: the holdout was spent in
addendum 17.

## Pre-stated expectation

Low but not negligible, and higher than addendum 22's. These are unused
*measurements* rather than re-weightings of used ones, which is the one kind of
addition this corpus could still support. Against that: reversals are rare, so
the per-fighter rate is estimated from very few events, and G3 to G5 are
ratios whose denominators are small for fighters who rarely grapple.

## Addendum 25: RESULT (2026-09-25)

**Zero of ten supported.** The only test to clear its BH threshold did so by
making predictions *worse*.

| target | measure | gain | p | |
|---|---|---|---|---|
| market residual | ground accuracy | **-0.0018** | .002 | survives correction, wrong direction |
| win model | sub attempts per control min | -0.0008 | .157 | |
| win model | ground accuracy | -0.0005 | .163 | |
| market residual | reversals | +0.0007 | .190 | |
| market residual | sub attempts per control min | -0.0004 | .217 | |
| win model | clinch accuracy | +0.0004 | .268 | |
| market residual | reversals conceded | -0.0005 | .305 | |
| win model | reversals | +0.0006 | .460 | |
| win model | reversals conceded | +0.0002 | .715 | |
| market residual | clinch accuracy | -0.0001 | .742 | |

Ground accuracy is worth a note: added to the market-residual model it is the
most statistically reliable result in the family, and it **hurts**, reliably.
A feature that is significantly bad is still a feature that does not go in,
and it is a useful reminder of what a small p-value does and does not mean.

### Why, in the data

Reversals barely exist: **11% of fighter-fights record one at all**, mean 0.13
per fight. Over a median career of five or six recorded bouts, a fighter's
reversal rate rests on well under one event. The shrinkage that keeps it stable
also removes what little variation there was.

The ratios have the same problem from the other end: ground accuracy is
undefined for the 41% of fighter-fights with no ground strikes attempted, and
rests on a median of six attempts when it exists.

### What was checked and does not exist

The round feed carries no timestamps and no positional labels. Strike-by-strike
timing and grappling position — guard, half guard, mount, back — are not in
this corpus at any price, and nothing derived from UFCStats will ever supply
them. That is the boundary: fourteen families have now been tested, and the
constraint has never been the search. It is that roughly seven recorded fights
per athlete, summarised as per-round totals, is all there is.

---

# Addendum 26: volume markets (2026-09-25)

Registered before building. DraftKings quotes markets the model has never
priced, and they are the ones this corpus is best equipped for — the data is
per-round counts of exactly these quantities.

| market | shape |
|---|---|
| Total significant strikes landed | per fighter, a ladder: 55+, 60+, 65+, 70+ |
| Significant strikes over/under | per fighter and combined |
| Round 1 significant strikes | per fighter, first round only |
| Most significant strikes | which fighter lands more |
| Total takedowns landed | per fighter, a ladder: 3+, 4+, 5+ |
| Most takedowns | which fighter lands more |

## Why these, and why they are different from everything tested so far

Every previous family tried to predict an outcome — who wins, how it ends.
These ask how much of something happens, which is what the feed actually
records. The model already projects strike and control rates with 80% ranges;
what is missing is a **count distribution**, not a new input.

## Method, fixed now

For each fighter: a strike rate per minute (already modelled) combined with the
fight-duration distribution from the survival curve, giving a distribution over
total strikes rather than a point estimate. Counts are modelled as negative
binomial, with the dispersion fitted on held-out fights, because strike counts
are over-dispersed relative to Poisson — a fighter who gets taken down in round
one and a fighter who stands and bangs are not the same process.

    P(60 or more strikes) = sum over fight lengths of
                            P(that length) x P(60+ strikes | that length)

"Most significant strikes" follows from the same two distributions.

## Amendment (2026-09-25): the model publishes a distribution, not the book's rungs

The first version of this addendum framed the target as the ladder a book
quotes — 55+, 60+, 65+. That was backwards. Ladders differ by fight and by
book, set by whoever is pricing that bout, so fitting to them makes this
model's output a function of someone else's pricing decisions, and a rung that
exists at one book and not another would change what we publish.

The model instead produces a **count distribution** for each fighter, and
publishes it on its own terms: the expected total, a range, and the
probability of clearing any threshold a reader cares to name. A reader with a
line in front of them reads their own number off it. Nothing in the fit, the
evaluation or the display refers to a book's ladder.

This also makes the evaluation cleaner: calibration of the whole distribution
is the thing to measure, rather than accuracy at three arbitrary thresholds
that move between fights.

## Evaluation and the bar

Graded on held-out fights against two baselines:

    C1  the fighter's own career average rate x the median fight length
    C2  the league average for that division and scheduled length

Reported as calibration of the whole distribution — the share of fights whose
actual count falls below each predicted quantile, which should track the
quantile itself — plus Brier at a few fixed thresholds chosen by the model, not
by a book. **Published only if it beats both**, and calibration slope falls
between 0.8 and 1.2 — a count model that is sharp but miscalibrated is worse
than useless on a ladder market, where every rung is priced off the tail.

Against the market: compared with DraftKings' lines where captured. No feed we
can reach quotes these, so that comparison depends on manual capture, and the
model is published on the baseline test alone, with the market comparison
reported separately if and when it exists.

## Pre-stated expectation

Moderate, and higher than any family since the opening-line finding. Volume is
the quantity this data measures most directly, and a count distribution is a
modelling gap rather than an information gap — which is the opposite of every
null recorded above. The risk is not that the signal is absent but that the
tails are wrong, which is exactly what the calibration bar is there to catch.

## Addendum 26: RESULT, first half (2026-09-25)

**Expected counts adopted. Ladder probabilities still to come.**

Prompted by an obvious question: why does the model show zero takedowns when a
book quotes a ladder from 3+ to 9+ for the same bout? Because the projection
used the MEDIAN, and 55% of fighters land no takedowns — so the median is
genuinely zero for most of them, and the fitted median was zero for every
fighter, carrying no information at all. Rosas Jr.'s career rate is 2.88
takedowns per 15 minutes and Barcelos's is 2.19; the rates were never the
problem, the statistic was.

A mean-rate model, on held-out fights:

| target | model | own career rate (C1) | league average (C2) | calibration slope |
|---|---|---|---|---|
| takedowns per 15 min | **1.401** | 1.532 | 1.681 | 0.87 |
| significant strikes per min | **2.044** | 2.092 | 2.154 | 0.85 |

Mean absolute error; lower is better. Both beat C1 and C2, P(better than own
career rate) is 1.000 for takedowns and 0.961 for strikes, and both calibration
slopes fall inside the 0.8 to 1.2 band fixed above. Published.

Still outstanding, and the harder half: the probability of clearing a given
total, which needs the distribution rather than the mean. The zero inflation
that broke the median is exactly what that model has to represent.

---

# Audit: the "hidden UFC metrics" list (2026-09-25)

Not a test — an audit of a proposed feature list against what the model already
has and what this corpus can support. Recorded so the same ground is not
covered twice.

## Already in the model

| proposed | where it lives |
|---|---|
| % strikes from clinch / on ground | `clinch_share`, `ground_share` |
| head/body/leg distribution | `body_share`, `leg_share` |
| control-time % | `ctrl_share` |
| knockdowns per 15 min | `kd15` |
| submission attempts per 15 | `sub15` |
| opponent-adjusted striking and takedowns | `adj_slpm`, `adj_td15` — the adjustment IS the opponent baseline |
| striking differential | `adj_slpm` and `sapm`, entered separately so the model can weight them |
| stance | `southpaw` |
| target-specific and position-specific defense | `str_def`, `td_def`; the position split was tested in addendum 25 |
| offense x defense interactions | `grapple_edge`, `ko_edge`, `sub_edge` |

## Already tested and closed

Pace decay and round-to-round output (addendum 6 fortitude cluster, 0 of 6,
cluster harmful). Output volatility and trend (addendum 22, 0 of 8). Position
accuracy and submission-per-control (addendum 25, 0 of 10). Recency weighting
(addendum 7, null). Style interactions (addendum 1, 0 of 9).

## Impossible here

Anything needing event sequences: chain wrestling, failed-takedown
consequences, counter-strikes after a miss, time-to-first-takedown. The round
feed has **no timestamps** — only per-round totals — so the order of events
inside a round is unrecoverable at any price.

UFC's own Weighted Striking Accuracy uses shot-difficulty data we do not have.
The nearest buildable analogue is below.

## Genuinely new, built and measured

| candidate | usable rows | solo AUC | nearest existing feature |
|---|---|---|---|
| accuracy residual (actual minus expected from position/target mix) | 100% | 0.550 | `d_str_acc`, **r = 0.78** |
| position entropy | 100% | 0.514 | `d_str_acc`, r = 0.28 |
| ground strikes per takedown | 81% | 0.509 | `d_str_acc`, r = 0.24 |
| control per takedown | 81% | 0.503 | `d_sapm`, r = 0.21 |
| target entropy | 100% | 0.502 | `sub_edge`, r = 0.21 |
| knockdowns per strike landed | 100% | 0.500 | `grapple_edge`, r = 0.08 |

For scale, the model's strongest single feature, age difference, has solo AUC
0.631. An AUC of 0.500 is a coin flip.

## Conclusion: none are worth a registered test

The only candidate with any standalone signal is the accuracy residual — the
analogue of UFC's Weighted Striking Accuracy — and it correlates **0.78** with
striking accuracy, which is already in the model. It is a rotation of an
existing feature, not a new one.

Everything else sits between 0.500 and 0.514, which is noise. The two takedown
conversion measures are also undefined for the 19% of bouts with no takedown,
the same sparsity that sank reversals in addendum 25.

The list is a good list. It is aimed at a richer feed than this one: the
features that would repay the effort need shot-difficulty labels or event
timestamps, and UFCStats publishes neither.

---

# Audit: the dataset-structure list (2026-09-25)

A second proposed feature list, audited the same way. Almost all of it is
either already built or already closed.

## Already built

One row per fighter per fight with leakage-safe rolling state, built by
walking fights in date order and updating after each — the exact structure
proposed, and the reason the leakage tests pass. Opponent-adjusted striking and
takedowns. Target and position shares. Knockdowns and submission attempts per
15. Separate models for winner, method, round, duration and per-fighter output
(strikes, control, takedowns, knockdowns), which is the "fight outputs" branch
of the proposed architecture. Time-based splits, never random. Logistic
regression benchmarked against gradient boosting, with the betting market as
the baseline every model is measured against.

## Already tested and closed

Recency windows and exponential weighting (addendum 7, null). Pace decay and
round-to-round output (addendum 6, 0 of 6, cluster harmful). Volatility
(addendum 22, 0 of 8). Conversion ratios — control per takedown, ground strikes
per takedown, submissions per control (addendum 25 and the 2026-09-25 audit,
all at or below AUC 0.51). Target and position entropy (same audit, 0.502 and
0.514). Knockdown per strike landed (0.500). Offence x defence interactions
(addendum 1, 0 of 9; three survive in the model as `grapple_edge`, `ko_edge`,
`sub_edge`).

## The one item not yet measured

**Style drift** — the size of the change between a fighter's recent profile and
his career profile, as a feature in its own right rather than as a re-weighting.
Recency weighting was tested and failed, but that asked whether recent form
predicts better than career form. This asks something different: whether a
fighter who has *changed* is less predictable. Untested here.

Prior: low. It is a second moment of a noisy quantity over ~6.5 fights, which
is the same shape as addendum 22's volatility family, and that returned 0 of 8.
Recorded as an open candidate rather than run, because the arithmetic that
closed addendum 22 applies unchanged.

---

# Addendum 27: style drift (2026-09-25)

Registered before computing. Recency weighting was tested and failed
(addendum 7): recent form does not predict better than career form. This asks
a different question — whether a fighter whose style has **changed** is worth
knowing about, either because he is improving or because he is less
predictable.

    drift = distance between a fighter's last-three-fight profile and his
            career profile, across clinch share, ground share, body share,
            leg share, striking rate and takedown rate

Built in the leakage-safe walk from prior fights only, differenced between
corners as every other feature is.

    D1  style drift
    D2  striking-rate drift alone (signed: rising or falling output)
    D3  grappling-rate drift alone (signed)

Added individually to the frozen 14 and to the market-residual model.
Benjamini-Hochberg at FDR 0.10 across all six tests. The holdout is spent, so
anything supported is a candidate needing forward confirmation.

Prior: low. This is a second moment of a noisy quantity over about six fights,
the same shape as the volatility family that returned 0 of 8.

## Addendum 27: RESULT (2026-09-25)

**Zero of six supported.** Every gain is negative or zero.

| target | measure | gain | p |
|---|---|---|---|
| win model | grappling drift | **-0.0065** | .023 |
| market residual | style drift | -0.0007 | .077 |
| win model | style drift | -0.0011 | .393 |
| win model | striking drift | +0.0000 | .453 |
| market residual | striking drift | -0.0002 | .727 |
| market residual | grappling drift | -0.0003 | .777 |

Grappling drift has the smallest p-value in the family and **makes the model
worse** by the largest margin of any feature tested in this project. It did not
clear its BH threshold, and it would not go in if it had.

Held out on 536 bouts for the win model and 756 for the residual. The prior was
low for the right reason: a drift measure is the difference between two noisy
means over a career of about six fights, so most of what it captures is the
sampling error of the earlier average.

That closes the last untested item on either proposed feature list.

---

# Addendum 28: confidence by evidence (2026-09-26)

Registered before fitting. Prompted by a bout where the model said 52/48 and
the market said 26/74, on two fighters with three and four UFC bouts between
them.

Measured first, on held-out fights with odds:

| | n | model log loss | market |
|---|---|---|---|
| all bouts | 854 | .6181 | .5802 |
| disagree by 20+ points | 156 | .6923 | .5955 |
| thin records (4 or fewer bouts) | 514 | .6256 | .5773 |
| **thin AND disagree by 20+** | **117** | **.6959** | **.5762** |

On that last group the model called 55% of winners against the market's 72%,
and **.6959 is worse than a coin flip at .6931**. That is not only missing
information — it is overconfidence, and overconfidence is correctable without
any new data.

## The correction

Shrink the published probability toward even money by an amount that depends
on how much evidence stands behind it:

    logit(p_shown) = lambda(n) x logit(p_model)

where n is the thinner record in the bout and lambda is fitted on the training
window only, as a step function over the bands n<=2, 3-4, 5-9, 10+. A lambda
below 1 pulls toward 50/50; the fit is free to return 1, which would mean the
model is already calibrated at that evidence level.

## The bar, fixed now

Adopted only if held-out log loss improves **overall** and in the thin band,
with a bootstrap interval excluding zero. Accuracy must not fall: shrinking
toward 50% cannot change which side is picked, so any accuracy change would
mean an error in the implementation rather than a finding.

This does not close the information gap — the market knows things about
prospects the corpus does not record. It stops the model overstating what it
knows, which is the part that is ours to fix. The information half stays where
it is: addendum 18, pre-UFC records, deferred.

## Addendum 28: RESULT (2026-09-26)

**Not adopted.** The correction makes things slightly worse everywhere.

| | n | before | after | gain |
|---|---|---|---|---|
| all held-out bouts | 1216 | .6271 | .6283 | **-0.0012** |
| thin records (4 or fewer) | 726 | .6312 | .6339 | **-0.0027** |
| 10+ prior bouts | 169 | .6272 | .6296 | -0.0023 |

Fitted lambda by band: 0.86 for two or fewer prior bouts, 0.86 for 3-4, 1.12
for 5-9, 0.92 for 10+. Accuracy unchanged at 65.71%, as it must be — shrinking
toward even money cannot change which side is picked, which confirms the
implementation.

### Why the earlier number was misleading

The .6959 that prompted this was measured on **117 bouts selected for
disagreeing with the market by 20 points or more**. Conditioning on
disagreement selects the bouts where the model is most likely wrong, so the
loss on that subset is not evidence that the model is overconfident in
general — it is arithmetic. Fitted across all evidence levels, the shrinkage
factors come out near 1 and the non-monotone pattern (0.86, 0.86, 1.12, 0.92)
is what noise looks like, not a confidence curve.

So the model is not systematically overconfident by evidence level. On thin
records it is simply less informed than the market, and that is an information
gap, not a calibration one. The only honest route to closing it is data the
corpus does not hold — a fighter's record before the UFC, which is addendum 18
and stays deferred.

Recorded because the selection effect is worth remembering: any subset chosen
for disagreeing with a better forecaster will make the worse forecaster look
badly calibrated.

---

# Audit: does accuracy vary by position on the card? (2026-09-26)

Descriptive, not a registered test. Prompted by 25 of 26 props landing on one
main event.

| position | n | accuracy | log loss | avg prior UFC bouts |
|---|---|---|---|---|
| main event | 70 | 67.1% | .6182 | 7.7 |
| rest of main card | 283 | 66.8% | .6203 | 6.3 |
| prelims | 277 | 69.0% | .6227 | 6.4 |
| early prelims | 199 | 65.8% | .6196 | 6.4 |

Flat. The 3-point spread sits inside the standard error on samples this size.

Against the market the gap looked smaller on main events — +0.0044 against
+0.0371 for prelims and early prelims — but bootstrapped, the difference is
**-0.0329 with a 95% interval of [-0.116, +0.049]**, crossing zero at P = 0.78.
No claim.

The mechanism would have been plausible: main-event fighters carry 7.7 prior
UFC bouts against 6.3 elsewhere, so the model is better informed exactly where
the market is sharpest. It is simply not visible at this sample size.

**On the 25-of-26 that prompted this:** props inside one bout are strongly
correlated — when a fight goes to a decision, the distance market, every
"ends before round" and every method contract resolve together. That is one
observation dressed as twenty-six, and it is why the scorecard requires 25
graded claims *per market across cards* before it shows a number.

Recorded alongside a change: the scorecard now stores each claim's card
segment and scheduled rounds, so this question can be answered properly from
graded props once enough cards have settled. That field cannot be recovered
retrospectively, which is why it goes in now.

---

# Audit: is there a confidence score beyond the probability? (2026-09-26)

Asked whether the model can say, before a fight, how much to trust itself —
in particular whether more recorded history on the two fighters means a more
accurate prediction.

Tested by predicting the model's own held-out log loss from pre-fight
quantities (829 bouts):

| predictor of the error | R2 |
|---|---|
| a constant (the average loss) | -0.009 |
| all evidence features together | +0.002 |
| how many fights we have on them | -0.009 |
| **its own confidence, \|p - 0.5\|** | **+0.057** |

And accuracy by how much history exists:

| thinner record | n | accuracy | log loss |
|---|---|---|---|
| 2-4 prior bouts | 339 | 66.1% | .6205 |
| 5-9 | 321 | 70.1% | .6176 |
| 10+ | 169 | 64.5% | .6272 |

Non-monotone, and the spread is inside the standard error.

**There is no confidence score to build.** The only thing carrying any signal
about the model's error is the probability it already publishes — which is
what a calibrated probability means. Knowing more about a fighter does not make
the prediction better, and a bout with fifteen fights of history behind it is
not a safer read than one with four.

This matches two earlier findings and completes the picture: the learning curve
is flat (quadrupling training data moved log loss by 0.0009, 2026-09-23), and
evidence-weighted recalibration made things worse (addendum 28). The constraint
is one bit of outcome per fight, and it does not relax with more fights on
either side of it.

On the related question of collapsing correlated props at settlement: not done,
and not recommended. Each prop is a separate contract and grading each
separately is correct. The correlation is a reason not to read a single card's
tally as independent evidence, not a reason to stop counting — which is what
the 25-claims-per-market threshold already handles.

---

# Measure change: props scored by Brier, not by threshold (2026-09-26)

The prop record was headlined by a count of "right sides" — the model said
above 50% and it happened, or below and it did not. Verified on held-out
fights that this measure is unable to distinguish a real model from a
forecaster that lowballs everything.

**GOES THE DISTANCE** (happens 53% of the time, n=846)

| forecaster | right side | Brier skill |
|---|---|---|
| the base rate itself | 52.8% | 0.000 |
| a real fitted model | 59.3% | +0.035 |
| lowballer, 2% on everything | 47.2% | -1.034 |
| noise around the base rate | 49.5% | -0.145 |

**ENDS IN ROUND 1** (happens 24% of the time)

| forecaster | right side | Brier skill |
|---|---|---|
| the base rate itself | **76.4%** | 0.000 |
| a real fitted model | **76.4%** | +0.023 |
| lowballer, 2% on everything | **76.4%** | -0.259 |
| noise around the base rate | 73.0% | -0.123 |

On the long-shot market all three score **identically** on the threshold
measure, because none of them ever crosses 50%. The measure is blind exactly
where most props live: a market that resolves "no" four times in five.

Brier separates them correctly in both cases, so the card summary now reports
**Brier skill against the base rate** — how much closer the model's
probabilities sat to what happened than the league rate would have — with the
right-side count kept as a secondary figure. Both are stored per row, so
nothing is lost and older cards can be rescored.

---

# Finding: ko_edge is a correction, not a threat (2026-09-26)

Noticed from the site: a bout showed "knockout threat 1.14 v 0.61" with the
bar favouring the fighter on 0.61. Not a display bug.

    ko_edge = own striking output x opponent's rate of losing by strikes

Both halves are already in the model on their own — `d_adj_slpm` at +0.245 and
`d_ko_loss_rate` at -0.179. The product is collinear with its own inputs, and
the fit gives it a **negative** weight of -0.121: a higher "knockout threat"
lowers the predicted win probability.

So the feature is not measuring what its name says. It is a residual
adjustment on two main effects that are already counted, and it earned its
place in the frozen 14 on predictive grounds, not interpretive ones.

The other two interactions behave as named: `grapple_edge` +0.156,
`sub_edge` +0.009 (the latter near zero).

**Display:** any interaction driver whose bar favours the corner with the
smaller component is now marked "correction", with a note that the model
already counts both halves separately. Showing a contradiction without
explanation was worse than showing nothing.

**Model:** unchanged. Removing or re-signing a feature in the frozen set needs
its own registration and a held-out test, and the holdout is spent. Recorded
here so the next model revision starts from the fact that this feature does not
do what its name suggests — and as a caution about naming an interaction after
the story that motivated it rather than after what it turns out to measure.

---

# Question answered: should the career breakdown use pro records? (2026-09-26)

The per-round finish breakdown on the site counts UFC bouts only. On the
current card that is a median of 4 finishes per fighter, with 11 of 24 having
three or fewer. The question was whether pulling in full professional records
would make it more informative.

The collector for pre-UFC records exists (addendum 18, parked) but needs
network. Tested the decisive proxy instead, on UFC data, which is cleaner than
any regional source could be.

**Does a fighter's own finish history predict his next finish?** Yes, modestly
— held out on 1,483 bouts:

| | AUC | Brier skill |
|---|---|---|
| wins by finish, from his own finish rate | 0.621 | +0.028 |
| wins by KO, from his KO share of finishes | 0.618 | +0.016 |
| wins in round 1, from his round-1 share | 0.607 | +0.011 |

**Does MORE history sharpen it?** That is what a pro record would buy. No:

| prior fights on record | n | AUC finish | AUC round 1 |
|---|---|---|---|
| 2-3 | 2658 | 0.570 | 0.552 |
| 4-6 | 2626 | 0.592 | 0.587 |
| 7-10 | 2193 | 0.605 | 0.564 |
| 11 or more | 2674 | 0.584 | 0.536 |

Non-monotone, peaking in the middle and falling again. A fighter with eleven
or more prior bouts is predicted **no better** than one with two or three:
+0.013 AUC, 95% interval [-0.017, +0.046].

## Decision: keep it UFC-only

The signal in a finish profile saturates after a handful of fights. Extending
the record would add observations that do not sharpen the estimate, while
importing two problems: regional finishes are not the same event as UFC
finishes, and a mixed denominator beside a line reading "9-1 in the UFC"
invites misreading.

The round-of-finish projection the breakdown sits beside is built from
thousands of fights with opponent adjustment, and that is where the estimate
comes from. The career counts are context, and four finishes are enough context
for the job they do.

---

# Addendum 29: career method mix in the method and round models (2026-09-26)

Registered before fitting. The site now shows how each fighter's UFC wins
arrived; the question is whether that belongs in the projection rather than
only beside it.

Established already (2026-09-26): a fighter's own finish history predicts his
next finish at AUC 0.621, his KO share at 0.618, his round-1 share at 0.607.
The method model does NOT currently see any of it — it uses the frozen 14 plus
symmetric sums of the panel stats, which carry rates (knockdowns, submission
attempts) but never the actual method mix of a fighter's wins.

Four measures, each built in the leakage-safe walk from prior bouts only:

    M1  own finish rate            finishes / fights
    M2  KO share of own finishes
    M3  submission share of own finishes
    M4  round-1 share of own finishes

Two targets:

    T1  the five-way method outcome (a by KO, a by sub, b by KO, b by sub,
        decision), scored by multinomial log loss
    T2  the fight ends in round 1, scored by log loss

Each measure added individually to the current feature set. Eight tests,
Benjamini-Hochberg at FDR 0.10. Bootstrap over 600 resamples for each p-value.
The holdout is spent, so anything supported is a forward candidate, not an
adoption.

Prior: moderate for T1, low for T2. The AUCs above are real but modest, and
the model already holds knockdown and submission rates, which are the
mechanisms a method mix would work through. The honest expectation is that most
of the signal is already carried and the increment is small.

## Addendum 29: RESULT (2026-09-26)

**One of eight supported, and it is small.** Held out on 1,300 bouts.

| target | measure | gain | p | BH |
|---|---|---|---|---|
| **method (five-way)** | **own finish rate** | **+0.0016** | .0017 | .0125 |
| ends in round 1 | sub share | 0.0000 | .0017 | .0250 |
| ends in round 1 | KO share | 0.0000 | .0017 | .0375 |
| ends in round 1 | own finish rate | 0.0000 | .0017 | .0500 |
| ends in round 1 | round-1 share | 0.0000 | .0017 | .0625 |
| method (five-way) | round-1 share | -0.0005 | .250 | .0750 |
| method (five-way) | sub share | +0.0017 | .550 | .0875 |
| method (five-way) | KO share | +0.0017 | .560 | .1000 |

Only **own finish rate in the method model** clears its threshold with a
positive gain, at +0.0016 multinomial log loss. For scale, adopting the finish
formula was worth +0.005 Brier.

### A caution in these numbers

The four "ends in round 1" rows show a gain of 0.0000 with a p-value of .0017.
That is the bootstrap detecting a consistently-signed difference of around a
ten-thousandth of a nat — statistically distinguishable from zero and
practically nothing. They fail only because the gain is not positive. It is a
clean demonstration that a small p-value is not a finding, and the reason this
project reports effect sizes beside every p.

Note also that KO share and submission share show gains of +0.0017 — the same
size as the survivor — at p = .55. The difference between them is not the
effect but its consistency across resamples.

### Decision

**Not adopted.** The holdout is spent, so a single survivor at this effect size
is a forward candidate, and the site's method and round projections are
unchanged. The career breakdown stays where it is: displayed beside the
projection as context, not folded into it.

The reason is in the registration and it held: the model already carries
knockdown and submission rates, which are the mechanisms a method mix works
through. Most of the signal measured on its own (AUC 0.62) is already inside
the model by another route.

---

# Addendum 30: championship-round experience (2026-09-26)

Registered before fitting. Distinct from the fortitude cluster (addendum 6,
0 of 6), which measured late-round *output*. This measures *exposure*: has a
fighter been in a five-round fight before, and has he actually contested
rounds four and five?

    E1  has fought a scheduled five-round bout before (0/1, differenced)
    E2  prior minutes contested beyond 15:00 (differenced)
    E3  E1 summed across both corners (for the fight-level target)
    E4  E2 summed across both corners

Two targets, on five-round bouts only:

    T1  the win, model = the frozen 14 plus the measure
    T2  the fight reaches round 4

Four tests, Benjamini-Hochberg at FDR 0.10, bootstrap over 600 resamples.

**Power, stated up front.** There are 673 five-round bouts since 2012, so a
standard split leaves about 134 held out — too few for a modest effect. The
test slice is widened to 40% for power, and the confidence interval is reported
beside every gain. A null here means "not detectable in 270 bouts", not "zero",
and that distinction is recorded now rather than argued afterwards.

Prior: low. Experience overall is already in the model (`d_log_exp`), and the
fortitude family found nothing in late-round behaviour.

## Addendum 30: RESULT (2026-09-26)

**A forward candidate, after correcting my own baseline.**

First pass, against the frozen 14:

| target | measure | n | gain | 95% CI | p |
|---|---|---|---|---|---|
| reaches round 4 | both corners' championship minutes | 504 | +0.0288 | [+0.0123, +0.0451] | .0017 |
| reaches round 4 | both corners' five-round starts | 504 | +0.0011 | [+0.0003, +0.0021] | .010 |
| the win | championship minutes | 252 | -0.0008 | [-0.0050, +0.0031] | .65 |
| the win | has fought five rounds | 252 | +0.0007 | [-0.0060, +0.0076] | .90 |

That +0.0288 would have been the largest gain in this project. **It was mostly
a weak baseline.** The frozen 14 is a *win* model; it contains nothing that
predicts how long a fight lasts, so any duration-aware feature improves it.
The correct comparison is against the model that does predict duration.

Re-run against the finish-formula inputs (knockdowns, control, pace,
submissions, age gap):

| measure | gain | 95% CI | p |
|---|---|---|---|
| **championship minutes** | **+0.0091** | [+0.0004, +0.0175] | .037 |
| five-round starts | -0.0007 | [-0.0012, -0.0001] | .023 |

The effect survives at **a third of its apparent size**, with a lower bound a
hair above zero. The binary "has fought five rounds before" is worthless once
the minutes are available, and slightly harmful.

### Decision

**Not adopted; carried forward.** Minutes actually contested past the
fifteen-minute mark look like a real, small predictor of whether a five-round
fight goes deep — distinct from the fortitude family, which measured
performance rather than exposure, and found nothing. But this used a widened
40% test slice for power on a scarce bout type, the holdout is spent, and the
interval nearly touches zero. It needs forward confirmation on five-round bouts
before it changes anything.

Nothing on the site changes. Recorded with the first pass shown in full,
because the difference between +0.0288 and +0.0091 was entirely in the choice
of baseline, and that is the more useful lesson than either number.

---

# Addendum 31: average fight time (2026-09-26)

Registered before fitting. Neither the finish formula (knockdowns, control,
pace, submissions, age gap, weight, women, five rounds) nor the survival model
sees how long a fighter's fights actually tend to last.

    A1  sum of both fighters' average fight minutes
    A2  difference between them

Three targets, each against the **finish-formula inputs** as the baseline —
the model that already predicts duration, not the win model. Addendum 30
showed that testing a duration feature against the frozen 14 inflates the gain
threefold.

    T1  the fight ends inside the distance
    T2  the fight ends before round 2
    T3  a five-round fight reaches round 4

Six tests, Benjamini-Hochberg at FDR 0.10, bootstrap over 600 resamples.

Prior: low. Average fight time is close to a restatement of a fighter's finish
rate, which addendum 29 found worth only +0.0016 in the method model, and the
formula already holds knockdowns, control and pace — the mechanisms that make
fights short.

## Addendum 31: RESULT (2026-09-26)

**Three of six supported, and they survive a corrected baseline.**

The two fighters' average fight lengths, summed. The difference between them
does nothing on any target, which is right — how long a fight lasts is a
property of the pair, not of one corner.

First pass used an incomplete baseline (knockdowns, control, pace,
submissions, age gap) and omitted weight class, women and scheduled rounds —
the same error addendum 30 had just caught, made again one addendum later.
Both passes:

| target | n | incomplete baseline | **complete finish formula** |
|---|---|---|---|
| ends inside the distance | 1658 | +0.0125 | **+0.0096** [+0.0039, +0.0164] |
| ends before round 2 | 1658 | +0.0180 | **+0.0101** [+0.0054, +0.0150] |
| five-rounder reaches round 4 | 378 | +0.0196 | **+0.0132** [+0.0039, +0.0224] |

The inflation from the missing controls was about a third — heavyweight fights
are short and five-rounders are long, and average fight time was partly
standing in for both. After controlling properly, all three intervals still
exclude zero by a clear margin.

For scale, adopting the finish formula itself was worth +0.005 Brier. These are
the largest confirmed gains of any candidate tested since.

### Decision

**Carried forward, not adopted.** The holdout is spent, so nothing enters the
model on the strength of a retrospective test. Average fight time joins the
forward list with championship minutes (addendum 30) and the two betting rules.

### Why this one is different from the nulls

Fourteen families failed because they tried to extract a new *kind* of
information from seven fights of per-round totals. This asks for something the
feed records directly and completely: how long a fighter's fights last. No
inference, no reconstruction, no second moment of a noisy mean. That is the
same reason the count models in addendum 26 worked where the behavioural
families did not.

---

# Diagnosis: where the market's advantage actually lives (2026-09-26)

Asked whether anything could make a decisive improvement. Measured the shape
of the deficit rather than guessing.

Held out, 582 bouts with odds. The market beats the model by **0.0305 log
loss** overall. But:

| | |
|---|---|
| bouts where the MODEL is closer | **40%** |
| the worst 10 bouts | 38% of the whole gap |
| the worst 25 bouts | **80% of the whole gap** |
| median gap per bout | +0.051 |

The deficit is not diffuse. Twenty-five bouts out of 582 carry four fifths of
it.

## What those 25 have in common

| | worst 25 | the other 557 |
|---|---|---|
| thinner record (fights) | 4.68 | 6.56 |
| age gap | 4.47 | 4.45 |
| model-market disagreement | **29.0 points** | 10.0 points |
| model called the wrong side | **24 of 25** | — |
| market called the wrong side | **2 of 25** | — |

These are bouts where the model was confident, the market disagreed sharply,
and the market was right — on thinner records than average.

## What this means for "decisive"

A broad feature cannot fix this. Closing a 0.0305 gap with features of the size
this project has found (the best confirmed candidate, average fight time, is
worth about 0.010 on a duration target) would take roughly four independent
finds, and fourteen families have already failed to produce one for the win
model.

The realistic target is not the average bout. It is the twenty-five: fights
where something knowable — but not recorded in per-round totals — made a
confident projection wrong. Those are the candidates worth collecting, in
order of plausibility:

1. **Short-notice and replacement bouts.** Recorded on the Wikipedia event
   pages the bonus collector already fetches. A fighter taking a bout on two
   weeks' notice is a different fighter, and nothing in the corpus says so.
2. **Missed weight.** Same pages, same scrape. A depleted or oversized opponent
   changes a fight and leaves no trace in career rates.
3. **Layoff reason.** The model has layoff length but not whether it was injury,
   suspension or inactivity.

All three are situational facts about a single bout, which is precisely the
category the corpus has no column for, and the category the market prices well.
None is tested. Recorded here as the next thing worth trying, ahead of any
further feature engineering on the existing columns.

---

# Addendum 32: official UFC rankings (2026-09-26)

Registered before fitting. The diagnosis above found the deficit concentrated
in 25 bouts where the model was confident, the market disagreed by 29 points,
and the market was right. The category identified as missing was *external
judgment about a fighter* — something no per-round total records.

The odds file already carries one such judgment: the UFC's own divisional
rankings at the time of the bout. A ranking is a matchmaker's assessment,
informed by tape and reputation, and nothing in the corpus reflects it.

    K1  difference in divisional rank (unranked treated as 16)
    K2  one fighter ranked and the other not (signed)
    K3  the bout is a title fight

Target: the win, added individually to the frozen 14.

**Coverage, stated up front.** Only 18% of bouts have both fighters ranked and
29% have either. K1 is therefore tested twice: on all bouts with the unranked
encoding, and on the ranked-only subset, which is reported separately because
the second is a different population, not a robustness check.

Five tests, Benjamini-Hochberg at FDR 0.10, bootstrap over 600 resamples.

Prior: moderate. This is the first candidate tested that carries information
from outside the fight record rather than a new arrangement of it. Against
that, rankings follow results, so much of what they encode may already be in
Elo and strength of schedule.

## Addendum 32: RESULT (2026-09-26)

**Zero of five.** Every gain is negative or zero.

| population | measure | n | gain | 95% CI | p |
|---|---|---|---|---|---|
| all bouts | title bout | 829 | -0.0000 | [-0.0000, +0.0000] | .28 |
| both ranked | rank difference | 187 | -0.0048 | [-0.0188, +0.0099] | .54 |
| all bouts | rank difference | 829 | -0.0013 | [-0.0066, +0.0033] | .56 |
| all bouts | ranked vs unranked | 829 | -0.0009 | [-0.0048, +0.0021] | .59 |
| both ranked | title bout | 187 | +0.0000 | [-0.0000, +0.0000] | .80 |

Matched 8,334 bouts to rankings, 2,296 with both fighters ranked.

The prior named the reason it might fail, and that is what happened: rankings
follow results, so a ranked fighter is one who has been beating good
opposition — which is what Elo and strength of schedule already measure. The
UFC's judgment adds nothing the record has not already shown.

Worth noting what this rules out. Rankings were the best available proxy for
"external judgment about a fighter", and the one piece of that category
obtainable without new scraping. Its failure does not settle the three
candidates named in the diagnosis — short notice, missed weight, layoff reason
— because those are facts about *this bout's circumstances*, not assessments of
a fighter's quality. A ranking cannot tell you a fighter took the fight on
eleven days' notice.

That distinction is now the whole of the remaining hypothesis: the market's
advantage on those 25 bouts is situational, not evaluative. Rankings tested the
evaluative half and it is null.

---

# Validation: are the parlay contracts calibrated? (2026-09-26)

The round-and-method contracts (fighter x method x round) went on the site
without ever being checked. Only their marginals had been validated. Measured
on 10,680 contracts across 812 held-out fights — one hit at most per fight,
decisions contributing none.

| predicted band | n | predicted | actual |
|---|---|---|---|
| 0-2% | 3596 | 1.2% | 1.1% |
| 2-4% | 3311 | 2.9% | 2.3% |
| 4-6% | 1689 | 4.9% | 4.7% |
| 6-9% | 1153 | **7.3%** | **5.4%** |
| 9-14% | 625 | 11.0% | 12.3% |
| 14%+ | 306 | 19.1% | 17.6% |

Overall: predicted 4.05% per contract against 3.61% actual, Brier skill +3.4%
over a flat base rate.

**The bias is in the finish level, not the joint.** Per fight the raw survival
model predicts finishes at 53.3% against an actual 47.5%. Applying a single
rescale of 0.891 brings the contracts to 3.61% predicted against 3.61% actual,
with skill essentially unchanged at +3.5%.

Production already applies exactly this correction, using the finish formula
rather than a held-out average (addendum 15). So the contracts as published are
close to unbiased, and the shape of the joint — which contract within a fight
— is sound without adjustment.

**No further calibration applied.** The one band that stands out, 6-9%
predicting 7.3% against 5.4%, is 1,153 contracts drawn from 812 fights, so the
rows are not independent and the deviation is within what that dependence
allows. Fitting a correction to it would be fitting noise, and the rescale that
production already performs removes the bias that is real.

Worth noting the skill number is modest by construction: +3.4% against a flat
base rate is what a 20-way split of a mostly-decision outcome allows. The
meaningful check is the calibration table, and it holds.

---

# Addendum 33: distance rate of a fighter's own bouts (2026-09-26)

Registered before fitting. Addendum 29 tested a fighter's own FINISH rate —
his wins by stoppage over his fights. This is a different quantity: the share
of his bouts that went the distance at all, whoever won. A fighter who is
regularly finished contributes to short fights without ever finishing one, and
the win-only measure cannot see him.

    S1  sum of both fighters' distance rates (their bouts that reached a decision)
    S2  the same, differenced

Two targets, against the **complete finish formula inputs** (weight class,
women, knockdowns, control, pace, age gap, submissions, five rounds):

    T1  the fight ends inside the distance
    T2  the fight ends before round 2

And the question that decides what gets used: S1 tested **on top of average
fight time**, which addendum 31 found worth +0.0096 on T1. Average fight time
is largely a consequence of how often a fighter's bouts end early, so the two
may be the same signal twice.

Six tests, Benjamini-Hochberg at FDR 0.10, bootstrap over 600 resamples.

Prior: moderate for S1 alone, low for S1 on top of average fight time.

## Addendum 33: RESULT (2026-09-26)

**Zero of six, and the reason is the useful part.**

| target | measure | gain | 95% CI | p |
|---|---|---|---|---|
| ends before round 2 | distance rate (sum) | +0.0041 | [+0.0003, +0.0073] | .037 |
| ends inside the distance | distance rate (sum) | +0.0047 | [-0.0007, +0.0102] | .093 |
| ends before round 2 | **on top of average fight time** | +0.0000 | [-0.0000, +0.0001] | .32 |
| ends inside the distance | **on top of average fight time** | -0.0004 | [-0.0020, +0.0011] | .55 |
| both targets | distance rate (difference) | 0.0000 | — | — |

On its own the distance rate does carry signal — +0.0047 and +0.0041, the right
sign and roughly the size expected. Neither cleared its BH threshold, and the
round-2 row missed by a hair (.037 against .0333).

**But on top of average fight time it is worth nothing at all.** They are the
same signal measured two ways, and the minutes version is the stronger carrier:
+0.0096 against +0.0047 on the same target, same baseline, same split.

That answers the question as asked. Screening for likely-finish matchups on
the share of a fighter's bouts that reached a decision is a sound idea, and the
model captures it better through how long his fights actually last. A rate
throws away the difference between a first-round knockout and a stoppage at
14:50; the minutes keep it.

The differenced version is exactly zero on both targets, as it should be —
whether a fight goes long is a property of the pair, not of one corner. Same
result as average fight time, which is another sign the two are one signal.

No change. Average fight time remains the forward candidate; the distance rate
is redundant with it and is not carried forward.

---

# Addendum 34: does a gating rule beat smooth use of the same inputs? (2026-09-26)

Registered before fitting. Proposal: gate on a threshold (each fighter's
finish share of wins exceeds his decision share), then weigh method mix
against the opponent, then consult the per-round breakdown — with a
second-order filter on the pair's combined decision rate.

This is a decision tree specified by hand. The question is not whether the
inputs matter — addendums 29, 31 and 33 measured that — but whether the
**gating structure** adds anything a model would not find on its own.

Four models, same target (the fight ends inside the distance), same baseline
(complete finish formula inputs), same split:

    G0  baseline only
    G1  baseline + the inputs entered smoothly (finish share, method mix,
        average fight time, distance rate), linear
    G2  baseline + the same inputs, gradient boosted — free to discover any
        threshold or interaction in them
    G3  baseline + the hand-specified gate as a binary, plus its second-order
        filter (combined decision rate below 50%)

If G3 beats G1 and G2, the structure is doing work. If G2 >= G3, the gate is a
worse version of something a tree finds automatically. If all three sit near
G0, the inputs were already carried.

Prior: the gate adds nothing over G2. Trees exist to find thresholds, and
nothing about the proposed one is unavailable to a model given the same
columns. The interesting outcome is G1 vs G2 — whether the signal in these
inputs is smooth or genuinely threshold-shaped.

## Addendum 34: RESULT (2026-09-26)

**The inputs are worth having. The gate is not.** Held out on 1,326 bouts,
target = the fight ends inside the distance.

| | log loss |
|---|---|
| G0 baseline (finish formula inputs) | .6599 |
| **G1 + the inputs, entered smoothly** | **.6466** |
| G2 + the same inputs, gradient boosted | .6774 |
| G3 + the hand-specified gate and its filter | .6537 |
| G3b + gate, filter AND the smooth inputs | .6470 |

Three things, in order of usefulness.

**The gate is a lossy version of the inputs.** G3 (.6537) beats the baseline,
so the rule is picking up something real — but G1 (.6466) beats it using the
same information without the threshold. And adding the gate to the smooth
inputs (G3b, .6470) is no better than the smooth inputs alone. The gate throws
away the difference between a fighter who finishes 51% of the time and one who
finishes 90%, and nothing is gained back by the structure.

**The signal is smooth, not threshold-shaped.** The prediction registered above
was that the interesting comparison would be G1 against G2. Gradient boosting,
free to find any threshold in these columns, came out **worst of all** at
.6774 — worse than the baseline. With five inputs over ~5,000 training bouts
it fits noise that a linear model cannot. If the relationship had a genuine
cliff in it, the tree would have found it and won.

**The features themselves are a real gain: .6599 to .6466.** That is larger
than anything in addendums 29 to 33, because it is all of them at once —
finish share, method mix, distance rate and average fight time entered
together.

### Decision

No change to the model. The holdout is spent and this was a structural test,
not a registered adoption. But it sharpens the forward candidate: what goes on
the forward list is **the block of career-outcome inputs entered smoothly**,
not average fight time alone, and not any gating rule.

Recorded because the instinct behind the proposal was right — these inputs do
predict finishes — and the specific mechanism proposed was the one part that
does not help.

---

# Addendum 35: base-rate condition C13, combined decision share (2026-09-26)

Registered before building, as conditions C1 to C12 were (addendums 10 to 12).

    C13  measure  the pair's average decision share of their wins
         outcome  the fight ends inside the distance
         level    fight
         why      two fighters who win by decision produce decisions

Descriptive, measured across every fight since 2012 with both fighters holding
at least two wins on record. Reported the same way as every other row: the
outcome rate in the lowest and highest quartile of the measure, against the
rate across all fights, with the same significance marking.

The marginal relationship is already measured (2026-09-26):

| pair's average decision share | n | finish rate |
|---|---|---|
| 0-15% | 149 | 71.8% |
| 15-30% | 594 | 60.6% |
| 30-45% | 850 | 54.1% |
| 45-60% | 842 | 46.4% |
| 60-75% | 586 | 37.5% |
| 75-100% | 226 | 31.0% |

Monotone across six bands with non-overlapping intervals at the ends. The gap
BETWEEN the two fighters is flat (48.7%, 51.6%, 47.2%, 50.3%), so the level is
the measure and the mismatch is not.

**This row is labelled "same measure", not "different measure".** The share of
a fighter's wins that went to decision, predicting whether this fight goes to
decision, is close to definitional — the same relationship C1 has for
takedowns. It earns a place as context, not as a discovery, and the panel's own
labelling must say so.

It is also NOT a model feature: addendum 33 found this quantity worth +0.0047
against the finish formula and nothing at all on top of average fight time.
Most of what the table above shows is already inside the projection beside it.

## Addendum 35: AMENDMENT (2026-09-26)

C13 originally measured the decision share of a fighter's **wins**. Changed to
the share of **all his bouts** that went the distance, won or lost, after
measuring both on 3,039 fights:

| measure | AUC | Q1 to Q4 |
|---|---|---|
| decision share of WINS | 0.623 | 62.5% to 35.3% (27 points) |
| **decision share of ALL bouts** | **0.647** | **67.8% to 33.2% (35 points)** |
| both together | no better than all-bouts alone (.6605 against .6599) |

A fighter who is regularly finished contributes to short fights without ever
finishing one, and the wins-only version cannot see him. The two correlate at
0.87, and the wins-only measure adds nothing once the participation version is
present, so it is replaced rather than joined.

The registered quartiles become 66.1 / 50.8 / 43.9 / 33.1 against a 48.8% base,
and the row's caption now says what it counts. Minimum raised from two wins to
three bouts on record.

This is an amendment, not a result: C13 is a descriptive panel row, and
choosing the better of two ways to measure the same registered idea is a
definition being sharpened before any claim rests on it.

---

# Addendum 36: pre-UFC records for thin fighters (2026-09-26)

Registered before collecting. This revives addendum 18 with a narrower target,
because a measurement changed the case for it.

## Why the earlier null does not settle this

The 2026-09-26 saturation test found that a fighter's finish profile stops
improving after a handful of bouts — 11 or more prior fights predicts no better
than 2 or 3 (AUC +0.013, interval [-0.017, +0.046]). That answered: **does more
history help a fighter who already has some?** No.

It did not answer: **does any history help a fighter who has none?** For a
debutant the model currently has nothing, and the site prints "no read".

That population is not marginal:

| prior UFC bouts | share of fighter-appearances since 2020 |
|---|---|
| debut, no record at all | 10.9% |
| 1 prior fight | 10.2% |
| 2-3 | 17.9% |
| 4-9 | 32.9% |
| 10 or more | 28.1% |

**21.1% of appearances are thin**, touching about 4.5 of the 12 bouts on a
typical card. Even at 2-3 prior bouts the finish signal is weak (AUC 0.570
against 0.592 at 4-6), so the useful range extends past the debutants.

## Sequence, and the gate that comes first

**Step 1 is coverage, not prediction.** A record source is useless here if it
misses precisely the fighters it is needed for. Before any model work:

    pull the last 12 months of debutants and one-fight fighters, and report
    what share have a retrievable professional record with a method split

**Bar: 70%.** Below that the feature cannot do its job, and the honest outcome
is to stop — a record present for the well-known half of debutants and absent
for the obscure half would add signal exactly where it is least needed.

**Step 2, only if the bar is cleared:** pre-UFC record and method split enter
as features for fighters with 3 or fewer UFC bouts, tested against the current
thin-record handling on the win, finish and method targets.

## On the source

Wikipedia is what the existing collector reads, and its weakness is the
population that matters: a fighter with no UFC bout often has no article. An
ESPN athlete endpoint would plausibly cover signed fighters better, since a
fighter appears there once matched. Neither can be checked from here.

The choice is settled by step 1 and nothing else: run the coverage count on
both, take whichever clears 70%, and prefer the more stable interface if both
do. Wikipedia has a documented API and an existing collector; an undocumented
endpoint is a maintenance risk, not a correctness one.

Prior: moderate for the thin population, low for everyone else. A regional
record against weak opposition is poor evidence, but it is being compared
against no evidence at all.

## Addendum 36: NOT PURSUED (2026-09-27)

The coverage probe was built and shipped but never ran: it failed on a missing
corpus, because the record workflow has no scrape step and the UFCStats CSVs
are not committed. That is a one-line fix, and it is not being made.

Decision: the model stays **UFC-only**. Pre-UFC records are not collected, and
step 2 is not attempted.

The reasoning stands where addendum 36 left it — 21% of fighter-appearances are
thin, and for those the comparison is against nothing rather than against good
data — so this is a choice, not a finding. What it buys:

- one source, one definition, one boundary. Every number on the site means
  "in the UFC", including average fight time, the method splits, the career
  records and C13. A mixed denominator would need explaining on every row.
- no dependency on an undocumented endpoint that can change without notice.
- no risk of a record present for well-known debutants and absent for obscure
  ones, which is signal arriving exactly where it is least needed.

`mmastat/record_probe.py` and `workflows/records.yml` stay in the tree unrun.
If the question is reopened, the gate is already written and the bar is already
fixed at 70%, which is the part that is hard to do honestly after the fact.

---

# Audit: which drivers actually carry the model? (2026-09-27)

Descriptive. Every feature in the frozen 14, measured two ways on 829 held-out
bouts: predictive power **alone**, and the cost of **removing it** from the
full model. Full-model log loss is 0.6208.

| driver | AUC alone | cost of removing |
|---|---|---|
| **age** | **0.664** | **+0.0178** |
| UFC mileage | 0.617 | +0.0027 |
| striking accuracy | 0.611 | +0.0010 |
| takedown threat | 0.607 | +0.0033 |
| **strikes absorbed** | 0.606 | **+0.0062** |
| submission threat | 0.584 | -0.0002 |
| layoff | 0.582 | -0.0013 |
| **career quality** | 0.573 | **+0.0055** |
| **strength of schedule** | 0.532 | **+0.0058** |
| striking defense | 0.529 | -0.0009 |
| losses by strikes | 0.521 | +0.0001 |
| reach | 0.520 | -0.0003 |
| striking vs chin | 0.510 | +0.0000 |
| striking output | 0.505 | +0.0009 |

## Age is the only outlier on both measures

At 0.664 alone it is 47 points clear of the next feature, and removing it costs
**three times** more than removing anything else. Nothing here rivals it.

## The two measures disagree, and that is the finding

**Strength of schedule looks useless alone (0.532) and is the second most
valuable thing in the model (+0.0058).** It only means anything once career
rating is present: a rating of 1550 says one thing against tough opposition and
another against weak. Career quality behaves the same way at a smaller scale.

Running the other way, **UFC mileage, striking accuracy, submission threat and
layoff all look strong alone and contribute nothing at the margin** — three of
the four are negative, meaning the model is very slightly better without them.
They are proxies for what age and the ratings already carry.

## Four features currently earn nothing

Submission threat, layoff, striking defense and reach all cost nothing or less
than nothing to remove, and striking vs chin sits at exactly 0.0000. Reach was
noted on 2026-09-26 as dead weight; this confirms it and adds three more.

**No change made.** Removing a feature from the frozen set needs its own
registration and a held-out test, and this holdout is spent. Recorded so the
next model revision starts from evidence rather than from the original
selection, which was made on a different slice of data and has not been
revisited since.

## Addendum 9: AMENDMENT — venue (2026-09-27)

The frozen rule says "Polymarket distance markets". It was written when the
global book was the only one; the CFTC-regulated US exchange now quotes the
same markets, and global capture has been retired.

**The rule runs on polymarket_us.** Nothing else about it changes — the
probability, the 0.05 trigger, the flat stake, the 200-bet bar and the +2% ROI
success line all stand as registered. The liquidity gates (spread <= 6c,
depth >= $250) apply to the US book's order book.

Why the change: a US reader cannot trade the global book, nothing on the site
ever displayed its prices, and holding two slug spaces at once produced every
mis-linked "verify" in this area. No bet has settled under this rule, so
nothing is being re-based mid-series.

The cost, stated plainly: a second price series that cannot be backfilled if it
is wanted later. `mmastat/polymarket.py` stays in the tree, unimported, with
the reason at the top.

## Addendum 37: RESULT — method mix does not move by year (2026-10-03)

Asked whether the KO / submission / decision split drifts year to year, so the
site could show "this year skews toward knockouts" against last year or a
three-year average. Measured on 6,913 decided bouts, 2012 through 2026.

**It does not move.** Three independent ways of asking agree:

- Homogeneity across all fifteen years: chi-square 29.8 on 28 df, **p = 0.37**.
  No evidence the underlying mix differs by year at all.
- The year-to-year scatter is the sample size and nothing else. Observed spread
  against what pure binomial variation gives at ~500 bouts a year: KO **1.02x**,
  submission **0.92x**, decision **1.20x**.
- No trend in any of the three: KO +0.10 pts/yr (p = 0.47), submission -0.14
  (p = 0.18), decision +0.03 (p = 0.85).

## The decisive test: does recency predict?

Walk-forward, base rate fitted only on years strictly before the test year,
scored by multiclass log loss on that year's actual bouts, 2016-2026:

| base rate | mean log loss |
|---|---|
| pooled, all prior years | **1.0179** |
| trailing 5 years | 1.0178 |
| trailing 3 years | 1.0187 |
| last year only | 1.0197 |

Identical to the fourth decimal, and **last year only — the version the feature
implied — is the worst of the four.** Recency buys nothing because there is no
signal to be recent about.

## 2026 is the trap this guards against

2026 sits at **37.2% KO against a 31.4% long-run rate**, which on its own tests
at p = 0.019 and looks like a story. It is one of fifteen years examined, so the
chance of something that extreme appearing *somewhere* in the series is about
one in four, and the year is partial — 390 bouts and still moving. Displaying it
would have been the single most prominent number on the site.

**Not built.** The base rates stay pooled. Recorded so this is not re-litigated:
the question is settled until the corpus roughly doubles, at which point a year
would be large enough for a real shift to clear the noise.

## Addendum 38: ADDITION — card shape panel (2026-10-03)

A descriptive readout at the top of the page, in the one unit the site did not
previously use: the whole card rather than the bout. Shows this card's projected
count of first-round finishes and of finishes inside the distance, each against
the same base rate scaled to the number of bouts actually modeled.

Not a new model and not a new market. The projection is the sum of the
per-bout `p_end_r1` the card already publishes; `mmastat/baserates.py:card_shape`
supplies the historical side.

## The assumption that had to be checked first

Summing per-bout probabilities is only legitimate if the per-card count is
binomial. If finishes clustered — a wild card where everyone swings — the real
spread would exceed a sum of independents and the panel would understate its own
error while looking precise.

**Measured over 596 cards: per-card variance is 1.02x what independent bouts
give.** No clustering. The ratio is recomputed on every build and published in
`baserates.json` as `card.overdispersion`, so the assumption is re-tested
continuously rather than resting on this one measurement.

## What it reports

A typical card is 12 bouts, of which **2.91** end in round one and **5.79**
inside the distance. Eight cards in ten land between 1 and 5 first-round
finishes; 2.7% have none. Of all knockouts **51%** land in round one, of all
submissions **48%**.

No bet is registered against this and no scoring rule changes. It is published
as history, in the same category as the division table.

## It is graded, because an ungraded claim is not a claim

The panel states two numbers before the fights, so both are scored afterwards.
`_card_tally` in `upcoming.py` runs inside `grade_archive` and the last-card
zone reports, for each: what was said, what happened, and what the base rate
alone would have said over the same bouts.

The base-rate column is the point. Landing near three first-round finishes when
three is simply the usual number is not a read, and without that column the
panel would score itself against nothing and look good for being unsurprising.

The comparison is restricted to the graded bouts, and the base rate is summed at
each bout's own scheduled length rather than applied flat — a five-round main
event has a different first-round rate than a three-round prelim, so a flat rate
times the bout count would hand the model an easier or harder target depending
on how many title fights the card happened to carry.

Verified against a hand computation on a real nine-bout card: every field of the
tally matches to the cent.

## Addendum 39: RESULT — stance (2026-10-04)

Asked again whether an open-stance matchup carries an edge. `d_southpaw` was
dropped from the feature set long ago as "no measurable effect" and H1 (leg
kicks x stance mismatch) failed in addendum 1 at beta -0.0513 with the wrong
sign, but neither is quite the plain question, so it was measured directly on
5,963 bouts with both stances known.

- **Raw: southpaws beat orthodox 1,013 of 1,923 = 52.7%**, 95% CI
  [50.4%, 54.9%], p = 0.020.
- Open-stance bouts finish slightly more often, 51.6% vs 49.2%, p = 0.084.

## Conditional on the model, which is the test that decides it

Trained to 2024-01-01, tested on 1,468 later bouts:

| | out-of-sample log loss |
|---|---|
| model as frozen | 0.61665 |
| + signed stance matchup | 0.61562 |

**-0.00104, P(helps) = 0.934, bootstrap 95% CI [-0.00246, +0.00035].** The
residual in open-stance bouts leans to the southpaw by +0.041 at p = 0.172.

Below the bar, interval crosses zero, and an order of magnitude smaller than
addendum 30's championship-minutes candidate at +0.0091. Most of the raw 52.7%
is southpaws being slightly stronger fighters, which `d_elo` already carries.

**No change made.** Forward candidate alongside 30, 31 and 34. The registered
holdout is spent, so it could not be confirmed now in any case.

---

# Addendum 41: RESULT - ape index, standalone and interacted (2026-10-04)

Asked whether reach relative to frame - (reach - height), the ape index -
predicts outcome, "if not standalone possibly in relation to other
factors/metrics". The examples offered were Jones, McGregor and Volkanovski,
all of whom do carry large positive ape indices.

Standalone was already answered: addendum 12 tested it as F3 and got +0.0001,
p = .505, failing BH. This re-tests it on the current corpus and then does the
part addendum 12 never did - interactions.

## The raw effect is real

On 9,626 mirrored rows with both corners' reach actually measured, win rate
rises monotonically with the ape-index edge:

| ape-index edge | bouts | win rate |
|---|---|---|
| -4in or worse | 789 | 45.5% |
| -4 to -2 | 1,915 | 48.3% |
| -2 to -0.5 | 1,344 | 49.9% |
| even | 1,530 | 50.0% |
| +0.5 to +2 | 2,471 | 50.5% |
| +2 to +4 | 1,202 | 52.9% |
| +4in or better | 375 | 56.3% |

Point-biserial r = +0.0474, p < 0.001. The intuition is not wrong at the
surface.

## But plain reach carries it, and carries more

r = +0.0727 for `d_reach` against +0.0474 for ape index, and the two correlate
at +0.666. Fitted together with nothing else in the model:

| fitted | d_reach | d_ape |
|---|---|---|
| ape alone | - | **+0.0949** |
| reach alone | +0.1461 | - |
| both | +0.1485 | **-0.0036** |

**Put reach beside it and 96% of the ape coefficient is absorbed.** Nearly all
of the raw ape-index effect is long-armed fighters winning, which `d_reach`
already holds. This is the same finding that put `d_height` in `DROPPED` as
"carried by d_reach", now measured rather than asserted.

Conditional on the frozen 14, trained to 2024-01-01 and tested on 1,872 later
rows: **-0.00060** all bouts, **-0.00049** measured-reach-only, P(helps) 0.14
and 0.16. It makes the model slightly worse.

## Interacted: zero of five

Registered family, BH at FDR 0.10, each with a stated mechanism:

| candidate | gain | 95% CI | p | BH |
|---|---|---|---|---|
| B1 ape x striking accuracy | -0.00061 | [-0.00181,+0.00062] | .313 | .020 |
| B3 long arms on a short frame | -0.00075 | [-0.00243,+0.00086] | .366 | .040 |
| B4 ape x takedown defense | -0.00040 | [-0.00135,+0.00056] | .407 | .060 |
| B2 ape x striking volume | -0.00077 | [-0.00262,+0.00101] | .411 | .080 |
| B5 ape x absorbed strikes | -0.00005 | [-0.00329,+0.00293] | .945 | .100 |

**Zero of five, every gain negative.** B3 was the Volkanovski shape explicitly -
long arms on a short frame - and it is the second worst of the five.

Ape index also does not predict the method. Among finishes, winners with a +2in
or better ape edge scored KO/TKO in 63.7% of them against 68.3% for winners at
-2in or worse: the wrong direction, p = 0.189.

## A structural trap worth recording

The first interaction family returned **identical gains to five decimals for
four different formulas**, which is a bug signature, not a result. Cause: every
model feature is antisymmetric, and the product of two antisymmetric
differentials is *symmetric* - it takes the same value in both orientations
while y flips. Under `fit_intercept=False` on a mirrored corpus its coefficient
is provably zero. Four candidates were structurally incapable of contributing
and would have been reported as null findings.

Interactions must be built from per-corner LEVELS and differenced, the way
`grapple_edge` already is: `a_ape * a_str_acc - b_ape * b_str_acc`. Verified
equal-and-opposite across orientations before the family was re-run. **Any
future interaction candidate in this project has to clear this check first.**

## As a knockdown component, which is the one place it had standing

Asked separately whether ape index belongs in the knockdown aggregation rather
than the win model. This is a better question than it looks. `PANEL_OWN`
already carries reach AND height, so in a LINEAR model ape index is exactly
collinear with features already present - it could not contribute by
construction. But the event targets are fit with `HistGradientBoostingClassifier`,
and a tree cannot build `reach - height` from axis-aligned splits. Handing a
tree the difference explicitly is genuinely new information even when both
components are already inputs.

Tested on the projection panel, 7,270 train / 1,282 test rows, `own_ape` and
`opp_ape` added to `FEATS`:

| target | AUC as shipped | + ape index | change | P(helps) |
|---|---|---|---|---|
| **knockdown** (>=1) | 0.6818 | 0.6788 | **-0.0030** | 0.316 |
| takedown (>=1), control | 0.7327 | 0.7325 | -0.0002 | 0.463 |

95% CI on the knockdown AUC change [-0.0159, +0.0090]. Brier and log loss agree.
The takedown row is a control: a limb-length measure should do nothing there,
and it does nothing, which says the test can tell the difference.

**No.** The one structural argument for ape index - that a tree cannot
construct it - was tested on the model where it applies, and it still does not
help.

## Everywhere else it could go

Asked whether it fits anywhere else - the takedown aggregation, the other
projections. Swept across every remaining target in the codebase rather than
answering one at a time. Panel split 7,270 train / 1,282 test; survival model
split on the same 0.85 date quantile it uses in production.

| model | target | metric | as shipped | + ape index | change |
|---|---|---|---|---|---|
| event (tree) | knockdown >=1 | AUC | 0.6818 | 0.6788 | **-0.0030** |
| event (tree) | takedown >=1 | AUC | 0.7327 | 0.7325 | -0.0002 |
| mean (tree) | strikes per min | MAE | 2.0525 | 2.0641 | -0.0117 |
| mean (tree) | takedowns per 15 | MAE | 1.4697 | 1.4654 | **+0.0044** |
| mean (tree) | control time sec/min | MAE | 8.6135 | 8.6203 | -0.0068 |
| mean (tree) | knockdowns per 15 | MAE | 1.6184 | 1.6317 | -0.0132 |
| competing risks | method + round, per interval | multiclass log loss | 0.21989 | 0.22037 | -0.00048 |

For MAE, positive change = ape index helps. The single positive row is takedowns
at +0.0044 with P(helps) = 0.758, nowhere near the bar and the weakest possible
reading of a four-target sweep.

The competing-risks test is the one that deserved its own shot. That model takes
`WIN_FEATURES` plus SYMMETRIC sums over `PANEL_OWN`, so ape index enters twice
and in two different roles: `d_ape` for who, and `sum_ape` - both fighters' arms
against both frames - for whether and when. The hypothesis was specific and
reasonable: two long-armed fighters fight at range, trade less cleanly and go to
decision more often. It is also a tree, so the collinearity argument does not
apply. It came back **-0.00048**.

## The count so far

Ten tests, across every model in this project:

- win model, standalone: **-0.00060**
- win model, five interactions under BH: **0 of 5**, all negative
- knockdown event, takedown event: both negative
- four continuous projection targets: three negative, one +0.0044 at P = 0.758
- competing risks (method and round): **-0.00048**
- method among finishes, descriptive: wrong direction, p = 0.189

**The question is closed.** Ape index is not a missing input to this model in
any of the places it could have been one.

## On the champions

Jones, McGregor and Volkanovski all have large positive ape indices, and this
is selection on the outcome: champions are picked because they are champions,
and the corpus contains long-armed fighters at every level of success. The
+4in bucket wins 56.3% of the time, which is a real edge and also 3.9% of
bouts - and `d_reach` already prices most of it.

**No change made.** Not a forward candidate either: unlike stance (39) or
championship minutes (30), it points the wrong way standalone and in all five
interactions.


---

# Addendum 42: PILOT - leg reach and the intermembral index (2026-10-04)

Asked whether arm length relative to LEG length correlates with outcome, and
then whether it could be backtested cheaply before committing to collection.
Both answered here. **Registered before any backfill exists**, so the eventual
test cannot be reverse-fitted to it.

## The corpus cannot answer this at all

UFCStats carries `HEIGHT, WEIGHT, REACH, STANCE, DOB` and nothing else. The one
leg-ish column in the stats file is HEAD/BODY/LEG strike targets, not
anthropometry. There is **no leg-reach data anywhere in the corpus**, for any
fighter, in any year. Unlike ape index this is not measured-and-null, it is
unmeasurable with what we hold.

UFC.com does publish it, and keeps pages after a fighter leaves: Ben Rothwell,
last fought 2021, still lists leg reach 43.00.

## Why a 42-fighter pilot can decide this

Ape index failed for a specific, diagnosable reason: it is a linear combination
of reach and height, so `R2(ape ~ height + reach) = 1.000` BY CONSTRUCTION and
`d_reach` absorbed 96% of its coefficient. That failure mode is testable on a
small sample, because it is about redundancy, not effect size. If leg reach is
similarly determined by what we already hold, the backfill is wasted before it
starts.

42 fighters collected from UFC.com, deliberately spanning flyweight to
heavyweight and both men's and women's divisions (height 64-77in, leg reach
36.0-46.0in). The pilot rows were not retained - see the result below.

| | result |
|---|---|
| `R2(leg_reach ~ height + reach)` | **0.739**, bootstrap 95% CI [0.540, 0.891] |
| residual SD - the genuinely new variation | **1.50 in** |
| `R2(intermembral ~ height + reach)` | **0.347** |
| corr(leg reach, height) - measurement sanity | **+0.858** |
| corr(intermembral, ape index) | +0.587 |

**The precondition passes.** Leg reach is NOT determined by height and reach:
roughly a quarter of its variance is new, worth 1.50in of per-fighter spread
against the 1.97in that real measured ape index carried - an input the corpus
demonstrably could resolve, since ape index produced a visible 45.5% -> 56.3%
raw gradient. The intermembral index is only 35% explained by what we hold,
where ape index was 100%. The +0.858 correlation with height says the
measurement behaves like a real body measurement rather than noise.

## What the pilot does NOT establish

It tests whether the input is NEW, not whether it PREDICTS. Ape index also had
a real raw gradient and still failed ten tests. Passing here earns the
collection, nothing more.

Three live risks:

1. **n = 42 and all of them ranked or champion-tier**, because recognisable
   names were needed to be sure of the URL slugs. The full roster may carry a
   different relationship.
2. **The CI on R2 is wide**, [0.540, 0.891]. At the pessimistic end the new
   variation falls to about 1.0in.
3. **Outliers may be bad data rather than real build variation.** Miocic reads
   77in tall with a 39.0in leg reach, 5.4in below prediction; Ankalaev reads
   75in with 46.0in, 3.0in above. A 7in gap on 2in of height is either genuine
   or inconsistent measurement, and the pilot cannot tell the two apart. If it
   is noise, it inflates the apparent new variation and the backfill buys
   nothing.

## Stage 2: a RANDOM sample, which is what the elite one could not tell us

The 42 were ranked fighters picked for slug-guessability, and the residual test
exposed how biased that is: the model under-predicts them by **+0.152** on
average, because champions over-perform by construction. A residual slope on
that sample came back -0.0025 win-prob per SD of index, cluster-bootstrapped by
fighter (36 clusters, not 504 rows) at 95% CI [-0.0323, +0.0247] - a null, but
an underpowered null on a skewed sample, so it decides nothing.

So 21 fighters were drawn at RANDOM from corpus fighters with >=6 bouts. Two
pages could not be read (robots.txt on one, HTTP 429 on another) and were
dropped rather than guessed. Of the 19 read:

| | |
|---|---|
| leg reach present | **15 of 19 (79%)** |
| missing | Hester, Brilz, Coleman, Simpson |

**The missingness is entirely era-based, and it separates perfectly.** Last
corpus appearance of the fighters WITH leg reach: 2016, 2019, 2019, 2020, 2021,
2022, and ten in 2026. Without: 2010, 2011, 2013, 2014. No overlap at all.

This is the single most useful thing the pilot found, and it is good news.
Era-based missingness is **not outcome-based** - it does not preferentially drop
losers, it just truncates the usable corpus to roughly 2016 onward:

| window | mirrored rows | fighters |
|---|---|---|
| 2012+ (full) | 8,382 | 1,488 |
| **2016+ (usable)** | **6,682** | **1,258** |
| 2018+ | 5,534 | 1,104 |

Restricting to 2016+ keeps **68%** of the corpus and costs only **1.21x** in
minimum detectable effect against the ape-index test. That is an acceptable
price, and far better than the selection-on-success that was feared.

## The elite-bias risk is retired

R2 re-estimated on all **57** fighters, now including fifteen journeymen and
women's-division fighters drawn at random:

| sample | R2(leg ~ height+reach) | residual SD |
|---|---|---|
| 42 elite only | 0.739 | 1.50 in |
| **57 incl. random journeymen** | **0.709** | **1.46 in** |

Barely moved. Risk 1 from stage 1 is closed: the relationship is not an artifact
of sampling champions.

## Collection constraints, measured

- `ufc.com/robots.txt` does **not** disallow `/athlete/`, but sets
  **crawl-delay: 15**. At 15s, 1,258 fighters is ~5.2 hours - too long for one
  Action run. Chunked at ~120 per daily run it is **~11 days**, and polite.
- `/athletes/all?*` IS disallowed, so the roster index cannot be crawled to
  enumerate fighters. Slugs must be built from names.
- Slug construction `first-last` lowercased and hyphenated resolved on **21 of
  21** attempts; the two failures were fetch-layer (robots, 429), not wrong
  URLs. Duplicate common names may take a `-1` suffix on UFC.com and will need
  handling.
- Corpus-side name matching hit **41 of 42**; the miss was Zhang Weili
  (surname-first), the exact failure mode `aliases.txt` exists for.

## Verdict after two stages

**Proceed, scoped to 2016+.** The precondition that killed ape index does not
hold here (R2 0.709, not 1.000), the elite-sampling worry is measured and gone,
and the missingness is benign. One risk stays open and cannot be closed without
collecting: whether outliers like Miocic's 39.0in leg reach at 77in tall are
real build variation or inconsistent measurement.

## Registered bars, fixed now

If the backfill proceeds, the test is the same shape as every other candidate
and must clear the same bar:

- Entered as `d_intermembral` (directional) and `sum_intermembral` (symmetric)
  built from LEVELS, per addendum 41's antisymmetry trap.
- Win model: out-of-sample log-loss gain with bootstrap 95% CI excluding zero.
- Projections and competing risks: the sweep in addendum 41, BH at FDR 0.10.
- Window is **2016-01-01 onward** (6,682 rows), fixed now by the era finding,
  not chosen later from results.
- **Coverage must reach 2,500 usable BOUTS** before any result is reported;
  below that, coverage is reported first and the test is not run. See the
  amendment below for why this replaced a fighter-count bar.

### Amendment, 2026-10-05: the bar is bouts, not fighters

The original bar read "80% of the 1,258 fighters". That was the wrong unit. The
feature is a DIFFERENTIAL, so a bout is only usable when BOTH corners are
collected, and fighter coverage and bout coverage are not proportional: the
most active fighters are heavily interconnected, because fighters face others
in their own division and era.

| fighters collected | usable bouts | share of window | fetch time |
|---|---|---|---|
| 100 | 542 | 8% | 0.4h |
| **400** | **3,144** | **47%** | **1.7h** |
| 600 | 4,568 | 68% | 2.5h |
| 1,258 | 6,682 | 100% | 5.2h |

At 3,144 rows the smallest detectable correlation is **r = 0.035**, below the
**r = 0.047** ape index showed. So 400 fighters is already a decisive test, not
a hint, at a third of the collection cost. `targets()` now returns fighters
most-active-first so the collection can be stopped at any point and what exists
is the most useful subset rather than an arbitrary one.

**This amends a bar registered yesterday, which deserves saying plainly.** It
is legitimate here only because the change was made BEFORE any leg-reach data
existed, for a reason with no connection to any result - the unit was simply
wrong - and because the new bar is stated in advance and is *harder* in the way
that matters: 2,500 usable bouts is a real power floor, where "80% of fighters"
was a proxy that could have been satisfied while leaving the test underpowered.
A bar moved after seeing results would not be defensible and this one must not
be cited as precedent for that.
- Fighters whose leg reach departs more than 4in from the height+reach
  prediction are flagged and the test is reported with and without them.

### Amendment, 2026-10-05: an externally supplied dataset must pass a control

The user offered to furnish leg reach from another assistant rather than wait
for the crawl. That is fine for SPEED and dangerous for VALIDITY, and the
difference is whether the numbers were read off ufc.com or recalled. Leg reach
is an obscure field; a language model asked for 400 of them from memory will
produce plausible, well-shaped, entirely invented values - and this whole
candidate rests on the claim that leg reach carries 1.46in of real variation
that height and reach do not explain. Confabulated numbers would manufacture
exactly that variation out of nothing, and could produce a spurious positive.

So the request list of 400 (the most active since 2016, 3,144 usable bouts)
deliberately includes **60 fighters whose real UFC.com values are already in
`legreach_pilot.csv`**, mixed in unmarked. They are the control.

**Acceptance criteria, fixed now, before any data is seen:**

1. **Mean absolute error on the 60 controls < 1.0 inch.** UFC.com reports to
   0.5in, so a reading source should land near-exact; 1.0in allows for
   transcription slips without admitting guesswork.
2. **At least 80% of controls within +/-1.0 inch** of the known value.
3. **"unknown" is not penalised.** A source that declines on fighters it cannot
   read is behaving correctly, and the era finding predicts genuine gaps.
   Coverage below the 2,500-bout bar simply means the crawl still runs.
4. A returned set with **suspiciously few unknowns** - near-total coverage where
   the random sample found 79% - is itself a warning sign, not a success.

If the controls fail, the dataset is discarded whole, not patched, and
`legreach.yml` collects it properly. **A failed control is not a reason to
lower the bar**; it is the bar doing its job.

---

## Addendum 42: RESULT - intermembral index (2026-10-05)

Collected the same day it was registered. 374 fighters, **2,698 usable bouts**
in the 2016+ window, clearing the 2,500 bar. Data furnished from UFC.com via a
second assistant and verified against the control set throughout: **42 of 43
exact, mean error 0.035 inches**. Two disagreements the control flagged
(Blanchfield, Prochazka) were checked by the user directly on ufc.com and the
supplied values were wrong; both were corrected to the verified figures before
the test ran. The control did exactly the job it was registered to do.

**The data and the collector were then removed from the repo.** Leg reach is
not retrieved by any source the pipeline already pulls, and a measurement that
predicts nothing is not worth a daily crawl, a cache file or a module to
maintain. The numbers below ARE the result; they do not need the rows kept
behind them. If anyone revisits this, collection starts from scratch - which is
cheap, and avoids a stale file quietly rotting in the tree.

### The precondition held, and this is the part worth keeping

| | pilot (57) | full set (374) |
|---|---|---|
| R2(leg ~ height + reach) | 0.709 | **0.775** |
| residual SD | 1.46 in | **1.29 in** |

Leg reach is genuinely not derivable from what the corpus holds. And unlike ape
index, intermembral index is **not absorbed by reach** - it is a suppressor:

| fitted | d_reach | d_intermembral |
|---|---|---|
| intermembral alone | - | -0.0527 |
| reach alone | +0.1556 | - |
| **both** | **+0.1846** | **-0.1040** |

Its coefficient roughly DOUBLES next to reach, and reach's grows too. Ape index
collapsed from +0.0949 to -0.0036 in the same test. So this candidate cleared
the exact hurdle that killed the previous one.

### It still does not predict

| test | effect | p | BH threshold | |
|---|---|---|---|---|
| control time (MAE) | **-0.2274** | .000 | .017 | significantly WORSE |
| strikes per min (MAE) | +0.0418 | .067 | .033 | misses |
| knockdown >=1 (AUC) | +0.0148 | .197 | .050 | misses |
| win model (log loss) | +0.0023 | .256 | .067 | misses |
| competing risks (log loss) | -0.0023 | .300 | .083 | misses |
| takedown >=1 (AUC) | +0.0002 | .948 | .100 | misses |

**Zero of six supported, BH at FDR 0.10.** The win-model gain was +0.00226 all
bouts and +0.00303 with the five >4in outliers removed, 95% CI
[-0.00184, +0.00618] and [-0.00226, +0.00827] - both crossing zero.

Raw, the gradient runs the WRONG way: fighters with a much lower intermembral
index won 54.3%, much higher 45.7%, r = -0.0264 at p = 0.170. The direction the
original intuition predicted is not there even descriptively.

Control time is this family's kinetic-power row - the smallest p-value in the
set attached to a significantly NEGATIVE effect. A "keep whatever is
significant" search would have promoted a feature that makes projections worse.

`sum_intermembral` contributed exactly nothing to the win model, to five
decimal places. That is addendum 41's antisymmetry trap behaving as documented:
a symmetric feature has a provably zero coefficient on a mirrored corpus under
`fit_intercept=False`. It was carried into the competing-risks model, where
symmetric terms do act, and the pair still came back at -0.00234.

### What this null is, and is not

Ape index failed because it was redundant. Intermembral index is **not**
redundant and still fails, which is a cleaner and more informative result: arm
length relative to leg length is real, measurable, independent information
about a fighter's build that does not predict who wins, how, or when.

Scope: fighters active roughly 2016 onward, since the era-based missingness
documented above excludes earlier ones. Not a claim about the sport across all
time.

**No change made.** Not a forward candidate: six tests, one marginal positive
that misses its corrected threshold, one significant negative.

---

**Original plan, for the record. No change made. Collection not started** - ~1,258 pages at a 15s crawl delay,
about 11 days of chunked daily runs, and the decision to spend that is the
user's.


---

# Addendum 43: why the fortitude cluster was null - the two preconditions (2026-10-05)

A proposal arrived for a "Late-Fight Performance Retention" / fatigue-resistance
index: round-by-round output retention, efficiency retention, a weighted
work-rate index with a slope across rounds, the opponent's decline as a relative
measure, and five-round fights as the natural experiment.

It is a good proposal and it is **almost exactly addendum 4**, which registered
and tested the same six ideas:

| proposed | addendum 4 feature |
|---|---|
| output retention (LFPR) | `d_late_volume_ret` |
| efficiency retention | `d_late_acc_delta` |
| grappling work retention | `d_ctrl_retention` |
| the opponent's decline | `d_induced_decay` |
| five-round experience | `d_deep_experience` |

**Zero of six supported, five of six carrying the wrong sign**, whole cluster
-0.0016 log loss. What addendum 4 did NOT do is explain why, beyond noting that
round-1 accuracy (0.462) and late accuracy (0.458) were close. Two preconditions
were measured now, and both fail.

## 1. There is no fade to measure. Output RISES.

Round totals are only comparable when every round is the full five minutes, so
this is decision fights only - 4,100 fights, 26,254 fighter-rounds. Measuring
fade on all fights is confounded: a round one that ended at 1:30 has fewer
attempts because it was shorter, not because anyone was fresh.

| round | sig-strike attempts | vs round 1 | accuracy |
|---|---|---|---|
| 1 | 36.6 | 100% | 0.431 |
| 2 | 39.3 | 107% | 0.439 |
| 3 | 41.1 | **113%** | 0.436 |
| 4 | 41.5 | 113% | 0.451 |
| 5 | 42.9 | **117%** | 0.450 |

Fighters throw **more** as the fight goes on, not less, and land at the same or
better rate. The premise the whole family rests on - that output decays and the
decay rate is informative - does not hold in aggregate. There is no league-wide
fade for individual variation to sit inside.

## 2. Retention is mostly fight-specific noise, not a fighter trait.

Split-half reliability: each fighter's round-3/round-1 retention computed
separately over their odd-numbered and even-numbered fights, for the 817
fighters with four or more measurable fights.

| quantity | split-half r | Spearman-Brown |
|---|---|---|
| **R3/R1 retention** | +0.159 | **0.274** |
| R1 volume itself (control) | +0.405 | **0.577** |

Retention is **less than half as reliable** as the raw volume it is built from.
It is not zero - p < 0.001, the trait faintly exists - but at 0.27 most of what
any such index measures is what happened in that particular fight, which is the
proposal's own stated worry (tactics, fight state, damage, who is ahead) showing
up as a number.

The control matters: the same method on R1 volume returns 0.577, so the test can
detect a real fighter trait when one is there. It is the retention that is thin,
not the method.

## What this does and does not rule out

The one refinement the proposal raises that addendum 4 did not try is
**conditioning on fight state** - a fighter ahead on the cards coasts, a fighter
behind pushes. That is a genuine confound and it is not controlled anywhere.

But it would be refining a quantity with 0.27 reliability, against an outcome
the unrefined version got wrong in five of six directions, in a sport with no
aggregate fade to explain. De-confounding cannot add reliability that is not
there. **Not pursued, and not a forward candidate.**

Scope note: restricting to decisions is itself a selection - fights that go the
distance are more competitive by construction - but it is the right sample for
this question, since round-3 output cannot be observed in a fight that ended in
round one.


## Addendum 40: TOOL — the UFC.com sandbox (2026-10-04)

A drawer tab that re-runs the win model on striking and grappling numbers
pasted from a UFC.com fighter page, to see how far the pick moves when those
inputs come from elsewhere.

`win_model` (the fourteen coefficients and the scaler) and a per-bout `fin`
block (the fourteen per-corner inputs) are now published in predictions.json,
so the page reproduces the real probability and then changes inputs. Verified:
the browser's recompute matches every published `p_a` to the four decimals
`p_a` is published at, and the feature rebuild matches `make_features` exactly
on 300 random corner pairs.

## Why it is a sensitivity test and not a second opinion

A UFC.com page carries seven of the fourteen inputs. The seven it does not —
career rating, strength of schedule, UFC mileage, losses by strikes, reach, age
and layoff — hold **55% of the model's weight** and include the three largest
coefficients, age above all. No paste can produce "what UFC.com's numbers say".

The swap is also not like for like: the model's rates are opponent-adjusted and
shrunk toward a divisional prior for fighters with little tape, while UFC.com's
are raw career averages. A raw number in a slot built for an adjusted one
changes what the number means, not only its source. Both facts are on screen in
the panel, not only here.

**Nothing it produces is stored, published or graded.** It is in memory, resets
on reload, and the ledger never sees it. When shown on a card it sits beside the
published probability and never replaces it: a tool for questioning the number
must not quietly become the number.

## The method read, and why it is context rather than a second opinion

The panel also parses "Win by Method" and sets a records-only method read beside
the model's. Those shares are conditional on winning — a UFC.com page publishes
no losses-by-method — so the only sound combination weights each man's own habit
by his chance of being the one who wins:
P(KO) = p(A) x A's KO share + p(B) x B's KO share, and likewise for submission
and decision. Verified to sum to one.

It is displayed, not averaged in, and the panel says why on screen. Addendum 29
registered this exact question and tested it on 1,300 held-out bouts: career KO
share **+0.0017 at p = .55**, submission share **+0.0017 at p = .55**, round-one
share **negative**, and all four round-one targets at **0.0000**. Only own finish
rate survived at +0.0016 and was not adopted.

The reason is mechanical rather than statistical, which is why no amount of
fresh data from a second source changes it: the model already carries knockdown
rate, submission rate and finish rate, and those are the mechanisms a career
method mix works through. Measured alone the mix reaches AUC 0.62 and nearly all
of it is already inside the model by another route. Pasting the same quantity
from UFC.com instead of UFCStats supplies a different *number*, not a different
*signal*.

So the standing decision from 29 holds — the career breakdown is shown beside
the projection, not folded into it — and the sandbox carries the measurement at
the point of use rather than leaving a reader to discover it here.

## Would the W-L record close the gap? Measured: no, and shrinkage matters far more

The win-side shares are missing the loss side, so the question was whether
pasting the record as a proxy would recover it. Scored as a method prediction on
6,823 bouts, leakage-safe (each fighter's record as it stood before the bout),
against the league base rate at 1.0236 nats:

| | raw | shrunk, k=5 |
|---|---|---|
| win-side mix (all UFC.com can give) | 2.1098 | **0.9794** |
| all-bouts mix (the corpus, with losses) | 1.8061 | **0.9770** |

Two findings, and the second is the one that mattered.

**The loss side is worth +0.0024.** Adding the record recovers almost nothing;
it is not the limiting factor. The idea was sound and the gap it closes is
negligible.

**Shrinkage is worth +1.13.** Raw career shares are not merely weak, they are
far worse than the base rate — three wins all by submission reads as 100%
submission, and averaging two such distributions produces confident nonsense.
Shrunk toward the league mix the same data BEATS the base rate by +0.044. The
panel had been displaying the raw version, which was the worst form of the
number; it now shrinks with k=5 and shows the raw figure in grey beside it so a
thin record is visibly thin. k=5 was best of 0/2/5/10/20/40 and the curve is
flat from 2 to 10, so nothing hangs on the exact constant.

None of this changes addendum 29's verdict. The mix beats guessing and does not
beat the model, because the model already carries the mechanisms it works
through. It is better context than it was, and still context.

## Timing: average the two corners, never sum them

With a record field supplying a denominator, first-round finishes over total
bouts gives the one timing number a UFC.com page carries. "Ends in round one" is
a shared event — either man can cause it — so summing the two rates looks right.
It is badly wrong. Measured on 6,823 bouts against a 0.5550 base rate:

| | sum | average |
|---|---|---|
| ends in round one, k=5 | 0.6380 | **0.5496** |
| ends inside the distance, k=5 | 1.1290 | **0.6917** |

Summing is worse than guessing in both. These are WIN-side rates that already
carry "and he won it", so adding them double-counts. Averaging wins, and it is
what shipped.

## What each piece is worth, on one scale

Best achievable as a standalone read, relative to its own base rate:

| read | better than guessing |
|---|---|
| win-by-method, shrunk | **4.3%** |
| first-round proxy, averaged | 1.4% |
| finish proxy, averaged | 1.0% |

The finish proxy is not built: the method read already implies it (KO + SUB
against DEC) and is four times stronger, so a separate number would be a second
and worse answer to a question already answered. The first-round proxy is built
despite being thin, because it is the only thing in the block that speaks to
WHEN rather than HOW, and P(round one | it finishes) falls out of the two reads
divided.

No per-round curve is possible from this source — UFC.com publishes a
first-round count and nothing for rounds two through five.

## Does shrinkage already handle thin records? Mostly, and k=5 is the right k

Gain over the base rate, bucketed by the THINNER corner's win count:

| wins | n | k=2 | k=5 | k=10 | k=20 |
|---|---|---|---|---|---|
| 1-2 | 2122 | +0.0089 | **+0.0235** | +0.0204 | +0.0140 |
| 3-5 | 1455 | +0.0422 | **+0.0499** | +0.0429 | +0.0308 |
| 6-10 | 701 | +0.0225 | +0.0340 | **+0.0348** | +0.0288 |
| 11-20 | 63 | **+0.0988** | +0.0932 | +0.0829 | +0.0663 |

**k=5 is best or near-best in every bucket, and nothing goes negative.**
Shrinking harder is not the fix: k=10 and k=20 both score worse nearly
everywhere, so taming the thin end that way costs accuracy at the thick end.

The ceiling each record size can reach, at its most lopsided (all wins inside
the distance), against the 49.5% league rate:

| wins | finish % | points past | clears the 12-point bar |
|---|---|---|---|
| 1 | 58.2 | +8.4 | no |
| 2 | 64.2 | +14.3 | yes |
| 3 | 68.7 | +18.8 | yes |
| 20 | 90.0 | +40.1 | yes |

So a **one-win record cannot make a call at all** — shrinkage caps it below the
bar. Two wins can, at +14.3, which is enough to clear the bar and displace the
model's call, while that bucket's measured gain is less than half the 3-5
bucket's.

**The fix is a gate, not more shrinkage.** Under three wins on either side the
read still shows and is marked thin — on the chip ("thin 2W") and on the drawer
verdict ("THIN — 2 WINS ON ONE SIDE") — but it may not lead or dim the model's
call. Leading is the one place the weaker read displaces the stronger one, so
that is the one place the record has to be thick enough to mean it.

## The thin-bout case, where the panel is at its strongest

The panel is also available on bouts the model marks `thin` (addendum 19: a
fighter with 0-1 prior UFC fights). It had been unreachable there, because the
drawer swaps the whole markets card for a winner-only card and the tab lived
inside the card it swapped out.

This is the one place the panel is not a second opinion on a number that already
exists. On a thin bout the model publishes **no** method and **no** round —
neither was ever tested on records that short, so it withholds them rather than
guessing — while a UFC.com page carries the fighter's entire career, including
bouts outside the UFC that the corpus has never held. So the usual objection
from addendum 29 does not apply: this is not the same evidence arriving by
another route, it is evidence the model genuinely cannot see.

Two consequences in the code. "Leading" now requires a model call to outrun —
with `m_decision` null the records read is the only read, and claiming it had
beaten something would be false. And the method block states why its model
column is empty, so a blank reads as a deliberate withholding rather than a
failure. The thin-record warning still applies on top, since a short UFC record
and a short career record are different things and a fighter can have both.

## No-read bouts, and the one number that must stay withheld

A no-read bout has no corpus state at all — the fighter is absent from UFCStats,
which is why there is no tile. These entries are now openable and carry the
panel, because the gap between "nothing" and "something from the records" is
the largest on the card.

The method and round read works here unchanged: it draws on the pasted records
and the league base rate, and on nothing from the corpus.

The WINNER read is different and is gated. Seven of the fourteen inputs have no
source, and zeroing their differentials does not express ignorance — it asserts
the two men are level on rating, strength of schedule, UFC mileage, chin and
layoff. **That assumption is wrong in a predictable direction for exactly this
population**: a fighter is no-read because he is new to the UFC, and a newcomer
is typically young and untested against someone established. A random error
would be tolerable; a systematic one is not.

So optional age and reach fields were added, both of which sit in the bio block
of a UFC.com fighter page. They recover the two largest missing weights:

| | share of the model's weight |
|---|---|
| from the pasted stats block | 44.9% |
| age alone | 18.8% |
| reach alone | 4.4% |
| rating, schedule, mileage, chin, layoff (no source) | 31.9% |

**Assumed equal without age and reach: 55.1%. With them: 31.9%.** The winner
number therefore appears only once an age or a reach is supplied on at least one
side, and it carries the remaining assumption in its own label. Below that bar
the method and round read still shows.

### Height, as a stand-in for reach only

Height is **not** a model input — `d_height` sits in `DROPPED` as "carried by
d_reach" — so typing it buys nothing on its own. Its one use is filling a
missing reach, which is exactly what the pipeline already does for about a
quarter of the corpus.

Measured on 2,487 fighters with both recorded:

| | |
|---|---|
| fitted line | reach ≈ **-2.23 + 1.056 × height** |
| R² | **0.790** |
| residual SD | **1.95 in** |
| within 1 in / 2 in / over 3 in | 40% / 70% / 12% |

In the model's own units, `d_reach` has coefficient +0.0971 against a scale of
3.228, so a 2-inch reach error moves the win probability by about **1.5 points**,
and reach is **4.4%** of the model's total weight. Small — but the comparison
that matters is not against a measured reach, it is against **no reach at all**,
which zeroes the differential and asserts the two men are level. For a pair six
inches apart in height that assumption is far wronger than a 2-inch estimate.

Parsed by PATTERN, not position: a feet'inches token is a height by
construction, an explicit `age`/`reach`/`height` label wins outright, and bare
numbers fall back to the age-then-reach order that already worked. A third
positional slot was rejected because a bare 70 is a plausible reach and a
plausible height, so order alone cannot disambiguate.

The field takes the UFC.com bio block pasted whole — label above value across
lines (Age / 36 / Height / 71.00 / Weight / 146.00 / Octagon Debut /
Oct. 20, 2013 / Reach / 74.00 / Leg reach / 40.00) — or a typed short form.
Three things in that block actively bite:

- **"Leg reach" contains "reach".** The plain label matched it. On the real
  block this went unnoticed only because UFC.com prints Reach first; fed a block
  with leg reach first, the fighter's reach became 40 inches, which then failed
  the sanity range and was dropped, leaving **no reach at all**.
- **"Octagon Debut Oct. 20, 2013" carries a 20.** With no Age line, the bare
  number fallback read the debut DAY as the fighter's age and reported 20.
- **Weight is a three-digit number in the same block.**

Decoy lines are now cut from the string before anything is matched. A later fix
was needed on top: a single global "found a label" gate skipped the fallback for
every field at once, so `32, 6'2"` — where the feet'inches counts as a label —
silently dropped the age. The fallback now runs per MISSING field, over a string
with the labelled values removed as well.

Ten input forms pass, including the real block, the block with leg reach printed
first, the block with Age or Reach missing, `6'2"`, `6 ft 2` and the mixed case
where one corner has a measured reach and the other only a height.

The panel says when a reach was estimated rather than given, with the error
size, so an estimate is never read as a measurement.

### Saying how much higher, and naming the outcome

A gold fill told a reader the records read was further from the league rate but
not by how much or in which direction, so the chip now spells the gap out:
"ufc.com FINISH 78% **+29 vs model**". The comparison is against the model's
number for the SAME outcome, which is the only form of "higher" that means
anything — a records FINISH set against a model DISTANCE would be two different
claims. It is null on a no-read bout, where there is no model number to be
higher than. Verified in both directions: +29 where the records run hot, and
**-14** where the model is the more extreme of the two.

A second chip names the single most likely outcome — "ufc.com VAN BY KO 50%" —
when one corner's route is six points clear of the next, and is suppressed
entirely otherwise. A chip is read at a glance, and a hedged chip is read as a
call.

The six corner-by-method cells and the "is it clear" test now live in shared
helpers (`sbCells`, `sbTop`) used by both the chip and the drawer verdict. They
were about to compute the same answer in two places, which is exactly how the
tile and the drawer came to disagree on the Pulyaev bout.

### The same three tiers as the model

The chip printed a bare "ufc.com FINISH 71%" at every strength. The model's own
length badge has used three tiers since it shipped — 12 points clear of the
league rate is a call, 5 to 12 a lean, under 5 neither — so a 71% from the
records read sat beside a model badge that would have called the identical
number LIKELY, and the two looked like different kinds of claim when they were
the same claim. The drawer verdict was already tiered correctly; only the chip
was not, which is the tile-and-drawer disagreement again in a new place.

The chip now carries the tier in the wording and in the weight: FINISH LIKELY
in gold, FINISH LEANS in the muted colour, FINISH - NO LEAN dimmed. The
thresholds are read from the same two constants as the model badge rather than
restated, so they cannot drift apart. Conviction is measured as distance from
the league base rate, not from 50% - a 55% finish call on a division that
finishes 56% of the time is no lean at all, and the old wording would have
printed it as a finish.

The round qualifier was reworded at the same time. "FINISH LIKELY ... R1 LIKELY"
used one word for two different claims in a single badge; it now reads "in R1" /
"after R1", which says where the finish lands without repeating the strength
word that already applies to the finish itself.

Verified across four hand-built shapes - heavy finishers, a mild tilt, a
league-average pair and decision grinders - with the drawer and chip agreeing on
the tier in every one.

### Provenance on the card

Once something is pasted, the no-read entry carries a summary — "ufc.com FINISH
55%" in the same gold dashed styling the tiles use, under a line reading "your
UFC.com read, not the model". Without it the work was invisible from the card
and a reader would have had to open every no-read entry to recall which ones
they had filled in.

On these bouts the risk runs the other way from the tiles. There is no model
number anywhere on the entry, so the danger is not that the pasted read is
confused WITH the model's but that it is mistaken FOR it — hence the wording
names the source rather than merely distinguishing two numbers.

Two defects found getting that to work, both of the same shape — a no-read bout
is not in `DATA.bouts`:

- `sbLoad` tested membership against `DATA.bouts` alone, so **every no-read
  sandbox was deleted on reload**, discarding exactly the pastes that cost the
  most effort. It now tests against `no_read` as well.
- The redraw was gated on the show-on-card flag, which a no-read bout cannot
  have because it has no tile to show anything on, so the card summary never
  refreshed.

### A bug this surfaced twice

With no winner probability, `pA` was null, and `pA*A + (1-pA)*B` collapses to
`0*A + 1*B`: the entire read became corner B's record with corner A silently
discarded. It rendered plausible numbers, which is why it survived the first
pass. Fixed in `sbMethodRead` and then found again in `sbVerdict`, which builds
its own six cells rather than reusing that output — on a test bout where corner
A was the heavy finisher the verdict named corner B's route. No winner
information now means EVEN weighting, in both places.

## The plain-language verdict, and the trap in it

The panel heads the rows with one sentence — "Finish likely · Van by KO/TKO ·
round 1". Thresholds are lifted from `lengthBadge` rather than invented: 12
points clear of the league rate is a call, 5 to 12 a lean, under 5 nothing. A
second scale would mean the same gap reads as "likely" in one place on the page
and "probable" in another, which is how a reader stops trusting both.

The trap, caught in testing on a balanced pair: the sentence named the largest
of the six corner-by-method cells, and that is **not** reliably in the family the
headline just called. Decision mass splits across two cells and finish mass
across four, so a fight at 59% finish can still have a single decision cell on
top — and it printed "Finish leans · by decision". That is precisely the
contradiction the tile carried on the Pulyaev bout, reappearing somewhere new.

Fixed the same way as the original: the named outcome is the best cell *within
the called family*, and when the top two in that family are within 6 points it
says "no clear favourite" rather than picking one. Five fight shapes checked —
submission grappler against a point-fighter, two knockout artists, two decision
grinders, a mild tilt and a dead-even pair — with an assertion that no headline
names an outcome from the other family.

# Addendum 44: the UFC.com check against the model - registered before any clean data exists (2026-10-06)

Written deliberately on a day when the usable sample size is **zero**. Every
check read entered so far was pasted after its card had finished and is
disqualified (see "Disqualified data" below), so there is nothing yet to peek
at. That is the only condition under which registering this is worth anything.

## What the check is

A second read of a bout built only from public fighter pages, standing beside
the model rather than inside it. As of this addendum it takes:

- the UFC.com rate block: strikes landed and absorbed per minute, striking
  accuracy and defence, takedowns per 15, takedown defence, submissions per 15
- the professional record
- the ESPN fight-history table: every bout with date, opponent, result, method,
  round, finish time and promotion

It does not see, and will never see, the seven inputs the model holds that the
public pages do not publish: career rating, strength of schedule, UFC mileage,
losses by strikes, reach, age and layoff - which together carry about 55% of the
model's weight. The check is therefore not a competitor to the model; it is a
differently-informed witness, and the question is whether it carries anything
the model does not.

**The check is frozen as of this addendum.** Its inputs are not to be changed
while this test runs. The ESPN history was added on the same day precisely so
that the frozen version is the one worth measuring - a mid-test change makes
every card before it worthless for this comparison.

## Registered weighting, declared not fitted

A fight at UFC, Contender Series or The Ultimate Fighter counts 1.0; a fight at
any other promotion counts 0.5, in every quantity derived from the history.

The rationale is stated in advance: a large share of a prospect's finishing
record is built on regional cards, and counting a regional knockout as equal
evidence to a UFC knockout is what makes a padded record read as finishing
power. In the first history examined (Gautier, 12 prior fights) six of the
twelve were outside the UFC.

**0.5 is a judgement, not a fitted parameter.** It is not to be adjusted after
seeing which value helps. Any later change to it is a new addendum with its own
bar and its own data, not a revision of this one.

## Disqualified data

A read is excluded from every test here if any of the following hold:

1. **Entered after its card.** A UFC.com page and an ESPN history are updated
   once a fight is over: the record, the rate stats, the method counts and the
   history's first row then contain the fight being predicted. Such a read is
   not a forecast. Operationally: entry timestamp at or after midday UTC on the
   day following the card date. The site enforces this - settled bouts no longer
   accept a read at all, and the entry timestamp is frozen at first entry rather
   than rewritten on reload.
2. **Any history row dated on or after the card.** Dropped at parse time.
3. **Blended.** A read mixed with the model's own numbers is not an independent
   witness. The blend control has been removed; reads are pure.
4. **Method cells that do not sum to one.** Guards the specific failure where
   the four per-corner cells were stored as zero and the check was silently
   graded as having predicted a decision on every bout.

## Hypotheses

**H1, primary.** On bouts where the model and the check call the length
differently, the check is nearer the outcome more often than chance.

Length is the primary because the two disagree about it far more than about the
winner - roughly five bouts a card against two - so it accumulates power two to
three times faster than anything else here.

**H2, secondary.** The same, for the winner.

**H3, secondary.** The same, for the round-one split.

**H4, secondary.** The same, for finish type.

**H5, mechanism.** The check's edge, if any, is concentrated in bouts where a
fighter's professional record extends well beyond his UFC record - that is,
where the history carries fights the model's corpus does not hold. Tested as an
interaction between the check's advantage and (total professional fights minus
UFC fights), summed over both corners.

H5 is the hypothesis worth having. H1-H4 can only say *that* the check differs;
H5 says *why*, and it is the only one of the five that would change the model
rather than merely rank two readers of it. If H1 passes and H5 fails, the
finding is that the check is better for a reason not yet identified, which is a
weaker and less actionable result, and it must be reported as such.

## Statistics

- **Primary test:** paired Brier difference on the length claim over
  disagreement bouts, with a bias-corrected bootstrap CI (10,000 resamples).
  Brier rather than a sign test because it uses the magnitude - a 51% call and a
  95% call are not the same claim.
- **Secondary tests:** the same, under Benjamini-Hochberg FDR at 0.10 across
  H2-H5. H1 is not part of the correction; it is the registered primary.
- **Bar:** H1 passes if the bootstrap CI on the paired Brier difference excludes
  zero in the check's favour.
- **Minimum n:** 40 length disagreements, roughly eight clean cards. Nothing is
  reported as a result before that, whatever the interim numbers look like.
- **Stopping rule:** the test runs to 40 disagreements and stops. It does not
  stop early on a favourable interim, and it does not continue past 40 hoping
  for one. If the bar is missed at 40 the finding is null and is recorded as
  null.

## Known limitation that no statistic fixes

A check exists only where a read was pasted, and the bouts worth pasting are the
interesting or doubtful ones - not a random sample of a card. Every column is
scored on an identical bout set, so model-against-check-against-market is fair;
but "the check went 8 of 10" describes the chosen bouts and not the card. The
only remedy is pasting every bout on a card rather than the interesting ones,
and until that happens the generalisation is to bouts like these, not to bouts.

## What was fixed on the way to this addendum

Recorded because each of these silently corrupted a number that was being shown
as evidence:

- The four per-corner method cells were stored as zero from the day they were
  introduced, because `sbMethodRead` returned only aggregate `{ko, sub, dec}`
  and the caller read `read.a_ko || 0`. The argmax over five cells therefore
  fell to "decision" on every bout, and the check was graded as having predicted
  a decision every time. The aggregate `dec` was correct throughout, which is
  why the length claim was unaffected and the error survived.
- The entry timestamp recorded the last recompute rather than the first entry,
  because the read object is rebuilt on every page load. The first load after a
  card resolved would have restamped every pre-fight read as post-hoc.
- The round estimator was round-one **wins** over **all** fights, so a fighter
  repeatedly stopped early scored zero in the numerator and counted in the
  denominator, and read as a slow starter. Replaced by the fight-level share.

# Addendum 45: AMENDMENT to addendum 44 - the round claim is as sharp as it can be, and no sharper (2026-10-06)

Recorded the same day as addendum 44, before any clean read exists, so nothing
here was chosen after seeing data it would affect.

## The question

Addendum 44 froze the check with a round claim of "round one, or later". The
obvious next step was an exact modal round, matching the sharper claim the model
makes, so that no part of the comparison is coarser than the rest. The ESPN
history makes it mechanically possible: every row carries the round its fight
ended in.

**Tested before building.** The precondition is the same one that closed the
fortitude cluster in addendum 43: if a quantity does not replicate within a
fighter, there is nothing fighter-specific in it to extract.

## Measurement

7,177 UFC bouts, 2010-2026. Each fighter's fights ordered by date and split in
half; the quantity computed in each half and correlated across fighters, then
Spearman-Browned to full length.

| quantity | min fights | n | r | p | reliability |
|---|---|---|---|---|---|
| P(round one \| finish) | 8 | 223 | +0.120 | 0.073 | **0.214** |
| P(round one \| finish) | 12 | 71 | +0.025 | 0.836 | **0.049** |
| P(ends by round 2 \| finish) | 8 | 223 | -0.010 | 0.882 | **-0.020** |
| P(finish at all) — CONTROL | 10 | 479 | +0.372 | 4.0e-17 | **0.542** |
| P(finish at all) — CONTROL | 16 | 167 | +0.427 | 8.7e-09 | **0.598** |

The control **rises** as the sample grows, which is what a real trait does. The
round quantities **fall toward zero**, which is what noise does. Reliability
0.21 falling to 0.05 is the same shape as the retention cluster's 0.274 against
its control of 0.577, and it is read the same way.

**Finding: WHEN a fighter finishes is not a measurable property of the fighter.
WHETHER he finishes is.**

An exact-round claim for the check is therefore not built. It is not a matter of
engineering effort; the information is not in the record. A per-fighter modal
round would be a precise-looking number with a reliability of 0.275, and
publishing it would make the round column look stronger while making it weaker.

## What survives, and the amendment

One regularity does replicate, because it is a league property indexed by a
reliable fighter quantity: **heavier finishers finish earlier.** Over 3,623
three-round finishes:

| pair's finish rate | n | P(R1 \| finish) | P(R2 \| finish) | P(R3 \| finish) |
|---|---|---|---|---|
| 0-30% | 219 | .402 | .333 | .196 |
| 30-45% | 739 | .441 | .327 | .185 |
| 45-60% | 958 | .455 | .317 | .166 |
| 60-75% | 1,081 | .510 | .295 | .130 |
| 75-100% | 626 | .569 | .272 | .104 |

Monotone, r = +0.100, p = 1.7e-9. Five-round fights spread the same finishes
further out - .376 in round one against .517 - so the curve is scaled by that
ratio rather than re-estimated on 362 bouts. Bucket edges were fixed before the
table was computed and are not to be moved.

**AMENDMENT to addendum 44.** The check's round estimator becomes

    P(ends in round one) = P(this fight finishes) x P(round one | finish, pair finish rate)

replacing the per-fighter round-one share that addendum 44's frozen version
used. Both inputs are reliable; the quantity replaced was not.

This is a change to a check that addendum 44 declared frozen, made the same day
and before a single qualifying read exists, so no accumulated data is
invalidated. The freeze stands from this amendment forward. Any later change
needs its own addendum and its own data.

The registered hypotheses, bars, FDR level, minimum n and stopping rule in
addendum 44 are unchanged. H3 continues to score the round-one split for both
sides, which is now the sharpest round claim the check is entitled to make - and
the exact-round row remains model-only, labelled as such, scored on its own
terms with no check column, exactly as before.

## Note on what this does not say

It does not say the model's modal round is worthless. The model builds it from a
competing-risks survival fit over the whole corpus, not from one fighter's nine
finishes, and it is scored on its own row. The finding is narrower: a round
claim read off an individual record does not replicate, so the check cannot make
one honestly.

## Addendum 45, amendment 2: the round claim is scored CONDITIONAL on a finish (2026-10-06)

Found while answering a plain question about how the round row is graded, which
is how this kind of thing is usually found.

### The defect

The round row is only ever graded on bouts that **finished** - on a decision
there is no round to call. But both sides were being scored on their
**unconditional** P(ends in round one), a probability taken across all outcomes
including the decision.

On the current card the model's unconditional figure runs .106 to .403 and never
approaches .5:

| bout | P(finish) | P(round one) | P(round one \| finish) |
|---|---|---|---|
| Van vs. Pantoja (5rd) | .489 | .106 | .216 |
| Baraniewski vs. Menifield | .725 | .403 | .556 |
| Tuivasa vs. Despaigne | .639 | .297 | .465 |
| O'Neill vs. Moura | .305 | .110 | .362 |

With a .5 threshold on that number, both reads call "after round one" on
essentially every bout - while round one is where **51.7%** of three-round
finishes actually land. A near-constant call scored against something close to a
coin flip is not a read, and it was making the round row look arbitrary for both
sides at once. It would also have been scored into H3.

This is a category error, not a tuning problem: a probability of one event was
being judged against a different event.

### The correction

Both sides are divided by their own finish probability before the call is taken:

    check:  P(round one) / (1 - P(decision))        both stored per read
    model:  p_end_r1      / (1 - m_decision)        both stored per archived bout

The call is then "round one" when that conditional is at or above .5, graded
against whether the finish landed in round one. The threshold now sits beside
the real base rate instead of somewhere the unconditional probability cannot
reach.

Worked example, from a settled bout: a check reading .42 unconditional on a
fight it gave a 78% chance of finishing is claiming .538 of its finishes land in
round one. The fight ended by knockout in round one. Under the old scoring that
read was marked **wrong**; under the correction it is marked right, which is
plainly the correct verdict.

### Scope

H3 in addendum 44 is unchanged in what it claims and in its bar; only the
quantity it is computed from is corrected. The exact-round row stays model-only
per amendment 1. No qualifying data exists yet, so nothing accumulated is
affected. Brier for the round row is now taken on the conditional as well, so
the magnitude and the verdict agree.

## Addendum 45, amendment 3: fight-history parsing, recorded for completeness (2026-10-06)

Not a change to what the check computes. Recorded anyway, because the freeze in
addendum 44 covers the check's inputs and this touches how a pasted block
becomes those inputs.

**Widened**, so a block pasted with or without ESPN's column header, with or
without a "Fight History" title, with the header repeated between fights, or
with the row on a single tab-separated line, all parse identically. Date shapes
accepted: `Jul 18, 2026`, `July 18, 2026`, `Jul. 18 2026`, `18 Jul 2026`,
`2026-07-18`. Results accepted as `W`/`L` or `Win`/`Loss`/`Lost`, any case.

**Column ORDER is still assumed** - date, opponent, result, method, round, time,
event. A reordered table returns nothing rather than guessing which cell is
which, because a wrong guess would mis-assign silently and never be seen.

**One defect closed.** The month was matched on a token's first three letters,
so "Marathon 18 2026" read as a March date and "Octagon 12 2024" as an October
one. An event cell misread as a date shifts every field after it, which is the
kind of corruption that produces plausible numbers rather than obvious errors -
the same failure mode as the zeroed method cells in addendum 44. Months are now
matched as whole tokens against an explicit list.

No qualifying read exists, so nothing accumulated is affected. The estimator,
the tier weighting, the as-of rule, the hypotheses, the bars and the stopping
rule are all unchanged.

## Addendum 45, amendment 4: the decision curve's marker is placed on the axis it was built from (2026-10-06)

Display only - the curve feeds no probability, it is the evidence shown beneath
the check's length read. Recorded because misplacing the marker misrepresents
that evidence.

`decision_curve()` accumulates each fighter's wins and decision wins from corpus
rows alone, so its x-axis is **decision share over UFC bouts only, unweighted**.
The marker was being computed from the whole professional record. For a fighter
whose career is mostly regional those are not the same number, and regional
records run early-finish heavy, so the marker drifted left into buckets
predicting a higher finish rate than the UFC record supports.

Measured on a constructed pair with two UFC wins and six regional wins:

| | career share | UFC-only share | bucket's finish rate |
|---|---|---|---|
| regional-heavy prospect | 13% | 50% | 70% vs 47% |
| established fighter | 18% | 17% | unchanged |

A 23-point error in the finish rate the table implies, for exactly the fighters
the check exists to read, and none at all for fighters with long UFC careers -
which is why it was invisible until fight histories made the UFC/non-UFC split
knowable.

Now: with a fight history, the marker uses UFC-tier wins only, and is withheld
unless both corners have at least two of them, matching the curve's own floor.
From a UFC.com Win-by-Method block the split is unknowable - that block is
career-wide and does not say which wins were in the UFC - so the marker stays
career-based there and the caption says so rather than implying a match.

The tier weighting is deliberately NOT applied here. The curve's axis carries no
weighting, so a weighted share would sit on a curve that was never estimated
from weighted shares. Weighting belongs in the read; the axis belongs to the
corpus.

## Addendum 45, amendment 5: the round badge collapsed into the finish call, and what that means for H3 (2026-10-06)

Noticed from the outside - "almost every finish and finish-likely shows R1 next
to it" - and the arithmetic confirms it.

### The collapse

The badge appended a round when `t.p / fin` cleared 0.55. After amendment 1,
`t.p` is `fin x r1GivenFinish(pair finish rate)`, so `fin` cancels and the
condition **is** the curve:

| pair finish rate | P(R1 \| finish), 3rd | badge |
|---|---|---|
| 0.50 | .455 | — |
| 0.62 | .510 | — |
| 0.78 | .569 | · in R1 |

A step function of the pair's finish rate - the same quantity the FINISH /
DISTANCE half of the badge is built from. "in R1" fired only at a 75%+ finish
rate, which is exactly the population reading FINISH LIKELY, so the badge stated
one fact twice; and "after R1" could never fire, the curve's floor of .402 being
above the .30 bar. The suffix is removed from the chip and from the drawer
verdict. The round NUMBER is unchanged and still scored.

### The honest consequence for H3

After amendment 1 the check's round claim carries **exactly the information in
the pair's finish rate, and no more**. P(ends in round one) is P(finish) times a
league curve indexed by that same finish rate, so the conditional share is
bounded in [.402, .569] for three-round fights and crosses the 0.5 call
threshold only as the pair's finish rate passes about 0.60.

So H3 as registered is not testing "can the check read rounds". It is testing
"does a pair's finish rate predict an early finish better than the model's
survival fit does". That is still a real and worthwhile question, and it is the
only round question the data supports - amendment 1 measured a reliability of
0.21 falling to 0.05 for anything fighter-specific. But it is a narrower claim
than the hypothesis as written, and recording it now is the difference between a
known limitation and a result that looks stronger than it is.

**H3 is retained with its bar and FDR unchanged, and is to be reported with this
sentence attached:** the check's round claim is a deterministic function of the
pair's finish rate, so a pass means the finish rate carries round information
the model's survival fit misses, not that the check reads rounds independently.

### Readability

Both round rows now carry the league figure alongside the two reads - the
earlier presentation gave "25% ends in round one" with nothing to judge it
against, when 25% IS the league rate for a three-round fight, and "47% of the
finishes in round one" reads as early until you know the league runs 52%.

# Addendum 46: recency weighting of the check's method mix — tested, null (2026-10-07)

Proposed from the outside: a fighter with a knockout-heavy career whose recent
wins have gone to the cards is arguably not the same fighter his career mix
describes, so the check's method mix might carry a recency weighting or a
secondary trend term.

Tested before building, on 6,915 UFC bouts 2010-2026. Walked forward in time so
each bout is predicted from the two fighters' PRIOR fights only; both corners
required 4+ priors; the pair's averaged, shrunk (k=5) finish rate is scored
against whether the fight actually finished. n = 2,309.

## Every recency scheme is worse than flat career, monotonically

| scheme | log loss | vs career |
|---|---|---|
| **career, flat — what the check does** | **0.65935** | — |
| decay, half-life 8 fights | 0.66074 | +0.00139 |
| decay, half-life 4 years | 0.66143 | +0.00208 |
| decay, half-life 5 fights | 0.66208 | +0.00273 |
| decay, half-life 3 fights | 0.66456 | +0.00521 |
| last 5 fights only | 0.66555 | +0.00620 |
| last 3 fights only | 0.67214 | +0.01279 |
| league base rate alone | 0.69303 | +0.03368 |

The ordering is the finding: the harder old fights are discounted, the worse the
read, with no interior optimum. The gradient points at "use every fight", and
flat career is that limit. For scale, the whole career-over-base-rate gain is
0.0337 - taking the last three fights throws away 38% of it.

The mechanism is variance, not bias. A method outcome is one Bernoulli draw per
fight; a career mix is already a small sample, and halving it to chase a trend
costs more in noise than any drift it recovers.

## A trend term adds nothing on top of the career rate

TREND = (last-3 finish rate) − (career finish rate), averaged over the pair;
spread sd 0.071, range −0.280 to +0.231.

| term | coefficient |
|---|---|
| career finish rate | **+5.713** |
| TREND | +0.535 |

LR chi2(1) = 0.540, **p = 0.462**. Bootstrap 95% CI on the trend coefficient
**[−0.932, +1.993] — includes zero**, against a career-rate coefficient an order
of magnitude larger and unambiguous.

## The premise itself is weak

Within-fighter, first half of a UFC career against second half, 640 fighters
with 8+ bouts: finish rate .510 → .493, a change of **−0.017**, paired
t = −1.51, **p = 0.131**. Fighters do drift slightly toward the cards as careers
run on, and the drift is not distinguishable from noise at this sample size.

## Why the pattern looks real anyway

With a true finish rate near the league's .492, the chance of any fighter
producing three straight non-finishes is about one in eight. Across the twenty-two
corners on an eleven-bout card, two or three fighters will be showing exactly
that pattern at any moment, every card, with nothing having changed about them.
The run is visible; the signal is not.

**Decision: not built.** The check's method mix stays flat over the career, and
the round-by-round panel added the same day shows the dates and the sequence, so
a reader can see a run for himself and weigh it as judgement rather than having
it folded into the number. Any future revisit needs its own addendum and its own
out-of-sample test, not this one re-read.

# Addendum 47: the Polymarket moneyline capture was reading the wrong market (2026-10-07)

Noticed from the outside — the site's split for Walker vs. Meerschaert did not
match what polymarket.us was showing.

## What happened

`moneylines()` in polymarket_us.py wrote one key per bout and let the LAST
matching market win. A method market ("who wins by decision") has two
fighter-named sides rather than Yes/No, so it cleared every gate and replaced
the real moneyline. Two similar fighters are near-equally likely to win a
decision, so the stored price sat near .50 on bout after bout:

| bout | stored | 25-book consensus | exchange |
|---|---|---|---|
| Walker vs. Meerschaert | .503 | .705 | 73/28 |
| Camilo vs. Herbert | .496 | .634 | — |
| Allen vs. Duncan | .496 | .547 | — |

It read as a dead market rather than a bug, which is why it survived.

**Fixed** two ways: method markets are refused outright by their question text —
they are never the moneyline, so ranking them below one is not enough, since a
bout whose real moneyline is missing would still publish a wrong number instead
of nothing — and what remains is ranked (declared winner market first, then
volume, ties keeping the row already held) rather than overwritten, so the order
the feed returns markets in cannot decide the price. Verified across four
orderings including props-only, which now yields no price.

## Scope, and why the rows were NOT deleted

662 contaminated moneyline rows, 195 flagged as qualifying bets, 158 settled —
against 307 settled sportsbook bets. A pooled report was carrying roughly a
third contaminated, and addendum 1's bar is 300 settled bets.

Cleaned ledger files were prepared and then **not used**. This file's own rule
is that the ledger is append-only, and the reason it gives is that a ledger you
can edit is one you will edit; a bad capture does not suspend that. The rows
stay as the record of what was captured. They are excluded AT READ TIME by a
dated constant, `BAD_PUS_ML_BEFORE`, which anyone can audit or lift, and
`report(include_bad_pus=True)` still shows the contaminated view.

Props are unaffected — they come from `map_props()`, a separate path.

## A second bug found on the way

`report()` defaulted to `path=LEDGER`, and `LEDGER` is the LEGACY single file
kept only "for call sites that pass an explicit path": 98 rows against 3,298 in
the monthly files. The forward-test readout was therefore reporting on a stale
fragment — 8 bets where the real record holds 307 settled sportsbook ones.
`read()` and `_market_for_card()` already default to the monthly files; report()
now agrees with them.

Effect on the readout:

| | triggered | settled |
|---|---|---|
| legacy file (what it was reading) | 8 | 8 |
| monthly files, broken capture excluded | **32** | **14** |
| monthly files, contaminated view | 45 | 24 |

## Not changed

The site's market gauge still reads `venue == "sportsbook"` — a devigged
consensus across ~25 books. Polymarket has never fed it, so nothing displayed
was ever wrong because of this bug. Any change there is a display decision, not
a correctness one, and would need its own note.

~~and now that the exchange prices are being read correctly the two largely
agree (72 against 70.5)~~ — **struck.** That sentence was written from the
exchange page, not from a capture made with the fix in place. See amendment 1.

## Amendment 1 (2026-10-08): the fix above did not work, and why

Asked whether the capture was working now, and the measured answer was **no**.
Two captures ran with the fix in place and priced every bout the same way the
contaminated rows did:

| capture (UTC) | rows | min | max | sd |
|---|---|---|---|---|
| 2026-10-08T01:32 | 12 | .495 | .505 | — |
| 2026-10-08T08:21 | 12 | .495 | .505 | .0043 |

against the books on the same six bouts: .295, .366, .471, .497, .512, and one
unpriced. The refusal and the ranking both ran and neither bit.

**The cause was one level further back.** `market_kind()` held its word list in
a dict and returned on the first substring hit, so insertion order decided
precedence: `"fight_winner"` was tested before `"method"` and `"decision"`.
The exchange types its method markets `ufc_fight_winner_by_decision`, which
therefore came back as kind **`winner`** — tying the real moneyline on rank, so
feed order chose between them exactly as before. The question-text refusal
missed it because on this feed the question is frequently just the bare bout
name ("Gerald Meerschaert vs Julius Walker") on every market of the bout, with
the only distinction in the type field.

The same misread also kept those markets **out of `map_props()`**, which
accepts only prop/total/other. One classification bug, two effects.

Fixed by reading the type as **whole tokens, most-specific-first** — a type
naming a method, round or length is a prop even when it also says "winner" —
and by extending the refusal to the stated type with its separators normalized
(`\b` does not fire at "by decision" while the underscores are still there).
Reproduced and verified offline: a decision market typed
`ufc_fight_winner_by_decision`, listed first, with 75× the volume of the real
moneyline, is now refused, and Meerschaert comes through at **.295** — the
book's figure, and consistent with the 73/28 on the exchange page. All 11
suite checks pass.

`BAD_PUS_ML_BEFORE` moves from `02:00` to `20:00` on 2026-10-08: captures run
at 02/10/16/22 UTC, so this excludes every run made today with the broken
classifier and admits the 22:00 run as the first trustworthy one.

### What this changes about how such a fix is confirmed

The first fix was shipped on a diagnosis read off the ledger alone, and
"verified across four orderings" verified the ranking logic against a feed
shape I had assumed rather than observed. The feed is only reachable from where
the capture runs, so a `ml_audit()` dump now prints, per event, every
two-fighter-named market with its type, price and the reason it was taken or
refused. **A price change on this venue is not confirmed by the code reading
correctly; it is confirmed by a capture log and a ledger row.** Until the 22:00
run is in, the correct statement is that the cause is identified and the fix is
verified offline — not that the capture is working.

### Rejected: a near-50% guard

Refusing any price in a band around .50 would have caught both bad batches, and
was rejected: Bonfim vs. Prado is a genuine pick'em at .497 on the books, and a
rule keyed to the value would discard real coin-flips while leaving the actual
defect in place. **Gate on market identity, never on the price it reports.**

# Addendum 48: the loss side of the record (2026-10-11)

Raised from the outside: the check reads a win-by-method breakdown for each
corner, so should it not read a loss-by-method breakdown too — does a man get
stopped by strikes, submitted, or beaten on the cards?

## What was already there, and what was not

Half of this is built and load-bearing, which is worth stating before anything
new is proposed:

| quantity | where | status |
|---|---|---|
| `d_ko_loss_rate` | `features.py` DIFF_KEYS | **one of the 14 win features** |
| `kd_against15` | CORE, method model | +0.23/SD; KO rate 14→18→22→24% across quartiles |
| `l_ko`, `l_sub`, `l_dec` | `espnDerive` | parsed, DISPLAYED as plain counts, nothing computed |
| submission-loss rate | nowhere | **does not exist**; `FighterState` has `w_ko`, `w_sub`, `l_ko` and no `l_sub` |

Two things follow. First, `d_finish_rate` — the WIN-side twin — was pruned as
"carried by `ko_edge`", while `d_ko_loss_rate` survived pruning. Being
finishable is not the mirror of being a finisher, and the corpus already says
so. Second, the gap is specifically the submission side: `sub_edge` prices one
man's submission offense against nothing at all on the other side of the cage.

**Decision losses are not proposed.** The three shares sum to one, so all three
is exact collinearity; and losing on the cards is the residual of the other two
rather than a property of the fighter — `d_elo` already carries "loses".

## Shipped now: display only

`espnDerive` gains tier-weighted loss counts (`lko_n`, `lsub_n`, `ldec_n`,
`l_total`), an all-fights `stop_rate` matching `ko_loss_rate`'s denominator, and
`sbLossMix()` shrinks the loss profile toward the league with the same k=5.

The league prior is `sbBaseMix()`, the win side's own, and no second constant
was measured. Every bout produces exactly one win and one loss and the method
belongs to the fight, so the method split over all losses in the league IS the
split over all bouts. Losses map to bouts one-to-one; there is no population
mismatch of the kind that broke the decision-curve marker (addendum 45).

The panel also reports where one man's finishing meets the other's way of
losing, when both halves lean past the league. **Nothing above it moves.** The
method rows are still built from wins alone.

## Registered, NOT yet run: the precondition

Before any loss-side quantity enters the read:

- **Split-half reliability** of each fighter's loss profile, odd/even fights,
  Spearman-Brown corrected. Bar: **≥ 0.40 and not falling as the sample grows.**
  Control: `ko_loss_rate` on the same fighters, which should clear it.
- Reported with a bootstrap CI, BH at FDR 0.10 across the three families.

The bar is set from what killed the round claim: a fighter's round-one share
measured 0.21 and fell to 0.05 as the sample grew, while his finish rate
measured 0.54 and rose to 0.60. Losses are rarer than wins — a 20-5 record is
five events split three ways — so the prior here is **low**, and lower for
submissions than for KOs. If it fails, it is recorded as a null and the panel
stays display-only permanently.

Not run in this session: the UFCStats CSVs are not in the repo.

# Addendum 49: cage size, and what addendum 8 did and did not test

Raised from the outside: the Apex cage is smaller than a standard one — is
there a statistical difference?

**The interaction is tested and null.** Addendum 8 registered it as V1, "small
cage (UFC Apex) x own pressure style", from `LOCATION`. Result: beta +0.0144,
**p = .567**, correct sign, nowhere near the BH threshold, in a family where
zero of five were supported and the smallest p-value was 0.140. It is on the
standing do-not-re-propose list with venue and altitude.

**But V1 tested the wrong target for this question.** Addendum 8 states that
winner hypotheses ran against outcome and only V3 ran against method. V1 was an
interaction with pressure style predicting **who wins** — while its own stated
rationale ends "and raise finish rates". The main effect on **method** was never
measured. A 25ft cage plausibly changes how a fight ends without changing who
wins it, and the method and round props are where this tool would use it.

So the narrow version is open: **does P(finish), conditional on the model's
existing method inputs, differ at the Apex?** It is a different hypothesis from
V1, not a re-proposal, and it must be registered as such before it is fitted.

**Two confounds decide whether it is worth running at all**, and both are severe
enough that an uncontrolled finish-rate comparison is worthless:

1. **Card tier.** Apex cards are overwhelmingly Fight Nights with lower-ranked
   fighters. A raw finish-rate gap is mostly matchmaking.
2. **Era.** Apex usage spiked in 2020–21 behind closed doors, with short-notice
   replacements and no crowd. "Apex" is substantially a proxy for a period that
   differed in several other ways at once, and addendum 9 already records that
   decision rates move by era.

Any test conditions on card segment and year, or it measures those instead. The
prior is low: nine families have now come back null, this one has already failed
in its interaction form, and the two confounds both push the same direction.
Registered as a candidate, not scheduled.

## Addendum 47, amendment 2 (2026-10-11): the market was never misread

The classifier fix of amendment 1 shipped. Ninety more moneyline rows were
captured between 2026-10-09T01:42 and 2026-10-11T00:38 and **every one of them
fell between .495 and .505** — Meerschaert at .503 against the books' .280,
unchanged. Third fix, third failure.

The `ml_audit()` dump added in amendment 1 then answered it in one read:

```
ufc-katcer-macsti-2026-10-17
  CANDIDATE rank=(1,0)  p=0.489  type=ufc_fight_winner  q=Who will win in the upcoming mma event Katly
ufc-julleb-gilurb-2026-10-17
  CANDIDATE rank=(1,0)  p=0.172  type=ufc_fight_winner  q=Who will win in the upcoming mma event Julie
```

Fourteen events, **one candidate each, no refusals anywhere**. Every one typed
`ufc_fight_winner`, every question a real moneyline question, `rank=(1,0)`.

**Nothing was ever being mistaken for the moneyline.** There was no second
market to lose a ranking contest to, so neither the ranking in addendum 47 nor
the classifier in amendment 1 could have changed any price — both were fixes to
real defects that were not causing this. The defect they were blamed for did
not exist.

What is actually true: the right market was selected every time and **it is not
trading**. Volume is `None` on all of them — provable without the feed, because
the capture runs `min_volume=200.0` and the gate rejects any volume *below* it,
so a `0.0` would have produced no rows at all. Prices sit within a point of the
seed with a uniform one-cent book. The single outlier, `.172`, is the one market
that has seen a trade.

The "absent volume is not low volume" exception — written when these markets
first arrived with a two-sided book and no volume field, and the gate rejected
all of them — is what has been publishing untraded books ever since.

**Fixed by gating on liquidity**: `PUS_REQUIRE_VOLUME` refuses a moneyline with
no volume signal. This publishes NOTHING from the venue until the feed carries
one, which is the correct output while every row it does publish is wrong, and
it is one flag to revert. Verified both directions: an untraded book yields zero
rows, a market with volume still comes through at the book's figure.

Gating on liquidity and not on the number, for the reason amendment 1 already
gave: Bonfim vs. Prado is a real pick'em at .497, and a rule keyed to the value
would discard genuine coin-flips. **The price is never the evidence; the market
is.**

`BAD_PUS_ML_BEFORE` moves to 2026-10-12T00:00:00Z, covering those 90 rows.

### The standing lesson, now that it has cost three attempts

Each of the three fixes was reasoned from the ledger — the only artifact
reachable from where the work happens — and each diagnosis was a mechanism that
could have produced the symptom, confirmed against no observation of the feed.
All three were wrong in the same way: they explained the number without ever
looking at the thing producing it. The audit dump cost one capture cycle and
settled it immediately.

**A venue fix is not confirmed by the code reading correctly, and a cause is not
established by being sufficient to explain the symptom.** Where the data source
cannot be reached from here, the first shipped change is the one that makes the
source describe itself.

The remaining open question is narrow and is recorded rather than guessed at:
whether any field in this payload distinguishes a market that has traded from
one that has not. The audit now prints the full key inventory of the first
declared winner market. If such a field exists it becomes the gate; if the
inventory is bare on every market, this feed cannot support a moneyline at all
and the venue is moneyline-dead by its own payload — which is also an answer,
and a publishable one.

# Addendum 50: the check's league base was pooled across divisions (2026-10-11)

Raised from the outside, about the loss panel: "I wouldn't want heavyweights to
show conflated lack of sub losses when the weight class has fewer subs on
average."

## Confirmed, and the submission axis is the smallest part of it

`sbBaseMix()` returned ONE mix, volume-weighted across all eleven divisions,
and every shrinkage and every "league" comparison on the check tab used it. The
divisions are nowhere near each other:

| division | n | ko | sub | dec |
|---|---|---|---|---|
| Heavyweight | 509 | .505 | .128 | .367 |
| Light Heavyweight | 520 | .450 | .165 | .385 |
| Middleweight | 814 | .376 | .179 | .445 |
| Lightweight | 1089 | .322 | .191 | .487 |
| Flyweight | 418 | .232 | .211 | .557 |
| Women's Strawweight | 378 | .140 | .198 | .662 |
| **POOLED — what was used** | 6855 | **.319** | **.177** | **.504** |

Submissions span .128 to .211, an 8-point spread. **KO spans 36 points and
decision 30.** A heavyweight was being shrunk toward a decision rate 14 points
above his division's and a KO rate 19 below it.

Worse than the shrinkage: the "league" column he was being COMPARED against
carried the same error, so a heavyweight whose losses are 45% by KO was flagged
`+13 above league` when he is in fact below his division's 50.5%. **The flag
could point the wrong way**, which is worse than no flag.

Measured on the same synthetic record — six KO wins, two KO losses — shrunk
under each base:

| base | loss ko | loss dec | win ko |
|---|---|---|---|
| Heavyweight | .646 | .262 | .775 |
| Flyweight | .405 | .453 | .621 |
| pooled (old) | .514 | .360 | .690 |

The identical record moves 24 points on KO-loss and 19 on decision by division.
Under the old base both read the same number.

**Fixed**: `sbBaseMix(bout)` returns the bout's own division where the payload
has one (all eleven carry n >= 251, ample for a three-way share) and falls back
to pooled for a catchweight or an unrecognised name, reporting which it used so
the panel can name it. All eleven bouts on the live card resolve to their own
division. This changes the check's method read going forward; reads already
captured keep the values they were captured with.

## Registered, not changed: is the 0.5 tier weight calibrated?

Asked in the same breath — the weighted decision share runs ~10 points above
the raw one on some bouts, which makes a fight look likelier to go the distance
than the plain record says.

Part of that gap was the division error above, and the bout cited (Boser vs.
Diniz) is a **heavyweight**, so it was carrying the full 14-point decision
error. That part is now gone.

The rest is the tier weight, and the honest status is:

- **The direction is principled.** Regional opposition is weaker, regional
  records are finish-heavy, and a fighter's non-UFC finishes overstate what he
  does at this level. Down-weighting them raises the decision share on purpose.
- **The magnitude is not measured.** UFC/DWCS/TUF = 1.0 and everything else =
  0.5 is **declared, not fitted** — the same standing caveat the tier weight
  has carried since it was introduced.
- **This project has already been bitten here once.** Addendum 45 moved the
  decision-curve marker to UFC-only unweighted precisely because regional
  records "drag a prospect's career share left into buckets predicting a higher
  finish rate than his UFC record supports". So the curve marker uses UFC-only
  while the method mix uses all-fights-at-half-weight: **two populations on one
  panel**, which is an inconsistency on its own terms.

It is measurable: for fighters holding both regional and UFC records, the ratio
of regional finish rate to UFC finish rate implies the weight directly, and 0.5
is a hypothesis that ratio can confirm or refuse. Registered as a candidate
with that as the stated test. **Not changed on a guess** — a weight moved to
make a number look better is the same error as a gate keyed to the price.

Not run in this session: the UFCStats CSVs are not in the repo.

# Addendum 51: the finish board, and making the check falsifiable (2026-10-11)

Two builds from the same session. Neither changes a model.

## The finish board

A grid below the upcoming card: bouts down, rounds across, the card's 25
likeliest finishes. Built from `round_of_victory`, which the competing-risks
model already publishes per corner, per family, per round, and which sums
exactly to `p_finish`. Finish-only; decisions are excluded by construction.

Two things are stated on the panel rather than in a footnote, because without
them the grid misleads:

**It is ranked by probability, not by value.** No venue this tool reads prices
a method-and-round contract, so there is no price to beat. Calling these
"optimal" would invent the half of the comparison that decides it. They are the
model's likeliest finishes and nothing stronger.

**Twenty-five picks are worth about 1.5 expected hits.** The largest single
cell on a typical card is 10-12% and most sit at 4-6%, so the 25 sum to roughly
1.5. A grid of twenty-five confident-looking chips implies a hit rate it cannot
deliver, so the expectation is printed in the header at the same weight as the
count. Within a bout the picks are mutually exclusive — a fight ends once — so
a row's combined figure is a true probability while the card total is an
expected count, and the two are labelled differently.

The panel also carries the round claim's own weakness: it went 2 of 4 on the
last card, and the round split remains the least-tested thing the model says.

## The check record was unfalsifiable

`cornerman.checkreads.v1` lived in one browser's localStorage. No export, no
copy, and nothing in `mmastat/` read it — verified by grep. So the question the
check exists to answer, whether a UFC.com read beats the model, could not be
settled across cards by anyone, and clearing site data erased the record
silently.

**Export and import added.** Import MERGES and the entry with the earlier
`first_ts` wins, because `first_ts` decides whether a read counts as a forecast
and a restore must not become a way to make a late read look early. The
consequence, stated on the panel: re-importing an old file can move a read's
timestamp backwards, never forwards.

The buttons render in their own row, NOT inside `ckStrip()`. ckStrip returns
nothing until a gradeable record exists, which is exactly the state of the
browser someone restoring a backup is sitting at — the import has to exist
before the record does. The first build put them inside ckStrip and they were
invisible when needed most.

## A storage ceiling that would have arrived quietly

Raised in the same breath, and real. Every stored read carried `sig` — the full
JSON of both pasted stat blocks, both records and both parsed ESPN histories —
and `CKR` is the permanent record and is never pruned. About 3KB a bout, a
dozen bouts a card, forty-odd cards a year: roughly 1.4MB a year against a 5MB
localStorage ceiling, so the record would have begun failing to save in about
three seasons, silently, which is the worst available failure for a forecasting
record.

`sig` is only ever compared for equality, so it is now a 32-bit hash plus the
source length — **12 bytes against 3,008 measured**. A stored read is ~300
bytes, which puts the ceiling decades out instead of seasons.

The migration was the delicate part: an entry from an earlier build holds the
full string, and comparing it against a hash reads as "inputs changed", which
restamps `first_ts` to now and silently reclassifies genuine pre-fight reads as
after-the-fact — the exact failure the `first_ts` mechanism was built to
prevent. A stored signature therefore matches EITHER form and is rewritten as a
hash once seen. Verified: an old full-string entry is treated as unchanged and
its `first_ts` survives.

## Addendum 51, amendment 1 (2026-10-11): the check may re-level the board, not reshape it

Asked for next: make the check a selectable inclusion on the finish board, and
use the check's round-by-round record — "where their fights have ended", six
KOs in round one, four in round two — to set the finish probabilities per
round.

**Half of that is sound and is built. The other half is a recorded null.**

### What the toggle does

The model's round cells decompose exactly into the four route totals
(`a_ko`, `a_sub`, `b_ko`, `b_sub`) — verified against the payload, not assumed,
to within 0.0002. The check publishes those same four cells, shrunk and
tier-weighted. So with the toggle on, each route's round cells are multiplied
by `check_route / model_route`: **the level of each route becomes the check's,
the shape across rounds within that route stays the model's.**

This is not a new mechanism. It is `k_fin` — which already rescales the
survival model's shape to a separately calibrated finish level — applied per
route instead of once overall.

Verified: with a planted check of .40/.02/.05/.03 against model routes of
.108/.187/.198/.042, the re-levelled route totals land on .40/.02/.05/.03
exactly, and the within-route round shares are unchanged to 1e-4 on all four.

Off by default; a bout with no check, or a read whose five cells fail
`cells_ok`, stays model-only and is not marked. The toggle disables itself when
no bout on the card has a check.

### Why the round history is refused

Reading round probabilities off a fighter's own round counts is the exact thing
addendum 45 measured and rejected. Split-half reliability of a fighter's
round-one share is **0.21, falling to 0.05 as the sample grows**, against
**0.54 rising to 0.60** for whether he finishes at all. Whether a man finishes
replicates. When he finishes does not.

That table is in the panel captioned as evidence "for reading rather than
computing with" for this reason. Putting a checkbox in front of it would not
make it replicate — it would re-introduce a recorded null behind a control that
implies it was tested. So the check sets how often a route happens and never
which round, and the panel says so on screen.

### The loss side is already wired, pending its test

"How they have been beaten" is not folded in here either, for a different
reason: it is display-only pending the split-half test registered as addendum
48, which has not been run. Nothing about this board needs changing when it
passes — the board reads the check's method cells, so if the loss side earns
its way into those cells it reaches the board automatically.

That is the intended path for durability: not a second input to the board, but
a better method read feeding the one input it already has.

## Addendum 51, amendment 2 (2026-10-11): the board ranked cells and read as if it ranked bouts

Reported from the outside: the same bouts appear whether the check is on or
off, and some of the bouts shown are not the likeliest finishes on either side.

Both halves of that were fair, and the second one was a real defect.

### The dilution, measured

The 25 are ranked CELL by cell. A five-round bout spreads the same finish
probability across twenty cells; a three-round bout concentrates it in twelve.
On the live card:

| bout | rds | p_finish | cells | max cell | picks in top 25 |
|---|---|---|---|---|---|
| Buckley v. Malott | 5 | **.593** | 20 | .072 | 6 |
| Boser v. Diniz | 3 | .527 | 12 | .120 | 5 |
| Barriault v. Daukaus | 3 | .514 | 12 | .087 | **7** |

The likeliest finish on the card drew fewer picks than a bout seven points
behind it, purely from being scheduled for five rounds.

Worse, the only per-bout number on the panel was headed "combined" and was the
sum of the cells that made the 25 — which reads as the bout's finish
probability and is not. A bout could be the best finish bet on the card and
show a small figure.

**Fixed as a display change, not a ranking change.** The bout's whole finish
probability now has its own `finish` column beside `picked`, and the note says
why they differ. Cell ranking is kept, because a cell is what you would
actually bet; what was wrong was a panel that reported one quantity under a
heading that implied the other.

### Bouts with no round split are now rows

Four of eleven publish no `round_of_victory`. They were dropped from the grid
and mentioned only as a count in the footnote, so a bout the model had declined
to split looked identical to a bout it had no opinion about. They appear at the
foot with empty cells and the reason stated.

### The toggle does reallocate — verified

The report that the check changes nothing is explained by the reads agreeing
with the model, not by the toggle being inert. Planting a check of .90 finish
on a bout the model puts at .297 moves that bout from 2 picks to 7 and drops
two other bouts by three and three. The mechanism reallocates across the whole
card; it only looks inert when the check and the model agree about how often a
fight ends, which on real reads they often will — both are shrunk toward the
same divisional base.

That agreement is itself a finding worth keeping rather than engineering
around: if the check's finish level rarely departs from the model's, the check
is adding little on this axis, and the honest response is to measure that once
the exported record exists rather than to amplify the difference for display.

## Addendum 51, amendment 3 (2026-10-11): thin bouts, and a spread allocation

Reported: the two highest finish reads on the card — on the check's own
numbers — never appear on the board.

**Correct, and structural.** Those bouts are the THIN ones. They publish no
`round_of_victory` at all, so the re-levelling in amendment 1 had nothing to
scale: a check read on a thin bout could not reach the board however high it
was. The toggle was re-levelling five bouts and leaving the two the check had
most to say about on the floor.

### Placing a bout the model would not split

With the check on, a thin bout carrying a complete five-cell read is now placed
from that read alone, spread across rounds by a borrowed shape.

**The shape is pooled from this card's other bouts at the same scheduled
length**, from the model's own survival output, normalised — measured at
`[.489, .324, .187]` for three rounds on the live card, summing to 1.

It is NOT taken from the league table, and that is a deliberate refusal.
`market_bases.ends_before` gives round one and round two cleanly but leaves the
final round as a residual against a finish rate the table does not carry at
that scheduled length; for five rounds the residual comes out **negative**.
Estimating that tail to fill the gap would be inventing precisely the number
the extrapolation rests on. The card's own bouts need no estimate and come from
the same model.

It is still an extrapolation — the level is a real read, the round shape is
borrowed from neighbouring fights — so those rows are marked **shape borrowed**
and the note says what that means. A thin bout with no check read stays off the
board entirely; nothing is placed from a borrowed shape alone.

### Two ways to spend the 25

**Cell** (default, unchanged): the top 25 cells straight down. What you would
bet individually, with the known dilution from amendment 2.

**Spread**: bouts ranked by their own finish probability, then one pick each
per pass until the 25 are gone — every bout covered before any is doubled, and
because the passes run in finish order the higher bouts collect their seconds
first. Measured on the live card with check on: 11 bouts covered at 2-3 picks
each against 8 bouts at 1-5 under cell ranking.

The two modes genuinely disagree, and neither is more correct in the abstract:
cell ranking answers "what are the biggest individual bets", spread answers
"cover the card's likeliest finishes". The second is what was being asked for
and was not available.

### Still true, and unchanged by any of this

The round shape is never read off a fighter's own round history, in any mode,
with or without the check. 0.21 split-half falling to 0.05. The check sets how
often a route happens; the shape across rounds comes from the model, or on a
borrowed row from the model's other bouts — never from the counts in "where
their fights have ended".

## Addendum 51, amendment 4 (2026-10-11): the board had no floor and contradicted the verdict panel

Asked: why are bouts at 44% and 58% finish on a board of likeliest finishes,
when 61% is the threshold that marks a bout FINISH LIKELY?

**The board had no finish threshold at all.** It ranked and allocated and never
filtered. So it was offering finish picks on a bout the verdict panel, on the
same page, labels DISTANCE LEANS. One tool, two opposite readings of one fight.

### What the 61% actually is

Not an absolute. `finBase = 1 - decBase = 49.5%`, and the badge fires at twelve
points above it:

| | rule | finish |
|---|---|---|
| finish likely | `fin - finBase >= .12` | >= 61.5% |
| finish leans | `fin - finBase >= .05` | >= 54.5% |
| distance leans | `dec - decBase >= .05` | <= 44.5% |
| distance likely | `dec - decBase >= .12` | <= 37.5% |

So of the two asked about: **Blanchfield at 44% is DISTANCE LEANS** — six
points under the league's own base — and had no business on the board.
**Croden at 58% is FINISH LEANS**, above the base, and belongs there.

### The floor

A bout is excluded when a decision is five points or more likelier than the
league rate — the exact line at which this tool starts saying "distance". Not a
number invented for this panel, and deliberately NOT the 61.5% badge bar, which
was never the inclusion test: a bout at the league base rate still qualifies.

Verified on the live card: Godínez/Souza (32%), Pereira/Zheleznyakova (34%) and
Prado/Bonfim (42%) drop out; Camilo/Herbert at 49% and Allen/Duncan at 54% stay.
The excluded bouts remain as rows with their verdict and no cells, and are named
in the note with their finish figure, so nothing disappears silently.

The check can still carry a bout back in, which is the point of having it: a
30% model bout given a 72% check read reads FINISH LIKELY and qualifies.

**This is a consistency rule, not a betting rule.** It cannot say a pick is
good. It only stops the board recommending finishes on fights this tool has
already called the other way, which is a defect of coherence rather than of
calibration — and the honest fix for that is to make the two panels obey one
rule, not to tune either of them.

### The cost, stated

On a decision-heavy card the floor leaves few qualifying bouts, and spread mode
then pushes 25 picks into three or four of them, reaching further down each
bout's cells than it otherwise would. Coverage is traded for coherence. The
lowest pick is printed in the header for exactly this reason.

## Addendum 51, amendment 5 (2026-10-11): hedging, ordering, and naming the two modes

Three corrections, all to allocation and presentation. No model changes.

### The second pick in a bout is now the other corner

Spread covered every BOUT before doubling any, but inside a bout it ordered by
probability alone — so a dominant fighter took the first three picks and the
row was three bets on one man rather than a position on the fight. With one
pick you are backing a man; with two on the same man you are backing him twice.

The per-bout order now puts the **other corner's best finish second**, then
falls back to probability for depth. Verified at the boundary: a second corner
at 50% of the leader is hedged into slot two ahead of the leader's larger
second cell; at exactly 25% it is still hedged; at 24.5% it is not; a lone
corner is untouched.

`FB_HEDGE_MIN_RATIO = 0.25` is the "unless completely unwarranted" clause —
below a quarter of the leading corner, a hedge is not worth a slot. **Declared,
not fitted.** There is no sample to fit it on, and a constant that looks
measured when it is not is worse than one that admits what it is.

### Rows sorted by finish probability, empty rows removed

Rows were in card order and included bouts with no picks, carrying their
verdict as an explanation. On a board of the card's likeliest finishes an empty
row reads as an oversight. Rows are now only bouts that drew a pick, ordered by
their own finish probability, highest first.

Nothing is hidden by this: the note already named every floor-excluded bout
with its figure, and a second clause now names bouts that **cleared** the floor
and still drew nothing — only possible under optimal, where every slot can go
to a bigger cell elsewhere, and worth saying because an eligible absent bout
would otherwise look like an omission.

### The modes are now named for what they do

Spread-off was never "cell ranking" to anyone but me — it is **optimal picks**,
the biggest individual cells with no attempt at coverage or hedging, and
several picks can land on one man. Spread-on is **hedged spread**. The label
reads whichever is active, and the note describes that mode rather than both.

The underlying values stay `cell` and `spread` so a stored preference survives
the rename; only what the reader sees changed.

## Addendum 51, amendment 6 (2026-10-11): the check was never recorded on the bouts it matters most for

Reported: Mahjoub and Leblanc, at 61% and 64% finish on the check's own read,
are absent from the board while Croden at 58% is on it.

**Neither bout is modelled.** On the live card they sit in `no_read` — "name
not in UFCStats corpus" — along with four others:

| | |
|---|---|
| modelled | 7 (2 of them thin) |
| no_read | **6** |

Six of thirteen bouts on this card have no model number at all.

### Two defects, one cause

`finishPicks` walked `d.bouts`. A no_read bout is not in `d.bouts`, so it could
never be placed however high its read — the same shape as the thin-bout gap in
amendment 3, one level further out.

The one underneath it is worse. **`ckCapture` built its index from `d.bouts`
and the last card only, so a read entered on a no_read bout was never captured
at all** — not stored, not graded, not counted in the record. The sandbox has
always accepted these bouts and the panel has always shown a read, so the reads
existed; they had nowhere to go.

That is exactly backwards. A bout the model cannot price is the case the check
exists FOR: it is the only read available, and the one place a UFC.com paste is
not a second opinion on a model number but the entire read. Excluding precisely
those from the record meant the check was unmeasured where it has the most to
add — and on this card that is nearly half the bouts.

### Fixed

`ckCapture` now indexes `no_read` bouts through `sbSynthetic`, so their reads
enter `CKR`, the graded record and the export like any other. The board walks
them alongside the thin bouts, placed from the check's cells and a borrowed
round shape, and the row universe was widened to match or a bout could earn
picks with nowhere to be drawn.

Those rows are marked **check only** rather than "shape borrowed": the
distinction is real and worth the extra word. A thin bout has a model that
declined to split a number it does have; a no_read bout has no rating, no age,
no reach, nothing. Verified: a no_read bout given a 64% check read is captured,
placed, marked, and sorts to the top of the board on its own figure.

### What this does not fix

These bouts are absent from the model for a reason — the fighters are not in
the corpus — so nothing about this gives them a model number, and the finish
board rows built this way rest entirely on a pasted record plus a round shape
borrowed from other fights. That is the most extrapolated thing on the panel
and it says so on the row.

## Addendum 51, amendment 7 (2026-10-11): the floor becomes a control, and why Croden belongs

Reported: Croden (58%), Jourdain (56%) and Chovancek (50%, "no lean") look
wrong on a board alongside 72% and 69% bouts — and they survive even under
optimal.

Two different things, and only one is a defect.

### Croden under optimal is correct

From the live board, bout finish against that bout's largest single cell:

| bout | finish | top cell |
|---|---|---|
| **Croden v. Chandler** | **58%** | **17%** |
| Barriault v. Daukaus | 69% | 15% |
| Buckley v. Malott | 69% | 11% |
| Leblanc v. Galanti | 64% | 7% |
| Chovancek v. Su-young | 50% | 7% |

**The 58% bout holds the biggest single bet on the card** — a three-round fight
with the finish mass concentrated in one corner — while the 69% five-rounder
spreads the same probability across twenty cells and tops out at 11%. Optimal
ranks cells, so Croden belongs there. Removing it would mean removing the best
available finish bet because the fight it sits in is unexceptional, which is
the dilution of amendment 2 running the other way.

Chovancek is the honest weak case: 50% finish, "no lean", 7% top cell.

### The floor is now selectable, with the tool's own tiers as stops

| stop | needs | bouts on the live card |
|---|---|---|
| not distance | > 44.5% | 10 |
| **finish leans** (default) | >= 54.5% | 9 |
| finish likely | >= 61.5% | 6 |

Default moved to **finish leans**, which drops the 50% bout. The stops are the
length tiers the verdict panel already uses, so at any setting the board agrees
with the rest of the page.

### What a floor cannot do here, stated rather than papered over

**No tier separates a 61% bout from a 58% one.** They are three points apart
and sit on the same side of every boundary available. Setting the floor to
"finish likely" removes Croden at 58% — and also removes Mahjoub at 61%, which
was specifically asked for two amendments ago.

A line at 60% would do exactly what was wanted on this card and would be fitted
to one Saturday; it would move next week and there is no sample to justify it.
So it is not offered. If Croden and Mahjoub should land differently, the thing
separating them is not the bout figure — it is the cell size, where Croden has
the largest on the card and Mahjoub the third smallest. That is what optimal
already ranks on, and it is the mode where the distinction is real.

## Addendum 51, amendment 8 (2026-10-11): bout-priority allocation, measured and rejected

Proposed: give priority to the highest-finish bouts and descend from there, so
picks are not "wasted on decision-likely or decently probable bouts in place of
covering more probable outcomes on a higher finish % bout". The reasoning came
off the decision-share curve — 70% finish in the lowest decision-share bucket
falling to 33% in the highest.

Measured on the model's real cells for the live card, 25 picks, three rules:

| rule | expected hits | P(nothing lands) | bouts | deepest |
|---|---|---|---|---|
| optimal (top cells) | **1.53** | **15.0%** | 5 | 7 |
| hedged spread | 1.50 | 16.3% | 5 | 5 |
| **bout-priority** | **1.01** | **23.7%** | 2 | 20 |

**Bout-priority is worse on both.** A third fewer expected hits AND a higher
chance of going nought for twenty-five. It is not a trade-off; it loses twice.

The reason is the dilution of amendment 2 pointing the other way. Filling the
highest-finish bout first means buying that bout's TWENTIETH-best cell — around
a point apiece on a five-rounder — while 12% and 8.7% cells sit untouched in
other fights. Concentrating on the likeliest fight to finish means buying its
worst contracts in preference to other fights' best ones.

**What the decision-share curve does and does not license.** It says which
BOUTS finish. That justifies a floor, which now exists and is selectable. It
says nothing about which of a bout's twelve-to-twenty (fighter, method, round)
contracts to buy, and a 70% bout scheduled for five rounds spreads that 70%
across twenty cells.

Optimal already prioritises high-finish bouts to exactly the degree their cells
earn it — on this card it went seven deep in one bout unprompted. The
prioritisation is done by cell size, which is the quantity being bet, rather
than by a bout-level label that does not survive contact with the scheduled
length.

**Kept as is.** Recorded so it is not re-proposed.

### One addition from the question

The header now carries **P(nothing lands)** beside expected hits. "1.5 expected"
and "a one-in-six chance of 0 for 25" are the same slate described twice, and
only the second answers what is actually being asked when twenty-five bets are
being spent. It is also the only place the two modes meaningfully differ —
hedging costs 0.03 expected hits and buys 1.3 points of bust risk — so the
trade-off is now visible rather than argued about.

## Addendum 51, amendment 9 (2026-10-11): a 60% floor, measured and offered as a preference

Asked for after amendment 7 declined to invent it. The decline was about
fitting a threshold to one card; the question deserved a number rather than a
restatement of the objection.

Measured on the live card's own check finishes
(72/69/69/65/65/64/61/58/56/50), 25 picks, optimal:

| floor | bouts | expected hits | P(nothing lands) | lowest pick |
|---|---|---|---|---|
| 44.5% (not distance) | 10 | 2.73 | 3.6% | 7.9% |
| **54.5% (finish leans)** | 9 | **2.73** | **3.4%** | 7.8% |
| 60% | 7 | 2.60 | 3.4% | 6.9% |
| 61.5% (finish likely) | 6 | 2.44 | 3.9% | 6.4% |

**54.5% remains the best of the four on both measures** — identical expected
hits to no floor at all, with the lowest bust risk. Dropping the 50% bout costs
nothing because its cells were never going to be bought anyway.

**60% costs about 5% of expected hits and buys nothing measurable.** Raising
the floor removes eligible bouts, so the same 25 picks reach further down each
surviving one: the lowest pick falls from 7.8% to 6.9%. The mechanism is the
dilution of amendment 2 for a third time, and it is also why 61.5% is worse
still — fewer bouts, deeper reach, and bust risk going back UP to 3.9%.

### Added anyway, and labelled

The cost is small and the choice is not mine. The distinction that resolves it:

- A threshold **discovered in data** to maximise something needs a sample. 60%
  has none, and the measurement says it maximises nothing.
- A threshold **chosen** because someone only wants to bet fights clearly
  likely to finish needs no sample at all. It is a preference, it is
  legitimate, and it costs what the table says it costs.

So it is a fourth stop reading **"60% (preference)"**, it is absolute rather
than derived from the league base like the other three, and the note says so
whenever it is active — including the 5% figure. Nobody reading this later
should mistake it for a measured bar.

Verified: at 60% the card keeps 72/69/69/65/65/64/61 and drops 58/56/50, which
is the split that prompted the question.

## Addendum 51, amendment 10 (2026-10-11): per-bout override, and the head-to-head grid already exists

### Switching a bout off by hand

A floor is a rule and cannot know that a man missed weight on Friday, that a
replacement came in on short notice, or that you simply will not bet a given
fight. Each row now carries a checkbox; switching one off **returns its slots
to the pool** rather than leaving the slate short.

Verified: a bout holding 4 of the 25 switched off, the total stayed at 25, and
its four slots went +1 each to four other bouts; switching it back restored the
original allocation exactly. The row stays visible, dimmed and marked
**switched off**, because a hidden row has no checkbox to switch back on and
would look identical to one the floor removed. The list is per bout name, so it
survives a reload and means nothing next week — the correct lifetime for a
judgement about one fight.

### The head-to-head strengths comparison is already what the board is made of

Asked whether a fighter could earn a method pick in a round by having a higher
share of that finish in that round than his opponent, and whether both could
earn one where both are strong.

**That is `round_of_victory`, and it is already built that way.**
`method_round(sa, sb, n_rounds)` builds its features from BOTH fighters and
predicts a five-class hazard every minute — `survive`, `a_ko`, `b_ko`,
`a_sub`, `b_sub` — so `a_ko_r1` against `b_ko_r1` is precisely "which of these
two is likelier to win by knockout in round one, against this opponent". Every
cell on the board is a head-to-head comparison already, and the hedge rule of
amendment 5 is exactly "where both corners are strong, both earn a pick".

What does not exist is **visibility**: the board shows the 25 picks, not the
full twelve-to-twenty cell grid per bout, so the comparison driving the picks
cannot be read off the page. A strengths view would be pure display of numbers
already computed, and is a safe addition.

**The version to refuse** is the one phrased as a fighter's own share of that
finish in that round, taken from the record. That is the counts in "where their
fights have ended", and it is the recorded null for the fourth time in this
addendum: 0.21 split-half falling to 0.05, against 0.54 rising to 0.60 for
whether he finishes at all. The model's per-round hazards are a different
quantity — fitted across the corpus against opponent state, not read off one
man's dozen fights — which is why they are usable where his own round counts
are not.

## Addendum 51, amendment 11 (2026-10-11): the pick count becomes a control

Twenty-five stays the ceiling and the default; the control only reduces.

Measured on the live card, check on, floor at finish leans, optimal:

| picks | expected hits | lowest pick | P(nothing lands) | bouts covered |
|---|---|---|---|---|
| 25 | 3.45 | 7.1% | 1% | 9 |
| 15 | 2.56 | 12.3% | 5% | 9 |
| 10 | 1.90 | 13.8% | 11% | 9 |
| 5 | 1.08 | 19.3% | 29% | 5 |

**This is the better lever than the floor, and the table shows why.** Raising
the floor removes whole bouts and then sends the same 25 picks deeper into the
survivors, so the worst pick gets WORSE — 7.8% to 6.9% between the 54.5% and
60% stops in amendment 9. Reducing the count removes the weakest cells and
nothing else: the lowest pick climbs from 7.1% to 12.3%, and coverage holds at
nine bouts until the count falls below about ten.

Both reduce expected hits, since fewer or worse cells is fewer or worse cells.
The difference is what gets given up. The floor gives up whole fights on a rule
that cannot see Friday's weigh-in; the count gives up the cells you were least
likely to win. The second is almost always the right thing to surrender.

The header reports the picks actually placed, not the number requested, so a
card with fewer qualifying cells than the setting says so rather than implying
it found 25.

## Addendum 51, amendment 12 (2026-10-12): an "all bouts" stop, and what the board is not

### The bottom stop

`all bouts` added below `not distance`: every fight with finish cells is
eligible, including ones this tool calls distance-leaning. It exists because
the per-bout checkboxes of amendment 10 now do the pruning a floor used to have
to do — with a manual override there is no longer a reason to refuse to SHOW a
bout, only a reason to default to hiding it. Paired with optimal it is the
answer to "the best cells on the card regardless of which fight they sit in",
which no other combination gave.

Verified across all five stops on the live card: 11 / 10 / 9 / 7 / 6 bouts.

### This is not a simulation, and the distinction matters

Asked whether anything like digital-twin modelling produces the finish paths.
It does not, and the reason is worth recording.

`method_round(sa, sb, n_rounds)` builds ONE covariate vector from both
fighters, then evaluates a five-class hazard — survive, a_ko, b_ko, a_sub,
b_sub — at every minute of the scheduled distance, varying only `t` and `rnd`.
Each minute's contribution is `survival-so-far x hazard`, accumulated into the
round. It is an **analytic competing-risks calculation, exact, with no
sampling**: run it twice and it returns the same number to the last decimal.
A Monte Carlo twin would approximate the same integral with noise.

**What a true twin would add, and why it is not here.** The covariates are
static across the fight: only the baseline hazard moves with time and round.
So nothing models a knockdown in round one raising the round-two KO hazard, or
a grappler fading after a hard first. Within-fight state evolution is exactly
what a simulation would buy.

Buying it means SPECIFYING those dynamics — how much a knockdown shifts the
subsequent hazard, how fatigue maps to takedown defence — and there is no
within-fight state data in this corpus to fit any of it. The parameters would
be chosen rather than estimated, and a simulation with invented dynamics
produces confident, detailed, wrong paths that look far more sophisticated than
the honest calculation they replace. It is the "machine for rendering noise"
risk with better graphics.

Registered as a null-by-construction rather than tested: it cannot be tested
without data this project does not hold.

### What the board actually neglects

Two things, named so they are not mistaken for oversights:

1. **Price.** These are ranked by probability because no venue this tool reads
   quotes a method-and-round contract. Without a price there is no edge, only a
   likelihood. That is the single biggest gap and it is not fixable from here.
2. **Agreement between the model and the check.** Both produce method cells,
   and a cell both back is better founded than one only a single source
   supports — but nothing currently uses the agreement as a ranking input. It
   is available and unused. It is NOT proposed until the exported check record
   can show the agreement is worth something, which is the same discipline the
   loss-side panel is waiting on.

# Addendum 52: the check's first forecasting sample (2026-10-12)

The export built in addendum 51 arrived. 34 reads, and for the first time the
check can be scored as a forecaster rather than described.

## What is in it

| group | n | entered | status |
|---|---|---|---|
| UFC 332 (3 Oct) | 10 | 6 Oct | **post-hoc**, excluded, as designed |
| Fight Night 10 Oct | 11 | **6 Oct, 22:25–23:38** | **genuine forecasts** — four days early |
| Fight Night 17 Oct | 12 | 11–12 Oct | pre-fight, unresolved |
| stale | 1 | — | no `first_ts`, all-zero cells |

The middle group is the thing that did not exist before: eleven reads entered
four days ahead of a card that is now graded.

## Winner, on the ten gradeable bouts

| | right | Brier |
|---|---|---|
| model | 5/10 | 0.3005 |
| **check** | **5/10** | **0.3053** |

The check matched the model's hit rate and was fractionally worse on Brier.

## All three, scored on the same five bouts

| | right | Brier |
|---|---|---|
| **market** | **4/5** | **0.2181** |
| model | 3/5 | 0.2599 |
| check | 2/5 | 0.2825 |

The market beat both, which is the standing result holding. The check was last.

Where it moved: it had Walker at .862 against the model's .725 and was right;
Price at .532 against .322 and was right; Franco at .120 against .268 and was
wrong. It is not tracking the model — it disagrees by up to 21 points — it
simply is not disagreeing in a profitable direction yet.

## Method

Check top pick **3/10**. It said "decision" on seven of ten, on a card that
produced eight finishes. Same structural problem the model's method metric has:
decision is one bucket against four finish buckets.

## Verdict: none, and that is the point

Ten bouts against a registered floor of twelve, and 5-vs-5 on the winner would
not separate two coins. **What has changed is that the question is now
answerable at all** — before this export the check generated no evidence that
could leave one browser.

The honest early read is that the check is not beating the model and neither is
beating the market. If that holds to a real sample, the conclusion is that a
UFC.com paste re-prices seven of fourteen inputs and the other seven carry more
weight — which is what the panel has said in prose since it was built, and
would then be measured rather than argued.

**Standing bar unchanged**: no claim about the check until the sample clears
CK_MIN, and the post-hoc group stays out of every count no matter how much it
would flatter the record.

## A defect the export exposed

Two keys for one bout: `Matheus Camilo vs. Jai Herbert` and
`Jai Herbert vs. Matheus Camilo`. The reversed one carries no `first_ts`,
all-zero method cells and no `cells_ok` — a legacy artifact of the
`sbMethodRead` bug, stored under the other corner order from a payload that
listed the fighters the other way round.

It is inert: `ckGrade` gates on `cells_ok === true` and skips it. But the bout
key being corner-order dependent means a card that flips the order silently
orphans a read rather than updating it, and the record keeps both. Logged here
rather than fixed, because the fix is an identity join on the bout the same way
`grade_archive` already prefers fighter ids over names, and that is a change
worth making deliberately rather than in passing.

## Addendum 52, amendment 1 (2026-10-12): storage measured on the real store, and a distance-only view

### Ninety percent of the record was dead signatures

The export made this measurable for the first time. On the real 34-read store:

| | reads | bytes | avg |
|---|---|---|---|
| legacy full-string `sig` | 21 | 31,471 | 1,498 |
| hashed `sig` | 12 | 3,162 | 263 |
| no sig | 1 | 170 | — |

The hash of amendment 51 only ever rewrites a read whose bout is still on the
current card or the last one. A read for any earlier card is never touched
again, so it keeps the full pasted-input string forever — and those 21 reads
held **90% of the whole record**.

`ckLoad` now compacts them once, on load. Verified against the actual exported
store: **33,887 bytes to 7,929, a 76.6% reduction, 34 of 34 reads intact, and
not one `first_ts` moved** — which is the field that decides whether a read
counts as a forecast and the only one that must never shift.

### The ceiling, now with real numbers rather than an estimate

At 260 bytes a compacted read:

| | reads | store | against a 5MB cap |
|---|---|---|---|
| 1 year (40 cards) | 520 | 0.13 MB | 2.6% |
| 5 years | 2,600 | 0.65 MB | 13% |
| 25 years | 13,000 | 3.2 MB | 65% |

Storage is not a constraint on this record and will not become one. The earlier
concern was correct about the mechanism and is now closed by measurement rather
than by argument.

### `distance only`

A sixth stop, between `all bouts` and `not distance`, showing ONLY what the
others exclude. It is not a floor: `all = dist + any` is a clean partition,
verified on the live card — all [56,54,49,42,34,32,30], dist [42,34,32,30],
any [56,54,49].

It is for inspecting what the board leaves behind — the finish cells inside
fights expected to go the cards — and the note says so rather than presenting
it as a slate. Those are the longest shots on any card by construction, and
without a price there is no way to tell a longshot worth taking from one that
is simply unlikely.

## Addendum 51, amendment 13 (2026-10-12): skew swept and rejected, and a correction

Proposed: a skew control distributing picks evenly, top-heavy or bottom-heavy
by the bouts' finish probabilities.

Skew is a parameter, so it was swept rather than argued about. Weighting each
bout by `finish^k` and allocating quotas in proportion, 25 picks, live card:

| allocation | expected hits | P(nothing lands) | bouts |
|---|---|---|---|
| **optimal (cells)** | **2.734** | **3.6%** | 10 |
| even (round-robin) | 2.691 | 4.1% | 10 |
| bottom-heavy k=-3 | 2.631 | 4.6% | 10 |
| bottom-heavy k=-1 | 2.677 | 4.3% | 10 |
| even k=0 | 2.723 | 3.9% | 10 |
| top-heavy k=1 | 2.708 | 3.9% | 10 |
| top-heavy k=2 | 2.708 | 3.9% | 10 |
| top-heavy k=4 | 2.677 | 3.9% | 10 |
| top-heavy k=8 | 2.538 | 3.8% | 8 |

**Every setting of the dial is dominated by optimal on both metrics.** Not a
trade-off at any value of k, in either direction. Not built.

The reason it cannot help: at 25 picks across ten eligible bouts, optimal
already covers all ten. There is no coverage left for a skew to buy back, so
every constraint it imposes can only move picks onto worse cells.

### The correction, which matters more than the skew

Checking whether skew helps at lower counts produced a result that contradicts
what was said in amendment 11 and in the panel's own note:

| picks | optimal: exp / bust / bouts | even: exp / bust / bouts |
|---|---|---|
| 25 | 2.734 / 3.6% / 10 | 2.691 / 4.1% / 10 |
| 15 | 1.895 / 10.8% / 7 | 1.791 / 13.2% / 10 |
| 10 | 1.412 / 19.4% / 6 | 1.239 / 26.4% / 10 |
| 5 | 0.792 / 40.8% / 4 | 0.682 / 47.8% / 5 |
| 3 | 0.502 / 57.7% / 3 | 0.422 / 63.2% / 3 |

**Optimal wins on BOTH axes at every count.** At ten picks it covers six bouts
against the spread's ten and still busts less often — 19.4% to 26.4%.

So the earlier claim that "hedging costs 0.03 expected hits and buys 1.3 points
of bust risk" was **wrong, and wrong in the flattering direction**: the figures
it was drawn from (optimal 15.0%, spread 16.3%) say the spread busts MORE. The
spread was being credited with buying variance reduction it does not deliver.

Diversification reduces variance when the positions are comparable. These run
from 17% to 2%, so thinning the good bouts gives up more mass than the extra
bouts return. Spreading across more bouts raises the ceiling on how many CAN
land and lowers the chance any of them do.

**Hedged spread is kept**, because covering both corners of a fight is a
legitimate preference — you may want a position on a bout rather than a bet on
a man. It is no longer described as reducing risk, in the code or on the panel,
because it does not.

## Addendum 51, amendment 14 (2026-10-12): skew swept at every pick count, and a conflation to own

Amendment 13 swept skew at 25 picks only, then — in the next breath — showed a
pick-count table that was comparing **optimal against hedged spread**, not
optimal against skew. Two different controls, presented adjacently, and the
reasonable reading of that pairing is "skew fails at 25 but the lower counts
are where it lives." That reading was invited by the way it was written, so the
sweep it implies has now actually been run.

Eligible set: the live payload at the `all` floor — five bouts, 68 cells,
finish probabilities .593 / .527 / .514 / .338 / .334. A narrower set than
amendment 13's ten bouts, which makes it the HARDER test for skew: with fewer
bouts and a wider spread between them, a quota rule has more room to matter.

Weighting each bout by `finish^k`, largest-remainder quotas, cells taken
best-first within each bout:

| picks | optimal | best k by exp hits | best k by bust |
|---|---|---|---|
| 25 | **1.533 / 20.4%** | k=1 → 1.502 / 21.1% | k=1 → 21.1% |
| 15 | **1.097 / 31.9%** | k=1 → 1.082 / 32.4% | k=1 → 32.4% |
| 10 | **0.820 / 42.4%** | k=4 → 0.787 / 43.9% | k=4 → 43.9% |
| 5 | **0.486 / 60.0%** | k=4 → 0.451 / 62.2% | k=4 → 62.2% |
| 3 | **0.319 / 71.3%** | k=0 → 0.278 / 74.6% | k=0 → 74.6% |

Twelve values of k from -3 to +8, five pick counts, two floors: **sixty
allocations, and not one of them beat optimal on either axis.** Optimal is
strictly best everywhere. The dial has no setting that is ever right.

### The one thing skew does buy, and why it is still not a control

Skew does move one number: coverage. At 15 picks optimal touches four bouts
and even quotas touch five; at 5 picks, three against five. So the dial buys
breadth — and pays for it in both expected hits and bust risk, which is the
same bill the hedged-spread mode already itemizes.

That is the argument against building it. Coverage is a legitimate thing to
want, it is already a checkbox, and the checkbox states what it costs. A skew
dial would be a second, blurrier route to the same place, with the cost spread
across a continuous parameter where it is harder to see. Three controls that
each do one legible thing beat four where two overlap.

**Not built.** The finding is recorded so it is not re-proposed: this is now
the second sweep to reject it, on a different eligible set, by a wider margin.

# Addendum 53: the missing division, and a promotion-tier list declined (2026-10-12)

## The missing division is not a scraper bug

Reported: a check-only bout — no model read — showed the POOLED league mix in
"how they have been beaten" rather than its division's.

The cause is structural, and worth stating because it looks like something to
fix upstream and is not. `data/upcoming.txt` is regenerated from Wikipedia on
every refresh. When the card itself does not name a division, `infer_division`
falls back to the most recent REAL division each fighter fought in, skipping
catchweights. That fallback returns `""` only when NEITHER fighter has a prior
bout in a known division — a debutant. And the same absence of fight history is
why the model declines to read the bout at all.

**One cause, two symptoms.** There is nothing upstream to scrape, and editing
`upcoming.txt` by hand does not survive the next refresh — the same constraint
that produced `data/corner_order.txt` as a separate override file.

### Why it mattered more than it looked

This is the error addendum 50 caught in a different place. Falling back to
pooled is not a mild approximation:

| base | ko | sub | n |
|---|---|---|---|
| pooled | .319 | .177 | 6,866 |
| Heavyweight | .506 | .127 | 510 |

**A 19-point error on KO and 5 on submission**, in the column a fighter's loss
mix is compared AGAINST. As addendum 50 put it, the above/below flag could point
the wrong way — which is worse than no flag. A debutant heavyweight was being
measured against a league that is 60% flyweights and bantamweights by volume.

### The fix

A division picker in the check panel, shown **only** when the card states none.
Options come from `baserates.json`'s own division list, so a value that cannot
resolve cannot be entered. Stored per bout in `SBOX`.

Three properties it has on purpose:

- **It never writes into `DATA`.** Verified: `b.weight_class` stays null after a
  pick. Nothing captured, graded or exported inherits an operator's guess as if
  the card had stated it.
- **It is marked as the operator's.** Gold dashed border, "yours, not the
  card's", and "(set)" beside it on the finish board. A borrowed number that
  looks like a scraped one is exactly the failure to avoid.
- **It commits on change, not on "Read both"**, because it changes which league
  every number in the panel is compared against; and **Clear does not clear it**,
  because clearing a bad paste should not cost a fact about the card.

Confirmed end to end in the browser: pooled `{div:null, n:6866, ko:.319}` →
`{div:"Heavyweight", n:510, ko:.506}`, persisted across reload, no page errors.
The panel already names the division it used, so setting it is self-confirming.

## A five-tier promotion list, considered and declined

Supplied: an LLM-generated ranking of MMA promotions into five tiers — UFC/PFL/
ONE at the top, through regional and amateur — with the question of whether the
0.5 tier weight is being assigned properly.

**Declined, for two reasons that are different from each other.**

### 1. It ranks the wrong axis

`espnTier()` is not a stature rating. It is an **exchangeability** rating with
respect to the thing being predicted: UFC fights. The question each fight in a
history has to answer is "how much does this tell me about what happens in the
Octagon", and by that measure a PFL or ONE knockout is not equal evidence to a
UFC one however major those promotions genuinely are. Promoting them to 1.0
because they are "global elite" would be a category error — correct on stature,
wrong on the only axis the weight exists to express.

### 2. It converts one unmeasured constant into four

The 0.5 is already flagged in addendum 50 as **declared, not fitted**, and
registered there as a candidate with a stated test: for fighters holding both
regional and UFC records, the ratio of regional finish rate to UFC finish rate
implies the weight directly. That test has not been run (the UFCStats CSVs are
not in the repo).

Replacing one declared constant with a four-step declared ladder does not move
it closer to measured. It makes it **look** calibrated while adding three more
unfitted parameters, each of which would then need its own test. This project's
own rule applies: a weight moved to make a number look better is the same error
as a gate keyed to the price.

### What the list did surface, and is worth a check

The binary classifier sends **everything that is not UFC/TUF/Contender Series to
0.5**, which means an amateur bout — if one appears in an ESPN history table —
counts the same as a Cage Warriors bout. The Wikipedia parser already excludes
amateur records explicitly (`wiki record parser` test: "3 pro rows parsed,
amateur excluded"); the ESPN path has no equivalent exclusion.

ESPN's fight-history tables are believed to be professional-only, so this may be
a non-issue. **Registered as a check, not a change**: if an amateur row is ever
observed in a pasted ESPN history, amateur goes to 0, not 0.5 — it is not weaker
evidence about UFC performance, it is evidence about a different sport's
qualifying tier. Not acted on before it is observed.

## Addendum 51, amendment 15 (2026-10-12): two more exclusion axes, and what they do NOT do

Requested: switch off a single cell (one bout, one round), and switch off a
round across the whole card, with the freed picks redistributing.

Built. It joins the per-bout switch from amendment 9, so the board now has three
exclusion axes: bout, round, cell.

### The line this does not cross

An exclusion is **not a claim about probability**. Switching off round 3 does not
say round 3 is less likely than the model has it, and nothing here reweights
anything. The cell keeps the probability it had; it is simply not somewhere the
operator will put money, and the 25 go to the next best cells that are.

That distinction is the entire reason this was safe to build. An exclusion that
quietly rescaled the remaining cells would be a model change wearing a checkbox,
and the board would stop meaning what its header says. Verified on screen: with
round 3 off the `finish` column still reads 59% / 53% / 51%, unchanged, because
it is computed from the full eligible set and not from the picked one.

### The cost, stated because the control has one

Exclusions can only make the slate worse on its own terms — they remove cells by
preference and backfill with weaker ones. Measured live at the `all` floor:

| state | expected hits | P(nothing lands) |
|---|---|---|
| nothing excluded | 1.5 | 15% |
| one cell off | 1.5 | 17% |
| one cell + round 3 off | 1.4 | 20% |

**Five points of bust risk for one round.** That is not an argument against the
control — a bet you do not want to make is worth more than 5 points of anything
— but it is the number, and the board should not hide it. The header already
recomputes both figures, so the cost is visible at the moment of the click.

### Three decisions inside it worth recording

**The excluded cell still renders.** The obvious implementation drops it and lets
it show as "—", which is wrong twice over: an excluded cell becomes
indistinguishable from a bout that never had a pick there, and there is nothing
left to click to put it back. Excluded cells keep their place, struck through,
carrying what they would have been worth.

**The round switch wins over the per-cell one, and says so.** A cell held off by
its column is drawn dimmer, is not clickable, and its tooltip names the round
switch. A control that appears clickable and does nothing is worse than one that
is visibly disabled.

**Lifetimes differ on purpose.** Cell exclusions are judgements about one fight,
so they are pruned to the current card's bouts, the same way SBOX is — the store
cannot grow across a season. Round exclusions are a standing betting preference
("I do not bet round 5"), so they persist; and because a preference you have
forgotten is worse than one you have to re-enter, the panel names every
switched-off round in words rather than only striking the column.

A shortfall line was added with them: when exclusions and the floor together
leave fewer than `FB_N` eligible cells, the panel says so explicitly. "19 picks"
in the header does not explain why it is not 25, and the honest answer — the
rest are **not being spent** rather than being spent on worse cells — is the
one worth showing.

### Not built: a fourth axis

Per-method exclusion within a cell (take the KO in round 3, not the submission)
was considered and left out. The request was for a round in a bout, the cell is
the unit the board is drawn in, and a fourth axis interacting with three others
is how an instrument becomes a form. Registered as available if wanted; not
added speculatively.

# Addendum 54: the finish board graded, and the check-model offset (2026-10-12)

Four things from one session: a graded record for the finish board, a coverage
and round-calibration decomposition, a route-level comparison between the check
and the model, and a concurrence mark. The last of those is the smallest and the
third is the one that matters.

## The integrity problem, solved before anything was built

The obvious implementation grades "what the board picked" by running the LIVE
board over an archived card. That is wrong in a way that would not look wrong:
the board's picks depend on the floor, the pick count, the mode and the
exclusions, so turning a knob today would silently rewrite what the record says
was picked in September. **It is the ledger-you-can-edit problem in a new
costume** — and this project's standing rule is that a ledger you can edit is a
ledger you will edit.

So grading runs against a FROZEN configuration that reads none of the live
controls: the top 25 cells, every bout eligible, no exclusions, no hedging. One
fixed question asked of every card — *are the model's biggest 25 finish cells
calibrated* — and no setting on the page can move the answer.

## It backfills, which is why it was worth building now

`history.json` already carried winner, method and round per bout; it did not
carry the round split to grade them against. One key added to the graded row in
`upcoming.py` fixes that, and because `grade_archive()` re-grades every archived
card from scratch on each run, **the whole existing record backfills on the next
pipeline pass** rather than starting from zero. Cost measured at +2.3 KB per
card, about 90 KB a year.

## What it says so far, which is not much

| card | cells | expected | landed |
|---|---|---|---|
| Allen vs. Duncan | 25 | 1.68 | 3 |
| UFC 332 | 25 | 2.19 | 5 |
| UFC 331 | 25 | 2.19 | 2 |
| **total** | **75** | **6.06** | **10** |

13.3% actual against 8.1% predicted — **+1.7 sd, which is not a result.** The
panel says so in those words. At roughly two expected hits a card it takes about
eleven cards to confirm a rate this far off and some eighty to catch a 20%
miscalibration, and a panel that let "10 against 6.06" read as the model beating
its own numbers would be worse than no panel.

### Coverage, which is the better early number

Of 15 finishes on graded cards, the 25 picks held the exact cell for **10**; the
full eligible set held it for **15 of 15**. The model has not once failed to put
weight on the cell that happened. The gap is the cost of the 25-pick budget, not
a modelling miss — different failures, different fixes, and a hit rate alone
cannot tell them apart.

### Round shape, which is where the early signal is

| round | finishes came | board weighted | gap |
|---|---|---|---|
| 1 | 67% (10) | 55% (3.31) | **+12** |
| 2 | 13% (2) | 40% (2.41) | **−26** |
| 3 | 13% (2) | 6% (0.34) | +8 |
| 5 | 7% (1) | 0% | +7 |

The round-two column is the sharp one: the board puts **40% of its weight in
round two and 13% of finishes arrived there**. Direction matches the recorded
finding that P(round one | finish) climbs 0.402 to 0.569 across decision-share
buckets. Fifteen finishes settles nothing. Registered as the first thing to
re-read at ten graded cards.

Only the SHARES compare, and the panel says so: the left column is every finish
that happened, the right is expected hits inside 25 selected cells. Printing the
raw counts side by side without that warning would invite a comparison between
two different kinds of quantity.

## The route offset — the real finding

The check and the model were compared at the **route** level (`a_ko`, `a_sub`,
`b_ko`, `b_sub`, `dec`), and the level is the whole point. With the check on, a
cell is the model's round shape times the check's route total: the round
dimension is entirely the model's, the route dimension entirely the check's.
Comparing cell by cell would compare a number with itself.

On 15 bouts carrying a check read:

| | gap (check − model) | direction |
|---|---|---|
| decision share | **−15.3 pts** | check lower in **15 of 15** |
| KO/TKO routes | +6.2 pts over 30 | — |
| SUB routes | +1.5 pts over 30 | — |

**Fifteen of fifteen in one direction is p ≈ 0.00003.** The two sources do not
disagree at random about how often fights end: the check reads finishes about
fifteen points hotter than the model, flowing into knockouts far more than
submissions. One of them is wrong, and the graded record is what will say which.

Caveat recorded on the panel itself: these are the bouts the operator chose to
paste, not a random sample, so selection cannot be excluded — though a clean
15/15 on direction is hard to produce from selection alone.

## Concurrence marked, and deliberately not promoted

Tested first, on 36 graded routes:

| | n | landed | they said |
|---|---|---|---|
| agree ≤3 pts | 8 | 1 (12.5%) | ~9% |
| disagree >3 pts | 28 | 6 (21.4%) | ~16% |

Both land about what they claimed. **Agreement carries no information about
whether a pick is better** — the apparent edge for disagreement is entirely that
disagreed routes carry higher probabilities. Weak at n=36, but there is certainly
no evidence for the intuition that convergence means confidence.

So the mark is a **thin left rule, not a ring**. A gold ring around a pick reads
as "this is a good one" whatever the caption says, and that reading is not
supported. The caption on the board states in words that it is concurrence only.

`FB_AGREE = 0.03` is declared, not fitted.

One consequence worth recording: on the live card only 1 of the 25 picks carries
the mark while 38 of 152 eligible cells do. **Picks concentrate on disagreement**,
because a route the check pushes above the model is exactly what lifts its cells
up the ranking. The board is, structurally, mostly betting the check's
disagreements with the model.

## Placement

The graded panel sits in the **Last card** zone, not on the board. The board is
the instrument bets are placed with; the record of whether it works is a
retrospective, and mixing them makes the slate harder to read without making the
record easier to find.

The single exception is carried up: one sentence of accumulated calibration sits
in the board's own note, because that number should change how confident you are
while you are choosing. The per-card table should not be in the way while you do.

# Addendum 55: the check was not beating anything — two denominator bugs (2026-10-12)

Three questions from one message. The first two were display faults. The third
was a reading of the page that the page had invited, and it is wrong.

## 1. The card totals were model-only, and the check had no total at all

`card_tally` scores the model's card-level claims against the base rate. The
check appeared on the fight tiles and nowhere else, so any impression of how it
was doing came from reading twenty individual rows by eye.

That is the subset error this project already warns about in writing, committed
by the page's LAYOUT rather than by its arithmetic. A read only exists on bouts
interesting enough to paste; totalling them by eye against the model's whole-card
record flatters the check by construction.

**Fixed**: a matched tally, restricted to the bouts carrying a read, with model,
check and market all scored on exactly those bouts, and post-hoc reads held out
on their own line.

## 2. The check's pick row was restating its own ends row

The model's pick row prints a per-corner contract — "Blanchfield by DEC 52%".
The check's printed the COMBINED decision — "by DEC 56%". Two different
quantities on one row labelled `pick`: 52% is one fighter winning on the cards,
56% is anybody winning on the cards. Side by side that invites reading 56 > 52
as more confidence about the same claim.

Worse: the check's combined decision IS its distance number, so the pick row was
restating the ends row directly above it and carrying **no information at all**.

**Fixed**: the decision cell renders by corner when one corner leads by the same
6 points used for "no clear favorite" elsewhere, with THAT corner's probability,
and as "split DEC" at the combined figure when neither does. Verified: a bout at
pA 0.80 with decision-heavy records now reads "Alvarez by DEC 58.6%" rather than
"by DEC 72.8%".

The GRADED cell set is untouched — five cells, decision combined, matching the
model's `m_decision` — and so is `norm()`. A display fix is not allowed to move
the record.

## 3. "The check beats the model and the market" — it does not

### The second denominator bug, which produced the impression

`pastGrid`'s "claims called" row counted each side over the claims IT answered.
On a bout where the model publishes no method report, the check was scored on
four claims and the model on two, and **the two rates were then ranked against
each other**. A side that answers more questions is not a side that is more often
right. The row was reading the first as the second.

### Matched, and split by whether the read could have seen the result

| | claims | check | model |
|---|---|---|---|
| all graded reads | 56 | **32** | 23 |
| **entered before the card** | 22 | **11** | 9 |
| entered after the card | 34 | **21** | 14 |

**The entire advantage is in the post-hoc reads.** On reads entered before the
fights the gap is two claims out of twenty-two, which is nothing. On finish type
specifically — the field a UFC.com page contaminates most directly, since the
Win-by-Method counts then contain the fight — live reads are **2/6 against 2/6,
exactly level**, while post-hoc reads are 6/9 against 3/9.

That is the leak behaving precisely as the as-of guard predicted in writing:
"it will look sharpest exactly where the leak is largest — method, and the
winner's own rates." This is confirmation of the leak hypothesis, not evidence
about the check's skill.

### On the winner, where a market price exists to compare against

| | n | right | Brier | log loss | mean p on winner |
|---|---|---|---|---|---|
| model | 20 | 11 | **0.2623** | **0.7271** | .513 |
| check | 20 | 11 | 0.2775 | 0.7730 | .512 |

Level on winners called, slightly WORSE on both proper scoring rules. On the 12
bouts carrying a price: model 8/12 (Brier 0.2257), check 7/12 (0.2566), **market
10/12 (0.1796)**. The market beats both comfortably and it is not close.

**So: no, there is nothing here to work with yet.** The check's apparent edge was
two denominator faults and a leak. Both faults are fixed; the leak was already
being flagged per bout and is now separated in the totals as well.

What remains true and unaffected is addendum 54's finding: the check and the
model disagree **systematically** about how often fights end, 15 of 15 in one
direction. That is still worth settling, and it is a different claim from "the
check is more accurate" — which, on matched claims and live reads, it is not.

## Addendum 54, amendment 1 (2026-10-12): the model arm was already there, and it was unmatched

Asked: should the graded panel show the model's hit/exp beside the check's?

**It already did** — the `expected` and `landed` columns ARE the model arm. The
asymmetry was formatting: the model got two labelled columns, the check one
compressed cell, which made the comparison hard to make by eye and the question
inevitable.

### The latent bug the question exposed

The check arm can only draw cells from bouts carrying a read; the model arm drew
from the whole card. **Two different universes in adjacent columns.** On the
cards in hand they coincide (6 of 6, 9 of 9, and 0 of 8 where no read exists), so
nothing was visibly wrong — but paste five bouts of ten and the check arm draws
from half the pool while the model draws from all of it, and the column reads as
a verdict on the check.

Same subset error as the card totals and the claims-called row. **Third time in
one session**, so it is written down as a rule: *any time two sides are placed in
adjacent columns, the first question is whether they were asked the same question
about the same bouts.*

**Fixed**: the model is re-run over exactly the bouts carrying a read, and both
arms are shown side by side with the read count beside them.

### What the matched comparison says

Over 15 bouts with a read across 2 cards:

| arm | expected | landed |
|---|---|---|
| model, same bouts | 3.87 | 8 |
| check's route weights | 5.30 | 8 |

**Identical hits; both under-called it; the check's claim was closer.** This is
the first evidence bearing on addendum 54's 15-of-15 finding — finishes arrived
more often than the model expected, which is the direction the check reads them.
Fifty cells settles nothing, but the direction is now on the record.

### A wording error caught before shipping

The first draft of that generated sentence read *"the check is more confident and
no more often right, which is a calibration difference, not an accuracy one."*
On identical hits that sounds like the extra confidence was unearned — and it is
**the opposite of what the figures beside it said**, since both arms under-called
the count and the higher claim was therefore the nearer one.

Recorded because it is the worst error this panel can make: wrong, in a voice
that sounds measured, directly above the numbers that contradict it. The line now
computes which arm was closer rather than asserting a verdict.

# Addendum 56: the check had no card-level finish count (2026-10-13)

Asked: is the check's expected finish amount stated anywhere on the upcoming
card, so it can be read against the graded board?

**The model's was; the check's was not.** The card-shape panel has projected
"first-round finishes" and "finishes inside the distance" since it was built,
and `card_tally` grades both afterwards. The check makes exactly the same claim
— every read carries a `dec`, so `sum(1 - dec)` is its expected finish count —
and it was never stated, so there was nothing to grade and nothing to compare.

**Added**, matched to the bouts carrying both a check read and a model decision
share. Third matched-denominator fix in two sessions, and this one was caught
before writing the code rather than after: the unmatched version summed the
check over ten bouts and the model over the six it had split, and the larger
number would have read as the bolder call when it was only the longer sum.

## The comparison asked for cannot be made yet, and the panel says so

"What happened when a similar amount was projected" needs a spread of
projections to bucket on. The three graded cards projected **2.7, 4.4 and 4.2**.
There is no "similar amount" to match against — any bucketing would be one card
per bucket wearing the clothes of a distribution.

What is available is the running total, matched the same way, and the panel
states it as a direction rather than a finding.

## What the running total says — third independent confirmation

Over 15 graded bouts carrying both reads:

| | finishes called | actual |
|---|---|---|
| model | 7.08 | **11** |
| check | 9.37 | **11** |

**Both under-called it; the model by 3.92 against the check's 1.63.**

This is now the third independent measurement pointing the same way:

1. Addendum 54: the check's decision share sits 15.3 points below the model's,
   lower in **15 of 15** bouts.
2. Addendum 54 amendment 1: on the graded board, matched, both arms landed 8 —
   the model having claimed 3.87 and the check 5.30, so the check's claim was
   the nearer one.
3. Here: card-level finish counts, matched — the model under-calls finishes by
   more than twice what the check does.

Three different slices of the same ~15 bouts, so these are **not independent
samples** and must not be treated as compounding evidence. What they do
establish is that the discrepancy is consistent across every level it can be
measured at — route, cell and card — rather than an artifact of one of them.

Registered: at ten graded cards, the question "is the model's finish rate too
low" gets re-read against all three. If it holds, the correction belongs in the
survival model's finish scaling, not in the check.

## Addendum 54, amendment 2 (2026-10-13): the spread arm, and why it is shown rather than toggled

Asked: does the graded panel account for optimal AND hedged spread, perhaps with
a toggle?

**It accounted only for optimal.** The frozen configuration was the top 25 cells
straight down — which is cell mode — so hedged spread, a mode in actual use, had
no graded record at all.

### Added, as a second frozen question — not as a setting

The frozen-config rule from addendum 54 was never "only one question". It was
"the question must not move with a live control". Two declared configurations,
each immutable, satisfy it exactly as one does; a toggle wired to `FB_MODE`
would not.

`FB_CANON.hedge = 0.25` pins the hedge ratio in the grader rather than reading
`FB_HEDGE_MIN_RATIO`. If that live constant were ever retuned, every past card's
spread record would otherwise move with it — the same silent-rewrite problem the
frozen config exists to prevent, one level down.

### Shown side by side, not behind a toggle

The request was for a toggle; both arms are shown instead. A toggle hides half
the answer and turns the panel into a place to find out which arrangement reads
better, which is the failure mode the whole frozen design is guarding against.
Side by side, the comparison IS the content. Cheap, and it removes the
temptation rather than relying on restraint.

### What it says

| arm | optimal | hedged spread |
|---|---|---|
| model | **10** / 6.06 | 9 / 5.72 |
| check on | **8** / 5.30 | 7 / 5.04 |

Spread lands **one fewer in both arms**, on lower expectation. The DIRECTION
matches amendment 13's sweep, which found optimal ahead on expected hits and on
bust risk at every pick count. The MARGIN is one pick and means nothing.

Stated on the panel in those terms, with the structural fact that explains it:
spread covers more bouts by construction; it does not land more.

# Addendum 57: what each slice of the 25 is worth, and card size (2026-10-13)

## The "minimum picks" number was declined, and what replaced it

Asked: show the fewest optimal/hedged picks it would have taken to produce the
same hit rate as 25.

**Measured first.** Where the hits actually fell inside the ranking:

| card | ranks of the hits | deepest |
|---|---|---|
| Allen vs. Duncan | 7, 17, 20 | 20 |
| UFC 332 | 4, 8, 9, 14, 16 | 16 |
| UFC 331 | 8, 14 | 14 |

Pooled: **4, 7, 8, 8, 9, 14, 14, 16, 17, 20** — three of ten at rank sixteen or
deeper, and the check arm carries one at 21. So the answer is "about twenty",
which is no saving.

**It would have been declined even had the number looked good.** It is hindsight
wearing the clothes of guidance: where a hit fell on a settled card says nothing
about where the next one falls, and a figure sitting beside the cells readout
would read as advice. It also degrades with evidence — as cards accumulate the
worst case drifts deeper and the number creeps toward 25 while never having said
anything. Same shape as the skew dial and the 60% floor: a parameter that looks
measured because a number came out of it.

**Built instead**: marginal expected hits by band of five, from the
probabilities rather than the outcomes.

| band | expected | share | landed |
|---|---|---|---|
| cells 1–5 | 2.12 | 35% | 1 |
| cells 6–10 | 1.31 | 22% | 4 |
| cells 11–15 | 1.03 | 17% | 2 |
| cells 16–20 | 0.87 | 14% | 3 |
| cells 21–25 | 0.74 | 12% | 0 |

**No elbow.** 35, 22, 17, 14, 12 — a smooth decline with no rank beyond which
cells stop contributing, and the last five still carry an eighth of the
expectation. That is the honest answer to "could I place fewer": yes, at a cost
readable from this table, which is the trade the picks box already makes.

The `landed` column is far too thin to read and is labelled as such. It is there
to accumulate: if the deep bands keep under-landing across ten cards, that is a
real finding about the tail of the ranking — and precisely the finding the
post-hoc minimum would have buried.

## Card size: the premise did not hold, and the question underneath it is real

Observed: the card with the most bouts also had the most finishes.

**The premise is not in the data.** All three graded cards carry ten bouts in
`history.json`. UFC 332 did not have more than the others, and its eight
finishes tie Allen vs. Duncan's eight on the same ten.

**And the count could not have carried information anyway.** Finishes scale with
bouts, so "more bouts, more finishes" is near-tautological. Only the per-bout
RATE can say anything — which is a real question with arguments both ways: a big
numbered card carries more ranked fighters, who may be harder to finish, while a
prelim-heavy card carries more mismatches.

**Not previously tracked. Added** to `card_shape()` in `baserates.py`, which
already groups by event with bouts/r1/fin — bucketed by card size rather than
fitted, since a slope through the available spread of sizes would claim more
precision than it has, and reported with its own n per bucket so a thin bucket
cannot read as a trend. The display states that the count is uninformative and
only the rate can move.

Note what is already known and is a DIFFERENT question: `overdispersion` is
**1.03**, so card-to-card variance is what independent bouts would give. There is
no "finish night" clustering to find. That says nothing about whether the rate
shifts with size, which is what the new table answers.

## The thing that turned up while checking

| card | bouts | finishes | rate |
|---|---|---|---|
| Allen vs. Duncan | 10 | 8 | 80% |
| UFC 332 | 10 | 8 | 80% |
| UFC 331 | 10 | 6 | 60% |
| **pooled** | **30** | **22** | **73%** |

Against a league finish rate of about **50%** (pooled divisions: ko .319 + sub
.177). Expected 14.9, observed 22, sd 2.74 — **z ≈ +2.6**.

That is past two standard deviations and it is the fourth measurement tonight
pointing the same way: finishes are arriving more often than the model expects.
It is also three cards, and these are the bouts that graded rather than every
bout scheduled, so it may be nothing but a hot run.

Registered with the rest: at ten graded cards, re-read the route split, the board
arms, the card-level counts and this rate together. If all four hold, the
correction belongs in the survival model's finish scaling.

## Addendum 51, amendment 16 (2026-10-13): the route switch — the fourth axis, built

Amendment 15 deferred a per-method exclusion "inside a cell" and registered it as
available if wanted. The unit asked for here is **the route** — a fighter and a
method across the whole bout — and it is the better one.

The route is what the model and the check both hold opinions in; it is what the
concurrence mark is computed on; and it is the way the thought actually arrives.
"I do not believe he submits anyone" is a statement about a man and a method, not
about round three. Switching it off cell by cell would take five clicks to say
one thing.

### The affordance is the method word itself

No new furniture. Clicking **SUB** or **KO/TKO** beside a name switches that
fighter's submissions or knockouts off in every round of that bout; clicking
anywhere else in the cell keeps the single-cell toggle it already had. The thing
you click is exactly the thing it turns off.

The inner control is tested first in the delegated handler, or it could never be
reached — the method word sits inside the cell that also listens.

### The risk named in amendment 15 is real, and is mitigated rather than denied

A cell can now be held off by its bout, its round, itself, or its route. Four
axes, and a reader who cannot tell which one is holding a cell has a form rather
than an instrument. Two mitigations:

- **every switched-off cell names its reason in its tooltip** — the round switch,
  the cell switch, or the route;
- **the status line enumerates all four**, naming the switched-off routes
  ("Buckley by KO, in every round of their bout"), with one control that clears
  everything together.

### A rendering case that had to be handled

A cell whose routes are individually off still has to draw, or the struck route
vanishes and there is nothing left to click to restore it — the same failure
amendment 15 fixed for whole cells, one level down. Such a cell stays live,
because its *other* route may still be running: on the live card, Buckley's
knockouts strike through in all five rounds while Malott's knockouts in the same
cells keep their picks.

Verified: switching off Buckley by KO removed its 3 picks, struck 5 cells,
redistributed to hold 25, and moved bust risk 15% → 16% — the same smooth cost
every exclusion carries.

# Addendum 58: a correct number that reads wrong, and a test for style imposition (2026-10-13)

## "55% finish but the pick says Jourdain by DEC 28%"

**Not wrong. Reconstructed at the reported shape** — 66/34 winner, decision-heavy
favorite — and the cells come out: finish 51.3%, decision 48.7%, largest finish
route 17%, largest single contract **Jourdain by DEC 33%**.

Four finish routes share the finish probability between them; a decision is
shared by only two. So on any fight near the line the biggest single CONTRACT is
routinely a decision even though the fight more often ends early. The two rows
answer different questions: `ends` is a two-way split of the whole fight, `pick`
is the biggest of five contracts.

**This was already explained — in the wrong place.** The identical note has sat
in `marketTabs` beside the gold row since that panel was built. The reader was in
the A–B grid, where ENDS and PICK are stacked with nothing between them.

**Fixed**: the grid now says it, inline, and only when the pick's family actually
contradicts the ends call. Worth recording as a class of defect: an explanation
written once, in the place the author happened to be working, does not cover the
other three places the same confusion arises.

## Does the fight follow ONE fighter, or the pair?

Asked: do finishes go to the fighter with the higher finish rate, and decisions
to the one with the higher decision rate — is there a pattern of outcomes
attaching to a man rather than to a matchup?

**Not previously testable; the tool assumes the answer.** `decision_curve`
averages the two career decision shares, and averaging is a modelling CHOICE that
has never been checked against the obvious competing hypothesis — that a finisher
drags a fight toward a finish harder than averaging implies, or that a
decision-heavy fighter imposes the cards.

**Built** as `style_imposition()` in `baserates.py`: three predictors of P(finish)
scored on the same bouts, so they are directly comparable.

| predictor | what it claims |
|---|---|
| the pair's average decision share | the fight is a blend — current treatment |
| the more finish-prone fighter alone | **the finisher imposes** |
| the more decision-prone fighter alone | **the grinder imposes** |

Scored by correlation and by the spread between extreme buckets. If either single
fighter separates further than the average, the fight follows one man and the
tool's blend is wrong. If neither does, averaging is right and the question is
closed — which is a result worth having either way.

Second output, the direct form of the question: among bouts that FINISHED, how
often the finish went to the more finish-prone fighter, **against how often he
simply won at all**. The gap between those two is the part that is about METHOD
rather than about being the better fighter — without that control, "the finisher
usually gets the finish" is mostly a restatement of "the better fighter usually
wins". A 20-point-gap subset is reported too, where the effect should be largest
if it exists.

Strict as-of throughout: every share is built from fights strictly before the
bout, the same discipline `decision_curve` uses.

**No result yet.** The corpus is not in this repo, so the table fills on the next
pipeline run and the panel says so rather than showing nothing. Registered now,
before the numbers exist, with the reading rule stated in advance: a single table
is not enough to move the model off averaging — if a single-fighter predictor
wins, it gets re-read on a later build before anything changes.

# Addendum 59: ape index — registered, with the reason it cannot be fitted yet (2026-10-13)

Proposed: height should inform how much a reach differential means. A fighter two
inches taller than an opponent with two inches more reach is not in the same
position as one the same height or shorter with that deficit.

**The proposal is sound and the variable is well defined.** It is the ape index —
reach minus height — differenced between corners.

## It survives the objection that killed height

`d_height` sits in `DROPPED` as "carried by d_reach", removed because the two
correlate above 0.85 and keeping both pushed the design matrix condition number
from ~10 to ~42. That is a collinearity decision, not a claim that height is
irrelevant.

**Ape index is the residual of reach on height**, so it is near-orthogonal to
both by construction and the collinearity that disqualified `d_height` does not
apply. This is a genuinely different variable, not height returning under
another name. The observation behind the request is correct: `d_reach` alone
cannot distinguish a tall fighter with long arms from a short one with longer.

## The finding that matters more than the proposal

**Reach is imputed from height for about 26% of fighters.** `loaders.py` fits
`reach = a + b * height` and fills the missing quarter from it.

For every one of those fighters the ape index is **exactly the regression line —
zero residual by construction.** A model handed this feature on the full corpus
would be partly fitting *was this fighter's reach imputed*, not how long his arms
are, and the fitted effect would be a measurement artifact wearing the shape of
anatomy.

The `reach_imputed` flag already exists, with a comment saying it is there "so
the effect of the imputation can be measured later". This is that later.

## Registered, not adopted

`ape_index_test()` added to `features.py`, restricted to bouts where **both**
corners carry a measured reach. Time-ordered split, no shuffling. WIN_FEATURES as
control, WIN_FEATURES + `d_ape` as treatment, held-out log loss, bootstrap
interval and P(better) — the same protocol that rejected the style features at
-0.0009, 95% CI [-0.0041, +0.0022], P(better) = 0.293.

**Decision rule, fixed before any number exists**: adopt only if the interval
excludes zero AND P(better) ≥ 0.95 AND it survives a re-run on a later corpus.
Anything short of that is recorded and the frozen fourteen are left alone.

The prior matters here and is stated up front: a reach effect in MMA is small to
begin with, and a residual on a small effect is smaller still. A result that
merely leans is exactly what noise looks like at this effect size. The function
also refuses rather than proceeding if fewer than 800 usable bouts survive the
measured-reach restriction, and returns the count so the restriction's cost is
visible instead of silent.

Not run: the corpus CSVs are not in this repo.

## What the site does today, unchanged

The check panel parses height and uses it only to impute reach when reach is
missing, then discards it — `delete out.height` — which is consistent with
`d_height` not being a model input. That stays as it is. Nothing on the page
changes until the test says something.

## Addendum 59, amendment 1 (2026-10-13): the span was got wrong, and the real hypothesis is an interaction

The clarification — "two inches shorter with one inch longer arms may cancel the
taller man's advantage; a way to measure the SEVERITY of the reach discrepancy" —
exposed an error in the addendum written an hour earlier.

### The error

Addendum 59 said the ape index "is the residual of reach on height, so it is
near-orthogonal to both by construction, and the collinearity that disqualified
d_height does not apply."

**That is wrong in the part that matters.**

```
d_ape = (ra - ha) - (rb - hb) = d_reach - d_height
```

so `span{d_reach, d_ape} == span{d_reach, d_height}` — rank 2 either way,
verified numerically. **Adding the ape index to a model that already carries
`d_reach` is the same model as adding `d_height` back**, reparameterised, with
identical predictions. It is not near-orthogonal either: r ≈ 0.6 against
`d_reach` on simulated anthropometry, not 0.

What the reparameterisation does buy is conditioning — 3.2 against 2.5 — which is
interpretability, not information. The claim that it escaped the collinearity
objection was the flattering reading, and it was not checked before it was
written.

### The hypothesis that is actually new

The proposal splits in two, and only one of them is a new degree of freedom:

| | claim | status |
|---|---|---|
| **H1, net length** | height offsets reach additively | **= restoring d_height**, rank 2 |
| **H2, severity** | the VALUE of a reach edge depends on height context | `d_reach × d_height`, **rank 3** |

H2 is the one the proposal describes, and the only one that can tell the tool
something `d_height` could not have.

H1 is still worth testing, for a reason unrelated to the proposal: **`d_height`
was dropped by a correlation rule (r > 0.85 with something kept), never by a
held-out comparison.** Whether it adds anything has never actually been measured.

### Rebuilt

`ape_index_test()` replaced by `length_test()`: three arms on identical rows —
WIN_FEATURES, + `d_ape` (H1), + `d_ape` and the centred interaction (H2). The
interaction is centred before multiplying, or it proxies the main effects.

Same restriction (both corners measured, not imputed), same protocol, same
decision rule, same prior against. The result now reports per arm, so "the net
length term did nothing but the interaction did" is a readable outcome rather
than one hidden inside a single number.

## Addendum 59, amendment 2 (2026-10-13): the test is probably underpowered, said before it runs

Asked whether backtesting shows a correlation. **It has not been run — the corpus
CSVs are not in this repo — and no number will be quoted that has not been
measured.** But the power can be worked out now, and it should be, because a test
that cannot resolve the effect it is looking for is worse than no test: it
returns "no effect" and that gets remembered as a finding.

The measured-reach restriction keeps about 0.74² ≈ **55% of bouts**. Against the
style-features test's held-out set of roughly 1,365 that leaves about **750**, and
the 95% interval widens from 0.0063 to about **0.0085** — so the smallest
improvement the test can distinguish from zero is roughly **0.0043 nats**.

For scale: the eight style features together moved held-out log loss by
**0.0009** and were rejected. A single reach interaction producing five times
that is not a plausible prior.

**Registered in advance, therefore**: a null result from `length_test()` means
*this test could not see an effect of the size plausibly present*, not *there is
no effect*. The distinction goes in the record now, before the number exists,
because it is exactly the distinction that gets lost afterwards.

# Addendum 60: size-adjusted round counts declined; the thin flag was the real gap (2026-10-13)

Proposed: where two fighters have very different numbers of recorded bouts, give
the thinner record a size-adjusted column in "Where their fights have ended", so
a small sample stops misleading the method and round picks.

**The instinct is right and the target is wrong**, and the reason is a result
already on the record.

## Shrinking rounds would be shrinking noise

A fighter's own ROUND history has split-half reliability **0.21, falling to 0.05
as the sample grows**. Whether he finishes at all runs **0.54 rising to 0.60**.

At reliability 0.05 the optimal weight on a fighter's own round distribution is
about **5%**. A "size-adjusted" column would therefore be about 95% league prior
— the league distribution, printed under a fighter's name, inviting exactly the
fighter-specific reading it cannot support.

That is the general hazard, worth stating plainly: **shrinkage makes a thin
record look trustworthy.** Where the underlying quantity replicates — the method
mix, reliability 0.54-0.60, already shrunk at k=5 and beating the base rate by
+0.044 — that is the entire point. Where it does not, shrinkage hides the
thinness without adding information, and the smoothness reads as confidence.

The panel is also labelled "the full record, plain counts · unweighted and
unshrunk — the evidence, not the read". Adding a modelled column to the one
surface that shows raw evidence would cost the thing it exists for.

## What the request actually needs was already there, one layer down

The board's round shape for a thin or unsplit bout is **pooled from the card's
other bouts at the same scheduled length**, not taken from the fighter. The
mechanism the proposal asks for already runs where the picks are made.

## The genuine gap, now closed

The finish board did not SAY when a pick rested on a thin record. The row carried
division, rounds, lean, check and "shape borrowed" — and not thinness, which is
the one of those a bettor most needs. Thinness was visible on the tile and on the
check chip, and absent from the surface where the bets are chosen.

Added: `thin NW` from the check's own minimum win count where a read exists, or
`thin record` from the model's flag. Two bouts on the live card carry it.

# Addendum 61: women's bouts yes, five-rounders no — and a base-rate gap (2026-10-13)

Two claims put to the corpus: that women's bouts and five-round fights both
finish less often than a typical three-round fight.

## Women's bouts — true, and the gap is large

| | finish rate | n |
|---|---|---|
| men, pooled | **51.7%** | 5,945 |
| women, pooled | **36.0%** | 910 |

**A 15.7-point gap, and the ranges do not overlap**: the lowest men's division
(Flyweight, 44.3%) sits above the highest women's (Bantamweight, 38.6%).
Women's Strawweight is the lowest cell in the sport at 33.8%.

**Already accounted for, on both sides.** The finish model carries `women` as an
explicit input (`FINISH_INPUTS`), and `sbBaseMix` has been division-aware since
addendum 50, so a women's bout is compared against its own division rather than
a pooled league.

## Five-round fights — false, and backwards

| scheduled | finish rate | ends before round 2 |
|---|---|---|
| three rounds | **45.6%** | 25.5% |
| five rounds | **57.0%** | 21.6% |

**Five-round fights finish MORE often, by 11.4 points.** Ten extra minutes
outweigh the fact that they start slower.

The intuition is not baseless, though — it is tracking a real effect in the
opposite direction. Five-rounders are **less likely to end early**: 21.6% before
round two against 25.5%, and still behind at round three (37.5% to 40.9%). They
only pass three-rounders by accumulating rounds four and five. Anyone betting
round-one or round-two finishes would correctly perceive five-rounders as the
worse bet, and then generalise it wrongly to the whole fight.

The model carries `five` as an explicit input alongside `women`, and the survival
model evaluates its hazard per minute to the scheduled length, so length is
handled structurally there.

## The gap the question exposed

`sbBaseMix` is division-aware and **not length-aware**. Three-rounders dominate
every division by volume, so a division rate is effectively a three-round rate —
and a five-round bout's check read was being compared against a base roughly
eleven points too low. Same class of fault as addendum 50's pooled-vs-division
error, one axis over.

**Fixed**: `divisions()` now emits `r3` and `r5` cells per division, and
`sbBaseMix` uses the bout's own scheduled length when that cell holds at least
60 bouts, falling back to the pooled division figure and naming which it used
(`Welter · 5R`).

### A trap caught before it ran

The first version split on `n_rounds`. In this corpus `n_rounds` is rounds
**FOUGHT** — the max round index in the per-round table — so it is 1 for every
first-round knockout. Splitting on it would have divided the data by whether the
fight finished and reported a finish rate near 100% for "three-round" bouts, in a
table whose whole purpose is finish rates.

Corrected to `sched_sec`, which comes from TIME FORMAT and is what
`projections.py` already uses for its `five` flag. Recorded because the wrong
version would have produced a dramatic, publishable-looking result that was
purely an artifact of the split.

## Addendum 51, amendment 17 (2026-10-13): clearest route — a sort, not an allocation

Proposed: bring "sure thing" bouts to the top — where one fighter submits and the
other knocks out, the method question has an answer, and that is a cleaner bet
than a bout with the same finish rate split evenly across four routes.

**Measured before building**, and it carries information the board did not have:

```
corr(top route share, how lopsided the winner is) = +0.06
corr(top route share, the bout's finish rate)     = -0.19
```

Near-independent of both columns already on the board, so it is not a
repackaging. And it reorders the card materially: **Buckley v Malott has the
highest finish probability at 59% and the lowest concentration at 37%** — five
rounds, both men carrying two routes — while **Boser v Diniz at 53% finish puts
56% of it in one route**. The likeliest finish is not the clearest bet, which is
exactly the claim behind the request.

### Measured at the route, not the cell

Cell-level concentration would mark every five-round bout as unclear for a purely
mechanical reason: the same probability spread over twenty boxes instead of
twelve. That is a property of the schedule, not the matchup. The route is where
the method question lives.

### It is a sort and a column, and touches nothing else

Verified: switching the sort leaves the picks identical — 25 cells, 1.533
expected, same cells in the same order. Row order and one column changed;
allocation did not.

That line is the reason this is safe where the skew dial was not. Picks stay
ranked by absolute probability because that is what maximises expected hits.

### The caveat is on the panel, because the sort invites the error

Under "clearest route" the top row on the live card is **Blanchfield v
Jasudavicius at 34% finish** — a bout the default floor would exclude. A 56%
route inside a 34% finish is **19% absolute**, well below cells further down the
board. Sorting by clarity and betting top-down would cost expected hits.

So the note says it in those words: the top row here is not the best bet, and the
sort means "where the method question has an answer", not "bet these first". A
control whose obvious misreading is more attractive than its correct one has to
carry the correction next to it.

# Addendum 62: the floor was still pooled — the fault's third and last home (2026-10-13)

Asked whether addendum 61's findings reached the board and the check. Traced all
three consumers rather than assumed:

| consumer | women | five rounds |
|---|---|---|
| the finish/survival model | ✓ `women` in FINISH_INPUTS | ✓ `five` in FINISH_INPUTS |
| the check's league column (`sbBaseMix`) | ✓ division-aware, addendum 50 | ✓ length-aware, addendum 61 |
| **the board's floor (`fbLean`)** | **✗ pooled** | **✗ pooled** |

`fbLean` was still comparing every bout against `market_bases.dec` — **one league
number, 49.6%** — and it is the worst place for that fault to survive, because
the floor does not merely label a row, it decides whether the bout reaches the
board at all.

## How wrong, concretely

The same 50% finish probability, before and after:

| | base | at 50% the floor now says | before |
|---|---|---|---|
| Women's Strawweight | 33.8% | **finish likely** — passes | no lean, excluded |
| Women's Flyweight | 36.6% | **finish likely** — passes | no lean, excluded |
| Middleweight | 55.5% | below its base | no lean |
| **Heavyweight** | **63.3%** | **distance likely** — excluded | no lean, admitted |

**Wrong in both directions at once, and systematically**: it admitted heavyweight
bouts that are quiet for heavyweights and excluded women's bouts that are busy
for their division. A 50% fight is a different object in the two divisions and
the board was treating them as the same.

**Fixed**: `fbLean` asks `sbBaseMix` for the bout's own base. The stops now mean
what they always claimed — points above THIS bout's base. `high` is untouched: an
absolute 60% is a stated preference, and a preference expressed in absolute terms
should not start moving with the division.

The floor explainer reported a single threshold; it now reports the range across
the card ("a bout needs 32–58% finish to appear") and says why there is a range.
One number there would have been the same lie the change removed.

## A defect the fix caused, and closed

With the bar set per division, a whole card can be quiet **for its own
composition** — and the live card is: every bout sits at or below its division's
base, which the pooled bar had been hiding by flattering the heavyweight and the
middleweight. Correct, and startling.

`finishBoard` returned `''` when no bout cleared the floor, so the board
**disappeared without a word**. Survivable while almost everything cleared a
pooled bar; not survivable now.

An empty board now renders its own explanation: the floor control, every bout
ranked by distance from its OWN base with that base printed, and a line saying a
card with nothing busy for its divisions is a real answer rather than a failure.
A tool that silently vanishes is worse than one that reports an empty result.

## Note on the figures

The five-round cells (`r3`/`r5` per division) arrive with the next pipeline run.
Until then `sbBaseMix` falls back to the pooled division figure, which is the
behaviour before this change for length and the corrected behaviour for division.

# Addendum 63: the finish probability had never been backtested (2026-10-13)

Asked whether there is a way to backtest what share of bouts over a given finish
probability actually finish.

**There was not, and the omission is the largest one found in this project.**
`track_record.json` carries held-out records for the winner, takedowns,
knockdowns and output ranges — and **nothing for the finish probability**, which
is the quantity the entire finish side of the tool rests on. Every "60% finish"
on the page was published with no evidence anywhere that 60% means 60%.

The data to check it was already present and unused: every graded bout carries a
`Go the distance` prop with the model's own number, so `1 - said` is its finish
probability and the outcome is scored beside it.

## What the graded cards say

23 bouts with a finish probability:

| the model said | bouts | avg said | finished |
|---|---|---|---|
| under 40% | 5 | 35% | 3/5 · 60% |
| 40–50% | 9 | 46% | 6/9 · 67% |
| 50–60% | 6 | 56% | 5/6 · 83% |
| 60% and up | 3 | 67% | 1/3 · 33% |
| **all** | **23** | **49%** | **15 · 65%** |

**+1.6 sd**, and two things are worth separating:

- **The ordering is right through the bulk** — 60%, 67%, 83% as the claim rises.
  The top band inverts, on three bouts, which is nothing.
- **The level is low.** 65% happened against 49% claimed.

**Brier 0.276 against 0.251 for always saying the league rate** — the flat
control is currently scoring BETTER. That is an unflattering number and it is
recorded as found. On this sample it is the level being low rather than the
ordering being wrong: a model that ranks correctly but sits sixteen points under
will lose to a constant when outcomes run hot.

At 23 bouts none of this is a finding. It is the fifth measurement in two days
pointing the same way, and the first one aimed directly at the model's own finish
number rather than at something downstream of it.

## Both halves built

**The panel**, in the graded zone, from the data already in `history.json` — it
works now and accumulates with every card.

**The proper backtest**, added to `reliability.build_record` as a `finish` entry:
`fit_finish_formula` trained strictly before the cut, scored strictly after, the
same split discipline the winner entry uses, reported as bands with a Brier
against the league-rate control. It arrives in `track_record.json` on the next
pipeline run, on the full corpus rather than 23 bouts.

Bands rather than a correlation, deliberately: the question is calibration, and a
single r would hide exactly the failure these cards hint at — correct ordering,
systematically low level.

Wrapped so a failure there can never break the build; an error is recorded in the
entry instead.

# Addendum 64: a pasted sportsbook line, and the suite that passed a broken page (2026-10-14)

## What a moneyline can and cannot do, said before building

Asked for, to make the finish board "as precisely adjusted as possible". **A
moneyline cannot do that.** It is P(this man wins) and carries no information
about whether a fight finishes, so it cannot touch the level error the graded
cards keep pointing at. What it does buy:

- **the check-only bouts.** On the live card 7 of 7 modelled bouts already carry
  a feed price — but the **6 no-read bouts carry none**. Those are exactly the
  bouts the model declined, so the check is the only read on them and there has
  never been anything to measure it against. Verified on the real paste: 5 bouts
  matched to the card, **2 of them with no feed price at all**.
- **route redistribution.** A winner probability moves finish probability between
  the corners — which man's routes are the big ones — not whether the fight ends
  early. Useful for route picks, useless for the finish rate.
- CLV accumulation toward the registered threshold.

The line that WOULD calibrate the finish side is the book's goes-the-distance
market. Said on the panel, with the invitation to paste that instead.

**It never overwrites `p_market`.** The feed price has its own as-of discipline;
a pasted one is the operator's at an unknown moment. Stored and shown separately,
or this is the editable-ledger problem again.

### Two guards in the parser

**A vig gate.** A correct two-way book sums to about 1.03–1.10 implied; the real
paste came in at a consistent 5.9–6.1% across all six bouts. Anything outside
1.00–1.18 means the two prices do not belong to each other — the commonest
symptom of a paste whose shape drifted — and the row is dropped rather than
de-vigged into a confident wrong number.

**Label lines are not fighters.** "Sat 5:10pm ET" and "More wagers" wear the same
markdown shape as a name. Without excluding them the parser pairs a time with the
next bout's first fighter and reads two prices belonging to neither.

Matching is on the pair of surnames, order-insensitive: the book and the card
disagree about first names often enough ("Timothy"/"Timmy",
"Marc-Andre"/"Marc Andre") that a full-string join drops real rows.

## The suite passed a page that would not run

While building this I shipped — into the working copy — an `index.html` whose
script had a duplicated `function ckIO(){` and therefore **did not parse at all**.
The page would have rendered completely blank.

**The suite reported ALL CHECKS PASSED.** Every Python test passed because none
of them look at the JavaScript. `test_site_features` greps for the presence of
thirty strings, and a broken file satisfies that perfectly — the strings are all
still there, in a script that never runs. **Presence is not the same as parses,
and nothing was checking the second.**

Added `test_site_script_balances`: a bracket/brace/paren scanner that understands
strings, template literals including nested `${}`, line and block comments, and
regex literals. Pure Python rather than shelling out to node, because the nightly
job has no node dependency and adding one would trade a silent failure for a
fragile build.

**Verified both ways**: re-introducing the duplicate makes it report `1 unclosed
— first is '{' at line 3627`, and removing it returns PASS.

### A false positive caught before it shipped

The first version read `/^\*?\s*\[([^\]]+)\]/` as division and then counted the
character class's brackets, failing on a file node parses happily. A checker that
cries wolf is worse than no checker — it trains you to ignore it. Regex-literal
handling added, with the usual heuristic for telling a literal from a division.

### And a false alarm of my own, recorded

Mid-debug I concluded the PREVIOUSLY shipped `index.html` was also broken and was
about to report that. It was not. My reconstruction of the earlier file — strip
this session's edits and re-check — cut from the inserted comment to the *first*
`function ckIO(){`, which left the duplicate in place. The reconstruction was the
thing that was broken.

Recorded because the lesson is specific: when a bisect says the fault predates
your change, verify the bisect before believing it. I came close to raising a
false alarm about already-delivered work.

## Addendum 64, amendment 1 (2026-10-14): fresher, yes — but not simply better

Reported: FanDuel updates more often than the tool's market line, so the paste is
the reliable one.

**The recency half is right, and measurable.** On the live payload
`generated_utc` is 2026-10-11T23:48Z against a card on the 17th — the feed price
is **2.6 days old** while a paste is from the moment it was made. Three days out
from a card that is a real gap, and the panel now states it instead of leaving
the reader to assume the feed is current.

**But the feed is not a stale FanDuel.** `market_source` is the-odds-api at
**15 to 20 books a bout** (17 on average here). FanDuel is one book. A single
book's line is not strictly sharper than a seventeen-book consensus — it is a
different object with its own lean.

So neither dominates:

| | paste | feed |
|---|---|---|
| recency | **now** | 2.6 days |
| breadth | 1 book | **17 books** |

And a gap between them cannot be attributed from the number alone. The live card
has exactly one: **Anheliger v Koslow, feed 51% against book 42%.** At 2.6 days
that is as likely to be line movement as error, and the panel says so in those
words rather than picking a winner.

**What changed**: the panel reports the feed's age and book count, names every
bout where the two disagree by 5+ points with both figures, and marks any price
pasted after the card as not-a-forecast — the same post-hoc rule the check reads
already carry, since a price pasted late is contaminated exactly as a late
UFC.com read is.

**What deliberately did not change**: the paste does not replace `p_market` or
`edge` anywhere. Those are pipeline data with their own as-of stamp, and letting
a fresher number silently overwrite a broader one — in the fields that feed the
graded record — is the editable-ledger problem in its most tempting form yet,
because this time the replacement would genuinely be more current.

## Addendum 64, amendment 2 (2026-10-14): a parser that only worked on the sample it was shown

Reported: the paste produced "No bouts read from that paste", and the only way to
get even that message was to click off the box.

**Two defects, and the first is the embarrassing one.**

### The parser required markdown

It matched `[Name](url)`, because that is the shape the sample arrived in. The
same card copied off the FanDuel **page** is bare lines, so it read nothing.

A parser that works on the one example it was given is a demo, not a parser —
and the failure mode was silent, which made it worse. The sample should have been
treated as one of several shapes from the start, not as the specification.

**Fixed**: a name is a name whether or not it arrived wrapped in a link. Verified
on both forms of the same card — markdown 6 bouts, plain text 4 of 4.

Label lines are still excluded by shape (days, times, "More wagers", prices,
section headers), and the vig gate still catches any pairing that slips through.
Rejected rows are now NAMED in the feedback rather than silently dropped, so a
bout that vanishes on a bad pairing says so.

### The only feedback was an alert, on blur

No signal while the paste was still fixable; an interruption once you had moved
on. Exactly the wrong order.

**Fixed**: a **Read it** button, and a live count that updates as you paste —
"4 bouts found: Chovancek/You, Croden/Chandler, Mahjoub/Faglier and 1 more". A
paste that reads nothing says so inline, in place, with no dialog. Verified: junk
input now reports "no bouts found — expected two names, then the two prices —
nothing stored", and no alert is raised.

# Addendum 65: the market decides WHO, the check keeps HOW (2026-10-15)

Asked whether the pasted book line should decide which fighter's finish routes
get prioritised — the observation being that a corner the book now favours can
be carrying fewer routes on the board than his opponent.

**Yes, and it is the one use of a moneyline this project can defend on measured
grounds.**

## The warrant

On the 12 graded bouts carrying a price, matched: the market went **10/12 at
Brier 0.180** against the check's **7/12 at 0.257**. The market is a materially
better winner estimate and it is not close.

But a moneyline knows **nothing** about method. So the division of labour writes
itself: the market decides WHO wins, the check keeps HOW he wins.

## The arithmetic is exact, not a fudge

The stored cells already factor the right way:

```
a_ko = P(A wins) x P(KO | A wins)
```

so dividing by the check's own `p_a` recovers each corner's conditional method
mix, and multiplying by the book's `q` re-aims it. **Verified on the export: all
34 reads have five cells summing to 1.000**, so the recovery is exact rather than
approximate.

Guarded at both ends — a corner the check puts at 2% or less has no stable
conditional mix to recover, since dividing by it turns rounding into a confident
number, so those bouts are left alone.

## What it does to the live card

| bout | check had | book has | effect |
|---|---|---|---|
| **Anheliger v Koslow** | 23.7% | **42.2%** | his KO route .097 → **.172**, Koslow's sub .379 → .287 |
| Croden v Chandler | 83.6% | 70.5% | .384 → .324 |
| Buckley v Malott | 52.7% | 47.6% | .331 → .299 |

The Anheliger row is the case the question was about: the check has him a heavy
underdog, the book has the fight near even, and the board was pointing its routes
at the wrong man. Bouts with no pasted price are untouched.

**Off by default**, because the pasted price is the operator's at an unknown
moment and this changes what the board picks. The row label names the shift
wherever it exceeds 3 points, so a re-aimed bout never looks like an unaimed one.

## A correction to addendum 64

Addendum 64 said a moneyline "carries no information about whether the fight
finishes" and "cannot touch the finish rate". **Too strong.**

It cannot correct a LEVEL bias — that claim stands. But re-aiming moves P(finish)
mechanically whenever the two corners finish at different rates when they win,
and the export has bouts at **.386 against .680** on finish-given-win. On the
live card the re-aim moved Anheliger/Koslow from .646 to .635 and Croden from
.578 to .565.

The narrower claim is the true one, and the broad version was the easier thing to
say.

## On the two bouts named

From the pasted prices: **Mahjoub −120, Faglier −106**, which de-vigs to Mahjoub
**51.5%** — so by those numbers Mahjoub is the narrow favourite, not Faglier. The
line may well have moved since Monday; the panel reports the paste's age for
exactly this reason. **Leblanc +420, Galanti −650** does make Galanti an **81.8%**
favourite, which is the kind of gap that moves a board hard.

# Addendum 66: Tapology as a second history source (2026-10-15)

The history box read ESPN tables only. Added Tapology, producing the identical
row shape, with both parsers run and the one that reads more rows winning —
cheaper than sniffing for a signature and not foolable by a stray marker.

## Why it is worth having rather than redundant

Tapology carries two things no existing source does:

- **regional bouts.** A Contender Series graduate's record is mostly Combate
  Global and EXF. ESPN is thin there and UFC.com has nothing at all.
- **the promotion on every row**, which is exactly what `espnTier()` needs.
  Verified: "Contender Series 2026" resolves to weight **1.0**, "Combate Global"
  to **0.5**, with no extra wiring.

## Four things in the format that bite, all handled

**Cancelled bouts** carry a `C` result and a "Cancelled Bout" detail. They never
happened; two sit in the middle of the sample and would otherwise have entered a
record.

**Amateur bouts** sit under an "amateur bouts" heading with identical shape.
Everything after it is dropped — the Wikipedia parser already excludes amateur,
and addendum 53 registered that amateur belongs at weight **zero**, not 0.5: it
is evidence about a different qualifying tier, not weaker evidence about this
one.

**Non-MMA bouts** appear in the same list. A Karate Combat fight shows a bare
discipline line ("Karate") where the running records normally sit — that line is
the signal, and the row is skipped rather than folded into an MMA method mix.

**The date** is `2026Aug 18` — year, month, day, no separators — which no
general date parser reads.

## Validated against the source's own arithmetic

Full sample: **17 pro MMA bouts, 2 cancelled skipped, 1 amateur dropped, 1
non-MMA skipped**, giving **15-2**. Tapology's own running-record line shows
14-2 going into the most recent fight, so 15-2 after — an independent check that
the parse neither invented nor lost a bout, which counting rows alone cannot
give.

Derived mix: 6 KO, 6 SUB, 3 DEC from 15 wins; tier-weighted shares .438 / .375 /
.188, the weighting pulling the two Contender Series results above the regional
ones as intended.

## The new suite check earned its place immediately

Integrating this, I made the **same mistake as yesterday**: the inserted block
ended with the anchor line and the anchor was concatenated again, producing
`function espnDerive(h){function espnDerive(h){` and a script that did not parse.

Yesterday that cost a long debugging detour and a false alarm about
already-shipped work. Today `site script parses` reported `1 unclosed — first is
'{' at line 4715` on the first run, and it was fixed in one edit.

The habit worth recording, since twice is a pattern: **when an inserted block
already ends with the anchor, replace the anchor with the block — do not append
the anchor again.**

## Addendum 66, amendment 1 (2026-10-15): the same mistake, twenty-four hours apart

Reported: the Tapology record did not process.

**I built the parser against the markdown sample again.** It required
`[Name](url)` because that is how the record arrived in conversation. Copied off
the Tapology **page** it is bare lines, and the parser read **zero rows** —
verified by stripping the links from the same sample and re-running.

This is the identical failure the FanDuel parser had **one day earlier**, from
the identical cause, and I recorded the lesson then without applying it to the
next parser I wrote. Writing it down was not the same as learning it.

**The rule, now stated as a rule rather than an observation:** a pasted-text
parser treats its sample as ONE shape, never as the specification, and is tested
against the stripped version before it ships.

### Rebuilt by shape rather than by position

Fields are found by what they look like — a date is `YYYYMon DD`, a detail
carries a middot, a method is one of five words — so an optional line appearing
or vanishing cannot shift everything after it. The old version walked forward
from the result marker and counted lines, which is why a single missing record
line could derail a whole block.

Verified: markdown and plain text now return **identical** results — 17 rows,
15-2, 2 cancelled skipped, 1 non-MMA skipped, 1 amateur dropped, tier-weighted
mix .438 / .375.

### And the silence, which is the part that made it cost a round

A zero-row parse produced **nothing at all** — no rows, no message, no change on
screen. Third time this exact shape of failure has appeared in three days.

A live count now sits under the history box: "17 bouts from Tapology · 15-2 · 2
cancelled skipped · 1 non-MMA skipped · 1 dropped", and on junk input "no bouts
read — ESPN table or Tapology record, linked or plain". It updates as you paste,
while the text is still in front of you.

**The general rule this project keeps relearning: any box that accepts a paste
reports what it read, immediately, in place.** Silence is the worst possible
answer because it is indistinguishable from success.

## Addendum 66, amendment 2 (2026-10-15): stop guessing, make the parser say what it saw

Still failing after amendment 1, and at that point **three rounds had been spent
guessing at a paste's shape from the outside** — each one a theory about what the
text looked like, tested against a reconstruction rather than the real thing.

The parser knows what it saw. Saying so turns the next failure into a one-line
answer instead of another round.

### Tolerances widened, measured per shape

| paste shape | before | after |
|---|---|---|
| markdown links | 17 rows | 17 rows |
| plain text | 17 rows | 17 rows |
| bullet instead of middot | 0 rows | **17 rows** |
| dates as "Aug 18, 2026" / "18 Aug 2026" / ISO | 0 rows | read |
| one long line, no breaks | 0 rows | still 0, and **says so** |

Four date shapes, four separator characters. The one-line case is genuinely hard
— the result marker, the method and the name all glue into a single token — and
a half-working splitter for it would be worse than an honest refusal.

### The failure message now diagnoses

```
no bouts read — ESPN table or Tapology record, linked or plain.
Saw 1 line, 0 W/L markers, 0 readable dates, 82 links.
That looks like one long line — the copy lost its line breaks.
```

and for a record whose dates do not match:

```
Saw 161 lines, 22 W/L markers, 0 readable dates, 61 links.
No date matched; Tapology writes them as 2026Aug 18.
```

Lines, result markers, readable dates and link count, with the single most
likely cause named. **Three failure modes now identify themselves**, where
before all three produced the same six words.

### The rule, stated for the third time and now implemented rather than noted

A paste box reports what it read. When it reads nothing it reports **what it
saw** — not a restatement of what it wanted. The first version of this message
said what the parser expected, which is useless to someone holding text that
does not match it: they already know it did not work, and the thing they cannot
see is why.

## Addendum 66, amendment 3 (2026-10-15): the date cell spans two lines

The diagnostic earned itself back on its first use. Reported verbatim:

> Saw **202 lines, 22 W/L markers, 0 readable dates**.

Twenty-two markers means the blocks were being found correctly. Zero dates with
two hundred lines — against a reconstruction of the same record at 161 — says the
real paste carries about forty MORE lines than expected and that the extra ones
are where the date should be.

**Tapology renders the date cell across two lines**: the year above the month
and day. Markdown collapses it to `2026Aug 18`; a copy off the page gives `2026`
then `Aug 18`, and no single-line pattern can match either half.

Reconstructed with the date split and the links stripped: **203 lines, 21
markers** against the reported 202 and 22 — the same document.

**Fixed**: the date scan tries a single line, then the pair ending there, in
both orders, and records how many lines the date consumed so the event line
above it is still found. The opponent scan skips both halves.

Verified across every shape now known, all returning identically:

| paste shape | rows | record | mix |
|---|---|---|---|
| markdown links | 17 | 15-2 | .438 / .375 / .188 |
| plain text, one-line dates | 17 | 15-2 | .438 / .375 / .188 |
| **plain text, split dates** | **17** | **15-2** | .438 / .375 / .188 |
| bullet separator + split dates | 17 | 15-2 | .438 / .375 / .188 |

### What this cost, and what fixed it

Three rounds of guessing from the outside, then one round once the parser
reported what it saw. The diagnostic did not merely point at the problem — the
line COUNT is what identified it, because 202 against an expected 161 is a fact
about the document that no amount of reasoning about plausible formats would
have produced.

The general form, worth keeping: **when a parser fails, report the shape of what
it received, not the shape it wanted.** The first is evidence; the second is
only a restatement of the failure.

---

## Addendum 67 (2026-10-16): time to finish, and why it is not an average fight time

Asked for: a read on the check side for *average fight time* from the ESPN /
Tapology history, "this way we can see which rounds they will likely perform
within."

**The statistic as named is not estimable from this data, and would be wrong if
it were.** Two separate reasons, and they compound:

1. **A decision is a censored observation.** A fight that reached the final
   horn did not last fifteen minutes because that is how long the man takes to
   finish; it lasted fifteen minutes because the clock ran out. The true
   time-to-finish for that bout is *greater than* the scheduled length, not
   equal to it. Averaging decisions in at their full length pulls every
   estimate toward the horn and makes a finisher with four decisions look
   slower than a finisher with none, when the difference is in how OFTEN he
   finishes, not how FAST.
2. **Tapology does not supply a time for a decision at all.** So even the wrong
   version is unavailable without imputing the scheduled length, which is
   exactly the imputation step 1 rules out.

Mixing the two questions is the specific failure: *how fast he finishes* and
*how often he finishes at all* are different quantities, and the second is
already reported directly above this panel as the finish share.

**What was built instead.** Time to finish **among finishes only**, with the
decisions counted out loud and excluded. Median leads, mean follows, because
one late stoppage drags a mean a long way on records this short. Round-one
share is shown as a raw count (`7/13`), not a percentage, for the same reason.
Unweighted and unshrunk, matching the "evidence, not the read" section it sits
under — tier weighting applies to what feeds the model, and nothing here does.

**Measured on the record that prompted it** (Perez, read through the Tapology
parser from addendum 66): 17 rows, 13 finishes, 4 decisions, and **13 of 13
finishes carry a usable round and time**. So the coverage is complete on the
finish side and zero on the decision side — which is the asymmetry described
above, arriving in the data exactly as predicted. Median 3:30, mean 5:45, 7 of
13 inside round one. The gap between median and mean is the whole argument for
leading with the median.

Gate: fewer than three timed finishes prints the count and says *too few to
read* rather than a number. Three is low, and is deliberately low — this panel
makes no forecast, so the cost of a thin figure is a thin figure, not a bad
bet.

**The standing null applies, and is restated on screen.** A fighter's own round
history does not replicate: split-half reliability **0.21 falling to 0.05** as
the sample grows, against **0.54 rising to 0.60** for whether he finishes at
all. This panel is that same unreliable quantity in continuous form. It is
therefore **recorded as evidence, not promoted to a read**:

- it does **not** feed the finish board;
- it does **not** feed the check's round read, which stays built from the
  pair's finish rate times the league's round shape at that finish rate;
- it does **not** feed the model;
- nothing downstream consumes `fin_times`.

If it is ever to be promoted, the test is pre-registered here: it must beat the
league-round-shape read on held-out bouts by a margin that survives the same
split-half check that killed the round history in the first place. Until then
the panel answers *what the record contains*, and the question it was asked —
which rounds a man will perform within on Saturday — is answered above it by
the league curve, not by this.

**Harness note.** The render was verified twice over, because the first probe
lied. `document.body.innerText` reported the panel absent while a direct call
to `sbMethodBlock` returned 17,256 characters containing it, and a screenshot
showed it on screen. The probe, not the panel, was broken: it injected the
sandbox markup into a detached container that the Read handler never
re-rendered. Recorded because the failure mode is attractive — an absent string
reads as a missing feature, and the cheap conclusion is to go editing working
code. **When a probe says a feature is missing, confirm the probe can see a
feature that is definitely there before believing it.** This is the same lesson
as the bisect in addendum 60, arriving from a different direction.

---

## Addendum 68: power density. REGISTERED 2026-10-17, before any fitting.

## Why this one, after zero-for-ten

The finish model carries `kd` (both corners' knockdowns per 15 min) and `pace`
(both corners' adjusted strikes landed per minute) as separate linear inputs. A
linear model in those two **cannot express their ratio.** Knockdowns per strike
landed is therefore the one combination the current specification is
structurally unable to reach, rather than a rearrangement of something it
already has. Every other rate in the model is per-minute, which confounds how
much a man throws with what happens when he lands.

Prior: LOW. Ten formulas tested, zero supported (addendum 12), and a gradient
booster representing every monotone transform and interaction simultaneously
lost to plain logistic regression. This is one specified test, not a sweep.

## Formula, fixed now

Per fighter, in the existing `_share` idiom from `state.py`:

    kd_per_ss = (KD + k * p0) / (SS_landed + k),   k = 60 significant strikes

`k = 60` is the same shrinkage constant the existing style shares use, taken
unchanged rather than chosen. `p0` is the league rate of knockdowns per
significant strike landed, computed **on the training block only**.

Pair feature, matching how `kd`, `pace`, `ctrl` and `sub` already enter
`finish_row` (sum of both corners, because the finish is a property of the
pair, not of one man):

    pdens = kd_per_ss_a + kd_per_ss_b

Added as a single new input to `FINISH_INPUTS`. One formula. No variants.

## Universe, split, outcome

- Universe: identical to `fit_finish_formula` — every bout from 2012-01-01
  with at least 2 prior bouts for each corner.
- Outcome: `y = 1` if the fight did NOT end in a decision.
- Split: chronological, train on the first 80%, test on the last 20%
  (`TEST_FRACTION = 0.20`, the project's standing split). No shuffling.

## Decision rule, fixed now

Primary metric: **held-out Brier score.**

Supported only if BOTH hold:
1. The Brier improvement's 95% bootstrap CI (2,000 fight-level resamples)
   excludes zero, and
2. P(better) >= 0.95.

**Both arms refit their own intercept on train**, so a pure level shift cannot
count as support. This is the load-bearing clause. The standing open finding is
that the model UNDER-CALLS finishes; a level error is an intercept correction,
not evidence for a new feature. If the only movement is in the base rate, that
is recorded as an intercept finding and **power density is rejected.**

Predicted sign: **POSITIVE.** A pair who score knockdowns per strike landed —
power rather than volume — should finish more often than their per-minute rates
alone imply. A negative coefficient falsifies the hypothesis regardless of fit.

Secondary, DESCRIPTIVE ONLY, not criteria: held-out log loss; mean predicted
versus actual finish rate on test; the fitted coefficient and its CI; whether
adding `pdens` changes the sign or magnitude of `kd` or `pace`.


## Addendum 68: RESULT (2026-10-17). NOT SUPPORTED, and the sign is wrong.

Corpus: 4,252 bouts from 2012-01-01 with 2+ prior fights per corner. Train
3,402 (to 2024-03-23), test 850 (2024-03-23 -> 2026-09-12). Finish rate .4921
train, .4706 test. League prior p0 = 0.00538 knockdowns per significant strike
landed, from train-block fights only.

**Primary, as registered — held-out Brier:**

| arm | Brier |
|---|---|
| baseline (8 inputs) | 0.23737 |
| + pdens | 0.23703 |
| gain | **+0.00034**, 95% CI **[-0.00006, +0.00073]**, P(better) = 0.953 |

Both criteria were required. P(better) cleared 0.95; **the CI does not exclude
zero.** Not supported.

**And the coefficient came back NEGATIVE: -0.1038 per standard deviation,
against a registered prediction of positive.** That falsifies the hypothesis on
its own terms, independent of the fit criteria. Registering the sign in advance
is what makes this unambiguous: a +0.00034 Brier gain with a backwards
coefficient is not a near miss, it is the wrong model fitting slightly better
by absorbing variance it was not supposed to touch.

### Why it failed, which is the part worth keeping

**`pdens` is not a new axis. It is `kd` wearing a denominator.**

- corr(pdens, kd) = **+0.933**; corr(pdens, pace) = -0.066
- Regressing pdens on (kd, pace): R^2 = **0.938**. Only **6.2% of its variance
  is new information.**

The reason is in the raw counts, and it is not subtle:

| term | mean | sd |
|---|---|---|
| knockdown numerator (both corners) | 4.97 | 4.58 |
| strike denominator (both corners) | 726.6 | 516.5 |

The numerator nearly doubles across pairs relative to its own mean. Knockdowns
are rare, so almost all the variation in "knockdowns per strike landed" is
variation in *knockdowns*, and the denominator mostly rescales it. **The
premise was that per-minute rates confound volume with effect. They do — but
dividing by volume does not separate them when the numerator carries ~94% of
the variance.**

What the model actually did with it is visible in the coefficient shift:
`kd` moved **+0.196 -> +0.298** while `pdens` took **-0.104**. The two split a
single signal, with pdens acting as a suppressor on kd rather than contributing
an axis. That is the collinear pair the `DROPPED` list exists to prevent, and
it is why the condition number matters: see addendum 1, where the composites
cut it from ~42 to ~10 precisely by *replacing* their ingredients instead of
sitting beside them.

**Eleven formulas tested, zero supported.** The booster result still stands
behind all of it: a model representing every monotone transform and interaction
simultaneously lost to plain logistic regression. The honest reading is that
the inputs are close to exhausted at this sample size, and further gains come
from better inputs, not better arithmetic on the inputs already present.

### EXPLORATORY, found after the registered test closed

**Not a criterion, not confirmatory, registered here only so the forward ledger
can test it honestly.**

The standing open finding — five independent slices suggesting the model
under-calls finishes — **does not reproduce on the held-out block as a global
bias.** Baseline predicted 0.4683 against 0.4706 actual over 850 bouts, a gap
of **+0.0022**. No probability bucket is more than 0.8 se off:

| predicted | n | predicted | actual | gap |
|---|---|---|---|---|
| 0.00-0.35 | 112 | 0.315 | 0.304 | -0.012 (-0.3 se) |
| 0.35-0.45 | 279 | 0.406 | 0.387 | -0.019 (-0.7 se) |
| 0.45-0.55 | 270 | 0.495 | 0.519 | +0.024 (+0.8 se) |
| 0.55-0.65 | 151 | 0.593 | 0.623 | +0.030 (+0.8 se) |
| 0.65-1.00 |  38 | 0.693 | 0.632 | -0.061 (-0.8 se) |

**But it is concentrated in time, not in the probability range:**

| year | n | predicted | actual | gap |
|---|---|---|---|---|
| 2024 | 275 | 0.471 | 0.440 | **-0.031** (-1.0 se) |
| 2025 | 339 | 0.467 | 0.463 | -0.004 (-0.1 se) |
| 2026 | 236 | 0.468 | **0.517** | **+0.049** (+1.5 se) |

2026 is the window every one of the five accumulating slices came from. +1.5 se
on 236 bouts is not significant alone and must not be reported as a finding.
But it reframes the open question: **if the finish rate is genuinely running
above the model's base in 2026, that is DRIFT, not misspecification** — the
same shape as the 12.3-point move in the UFC decision rate already recorded —
and the correction is an intercept or a recency weight, not a new feature. It
is emphatically not a reason to go looking for more formulas; addendum 68 is
what happens when you do.

**This changes the registered re-read at ten graded cards.** The question to
ask of that data is no longer "does the finish model need another input" but
"is the 2026 base rate above the training base rate, and by how much." Those
have different corrections and only one of them is supported by anything.

---

## Addendum 69 (2026-10-19): the conditional round split, and two pieces of furniture

### The matched-denominator problem, showing up as a reading problem

The drawer's "where it ends" bar is **unconditional** — round one as a share of
every way the fight can end. The graded card asks a **conditional** question:
given that it finished, was it round one or later. Same subject, different
denominators, and the conditional form was reachable on the upcoming card only
as a clause at the end of a paragraph.

So a bout read "30% round one" before the card and "30% of its finishes in
round one" after it, and the reader had to work out that those are not the same
30%. That is the denominator discipline this project applies to every
side-by-side comparison, failing on the one axis nobody checked: **the same
quantity stated two different ways in two different places, days apart.**

**Built:** a second track under the first, `if it finishes, how early`, round
one against after round one, model and records, with the league's conditional
rate as the tick. It is the first bar divided by its own finish share — stated
on screen, because a derived number that looks measured is the next version of
this same mistake.

**Both segments are gold-family and the blue never shows.** That is the entire
visual grammar of the change: on this page blue means distance, and there is no
distance inside a bar that is conditioned on finishing. The model's row had to
be re-pointed at the dim GREY rather than the dim gold, or it rendered half
grey and half gold and read as two sources in one bar — while the note
underneath promised no blue in it. A caption that contradicts the picture above
it is the defect this panel has had to fix twice before.

**Nothing new is computed and nothing is claimed.** The recorded null still
governs: a fighter's own round history does not replicate, split-half 0.21
falling to 0.05 against 0.54 rising to 0.60 for whether he finishes at all.
This is a second view of a number already on the page, placed so that the
before and the after can be read against each other without arithmetic.

### Two pieces of furniture

**The clash explainer is now a hover.** Six lines sat open under the ab-grid on
every bout where `ends` and `pick` named different families, explaining that
the two rows answer different questions. It is read once and then it is
furniture. The row still *says* "not a contradiction" — that has to be visible
the moment the clash is seen — and the reasoning moved to the title attribute.
Plain text there, with no markup: a title renders tags literally.

**The page has an icon.** A corner stool cut out of the site's gold, inlined as
a base64 data URI in the `<link rel="icon">` rather than shipped as a second
file. The deployment is one file uploaded through a web UI, and **a favicon
that lives in a second file is a favicon that goes missing the first time only
`index.html` is uploaded.** The gold field is doing the work rather than the
mark: candidates drawn as a dark tile with a gold figure were tested in a
simulated tab strip and dissolved into the browser chrome, since the tab bar is
already dark. Inverting it — gold field, dark cut-out — is what made it legible
at 16px. To change it, replace the payload; nothing else references it.

---

## Addendum 70 (2026-10-19): marking model-check agreement without ranking it

A strip down the left edge of each upcoming-card tile: **gold** where the model
and the check both call a finish, **steel** where both call the distance,
**split gold-over-steel** where they differ, **nothing** where there is no
second opinion.

### Why not the border, which is what was asked for

`.tile.is-hot` already owns `border-color`, for a market edge of five points or
more. A bout that is both hot and agreed would then have one border and two
things to say, and no way for the reader to know which meaning was being shown.
The strip is a separate channel, and it reads vertically down a column of
tiles, which is the scanning motion this is actually for.

The palette was constrained harder than it looks. The stylesheet already
records why the hot border is neutral bone: *"Orange read as the red corner,
and gold already means the market everywhere else, so the tile highlight is
neutral."* Gold therefore means the MARKET on a tile and a FINISH in the
drawer, and the strip deliberately imports the drawer's meaning — which is
defensible only because the strip is a drawer-side quantity. The steel is the
drawer's muted blue and expressly **not** `--bluesoft`, because on a tile
`--bluesoft` is the blue CORNER and a strip in a corner colour would read as a
fighter rather than as an outcome.

### What this must not become, which is the whole design constraint

**Whether model-check agreement predicts accuracy is an OPEN registered
question.** It is H1 of the check-against-model test: 40 length disagreements
required, roughly eight clean cards, with a stopping rule and an explicit
instruction that nothing is reported before that. It is nowhere near resolved.

And the market work already records the adjacent trap: **conditioning on
disagreement with a better forecaster selects the bouts where the worse one is
most likely wrong.** So "they agree, therefore this is the safer bout" is not
merely unearned — it may run backwards.

Two consequences, both binding:

1. **All three states are drawn at equal weight.** Agreement is not brightened,
   the split is not dimmed or greyed. A reader absorbs a visual ordering whether
   or not the caption disclaims it, so there is no ordering to absorb.
2. **The split is both colours, not a third one.** A third hue would name a
   third category — "uncertain" — which is a claim about the bout. Two colours
   stacked say only that the two readers differ, which is a fact about the
   readers. It also keeps the colour budget at two on a page that has none
   spare.

### Two silences, both drawn as nothing

- **No check pasted** — there is no second reader, so there is no agreement to
  report.
- **Model publishes no method split** — there is nothing for the check to agree
  WITH.

Both get no strip rather than a "no agreement" mark. Marking either as a
disagreement would report an absent opinion as a conflicting one, which is the
same error as grading a silent model as having predicted a decision — a defect
this project has already had to fix once.

**A thin check still counts.** Thinness is flagged in its own places and is a
statement about the record's size, not about what the check read. Suppressing
the strip there would quietly redefine it as "agreement among checks I judged
solid enough", which is a different and unstated quantity.

### The counter

The card header carries a key chip with the three swatches and a running
`N agree · M differ`. The differ tally **is** the disagreement set H1 scores, so
the chip doubles as a progress read toward the registered 40 — which is the
only thing the page is allowed to say about those bouts, and is strictly a
count, not a verdict. It is omitted entirely when no bout carries a strip
rather than displayed as `0 agree · 0 differ`, which would look like a
measurement.

---

## Addendum 69, amendment 1 (2026-10-19): the mark is the help button

The "?" circle beside the wordmark is replaced by the stool icon built in
addendum 69. The explainer already opened on hover — `.tipwrap:hover .tip` was
there all along — so nothing about the interaction changed; only the glyph did.

The reason it is worth recording: **the symbol that identifies the page in a
row of tabs is now the symbol you reach for to ask what the page is.** One mark
doing both jobs rather than a logo sitting next to a piece of punctuation.

The cost is that a logo does not normally invite a hover, so the affordance had
to be rebuilt by other means: the help cursor, a resting state at 72% opacity
that lifts to full on hover, and a gold ring that appears with it. Without
those the icon reads as decoration and the explainer becomes unreachable —
which would be a worse outcome than the "?" it replaced. The `aria-label`
stays and matters more than before, because the button now contains no text at
all.

---

## Addendum 71: breadth of edge. REGISTERED 2026-10-19, before any fitting.

## The question, and the trap in it

Asked: of the per-fighter log-odds contributions shown on each bout, were any
indicative of outcome — and did fighters with more of them leaning their way
win more often on average?

**The literal question has a trivially affirmative answer that means nothing.**
The win model is a logistic regression with `fit_intercept=False` on
standardised features, so the model's logit IS the sum of the displayed
contributions. A fighter with more features leaning his way therefore has a
higher model probability almost by construction, and "he wins more often"
restates the model's calibration rather than discovering anything. Reported on
its own it would be a finding-shaped non-finding.

The question that is NOT already answered is whether the SHAPE of the edge
carries information the TOTAL does not. Two fighters can hold the same summed
log-odds, one by leading narrowly on twelve features and the other by leading
hugely on three. If breadth matters, the model is misspecified, because a
correctly specified logistic model's logit is a sufficient statistic and the
count of favourable terms adds nothing.

Prior: LOW, for exactly that reason, and lower still given eleven formulas
tested and zero supported.

## Definitions, fixed now

For each bout, using the model's own standardisation:

    contribution_j = coef_j * z_j          (14 features, WIN_FEATURES)
    logit          = sum_j contribution_j  (exactly, since fit_intercept=False)
    breadth        = #{j : contribution_j > 0} - #{j : contribution_j < 0}

`breadth` runs -14..+14 and is antisymmetric under swapping corners, like every
other feature in this model.

## Universe, split, fitting

- Universe: the standard training universe — both corners with 2+ prior bouts,
  decisive results only, from 2012-01-01.
- One orientation per fight (`orient == 0`), so a fight contributes one row and
  the mirrored copy is not counted twice.
- Split: chronological, first 80% train / last 20% test (`TEST_FRACTION`).
- The win model is **refit on the training block only** —
  `LogisticRegression(max_iter=4000, C=0.5, fit_intercept=False)` on
  `StandardScaler`-ed `WIN_FEATURES`, matching `train.py`. The shipped frozen
  model is not used, because it has seen the test block.

## H1, primary: does breadth add to the total?

- Baseline: logistic on `[logit]` alone.
- Treatment: logistic on `[logit, breadth]`.
- Both refit their own intercept on train, so a level shift cannot count.
- Primary metric: **held-out Brier.**
- **Supported only if** the 95% bootstrap CI (2,000 fight-level resamples)
  excludes zero AND P(better) >= 0.95.
- Predicted sign: **POSITIVE**. A negative coefficient falsifies the
  hypothesis regardless of fit.

## H2, secondary: is any single contribution indicative beyond the model?

For each of the 14 features, add `contribution_j` to `[logit]` and score
held-out Brier. Since the logit already contains that contribution, a gain
means the model under-weights that feature out of sample.

- **Benjamini-Hochberg at FDR 0.10 across all 14.**
- Supported individually only if it survives correction AND improves held-out
  Brier.

## Descriptive, NOT a test

Raw win rate by `breadth` bucket, unconditional. This is the question as
literally asked and it is expected to show a strong monotone trend. It is
reported **beside** H1 precisely so the two can be told apart: the trend is the
model working, and H1 is the only thing that would be news.


## Addendum 71: RESULT (2026-10-19). H1 null. H2 null — after correcting a hole in my own decision rule.

4,167 bouts, train 3,334 (to 2024-03-30), test 833 (to 2026-09-12). Win model
refit on train only. `breadth` runs -10..+12, sd 3.81, and correlates **+0.696**
with the logit — as expected, since it is a coarsened version of it.

### Descriptive: the question as literally asked

| breadth | n | won | model said | gap |
|---|---|---|---|---|
| -14..-6 | 78 | 0.282 | 0.385 | -0.103 (-2.0 se) |
| -5..-3 | 100 | 0.470 | 0.478 | -0.008 (-0.2 se) |
| -2..0 | 339 | 0.487 | 0.549 | -0.063 (-2.3 se) |
| +1..+2 | 137 | 0.650 | 0.638 | +0.012 (+0.3 se) |
| +3..+5 | 93 | 0.645 | 0.694 | -0.049 (-1.0 se) |
| +6..+14 | 86 | 0.802 | 0.756 | +0.046 (+1.1 se) |

**Yes, emphatically** — 28% up to 80%. And the model column tracks it the whole
way, 38.5% to 75.6%, which is the point: **the trend is the model, not a
discovery.** The residual gaps are non-monotone in breadth (negative at the
bottom, negative in the middle, positive at the top), so they are not a breadth
effect; they are consistent with the model running slightly over-confident on
this test block, which is a drift question and is already open elsewhere.

### H1: breadth adds nothing to the total

| arm | held-out Brier |
|---|---|
| `[logit]` | 0.21602 |
| `[logit, breadth]` | 0.21599 |
| gain | **+0.00003**, 95% CI **[-0.00023, +0.00028]**, P(better) **0.598** |

**NOT SUPPORTED**, and not close — P(better) barely beats a coin. The
coefficient is +0.0066, the predicted direction, and indistinguishable from
zero.

**The shape of an edge carries nothing the size of it does not.** Twelve narrow
advantages and three large ones are worth the same if they sum the same. This
is what a correctly specified logistic model is supposed to do — the logit is a
sufficient statistic — so the null is the model passing a test it should pass,
and a pass here would have been evidence of misspecification.

### H2, and the methodological correction that is the real content here

By the letter of the rule I registered, **two of fourteen passed**:
`d_log_layoff` (p = .000) and `d_age` (p = .003), both under BH.

**Both are artifacts of a hole in that rule, and I am recording them as null.**

The gains:

| feature | Brier gain |
|---|---|
| d_log_layoff | **+5.5e-07** |
| d_age | **+4.3e-06** |
| d_elo | +1.1e-05 |
| d_str_acc | +2.1e-05 |

Against a baseline Brier of **0.216**. For scale: **flipping a single bout of
833 moves Brier by 1.2e-03** — roughly *two thousand times* the supposedly
significant `d_log_layoff` effect. These gains are three orders of magnitude
below the resolution of one fight.

The mechanism is specific and worth knowing. **A bootstrap p-value on a
difference tests the CONSISTENCY of its sign, not its magnitude.** A gain that
is microscopic but reliably positive across resamples drives p toward zero
exactly as a large one does. And here there is a reason for the reliable sign:
the win model is fitted with `C=0.5`, so re-admitting a feature's own
contribution lets the second-stage fit recover a sliver of that shrinkage. The
direction is systematic for every feature; the size is nothing.

**My registration said "improves held-out Brier" and set no minimum effect
size.** A gain of 5e-07 improves held-out Brier. The rule was satisfied and the
conclusion was still wrong, which makes this my error and not a finding.

**Amendment, binding on every future Brier test in this file:** a result must
clear a pre-specified **minimum effect of one tenth of a single flipped bout**,
i.e. `0.1 / n_test` in Brier units — 1.2e-04 on a test block of this size — in
addition to its CI and P(better) conditions. Applied here, **H2 is zero of
fourteen**, and H1's +3e-05 also sits below the floor, which it would have
failed on anyway.

Noted for the record: addendum 68's registration carried a sign prediction,
which is what caught power density despite its P(better) of 0.953. This one
carried no effect-size floor, and that is what let two nulls through. **Both
guards are needed; each catches what the other misses.**

---

## Addendum 72: does a finish rate mean the same thing at 8 fights as at 30?
## REGISTERED 2026-10-19, before any fitting.

## What is already settled, and what is not

**Settled (addendum 46).** Recency weighting of the finish rate is worse than
flat career, monotonically, with no interior optimum: half-life 8 fights
+0.00139 log loss, last-5-only +0.00620, last-3-only +0.01279, against a
career-over-base-rate gain of 0.0337. A TREND term adds nothing on top. So
"discount his old fights" is rejected, and the gradient points at *use every
fight*. The mechanism recorded there is variance, not bias: a method outcome is
one Bernoulli draw per fight, and halving the sample to chase a trend costs more
in noise than any drift it recovers.

**Not settled, and the actual question here.** Addendum 46 discounted old
fights uniformly. It did not ask whether the career rate carries a *different
meaning* depending on how long the career is — which is the comparison problem:
a 30-fight veteran and an 8-fight prospect both reading 50%, who finishes the
next man? Shrinkage already handles the difference in RELIABILITY (k=4 pulls the
short record toward the league). This asks whether there is also a difference in
BIAS.

Prior: LOW for a decay effect, given 46. The descriptive arc, however, is simply
unmeasured and is worth having on the record either way.

## Universe and outcome

- One row per fighter per fight (both corners), from 2012-01-01, requiring 2+
  prior bouts for that fighter.
- Outcome `y = 1` if **this fighter finished his opponent in this bout** — he
  won and the method was not a decision. Scored per fighter, not per bout.
- Predictors from his pre-fight snapshot only: `finish_rate` (shrunk, k=4, as
  the site shows it), `log1p(n_prior)`, `age`.
- Chronological split, first 80% train / last 20% test.

## H1, primary: the interaction

- Baseline: `[finish_rate, log1p(n_prior)]`
- Treatment: baseline + `finish_rate x log1p(n_prior)`
- Primary metric: **held-out Brier.**
- **Supported only if all three hold:** 95% bootstrap CI (2,000 resamples)
  excludes zero; P(better) >= 0.95; and the gain clears the **addendum 71
  effect-size floor of 0.1 / n_test** in Brier units.
- **Predicted sign: NEGATIVE.** The hypothesis under test is that a long record
  dilutes — that a given finish rate built over 30 fights converts to fewer
  finishes now than the same rate built over 8, because the long record averages
  in an earlier and more finishing-prone phase. A positive interaction
  falsifies it.

## H2, secondary: age on top

- Baseline as above; treatment adds `age`. Same three conditions.
- **Predicted sign: NEGATIVE.**

## Descriptive, NOT tests

1. Finish rate by **age** bucket and by **career fight number** bucket, at the
   population level. This is the "at what point does it decline" question in its
   plainest form.
2. **Chronological split-half against random split-half, on the SAME fighters.**
   For every fighter with 8+ recorded bouts, correlate his first-half finish
   rate with his second-half, then correlate a random half with its complement.
   Same men, same sample sizes, only the split rule differs — so **any gap
   between the two correlations IS the within-career decay**, with the sampling
   noise matched out. The recorded random split-half for "does he finish at all"
   is 0.54 rising to 0.60; a chronological figure materially below that is
   decay, and one at parity is a career rate that holds.


## Addendum 72: RESULT (2026-10-19). The decline is by AGE, not by record size.

10,439 fighter-fights from 2012, train 8,351 (to 2024-02-17), test 2,088.
Effect-size floor 4.79e-05 (addendum 71).

### H1: a long record does NOT dilute. NOT SUPPORTED.

| arm | held-out Brier |
|---|---|
| `[finish_rate, log n]` | 0.17411 |
| + `finish_rate x log n` | 0.17414 |
| gain | **-0.00003**, CI [-0.00021, +0.00014], P(better) **0.328** |

Coefficient **+0.1066**, against a registered prediction of negative. The
premise behind the question — that a thirty-fight record averages in an older,
more finishing-prone phase and so overstates the man today — **is rejected, and
the point estimate leans the other way.** A 50% finish rate built over thirty
fights means what a 50% rate built over eight means. The difference between
them is precision, not bias, and shrinkage (k=4) already handles precision.

### Descriptive: where the decline actually lives

**By age** — a smooth, monotone slide with no breakpoint:

| age | n | finishes | their avg career rate |
|---|---|---|---|
| under 26 | 799 | **0.314** ±.016 | 0.472 |
| 26-29 | 2,045 | 0.282 ±.010 | 0.446 |
| 29-32 | 3,055 | 0.250 ±.008 | 0.423 |
| 32-35 | 2,515 | 0.222 ±.008 | 0.406 |
| 35+ | 2,025 | **0.200** ±.009 | 0.392 |

**By career fight number** — essentially flat until about fifteen:

| fight # | n | finishes |
|---|---|---|
| 2-4 | 2,697 | 0.248 ±.008 |
| 5-8 | 2,331 | 0.250 ±.009 |
| 9-14 | 2,074 | 0.240 ±.009 |
| 15-22 | 1,046 | 0.219 ±.013 |
| 23+ | 363 | 0.226 ±.022 |

**Mileage does not dull a finisher; years do.** Eleven points across the age
range against roughly two or three across the fight-count range, and the
fight-count figures are flat within noise through the first fourteen bouts.
**There is no "point at which" to name** — the age curve is a continuous slide,
so any threshold would be invented rather than found.

### Descriptive: the ordering survives, the level does not

Matched comparison on the same 788 fighters with 8+ recorded bouts, same half
sizes, only the split rule differing:

| split | r |
|---|---|
| RANDOM half vs half | +0.249 |
| CHRONOLOGICAL first half vs second | **+0.261** |
| gap (= within-career decay) | **-0.012** |

**No decay in rank.** Who finishes more than whom is as predictable across time
as it is at random — if anything marginally more so. But the levels move a long
way: mean finish rate **0.371 in the first half, 0.230 in the second**, down
14.2 points.

So the two halves of the picture are: everyone slides down together, and the
order they stand in does not change. A fighter who out-finished his peers at 27
out-finishes them at 35; both are finishing less.

**Caveat that no statistic here removes.** That 14-point level drop is
confounded with opponent quality. The corpus is UFC-only, so a fighter's later
bouts are against better opposition almost by construction, and some of the
drop is the division rising to meet him rather than him declining. The rank
correlation is immune to this — it asks about ordering, not level — which is
why the ordering result is the stronger of the two. The level figure should be
read as an upper bound on decline, not an estimate of it.

**Also not comparable to the recorded 0.54.** That figure is the split-half
reliability of the shrunk, pair-level finish read. This is raw, per-fighter,
half-career, roughly four bouts per half. The matched random/chronological pair
above is the valid comparison; the 0.54 is a different measurement and is not
a benchmark for it.

### H2: age adds beyond the career rate. SUPPORTED.

| arm | Brier | |
|---|---|---|
| `[finish_rate, log n]` | 0.17411 | |
| + `age` | 0.17306 | gain **+0.00105**, CI [+0.00016, +0.00201], P **0.989** |

Coefficient **-0.1766**, the predicted sign. Clears the effect floor by more
than twentyfold. All three conditions met.

Which raised the only question that could change the product, and it needed its
own registration rather than an extrapolation from here.


---

## Addendum 73: age LEVEL in the production finish model.
## REGISTERED 2026-10-19, before fitting. Follow-up to addendum 72 H2.

72's H2 showed age predicts whether a fighter finishes his opponent BEYOND his
career finish rate and experience. That was against a two-input baseline. It
does NOT establish that age adds to the production finish model, whose eight
inputs (kd, ctrl, pace, agegap, sub, five, wt, women) may already proxy it.

Note what the production model does and does not carry: `agegap` is
|age_a - age_b|, the DIFFERENCE. There is no age LEVEL term. Two 36-year-olds
and two 26-year-olds have identical agegap and, 72 suggests, different finish
probabilities.

Formula, fixed now: `agelvl = (age_a + age_b) / 2`, the pair's mean age, matching
how kd / ctrl / pace / sub already combine the two corners.

- Universe and split: identical to `fit_finish_formula` - bouts from
  2012-01-01, 2+ priors per corner, outcome = not a decision. Chronological
  80/20.
- Baseline: the eight FINISH_INPUTS. Treatment: those plus `agelvl`.
- Primary: held-out Brier. Supported only if ALL THREE hold - 95% bootstrap CI
  (2,000) excludes zero; P(better) >= 0.95; gain >= 0.1/n_test (addendum 71).
- Predicted sign: NEGATIVE. Older pairs finish less.
- Secondary, descriptive: whether agegap's coefficient moves when the level is
  admitted, which would say the gap term has been absorbing the level.


## Addendum 73: RESULT (2026-10-19). NOT SUPPORTED, and this is why 72's H2 was not enough.

4,252 bouts, train 3,402, test 850, floor 1.18e-04. `agelvl` correlates only
+0.103 with `agegap`, so it is very nearly a new axis.

| arm | held-out Brier |
|---|---|
| the eight FINISH_INPUTS | 0.23737 |
| + `agelvl` | 0.23737 |
| gain | **+0.00000**, CI [-0.00051, +0.00047], P(better) **0.510** |

Coefficient -0.0309 — the predicted direction, and nothing. `agegap` barely
moves when the level is admitted (+0.0302 -> +0.0330), so the gap term was not
quietly carrying the level either.

**Age adds nothing the production model does not already hold.** Knockdown rate,
control share and striking pace evidently carry whatever age was standing in
for in 72's thin baseline — which is the expected relationship between a
demographic variable and the performance measures it acts through.

**The methodological point is the one to keep.** 72's H2 passed every condition:
CI clear of zero, P = 0.989, effect twenty times the floor, sign as predicted.
It was a real relationship. It was also **not an improvement to anything**,
because the baseline it beat was a two-input stand-in rather than the model that
would have used it. A supported result against a weak baseline is a statement
about the baseline.

So the rule, now explicit: **a finding is only actionable when the baseline it
beat is the thing it would replace.** Extrapolating 72's H2 into "add age to the
finish model" would have shipped a null as a feature, and the only reason it did
not is that the follow-up was registered and run separately rather than assumed.

Twelve formulas and additions tested now. One supported against a toy baseline,
zero against the model in production.

---

## Addendum 74 (2026-10-20): calibration of the combined finish read, and where it actually crosses half

Descriptive, not a registered test — it measures an existing published quantity
rather than proposing a new one. No split is needed: `walk()` builds each
corner's rate from PRIOR fights only, so every bout is an honest out-of-sample
observation of its own number.

2,681 bouts from 2012, both corners with 4+ priors, overall finish rate
**0.494**. Each corner's finish rate rebuilt at the check's **k=5** rather than
the model's k=4.

### The question as asked: does above-50% combined deliver above half?

| | n | finished |
|---|---|---|
| combined average >= 0.50 | 590 | **0.627** ±.020 — **+6.4 se above half** |
| combined average < 0.50 | 2,091 | 0.457 ±.011 — -4.0 se |

**Yes, and by a wide margin.**

### But the average under-states across the ENTIRE range

| combined avg | n | claimed | actual | gap |
|---|---|---|---|---|
| 0.00-0.30 | 211 | 0.269 | 0.341 | **+0.072** |
| 0.30-0.38 | 665 | 0.344 | 0.391 | **+0.047** |
| 0.38-0.44 | 660 | 0.410 | 0.505 | **+0.095** |
| 0.44-0.50 | 555 | 0.470 | 0.523 | **+0.053** |
| 0.50-0.56 | 398 | 0.527 | 0.611 | **+0.084** |
| 0.56-0.64 | 160 | 0.588 | 0.675 | **+0.087** |

**Six buckets, six positive gaps, mean about +0.07.** This is a LEVEL error, not
a slope error — the ordering is fine and every bucket is shifted by roughly the
same amount. It is the same shape as the accumulating under-call finding, now on
2,681 bouts instead of slices of fifteen to twenty-three, and it is the
strongest corroboration that finding has.

### Which means the crossing point is NOT 0.50

By twentiles of the combined average, the actual finish rate passes half at
roughly **0.37-0.40**, not at 0.50:

| combined avg | n | finished |
|---|---|---|
| 0.346-0.359 | 135 | 0.363 |
| **0.372-0.386** | 132 | **0.523** |
| 0.398-0.409 | 136 | 0.544 |
| 0.420-0.433 | 137 | 0.533 |
| 0.448-0.462 | 133 | 0.489 |
| 0.476-0.491 | 134 | 0.567 |
| 0.505-0.524 | 134 | 0.642 |
| 0.576-0.742 | 135 | 0.659 |

**The exact crossing point is NOT identified and must not be used as a cut.**
The band from 0.37 to 0.50 is flat and noisy — 0.523, 0.544, 0.533, 0.489,
0.537, 0.567, 0.522 — and a threshold chosen by looking at which twentile first
clears 0.500 is selected on the same data it would be scored against. That is
precisely the post-hoc selection already rejected for the minimum-picks idea.
**Any operational cut must be registered forward and scored on later cards.**

### The union form is worse, and in the other direction

| union 1-(1-a)(1-b) | n | claimed | actual | gap |
|---|---|---|---|---|
| 0.50-0.60 | 546 | 0.558 | 0.357 | **-0.201** |
| 0.60-0.68 | 708 | 0.642 | 0.510 | -0.132 |
| 0.68-0.74 | 518 | 0.710 | 0.517 | **-0.192** |
| 0.74-0.80 | 474 | 0.768 | 0.576 | **-0.192** |
| 0.80-1.01 | 269 | 0.834 | 0.651 | **-0.184** |

Treating the two corners as independent over-states by 13 to 20 points
everywhere. The reason is that they are not independent: a finisher meets a
durable man and does not get his career rate. The truth sits between an average
that reads 7 points low and a union that reads 18 points high, and **neither
form is the right combination rule.**

**Spearman is identical for both: +0.188 and +0.188.** The two forms rank bouts
the same way, so the choice between them is purely about level and not at all
about ordering. That also caps what any recalibration can buy: it can fix the
level, and it cannot improve the ranking, which is where a betting edge would
have to come from.

### What this is NOT

The drawer does not display this quantity. `sbMethodRead` combines the two
corners **weighted by who wins**, over method shares from the pasted record —
which includes non-UFC bouts at half weight — and shrinks toward the division
base. This is the corpus-side analogue built from UFC fights only and a simple
average. **The structure here (level low, ordering sound, union far worse)
should carry; the exact +0.07 should not be read as the drawer's error**, and
no correction should be applied to the shipped read on the strength of this
table alone.

---

## Addendum 75 (2026-10-21): the bracket/count-off finish board, tested and rejected

Proposed: allocate a finish-board pick by comparing the two corners' RAW COUNTS
of a method in a round — fighter A has 3 round-one KOs, fighter B has 2, so the
R1-KO cell goes to A.

Rule fixed before running: legitimate only if the count-leader takes the finish
meaningfully more than half the time AND beats selection by plain career finish
rate.

2,681 bouts from 2012, both corners 4+ priors, snapshot-before-update so every
row uses prior fights only. The statistic is the clean one: **conditional on the
bout actually ending that way, was it the selected man?** Chance is 0.500.

### Result

| selector | n | leader got it | vs coin flip |
|---|---|---|---|
| **more prior R1 KOs — the proposal** | 314 | **0.497** ±.028 | **-0.1 se** |
| higher career finish RATE | 406 | **0.576** ±.025 | **+3.1 se** |
| more prior R1 finishes, counts | 502 | 0.514 ±.022 | +0.6 se |
| higher career finish RATE | 591 | **0.587** ±.020 | **+4.3 se** |

**The count-off is exactly a coin flip.** Not weak — indistinguishable from
chance, on 314 bouts that genuinely ended in a round-one knockout.

### Why it fails, which is the part worth keeping

The count is substantially a measure of CAREER LENGTH, not of finishing:

- when a man leads on R1-KO count he has more career fights **64.1%** of the time
- his mean career fights **13.1** against his opponent's **9.9**
- his mean career finish rate 0.417 against 0.346

So the count-leader IS the better finisher on average — the signal is in there —
and **the count form destroys it by mixing it with experience.** A thirty-fight
veteran out-counts an eight-fight prospect on raw totals while finishing less
often per fight. Rate 0.576, count 0.497: the contamination cancels the signal
almost exactly. This is the same error addendum 72 identified from the other
direction, where record LENGTH was shown not to dilute the RATE — the rate is
the quantity that carries, and any form that lets record size in corrupts it.

### And the rate form adds nothing over what is already used

| selector | n | leader got it |
|---|---|---|
| higher R1-KO RATE | 365 | 0.567 ±.026 |
| higher career finish rate | 406 | **0.576** ±.025 |
| higher R1-FINISH RATE | 580 | 0.571 ±.021 |
| higher career finish rate | 591 | **0.587** ±.020 |

Round-specific rates lose to the plain career finish rate on both comparisons.
Not by much, and inside noise — but there is **no direction in which the
round-specific version is better**, which is the recorded null arriving exactly
where it was predicted to: split-half 0.21 falling to 0.05 for a fighter's own
round shape, against 0.54 rising to 0.60 for whether he finishes at all. Knowing
*which round* a man's past finishes landed in tells you nothing beyond knowing
*that* he finishes.

### Two further practical objections

**It would be silent on a third of matchups.** 31.9% of fighter-rows have EQUAL
R1-KO counts, so the bracket has no opinion there and needs a tiebreak — which
would end up being the finish rate, i.e. the thing that works, reached by the
long way round.

**It discards the opponent entirely.** The board's current lean pairs one man's
finishing against the other man's way of being beaten. A count-off between two
career totals cannot see who is across from him, which is the single largest
thing the finish board knows.

**Verdict: not built.** The idea's working part — that the more dangerous
finisher should get the cell — is already what the board does, through the
quantity that replicates.

---

## Addendum 76 (2026-10-25): a third card view — bouts with a check

The card filter was a boolean, `ONLY_GAPS`, with two buttons. It is now a
three-state mode, `FMODE`, adding **"With a check (N)"** beside "All bouts" and
"Only disagreements".

**Why a mode and not a second boolean.** Two independent flags give four
states, two of which — "disagreements AND checked", and "neither" — nobody
asked for, and both of which would still need a label and a count. One mode,
three mutually exclusive views, one button lit at a time.

**The predicate is deliberately not `st.on`.** That flag means *show this check
beside the model on the card*, which is a display choice made after the work is
done. A read entered and then switched off is still a bout being worked on, and
gating the filter on it would hide precisely the bout the user went looking
for. The test is instead whether any of the four paste fields hold anything, so
a half-entered check — one corner done, the other not — still appears. Those
are the ones most likely to be hunted for.

**It spans both lists.** A bout the model declined can carry a check, and that
is the one place a check has nothing to be measured against — so it is the one
place it is most worth finding again. The count covers modeled bouts and
no-read bouts together, and the no-read entries survive this filter where they
are dropped by the disagreement filter. Verified: a check with `on:false` is
included, a no-read bout with a check is included, and an SBOX entry with no
pasted content is correctly excluded from both the view and the count.

The hint line beside the buttons swaps with the mode rather than stating the
disagreement threshold under a view that has nothing to do with it.

---

## Addendum 77 (2026-10-27): a base-rate floor on the method table

### The gap

The graded props panel has always reported a control — "right on 30 of 40
props" set beside "the base rate alone got 27" — so that a read cannot take
credit for following the base rate. **The four method rows of "how the fight
ends" had no such column.** They reported check against model and nothing else.

That makes the rows unreadable. "The check got 56% on finish type" says nothing
without "always naming the commonest outcome gets X%", and a read that leans
toward the common outcome will beat the model while contributing nothing at
all.

This surfaced from a live reading of the panel: the check led the model on all
four rows (+1, +3, +5, +2 bouts) while losing the winner row 7/19 to 11/19. The
four rows are not four results — the full call contains the finish type which
contains the length, scored on overlapping bouts, so one method lean wins all
four mechanically. And **the full call can be won without naming a fighter**:
`check_right = top === actual` over five cells of which one is `decision`. A
read that leans to the cards collects full calls while never picking a man,
which is the same hedging visible in its winner Brier — 0.304 against the
model's 0.302, level, across a 21-point hit-rate gap.

Under the most favourable exact McNemar consistent with the totals — every
discordant pair breaking the leader's way — the best row reaches p = 0.062 and
the rest are 0.25 to 1.00. Nothing is significant, and the registered
40-disagreement bar still governs. But the missing control is a defect
independent of the sample size, and it is fixed here.

### The floors, each matched to its own bout

| row | the floor |
|---|---|
| ends early or goes the distance | the prop's own per-bout published base, so division-specific by construction |
| finish type | the commonest family in that bout's division — in practice almost always the decision |
| full call | the largest of the five cells under base rates alone, finish mass split evenly between corners because a base rate has no opinion on who wins |
| round one, or past it | the league's CONDITIONAL round-one share, .517 on three rounds and .376 on five — the same figure the drawer's "if it finishes, how early" tick uses |
| exact round named | always round one, the largest single bucket either way |

Every figure summed over the **same array** as the two columns beside it. A
control on a different bout set is not a control.

### The floor is not a third reader, and the display enforces it

- The column is the quietest on the table, `--dim`, and never takes the gold.
- A figure at or below the floor is **struck through** — not reddened, because
  red means a miss on this page and this is not a miss; it is a number that
  turns out not to mean anything.
- **`ckbest` is suppressed when the leader is itself at or below the floor.**
  This was caught in review: the first build marked the check gold for leading
  the model on the full call while striking it through for sitting under the
  base, which is two contradictory verdicts in one cell. Crowning the better of
  two reads that both failed is precisely the reading this column exists to
  prevent, so when neither clears the bar, neither is marked.

### The hedging diagnostic

On the full-call row, a hover: *"check named the decision cell on N of M, the
model on K; it was actually a decision J times."* One tooltip, no new panel —
the same move as the clash explainer in addendum 69. It tests the hedging
account directly, and if the check's decision count approaches M the four-row
lead is one behaviour rather than four findings.

### What it can and cannot settle

Three outcomes, all informative. Check clears the floor and the model does not:
real, and it would be reported. Check tracks the floor: the lead is hedging and
the four rows collapse to one. Both lose to the floor: the finding is about the
model, and is a different finding worth having.

It does not improve the sample. Eighteen to twenty-six bouts stays small and
the registered bar is unchanged. **This column changes which question the table
asks, not how much power there is to answer it.**

Not computable here: `CKR` lives in the browser's localStorage, so the figures
fill in on the user's machine. The table was verified against synthesised
pre-card reads covering every row, including the strike-through and
suppressed-crown paths.

---

## Addendum 77, amendment 1 (2026-10-27): the floor was wrong on binary claims

The column shipped hours earlier reported **39%** as the floor for "ends early
or goes the distance" — a TWO-WAY claim. A coin scores 50%. The base-following
rule had simply been wrong-footed: on these 18 bouts it called the
division-leaning side and lost 11 of them, which is itself a reading of the
sample rather than a floor.

Crediting a read with beating 39% on a binary claim is crediting it with
beating something worse than guessing. **The floor is now the best UNINFORMED
strategy available: the higher of the base-rate rule and blind chance** — 50%
on a two-way claim, 1/3 on the finish type, 1/5 on the five-cell full call,
1/rounds on the exact round. The cell prints whichever one is governing, so a
floor reading "50% chance" says out loud that the base rule lost to a coin
there.

Caught by reading the live figures, not by a test. A control that can itself be
wrong-footed is not a control, and the binary case is exactly where that
happens.

## Addendum 78 (2026-10-27): first real reading — the floor indicts the MODEL

The graded record, pre-card reads only, against the corrected floor:

| claim | n | model | check | floor |
|---|---|---|---|---|
| ends early or goes the distance | 18 | 78% 14/18 | **83% 15/18** | 50% chance |
| finish type | 18 | **39% 7/18** | **56% 10/18** | 39% 7/18 |
| full call — fighter and method | 26 | **27% 7/26** | **46% 12/26** | 27% 7/26 |
| round one, or past it | 11 | **36% 4/11** | **55% 6/11** | 82% 9/11 |
| exact round named | 11 | **64% 7/11** | n/a | 64% 7/11 |

**The model is at or below the floor on four of the five rows**, and on three of
them its count is EXACTLY the floor's: 7/18, 7/26, 7/11. The check clears the
floor on three.

This was built to test whether the check's lead was hedging. It answered a
different question. The claim under examination was "is the check better than
the model"; the floor says **the model's method and round reads are doing
nothing at all** on this sample, and the check's lead over it is therefore not
the interesting quantity.

**Equal counts are not identical picks.** 7/18 and 7/18 can be different sevens,
and the hover on the full-call row reports each side's decision-cell count,
which is what distinguishes "the model IS the base rate" from "the model is
wrong in a different place than the base rate". That diagnostic has to be read
before the stronger claim is made.

### What is and is not significant

Exact tests, most favourable pairing the totals allow:

| comparison | best-case p |
|---|---|
| check vs floor, early/distance (binomial vs 50%) | **0.008** |
| model vs floor, early/distance (binomial vs 50%) | **0.031** |
| check vs floor, full call | 0.062 |
| check vs floor, finish type | 0.250 |
| model vs floor, round one | 0.062 (model WORSE) |

**Only the length row is established.** Both reads genuinely beat a coin at
calling early-versus-distance, and they are a bout apart from each other. The
check's method edge remains unconfirmed at 0.062 and 0.250, and the registered
40-disagreement bar is unchanged.

### The round row is the clearest negative, and it is for both

Floor 9/11; check 6/11; model 4/11. **Both reads are substantially worse than
"call round one on a three-rounder and after it on a five".** This is the
recorded null arriving where it was always predicted: split-half 0.21 falling
to 0.05 for a fighter's own round shape. The model's 4/11 against a 9/11 floor
is the single worst cell in the table.

### Registered now, before more cards

1. If the model's method count continues to track the floor exactly, the
   question becomes whether its published method split is adding anything over
   the division base — a question about the MODEL, and a candidate for removal
   rather than improvement.
2. The round rows for both reads are candidates for withdrawal from the page,
   not repair. A claim that loses to one line of arithmetic over eleven bouts
   has to clear the floor before it is shown as a read again.
3. Neither is acted on before the registered bar. This is an interim, and the
   stopping rule says interims do not move thresholds.

---

## Addendum 79: does the model's METHOD and ROUND read beat the floor?
## REGISTERED 2026-10-27, before any fitting.

## Why this needs no checks

Addendum 78 found the model at or below the base-rate floor on four of five
rows of the graded method table, with its count EXACTLY equal to the floor's on
three of them (7/18, 7/26, 7/11). That sample is 26 bouts and every row depends
on a pasted check existing.

This question does not. "Does the model's method split beat the division base
rate" is model-against-floor, so it runs on the whole corpus, walked forward,
with no checks involved and no wait for the registered 40 disagreements.

If the model clears the floor at corpus scale, the 26-bout table is a cold
streak and nothing changes. If it does not, the finding is real at real sample
size.

## Universe, split, fitting

- The pipeline's own recipe, unchanged: survival model fitted on dates up to
  the 0.85 quantile of the expanded panel, hazards calibrated on the remainder,
  the finish formula rescaling the level exactly as `upcoming.py` does.
- Scored only on bouts AFTER the survival model's calibration cut, so every
  scored bout is out of sample for every component.
- Both corners 2+ priors, decisive results, from 2012-01-01.

## The floors, matched per bout

- **Method, 5 cells** (`decision`, `a_ko`, `a_sub`, `b_ko`, `b_sub`): the
  largest cell under that bout's own division base, finish mass split evenly
  between corners. Blind chance is 1/5.
- **Finish type, 3 families**: the commonest family in that division. Blind
  chance is 1/3.
- **Round one or past, conditional on a finish**: the league's conditional
  round-one share, .517 on three rounds and .376 on five. Blind chance is 1/2.

The reported floor on each row is the HIGHER of the base-rate rule and blind
chance, per addendum 77 amendment 1.

Division bases are computed on the TRAINING block only.

## Decision rule, fixed now

For each of the three rows, the model is credited only if it beats the floor
with a 95% bootstrap CI (2,000 resamples) on the paired difference excluding
zero, AND the gain clears the addendum 71 effect-size floor of `0.1 / n_test`.

**Predicted: the model beats the floor on method and finish type, and does NOT
beat it on round one.** The round prediction follows the recorded null — a
fighter's own round shape does not replicate, split-half 0.21 falling to 0.05 —
and the model's round number is built from the league curve, so it should track
the floor rather than beat it.

## What follows from each outcome, stated before seeing it

- **Model clears the floor on method:** the 26-bout table was a cold streak.
  Nothing changes, and addendum 78's registered candidates are withdrawn.
- **Model does not clear it on method:** the method split is a candidate for
  WITHHOLDING, not repair — the model already declines to publish a method on
  bouts too thin to support one, so there is precedent for showing nothing
  rather than showing a number that has not earned its place.
- **Model does not clear it on round:** same, for the round row, on both the
  model and the check sides.


## Addendum 79: RESULT (2026-10-27). All three fail on top-pick — and my prediction was wrong on two of three.

622 out-of-sample bouts from 2024-10-27, every component fitted before the cut.

| claim | n | model | base rule | floor | gain | 95% CI |
|---|---|---|---|---|---|---|
| full call, 5 cells | 622 | 0.511 | 0.508 | 0.508 | +0.0032 | [-0.0096, +0.0161] |
| finish type, 3 families | 622 | 0.514 | 0.508 | 0.508 | +0.0064 | [-0.0064, +0.0209] |
| round one, or past | 306 | 0.520 | 0.575 | **0.575** | **-0.0556** | [-0.1569, +0.0392] |

**To measurement precision the model's method TOP PICK is the division base
rate.** The 26-bout graded table, where the model's count equalled the floor's
exactly on three rows, was not a cold streak — it was reading something real,
and it holds at twenty-four times the sample.

**Registered prediction: model beats the floor on method and finish type, fails
on round one. It failed on all three.** The round call was right for the stated
reason. The other two were simply wrong, and writing them down beforehand is
the only thing that makes that visible rather than retrofittable.

## Addendum 80: RESULT (2026-10-27). The proper score REVERSES it. The method split stays.

Top-pick accuracy is argmax agreement. This project has twice recorded that
accuracy moves while probabilities go the other way (addendum 11), so before
withdrawing a component on an argmax tie, the distributions were scored with a
proper rule — same 622 bouts, model's five-cell distribution against the base
distribution.

| rule | model | base | model better by | 95% CI | P(better) |
|---|---|---|---|---|---|
| multiclass Brier | **0.63783** | 0.66132 | **+0.02350** | [+0.01169, +0.03553] | **1.000** |
| log loss | **1.23876** | 1.32416 | **+0.08540** | [+0.05385, +0.11601] | **1.000** |

Both CIs clear of zero by a wide margin, P(better) = 1.000 on 2,000 resamples,
and the Brier gain is **146 times** the addendum 71 effect-size floor.

**The model's method distribution carries real information. Its top pick is the
base rate; its probabilities are not.** The registered withholding consequence
from addendum 79 is therefore **withdrawn**, and so are addendum 78's
candidates for the method split.

### The finding is now about the TABLE, not about the model

Every row of "how the fight ends" is scored on **top-pick accuracy**, which has
just been shown at corpus scale to be blind to a difference that a proper rule
calls certain. That means:

- The model's apparent failure against the floor was an artifact of the metric.
- **The check's lead on those rows is measured the same way**, so it does not
  establish that the check's method read is better. It establishes that its
  argmax lands more often on 18 to 26 bouts. Those are different claims and the
  table cannot tell them apart.

**Registered next step:** the method rows need a proper score beside the hit
counts — multiclass Brier for check, model and base on the same bouts. The
check already stores its five cells with a `cells_ok` flag, so this is
computable in the browser with no new data. Until it exists, **no comparison
between the check and the model on method is to be treated as settled in either
direction**, including the three rows where the check currently clears the
floor.

### Still open

The ROUND row was scored only on top-pick, where the model trails the floor by
5.6 points on 306 finishes (CI spanning zero). Whether its round PROBABILITY
beats the floor's is not yet measured and is not claimed either way. The
recorded null predicts it does not.

### Twice wrong in one evening

I predicted the model would clear the floor on method and finish type: wrong.
I then came close to recommending withdrawal of a component that a proper
scoring rule says is certainly informative — stopped only because the
registration named the metric as crude before the number arrived. **An argmax
tie is not evidence of no information, and a 5e-07 sign-consistent gain is not
evidence of information. Both errors are the same error.**

---

## Addendum 81 (2026-10-27): the ROUND claim fails as a probability too

Addendum 79 left this open: the round row was scored only on top-pick, where
the model trailed the floor by 5.6 points. Scored properly, same 306
out-of-sample finishes:

| rule | model | floor | model better by | 95% CI | P(better) |
|---|---|---|---|---|---|
| Brier | 0.24768 | **0.24341** | **-0.00427** | [-0.01627, +0.00757] | 0.234 |
| log loss | 0.68803 | **0.67978** | **-0.00824** | [-0.03420, +0.01521] | 0.253 |

**No detectable gain on either rule, and the point estimate is negative on
both.** This is now the ONE component with corpus-scale evidence against it on
BOTH the crude metric and the proper one — which is exactly what separates it
from the method split, where the two metrics disagreed and the proper one won.

The recorded null predicted this and is confirmed at scale: a fighter's own
round shape does not replicate, split-half 0.21 falling to 0.05.

### A level error sits underneath it

| | round-one share |
|---|---|
| actual | **0.513** |
| model's mean P | **0.409** |
| floor's P | 0.495 |

**The model's conditional round-one probability runs about ten points low.**
That is a calibration fault, not a resolution fault, and it is the same
direction as every other under-call on the record — addendum 74's seven-point
shortfall on the combined finish read, addendum 68's +0.049 in 2026. Three
independent surfaces now point the same way.

**Registered, not acted on:** an intercept correction on the conditional
round-one probability is the candidate, tested the way addendum 73 was tested —
against the production read, with the sign and the effect floor fixed first.
It is NOT to be fitted on this sample and reported from it.

## Addendum 82 (2026-10-27): the graded table gets a proper score

Two changes, both following from addendum 80.

**`upcoming.py` now carries the model's full five-cell method split** —
`m_a_ko`, `m_a_sub`, `m_b_ko`, `m_b_sub` — into each graded row. `history.json`
held `m_decision` alone, so the browser could only ever score an argmax, and
reported a tie where a proper rule reports P(better) = 1.000. Four numbers per
bout; `grade_archive()` re-grades from scratch each run, so the whole record
backfills on the next pass.

**The method table gains a probability line**, not a sixth column: multiclass
Brier for model, check and base rate over the bouts where all three
distributions exist, with the lowest marked. Matched denominators — a proper
score computed on a different bout set per column would be the same fault the
"claims called" row was fixed for.

The line carries its own instruction: *read this before the hit counts above*,
with the reason stated — the counts are an argmax, and an argmax has now been
shown at corpus scale to tie where the distribution is decisively ahead. Before
a build carrying the five cells has run, the line says so rather than
displaying two columns of three.

**Nothing is concluded from it yet.** On 18 to 26 bouts a proper score is still
a small sample; what changes is that the question is now being asked with an
instrument that can answer it.

---

## Addendum 83: is there a blend weight that beats both ends?
## REGISTERED 2026-10-27, before any fitting.

The check overrides 9 of the 14 win-model inputs (SB_MAP: str_acc, slpm->adj_slpm,
sapm, td15->adj_td15, sub15, str_def, td_def, age, reach). Five are always held
at model values (elo, opp_elo, log_exp, ko_loss_rate, log_layoff). age and reach
are bio and identical on both sides, so the live blend moves 7 slots.

`st.blend` was a slider, fixed at w=1.0 with the note "a check that is 70% the
model is not a second opinion, it is the model." That was a MEASUREMENT
decision — keeping the check clean as an independent read. It is not a claim
that w=1 forecasts best. This tests the forecasting question.

## Reconstructing the check without a paste

UFC.com publishes RAW career-to-date aggregates over UFC bouts: landed/minute,
absorbed/minute, accuracy, defense, takedowns per 15, submission attempts per
15. `FighterState` already accumulates every one of those counters before it
shrinks them toward a prior and multiplies by a strength-of-schedule factor. So
the UFC.com value is the unshrunk, unadjusted form of a number the state
already holds, and it can be rebuilt for every bout in the corpus.

Caveat recorded up front: this is the MECHANISM, not the user's usage. Real
checks are entered on the interesting bouts, not a random sample, and a real
paste can be wrong or partial. The sweep says what blending does, not what the
26 entered checks did.

## Procedure

- Walk the corpus from 2012-01-01, both corners 2+ priors, decisive results.
- Chronological THREE-way split: 60% train, 20% validation, 20% test.
- Win model fitted ONCE on train, on pure model features, exactly as
  `train.py` does (C=0.5, fit_intercept=False, standardised).
- For w in 0.00 .. 1.00 by 0.05, blend the 9 mapped slots per corner
  (model*(1-w) + ufc*w), rebuild the 14 features, and score with the SAME fitted
  coefficients — which is precisely what `sbProb` does in the browser.
- **w is chosen on VALIDATION only, then confirmed once on TEST.**

That split is not optional. Sweeping 21 weights and reporting the best on the
same data is how the recency half-life was nearly mis-reported (Ablation 2),
and the discipline that caught it then is the discipline here.

## Decision rule, fixed now

The blend is supported only if, on the TEST block, the validation-chosen w
beats BOTH endpoints — w=0 (pure model) and w=1 (pure check) — on held-out
Brier, with a 95% bootstrap CI (2,000) excluding zero against w=0, and a gain
clearing 0.1/n_test.

Predicted: w* lies strictly between 0 and 1 and beats w=1 comfortably; whether
it beats w=0 is the open question and the prior is AGAINST it, because the
model's inputs are opponent-adjusted and shrunk and the UFC.com ones are
neither.


## Addendum 83: RESULT (2026-10-27). No interior optimum. The gradient points at the model.

4,167 bouts. Train 2,500 (to 2021-09-25), validation 833 (to 2024-03-30), test
834 (to 2026-09-12). Win model fitted once on train; the same coefficients
score every blend, which is what `sbProb` does in the browser.

**The validation curve is MONOTONE.**

| w | validation Brier | | w | validation Brier |
|---|---|---|---|---|
| 0.00 | **0.22795** | | 0.55 | 0.22881 |
| 0.05 | **0.22795** | | 0.65 | 0.22917 |
| 0.15 | 0.22799 | | 0.75 | 0.22958 |
| 0.25 | 0.22809 | | 0.85 | 0.23003 |
| 0.35 | 0.22827 | | 0.95 | 0.23053 |
| 0.45 | 0.22851 | | 1.00 | **0.23080** |

Every step away from the model's inputs makes the read worse, with no interior
minimum. Validation picked w* = 0.05, which is w = 0 to five decimal places.

**Confirmation on test (n=834):**

| arm | Brier |
|---|---|
| w=0, pure model | 0.21684 |
| w=0.05 | 0.21677 |
| w=1, pure check | 0.21879 |

| comparison | gain | 95% CI | P | floor |
|---|---|---|---|---|
| w* vs pure model | +0.00007 | [-0.00009, +0.00024] | 0.802 | **fails** |
| w* vs pure check | +0.00202 | [-0.00111, +0.00504] | 0.895 | clears |

**BLEND NOT SUPPORTED.** No weight beats the model, and w* does not even beat
pure check at the registered bar.

### The validation block earned its keep, visibly

The TEST column — blind, not used for selection — has a shallow dip at
w = 0.20-0.25 (0.21666 against 0.21684 at w=0), and that gain of 1.8e-04 would
have cleared the effect floor of 1.2e-04. **A sweep without a validation block
would have reported "optimal blend ≈ 0.22, beats the pure model" and it would
have been wrong.** Validation says the dip is not there; it is the shape of one
sample. This is Ablation 2's lesson arriving in a new place, and it is the
second time tonight that a guard fixed in advance stopped a false positive.

### What it settles

**The check's winner read is strictly degraded, monotonically, by its own
inputs.** It is the same model with unshrunk, opponent-unadjusted numbers, and
the gradient says every ounce of that substitution costs. So the check should
not be blended into the winner line at ANY weight, and w=1 was already the
right setting for the reason it was chosen — it keeps the check a clean
independent read — not merely a defensible one.

It also sharpens where the check could still be worth something: **not in the
winner line, which goes through the model's coefficients, but in the method
read, which is the check's own arithmetic on the pasted record and never
touches `sbProb`.** That is the one surface where it is not a degraded copy of
the model, and it is exactly the surface the addendum 82 Brier line was built
to measure.

### Prediction scored

Registered: w* strictly interior, beating w=1 comfortably, probably not beating
w=0. Outcome: w* sat at the model end, did NOT beat w=1 at the bar, and did not
beat w=0. **Right on the conclusion, wrong on the shape** — I expected the two
input sets to have complementary errors and they do not; the UFC.com set is
simply worse on every axis the win model uses.
