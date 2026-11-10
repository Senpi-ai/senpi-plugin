---
name: senpi-trader-research
description: >-
  Research public Hyperliquid traders with the Senpi connector. Use for "find top traders", "best
  traders this month", "who's consistent?", "find traders to copy", "who could I mirror?",
  "compare these wallets", "is 0x… any good?", "show me their trades". Calls find_top_traders
  (ranked search, or with shortlist a ranking for copyability), get_wallet_profile (who a wallet
  is, 1–5 at once; with vet, its current book read for copyability), get_wallet_closed_trades (a
  wallet's trades), get_wallet_pnl_history (its P&L curve) and get_market_pulse (the day's tape a
  shortlist is read against).
  Read-only public data; nothing here copies or follows anyone.
---

# Trader Research

Four tools:

- `find_top_traders` — ranked traders over a `window` (daily/weekly/monthly, all_time; default
  monthly), with `sort_by` (roi — the default — pnl, realized_pnl, win_rate, max_drawdown,
  gain_to_pain, trader_age) and `limit` (default 20, max 1000). A null `maxDrawdown` or
  `returnOnInvestment` means not computed — never "0% drawdown" or "flat"; quote
  `generated_at` as the ranking's time. With `shortlist: true` it ranks for copyability instead
  (below).
- `get_wallet_profile` — who a wallet is, for 1 to 5 addresses: the ranking row over the `window`
  (default **all_time**, the whole record) with its labels, and `closed_trades` (the real count
  from the trade history); `found: false` means Senpi has no row for it. A read that failed is
  named in `sources_unavailable`; the rest stands. With `vet: true` each wallet also carries the
  copyability read of its current book (below). The full position list is `get_wallet_positions`,
  the board's read `get_leaderboard` with `trader`, and a scored comparison `compare_wallets`
  (senpi-quant-desk).

- `get_wallet_closed_trades` — one wallet's closed trades, newest first, a page of 50 per call (up
  to 200 with `last`): `address`, with `window_days` (default 30) or `last` ("their last 20
  trades"), an optional `coin`, and `offset` for the next page (`has_more`, `next_offset`,
  `total_count`; with a `coin` the filter is applied to the page, so `total_count` is null,
  `total_count_all_coins` is the wallet's and `coin_matches_on_page` the page's). Each trade
  carries side, entry and exit, size, leverage, times, `realized_pnl` (gross, before fees), `fees`,
  `net_pnl` (after fees) and `liquidation`; the page's `totals` give count, gross PnL, fees, net PnL
  after fees and win rate (counted on net) for the rows returned, not the whole history. Funding
  is not included.
- `get_wallet_pnl_history` — the wallet's P&L and account-value series over `window_days` (7–90,
  default 30), its `flows` (deposits and withdrawals), `equity` start/end/avg (what the account
  held), `equity_ex_flows_summary` (that less deposits and withdrawals: the return base),
  `ledger_net_pnl_usd`, `return_on_avg_equity` (a fraction) and `drawdown`. On a unified account
  (`whole_account: true`) the drawdown is measured against the whole account's value. A null
  drawdown means there was no data to measure, not no drawdown; an `abstraction` entry in
  `sources_unavailable` means the account mode couldn't be read, so the figures may be the
  perps-only side.

- `find_top_traders` with `size_band` (5k-10k, 10k-25k, 25k-100k, 100k-1m, whales) ranks by
  P&L within an account-size bracket off Hyperliquid's public leaderboard instead of Senpi's
  ranking — accounts that actually trade (at least $250k of window volume), the most profitable
  first, or the least with `losers: true`; the window is weekly, monthly or all_time. This is how
  "find me whales to look at" is answered; `sort_by` does not apply with a band.

## Copyability: the shortlist and the vet

A track record says whether a trader is good; it never says whether their book could be mirrored
right now. These two reads add that.

- **"Find traders to copy", "who could I mirror?", "who's consistent?"** → `find_top_traders` with
  `shortlist: true` and no `window` or `sort_by` (the shortlist blends the 7-day return, 30-day
  return and 30-day realized-profit rankings; naming a window or sort makes it one ranking). The
  `shortlist` comes back already ordered for copyability — present it in that order, never re-sorted
  by ROI or by fit. `seen_in` lists the rankings each trader appears in: in two or three means proven
  *and* performing now — say so. `pool` is how many traders the rankings held, `enriched` how many
  had their book read.
