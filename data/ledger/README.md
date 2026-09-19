# Forward odds ledger

`odds_log.jsonl` is written here by `python -m mmastat.ledger capture`, four
times a day via `.github/workflows/capture.yml`. It **is** committed — unlike
the rest of `data/` — because it is the experiment, not an input to it.

One row per fighter-price per capture:

    captured_utc, event, event_date, fighter, opponent,
    p_market_devig, implied_with_vig, p_model, edge, books, bet,
    settled, won

Rules, enforced in code:

- **Append only.** `settle` marks outcomes; nothing else is ever rewritten.
- **Frozen coefficients.** The rule lives in `mmastat/residual_model.json` and
  is applied, never refitted. Refitting would turn the forward test back into
  a retrospective one.
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
