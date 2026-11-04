---
name: senpi-improve-trades
description: >-
  Review the signed-in user's own closed Hyperliquid trades with the Senpi connector. Use for
  "review my trades", "how did I trade this month?", "where am I losing money?", "what should I
  fix?", "my win rate?". Calls review_my_trades. Reads only the connected user's own account.
  Read-only.
---

# Trade Review

One tool: `review_my_trades` with `window_days` (default 7, max 365) or `last` (the N most recent
closed trades, for "my last 10 trades"). It reads the user's whole book — every Senpi strategy
wallet (active, paused **and closed**: a closed strategy's trades are history, not a live
verdict), every saved wallet, and the Senpi main wallet — and returns `wallets` (each with its
`kind`, `label`, `status` and whether its history was read), `trades` (each with its wallet and
strategy), trade count, net realized PnL, total fees, win rate, and the largest wins and losses.

## Presenting the review

- Lead with the net number after fees, then the shape: win rate, how concentrated the PnL is in
  the largest wins/losses.
- The honest readings this data supports: fee drag (fees vs net PnL), asymmetry (are losses larger
  than wins), concentration (one trade carrying the month). Say what the data shows — and say what
  it cannot show (entries/exits quality needs per-trade inspection that isn't in this summary).
- `trades_count: 0` with wallets reviewed means no closed trades in the window — an answer, not an
  error. A wallet with `history_read: "unavailable"` (also named in `sources_unavailable`) is
  unknown, not $0: say its trades are missing from the totals.
- Group the reading by strategy when more than one traded: the `strategy` and `strategy_status`
  on each trade are there for that.
- Coaching stays descriptive: point at patterns in their own record, never prescribe a trade, size,
  or leverage. Changes to how they trade happen in their own decisions and Senpi app settings.
