# Forward odds ledger

`odds_log.jsonl` is written here by `python -m mmastat.ledger capture`, four
times a day via `.github/workflows/capture.yml`. It **is** committed — unlike
the rest of `data/` — because it is the experiment, not an input to it.

## Two venues, never pooled

| venue | source | auth | cost of trading |
|---|---|---|---|
| `sportsbook` | The Odds API consensus | `ODDS_API_KEY` | ~3.7% two-way overround |
| `polymarket` | Gamma + CLOB, public | **none** | the bid-ask spread, logged per row |

The pre-registered rule was frozen on sportsbook prices, so Polymarket rows
accumulate as a **separate test with their own count toward 300**. Pooling a
second venue into a running experiment widens the population mid-flight, which
is the same error as re-specifying a hypothesis after seeing data.

Polymarket matters for one reason: **a prediction market has almost no vig.**
The residual model's measured advantage is +0.0035 log loss — hopeless against
a bookmaker's margin, but the right order of magnitude against a venue whose
cost is a one- or two-cent spread. Whether that survives contact with reality
is exactly what the ledger is for.

**Three guards against capturing a decided fight.** Polymarket leaves markets
listed until they resolve and then quotes them at 1.0 / 0.0. A run after the
bell logged eight such rows as if they were forecasts the model got exactly
right — the one failure mode that manufactures evidence instead of destroying
it. Now: `capture` refuses any card dated in the past, `moneylines` rejects
prices within 2 cents of certainty, and `settle` prunes any that slipped
through. `python -m mmastat.ledger prune` runs the cleanup by hand.

Prices from thin books are dropped rather than recorded: wider than 6 cents or
under $250 of depth and the row never appears. A price you cannot trade is not
a price, and letting one in would quietly flatter the comparison.

One row per fighter-price per capture:

    captured_utc, venue, event, event_date, fighter, opponent,
    p_market_devig, implied_with_vig, p_model, edge, bet,
    books, spread, depth_usd, settled, won

Rules, enforced in code:

- **Deduplicated on every read and write**, keyed on
  (captured_utc, event_date, fighter, opponent). A scheduled job committing an
  append-only file will eventually duplicate it — a rebase replays a local
  rewrite onto a remote that already has it and both copies survive. That
  happened on the second live capture. Duplicates would double-count in CLV
  and ROI. `.gitattributes` also sets `merge=union` on this file, so a merge
  keeps both sides and dedupe cleans up: no captured prediction is ever lost.
- **Append only.** `settle` marks outcomes; nothing else is ever rewritten.
- **Frozen coefficients.** The rule lives in `mmastat/residual_model.json` and
  is applied, never refitted. Refitting would turn the forward test back into
  a retrospective one.
- **Settlement is re-derived from the corpus every run**, not skipped once
  set, so a bad match heals itself on the next pass. Captured prediction
  fields are never touched; only outcome fields are.
- **Matching requires the event date**, within 4 days, not just the fighter
  pair. 424 corpus fights are rematches — on the very first live capture, pair-
  only matching settled a Van vs Pantoja rematch with their 2025-12-06 first
  meeting, marking tonight's fight decided hours before it happened.
  `tests.py::test_settle_respects_dates` now guards this.
- **The last row before an event is the closing price**, which is what CLV is
  measured against.

`python -m mmastat.ledger report` shows where it stands.

**CLV is measured on the backed side only.** Averaged across both corners it is
identically zero — every point the favourite gains, the underdog loses — and
the first version did exactly that, reporting -0.0 on a card where lines had
moved almost two points. `all_sides_move_pp` is kept in the output purely as a
check: it should stay at 0.0, and if it drifts the two sides of a fight are no
longer being paired correctly.

## How long this takes

The rule triggers on roughly 14% of prices, or about **180 qualifying bets a
year**. The pre-registered threshold is 300 settled bets, so a verdict on ROI
is about **20 months** away.

Closing line value converges much faster — a few dozen bets — which is why
`report` puts CLV first. If the model is systematically getting worse prices
than the close, that shows up long before ROI could, and it is sufficient to
kill the rule early.