- **"Is 0x… any good?", "should I copy 0x…?"** → `get_wallet_profile` with that address and
  `vet: true`. Its `reliability` uses the real closed-trade count.
- **Market fit** → also call `get_market_pulse` and say, for the top candidates, whether their book
  (its net bias and biggest names) leans with or against what is working today. The connector has
  no market-fit figure: this is your read, and the one thing that may move the pick off the first
  row — say so in the same line when it does. Market fit never rescues a near-liquidation record.

What to say from each row:

- **How copyable now** — `mirrorability.fresh_entry_surface_pct` as "about N% of their book is still
  near their entry" (within 5% on the side a mirror's slippage gates on). Lead with that share, not
  the fit word. An unknown fit with no `book` means their positions couldn't be read right now —
  say that, never "no positions" or "flat".
- **What they hold** — `book`: open positions, longs and shorts, net bias, biggest names. A mirror
  inherits this book.
- **Rough minimum to mirror it** — `min_mirror_budget.min_budget_usd` as "a rough minimum of about $X
  to open their current book at Hyperliquid's position minimums", and `opens_nothing_below_usd` as
  the floor below which nothing would open. It is information about the trader's book, an estimate
  only — never advice on how much to put in, never an offer to set anything up. Null means nothing
  in the book would open now.
- **Activity** — last trade and trades per day: a mirror only acts when the trader does. The 4h
  `momentum` (hot, cold, flat) is P&L direction, not activity; it is unknown below the top ten
  rows or when the trader isn't on the board — never call that idle.
- **Reliability** — solid, ok, choppy, or a record too short to trust. Never quote a closed-trade
  count for a shortlist row: the shortlist has none. The vet has the real count.
- **Every flag, in plain words** (never the flag's name):
  - too short a record to trust (under 5 closed trades or under a week of history)
  - erratic results
  - came near liquidation once (a max drawdown of 83% or worse) — the only drawdown to alarm on;
    drawdowns of 50–80% are normal for leveraged perps
  - a positive return percentage beside a negative dollar P&L — show both, don't lead with the
    percentage
  - trades so often a copy would bleed fees (over 8 trades a day)
  - rarely opens new trades (a mirror would sit idle between them)
  - hasn't traded in over a month
  - using over 80% (high) or over 90% (critical) of their margin
  - underwater on their open positions right now
  - most of the book in one position; only one position
  - nothing open right now — nothing for a mirror to open until they trade again

The shortlist answer: one line with the pick (the first row unless market fit moves it, and why),
a table in the shortlist's order (address, share near entry, book, rough minimum, last traded,
reliability, flags), one line per top candidate on why (record, copyability now, market fit), then
the tempting names you passed over — what would have drawn the user (a big ROI, top of a ranking)
and the flag that rules them out.

The vet answer: a verdict line with the biggest reason; the track record (ROI, win rate, max
drawdown, closed trades, history); the labels in plain words; what they hold now with margin use;
right now (4h momentum, how often and how recently they trade); every flag in plain words; the
rough minimum.

## Judging a trader honestly

- Never rank on ROI alone. A high-ROI trader with a deep max drawdown or a stale last trade is a
  different proposition — surface win rate, drawdown, and recency together.
- For "is this wallet good?", the vet above; a benchmark trader from the shortlist gives context a
  single profile lacks, and `get_wallet_positions` lists every position they hold.
- `found: false` for an address means Senpi has no ranking row for it in that window — say the
  window, don't call the trader bad. When comparing records, say which window the numbers cover:
  all-time and monthly rank the same wallets differently.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown.
- A compact table reads best: address (shortened), ROI, win rate, drawdown, current exposure.
- Quote `as_of`. Describe the record; never promise the record continues, and never tell the user
  to copy a trader. Copying/mirroring is a Senpi-app action, not something these tools do.
- "Show me their trades" → `get_wallet_closed_trades`; "how has their equity moved" → `get_wallet_pnl_history`.
