---
name: senpi-trader-research
description: >-
  Research public Hyperliquid traders with the Senpi connector. Use for "find top traders", "best
  traders this month", "who's consistent?", "compare these wallets", "is 0x… any good?", "show me
  their trades". Calls find_top_traders (ranked search), compare_traders (2–5 wallets side by
  side), get_wallet_closed_trades (a wallet's trades) and get_wallet_pnl_history (its P&L curve).
  Read-only public data; nothing here copies or follows anyone.
---

# Trader Research

Four tools:

- `find_top_traders` — ranked traders over a `window` (daily/weekly/monthly, all_time; default
  monthly), with `sort_by` (roi — the default — pnl, realized_pnl, win_rate, max_drawdown,
  gain_to_pain, trader_age) and `limit` (default 20, max 1000). For "who's consistent?", read
  more than one window and keep the wallets that rank in several.
- `compare_traders` — 2 to 5 addresses side by side, each as a vet dossier: the ranking row over
  the `window` (default **all_time**, the whole record) with its labels, `closed_trades` (the real
  count from the trade history), `open_positions` (the current book) and `momentum_4h` (the
  board's read). A read that failed is named in `sources_unavailable`; the rest of the dossier
  stands.

- `get_wallet_closed_trades` — one wallet's closed trades, newest first, one page of up to 200 per
  call: `address`, with `window_days` (default 30) or `last` ("their last 20 trades"), an optional
  `coin`, and `offset` for the next page (`has_more`, `next_offset`, `total_count`). Each trade
  carries side, entry and exit, size, leverage, times, realized PnL, fees and `liquidation`; the
  page's `totals` give count, net PnL, fees and win rate for the rows returned, not the whole
  history.
- `get_wallet_pnl_history` — the wallet's P&L and account-value series over `window_days` (7–90,
  default 30), its `flows` (deposits and withdrawals), `equity` start/end/avg, `ledger_net_pnl_usd`,
  `return_on_avg_equity` and `drawdown`. On a unified account (`whole_account: true`) the drawdown
  is measured against the whole account's value.

- `find_top_traders` with `size_band` (5k-10k, 10k-25k, 25k-100k, 100k-1m, whales) ranks by
  P&L within an account-size bracket off Hyperliquid's public leaderboard instead of Senpi's
  ranking — accounts that actually trade (at least $250k of window volume), the most profitable
  first, or the least with `losers: true`; the window is weekly, monthly or all_time. This is how
  "find me whales to look at" is answered; `sort_by` does not apply with a band.

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
- "Show me their trades" → `get_wallet_closed_trades`; "how has their equity moved" → `get_wallet_pnl_history`.
