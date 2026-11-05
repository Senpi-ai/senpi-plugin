---
name: senpi-improve-trades
description: >-
  Review the signed-in user's own closed Hyperliquid trades with the Senpi connector. Use for
  "review my trades", "how did I trade this month?", "where am I losing money?", "what should I
  fix?", "my win rate?". Calls get_wallet_closed_trades with no address, which reads the
  connected user's own book. Read-only.
---

# Trade Review

One tool: `get_wallet_closed_trades` with **no address**, with `window_days` (default 30, max 365)
or `last` (the N most recent closed trades, for "my last 10 trades"). With no address it reads
the user's whole book — every Senpi strategy wallet (active, paused **and closed**: a closed
strategy's trades are history, not a live verdict), every saved wallet, and the Senpi main
wallet — paging each to the window start, and returns `wallets` (each with its `kind`, `label`,
`status`, whether its history was read and whether it was `truncated`), `totals` over every
trade in the window (`trades`, `net_realized_pnl_usd`, `fees_usd`, `win_rate`, `largest_wins`,
`largest_losses`), and `trades` — the first page of up to 200, newest first, each with its
wallet, strategy and `strategy_status`; `has_more` and `next_offset` page the rest. A wallet in
`truncated_wallets` had more closes than the 2,000 read: say its totals are short rather than
complete.

## Presenting the review

- Lead with the net number after fees, then the shape: win rate, how concentrated the PnL is in
  the largest wins/losses.
- The honest readings this data supports: fee drag (fees vs net PnL), asymmetry (are losses larger
  than wins), concentration (one trade carrying the month). Say what the data shows — and say what
  it cannot show (entries/exits quality needs per-trade inspection that isn't in this summary).
- `totals.trades: 0` with wallets read means no closed trades in the window — an answer, not an
  error. A wallet with `history_read: "unavailable"` (also named in `sources_unavailable`) is
  unknown, not $0: say its trades are missing from the totals.
- Group the reading by strategy when more than one traded: the `strategy` and `strategy_status`
  on each trade are there for that.
- Coaching stays descriptive: point at patterns in their own record, never prescribe a trade, size,
  or leverage. Changes to how they trade happen in their own decisions and Senpi app settings.
