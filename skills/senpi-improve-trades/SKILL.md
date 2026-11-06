---
name: senpi-improve-trades
description: >-
  Review the signed-in user's own closed Hyperliquid trades with the Senpi connector. Use for
  "review my trades", "how did I trade this month?", "where am I losing money?", "what should I
  fix?", "my win rate?". Calls get_wallet_closed_trades, get_wallet_pnl_history and
  get_my_stop_events with no address, which reads the connected user's own book. Read-only.
---

# Trade Review

Three calls, in this order, over the same window. First `get_wallet_closed_trades` with **no address**, with `window_days` (default 30, max 365)
or `last` (the N most recent closed trades, for "my last 10 trades"; then derive the window for the other two calls from the oldest returned trade's close time, or use 30 days if none came back, and say which you used). With no address it reads
the user's whole book — every Senpi strategy wallet (active, paused **and closed**: a closed
strategy's trades are history, not a live verdict), every saved wallet, and the Senpi main
wallet — paging each to the window start, and returns `wallets` (each with its `kind`, `label`,
`status`, whether its history was read and whether it was `truncated`), `totals` over every
trade in the window (`trades`, `net_realized_pnl_usd`, `fees_usd`, `win_rate`, `largest_wins`,
`largest_losses`), and `trades` — the first page of up to 200, newest first, each with its
wallet, strategy and `strategy_status`; `has_more` and `next_offset` page the rest. A wallet in
`truncated_wallets` had more closes than the 2,000 read: say its totals are short rather than
complete.

Second, `get_wallet_pnl_history` with **no address** and the same `window_days` (it reads 7 to 90
days: it rejects windows under 7, so ask for 7 and say the equity path covers 7 days; for a longer window ask for 90 and say the equity path covers the last 90). It returns one
entry per own wallet, each with `equity` (`start`, `end`, `avg`: what the wallet held), `equity_ex_flows_summary` (the
equity less deposits and withdrawals: the return base), `return_on_avg_equity` (a fraction: multiply by 100) and `drawdown` (`dd`, `dd_pct`,
`in_drawdown`, `current_dd_pct`); `wallets_omitted` names wallets it did not read. `dd_pct` and
`current_dd_pct` are fractions too: multiply by 100 when you present the equity block.

Third, `get_my_stop_events` with `since` set to the window start as an RFC 3339 time (and
`strategy_id` only if the user asked about one strategy). It returns `events` (newest first, default limit 100),
`strategies`, `strategies_omitted`, `sources_unavailable` and `truncated`; when `truncated` is true the
timeline is cut, so say it is incomplete.

## Presenting the review

Write for the user, not about the tools. Never name a tool, argument or response field, never show a
field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
request ids): say in plain words what was read and what it found. A failed read is "couldn't be read
right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown. For
example, "your strategy wallets couldn't be read, so these numbers cover only your main wallet", not
`sources_unavailable: ["strategies"]`; "read in full", not `history_read: ok`; "drawdown", not
`dd_pct`.

Four blocks, in this order. Quote `as_of`.

1. **The net and the shape** (from the closed trades). Lead with the net number after fees, then
   win rate and how concentrated the PnL is in the largest wins/losses.
2. **The equity path** (from the PnL history), per wallet: start and end equity, return on average
   equity (`return_on_avg_equity` times 100), the max drawdown (`dd`, and `dd_pct` times 100) and whether the wallet is in drawdown
   now. Read the return from `return_on_avg_equity`, not from end minus start: deposits and
   withdrawals move equity without being trading. A wallet in `wallets_omitted` is missing, not flat.
3. **What the stops did** (from the stop events): the events in the window, grouped by strategy
   (a tier trigger, a lock move, an arm, a stop). No events is an answer: say no stop acted in the
   window. Name any strategy in `strategies_omitted` (and any `sources_unavailable`) as unread, not
   as quiet.
4. **The honest readings** this data supports, below.

- The honest readings, drawn across the blocks: fee drag (fees vs net PnL), asymmetry (are losses larger
  than wins), concentration (one trade carrying the month). Say what the data shows — and say what
  it cannot show (entries/exits quality needs per-trade inspection that isn't in this summary).
- `totals.trades: 0` with wallets read means no closed trades in the window — an answer, not an
  error. A wallet with `history_read: "unavailable"` (also named in `sources_unavailable`) is
  unknown, not $0: say its trades are missing from the totals.
- Group the reading by strategy when more than one traded: the `strategy` and `strategy_status`
  on each trade are there for that.
- Coaching stays descriptive: point at patterns in their own record, never prescribe a trade, size,
  or leverage. Changes to how they trade happen in their own decisions and Senpi app settings.
