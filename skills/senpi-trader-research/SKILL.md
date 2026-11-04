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

- `find_top_traders` — ranked traders over a `window` (daily/weekly/monthly, all_time; default
  monthly), with `sort_by` (roi — the default — pnl, realized_pnl, win_rate, max_drawdown,
  gain_to_pain, trader_age) and `limit` (default 20, max 1000). For "who's consistent?", read
  more than one window and keep the wallets that rank in several.
- `compare_traders` — 2 to 5 addresses side by side, each as a vet dossier: the ranking row over
  the `window` (default **all_time**, the whole record) with its labels, `closed_trades` (the real
  count from the trade history), `open_positions` (the current book) and `momentum_4h` (the
  board's read). A read that failed is named in `sources_unavailable`; the rest of the dossier
  stands.

## Judging a trader honestly

- Never rank on ROI alone. A high-ROI trader with a deep max drawdown or a stale last trade is a
  different proposition — surface win rate, drawdown, and recency together.
- For "is this wallet good?", compare_traders with just that address plus a benchmark trader from
  find_top_traders gives context a single profile lacks.
- `found: false` for an address means no profile in the window and no open book — say the
  window, don't call the trader bad. When comparing records, say which window the numbers cover:
  all-time and monthly rank the same wallets differently.

## Presenting the result

- A compact table reads best: address (shortened), ROI, win rate, drawdown, current exposure.
- Quote `as_of`. Describe the record; never promise the record continues, and never tell the user
  to copy a trader. Copying/mirroring is a Senpi-app action, not something these tools do.
