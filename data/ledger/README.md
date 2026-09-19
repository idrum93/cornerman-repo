# Forward odds ledger

`odds_log.jsonl` is written here by `python -m mmastat.ledger capture`, four
times a day via `.github/workflows/capture.yml`. It **is** committed — unlike
the rest of `data/` — because it is the experiment, not an input to it.

One row per fighter-price per capture:

    captured_utc, event, event_date, fighter, opponent,
    p_market_devig, implied_with_vig, p_model, edge, books, bet,
    settled, won

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

## How long this takes

The rule triggers on roughly 14% of prices, or about **180 qualifying bets a
year**. The pre-registered threshold is 300 settled bets, so a verdict on ROI
is about **20 months** away.

Closing line value converges much faster — a few dozen bets — which is why
`report` puts CLV first. If the model is systematically getting worse prices
than the close, that shows up long before ROI could, and it is sufficient to
kill the rule early.
