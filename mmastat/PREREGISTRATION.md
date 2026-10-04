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
