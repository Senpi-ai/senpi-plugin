---
name: senpi-improve-trades
description: >-
  Review the signed-in user's own closed Hyperliquid trades with the Senpi connector. Use for
  "review my trades", "how did I trade this month?", "where am I losing money?", "what should I
  fix?", "my win rate?", "how did my exits do?", "did I sell too early?". Calls
  get_wallet_closed_trades (with review), get_wallet_pnl_history and get_my_stop_events with no
  address, which reads the connected user's own book. Read-only.
---

# Trade Review

Three calls, in this order, over the same window. First `get_wallet_closed_trades` with **no address** and `review: true`, with `window_days` (default 30, max 365)
or `last` (the N most recent closed trades, for "my last 10 trades"; then derive the window for the other two calls from the oldest returned trade's close time, or use 30 days if none came back, and say which you used). With no address it reads
the user's whole book — every Senpi strategy wallet (active, paused **and closed**: a closed
strategy's trades are history, not a live verdict), every saved wallet, and the Senpi main
wallet — paging each to the window start, and returns `wallets` (each with its `kind`, `label`,
`status`, whether its history was read and whether it was `truncated`), `totals` over every
trade in the window, and `trades` — the first page of up to 200, newest first, each with its
wallet, strategy, `strategy_status`, `realized_pnl` (gross, before fees), `fees` and `net_pnl`
(after fees); `has_more` and `next_offset` page the rest. The totals: `trades`, `wins`, `losses`,
`break_even`, `gross_realized_pnl_usd` (before fees), `fees_usd`, `net_realized_pnl_usd` (gross
less fees — the number to lead with), `win_rate` (a fraction, wins counted on net after fees, the
app's rule), and `largest_wins` / `largest_losses` ranked by net. `net_realized_pnl_usd` is null
when some trades carry no fee (`trades_missing_fees`): then quote the gross and say fees aren't
netted. Those trades have no net, so they are in none of `wins`, `losses` or `break_even`, and the
win rate covers only the trades with fees: say so when `trades_missing_fees` is above 0. Funding is in none of these (`funding_included: false`). A wallet in
`truncated_wallets` had more closes than the 2,000 read: say its totals are short rather than
complete. `strategies_closed_before_window` counts strategies that closed before the window
started: they can have no trade in it, so they were not read — never call them missing or
unreadable; if the user asks, say they closed before the period. Every wallet is read:
`wallets_read` counts them, `wallets` lists the ones with a trade in the window (or a read that
failed or ran out) and `wallets_without_trades` counts the quiet rest. `trades` comes a page at a
time: the totals already cover every trade, so follow `next_offset` only when the user wants the
trades themselves listed. `wallets_omitted` lists wallets past the 200 one read covers (live
wallets are read first, then closed strategies from the most recently closed, so the ones closed
longest ago are left out): their trades
are not in the totals, so say how many wallets were left out and that the totals cover the rest —
not that they "couldn't be read".

With `review: true` each trade also carries `exit` and `if_held`, and `review` holds three summaries
over every trade in the window (complete whatever the page):

- `exit` — how the trade ended, from its Senpi ratchet-stop record on the user's own strategy
  wallets: `SL_TRIGGERED` (the stop fired: a hard stop when no tier had armed, else a locked profit
  tier, with `tier_number` and `high_water_roe`), `CLOSED_OFF_LADDER` (the position went away by
  another route — the strategy's runtime, the agent or the user on the venue; the record can't
  tell which, so never "you closed it"), `LIQUIDATED`, `ADL`, `UNKNOWN` (no record matched: the
  exit mechanism isn't known — never guess one) or `NOT_A_STRATEGY_WALLET` (a saved or main-wallet
  trade). `premature: true` marks a tier 1 or 2 lock on a high-water ROE of 5% or less: the lock
  armed and trailed out almost at once. `record_unread` means that wallet's record couldn't be
  read; `record_capped` means the record holds only its newest 100 stops, so an older trade's may
  be past it.
- `if_held` — what holding from the exit to now would have added (`delta_usd` positive,
  `held_higher`) or given back (`exit_ahead`), at today's mark. It is hindsight over one stretch of
  the market and ignores the risk the exit avoided: context, never a grade. `held_higher` is never
  "you exited too early". `unknown` means no current price or side.
- `review.timing` — the counts of exits ahead and held-higher, `if_all_held_to_now_usd` (the whole
  book's hold-to-now, beside the realized P&L, never a target), by crypto and equity/index.
- `review.exit_mix` — closes by how they ended, overall, by asset class and by strategy, with the
  premature locks and a few examples. `sources` says how many exits came from a record, had none,
  or sat on a wallet whose record couldn't be read.
- `review.book_vs_market` — the 4h board's 12 biggest movers, whether the book traded each and on
  which side (`aligned`: long into a rise or short into a fall), and the `gaps` it didn't trade. The
  board is the last 4 hours and the book the whole window: say so, and never call a gap a mistake.

Second, `get_wallet_pnl_history` with **no address** and the same `window_days` (it reads 7 to 90
days: it rejects windows under 7, so ask for 7 and say the equity path covers 7 days; for a longer window ask for 90 and say the equity path covers the last 90). It returns one
entry per own wallet, a page of wallets at a time: while `next_offset` is set, call it again with
`offset` set to it, and read every page before you present the equity block. Each entry has `equity` (`start`, `end`, `avg`: what the wallet held), `equity_ex_flows_summary` (the
equity less deposits and withdrawals: the return base), `return_on_avg_equity` (a fraction: multiply by 100) and `drawdown` (`dd`, `dd_pct`,
`in_drawdown`, `current_dd_pct`) and `ledger_net_pnl_usd` (the account's P&L in the window as
Hyperliquid books it); `wallets_omitted` names wallets it did not read, and
`strategies_closed_before_window` counts the ones skipped because they closed earlier. `dd_pct` and
`current_dd_pct` are fractions too: multiply by 100 when you present the equity block. A null
drawdown means none could be measured (no P&L in the window), not a drawdown of 0: say "no
drawdown measured", never "0%".

Third, `get_my_stop_events` with `since` set to the window start as an RFC 3339 time (and
`strategy_id` only if the user asked about one strategy). It returns `events` (newest first, a page
at a time, up to `limit`), `strategies` (each with `by_type`: how many events of each type it had in
the window — complete whatever the page), `total_events`, `strategies_omitted`,
`strategies_closed_before_since` (a count), `sources_unavailable`, `truncated` and `next_offset`.
Summarise the stops from `by_type`, which covers every event: no further page is needed for that.
When the user wants the events themselves, follow `next_offset` (call again with `offset` set to it)
until it is null. A strategy whose
`capped` is true had more than 2,000 events in the period: say its counts are at least that many.

## Presenting the review

Write for the user, not about the tools. Never name a tool, argument or response field, never show a
field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
request ids): say in plain words what was read and what it found. A failed read is "couldn't be read
right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown. For
example, "your strategy wallets couldn't be read, so these numbers cover only your main wallet", not
`sources_unavailable: ["strategies"]`; "read in full", not `history_read: ok`; "drawdown", not
`dd_pct`.

Five blocks, in this order. Quote `as_of`.

1. **The net and the shape** (from the closed trades). Lead with the net number after fees, show
   the gross and the fees beside it, then win rate (wins counted after fees) and how concentrated
   the PnL is in the largest wins/losses. Say funding is not included. **The review is of the
   Senpi-managed wallets**: take these numbers from `review.senpi_totals`, not from `totals`
   (which adds every wallet together). When `review.saved_wallets` is present, give the saved
   wallets one line of their own after it — "your saved wallet, which you trade by hand: N closes,
   net $X; it is not part of the review above" — and never mix them into the review's counts.
   Then a per-wallet table from `wallets`: each wallet or strategy, its closes, wins and losses,
   fees and net after fees, largest net loss first, with closed strategies marked as closed.
2. **The equity path** (from the PnL history), per wallet: start and end equity, return on average
   equity (`return_on_avg_equity` times 100), the max drawdown (`dd`, and `dd_pct` times 100) and whether the wallet is in drawdown
   now. Read the return from `return_on_avg_equity`, not from end minus start: deposits and
   withdrawals move equity without being trading. A wallet in `wallets_omitted` is missing, not flat.
   **The ledger and the closed trades measure different things — never call them inconsistent.**
   The ledger is everything that moved the account in the window: closed trades, open positions'
   unrealized P&L, funding and fees. The closed trades are only positions that closed in the window,
   after fees, before funding, including the full P&L of trades opened before the window. When they
   differ, say which of those explains it (open positions down or up, funding paid, trades opened
   earlier), not that the data doesn't reconcile.
3. **How the trades ended** (from `exit` and `review.exit_mix`): how many closes the stop fired on,
   how many went off the ladder, how many were liquidated, and how many are unknown, per strategy
   when more than one traded; the premature locks with an example or two. Then the stop activity
   from the stop events: per strategy, the counts from `by_type` (stops hit, tier triggers, lock
   moves, arms). Both read Senpi's ratchet stops only. No events is "no Senpi ratchet stop acted in
   the window", never "no stop fired"; an `UNKNOWN` exit is "how this one closed isn't on record",
   never "it closed without a stop". A stop resting on Hyperliquid's book, a manual close on the
   venue or the runtime's own close reason leave no record here. Name any strategy in
   `strategies_omitted` (and any `sources_unavailable`) as unread, not as quiet.
4. **Timing and the market** (from `review.timing` and `review.book_vs_market`): how many exits got
   out ahead of a reversal and how many would be higher held to now, the book's hold-to-now total
   beside its realized P&L (hindsight, not a verdict), then the board's movers the book traded, on
   which side, and the ones it didn't.
5. **The honest readings** this data supports, below.

- The honest readings, drawn across the blocks: fee drag (fees vs net PnL), asymmetry (are losses larger
  than wins), concentration (one trade carrying the month), premature locks (a tier locking and
  trailing out on a small gain, again and again, is a pattern in the stop's settings, worth naming).
  Say what the data shows and what it can't: the close reason a strategy's runtime recorded, the
  signals it skipped and orders that failed live in the runtime on the user's machine and aren't
  visible here.
- Execution (maker vs taker, fees in dollars against what the book made) is the Quant Desk's read:
  offer to run it on their wallets (senpi-quant-desk) rather than estimating it from the trades.
- `totals.trades: 0` with wallets read means no closed trades in the window — an answer, not an
  error. A wallet with `history_read: "unavailable"` (also named in `sources_unavailable`) is
  unknown, not $0: say its trades are missing from the totals.
- Group the reading by strategy when more than one traded: the `strategy` and `strategy_status`
  on each trade are there for that.
- Coaching stays descriptive: point at patterns in their own record, never prescribe a trade, size,
  or leverage. Changes to how they trade happen in their own decisions and Senpi app settings.
