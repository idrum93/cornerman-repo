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
