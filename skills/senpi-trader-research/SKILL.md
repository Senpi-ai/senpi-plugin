---
name: senpi-trader-research
description: >-
  Research public Hyperliquid traders with the Senpi connector. Use for "find top traders", "best
  traders this month", "who's consistent?", "compare these wallets", "is 0x… any good?". Calls
  find_top_traders (ranked search) and compare_traders (2–5 wallets side by side). Read-only
  public data; nothing here copies or follows anyone.
---

# Trader Research

Two tools:

- `find_top_traders` — ranked traders over a `window` (daily/weekly/monthly/all_time), with
  `sort_by` (roi, pnl, realized_pnl, win_rate, max_drawdown, gain_to_pain, trader_age) and `limit`
  (max 20).
- `compare_traders` — 2 to 5 addresses side by side: performance profile plus current open
  positions.

## Judging a trader honestly

- Never rank on ROI alone. A high-ROI trader with a deep max drawdown or a stale last trade is a
  different proposition — surface win rate, drawdown, and recency together.
- For "is this wallet good?", compare_traders with just that address plus a benchmark trader from
  find_top_traders gives context a single profile lacks.
- `found: false` for an address means no profile in the window — say the window, don't call the
  trader bad.

## Presenting the result

- A compact table reads best: address (shortened), ROI, win rate, drawdown, current exposure.
- Quote `as_of`. Describe the record; never promise the record continues, and never tell the user
  to copy a trader. Copying/mirroring is a Senpi-app action, not something these tools do.
