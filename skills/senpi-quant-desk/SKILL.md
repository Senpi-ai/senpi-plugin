---
name: senpi-quant-desk
description: >-
  Quant Desk — read a Hyperliquid wallet like a quant with the Senpi connector: a 0-100 quant score
  with six explained dimensions, archetype and verdict, the live book's protection, the P&L
  waterfall and leaks priced in dollars, the strategy read, market fit, smart-money comparison
  and where the edge is. Use for "run quant desk", "run AI quant", "score my trading", "rate my
  trading", "find leaks", "where am I leaking money", "analyze my wallet", "score this trader 0x…",
  "is my book protected?", "compare these wallets with the desk", "which of these is the better
  trader", "find me traders to analyze / run the desk on", "what fits me today". Calls
  get_wallet_analysis (the analysis, by parts) and get_wallet_positions (the live book), with
  find_top_traders (size_band) for candidates, get_my_portfolio for the user's wallets and
  quant_desk_compare for two to five wallets side by side. The user's own book needs their Senpi
  sign-in; any other address is public data. Read-only.
---

# Quant Desk

Every number comes from the desk's tools, computed server-side. Never recompute, estimate or
re-derive a score, a P&L figure or a leak yourself — relay what the tools return. The tools return
data only; the words are yours, and this file says how to put them.

Quant Desk reads — a 0-100 score, leaks, protection, the side-by-side, candidates to run the desk
on, live matches — are this skill's; a plain ranked list of traders or a metrics-only comparison
stays with `senpi-trader-research` (`find_top_traders`, `compare_traders`).

## Two tools

- `get_wallet_analysis` — one analysis, cached ten minutes, returned by parts (`include`):
  `overview` and `leaks` by default; `performance`, `strategy`, `context`, `smart`, `market`,
  `edge`, `scout`, `replay`, `funding` and `windows` on request; `["all"]` is every part but
  `replay`. Ask for what the question needs: the default for a first read, one part for a
  follow-up. Every part is the full view — the list only trims the response.
- `get_wallet_positions` — the live book, read in seconds without the trade history: each open
  position with entry, mark, leverage, liquidation price and distance, margin used and at risk,
  the coin's average daily range (`daily_range_pct`), its stops and a protection `status`.

## Whose book

- **An address given** (`address: 0x…`) → that wallet, from public data.
- **No address** → the user's own book (all their Senpi strategy wallets, read as one).
- "find me traders to analyse" / no address and no own book → `find_top_traders` with
  `size_band`; ask the band first (a $9k book and a $9M book teach different lessons), then the
  window — relay the candidates with their numbers, then run the desk on the one they pick.
- "My wallets" / "which of my wallets" → `get_my_portfolio`: its `wallets` list, largest first,
  each usable as the `address`.
- Treat an address as the user's own when they say it is theirs; as research when they're reading
  someone else ("score this trader").
- `window_days` is optional: 7 to 90, default 90.

## Run it in stages

Stage it, don't dump it. The first `get_wallet_analysis` call does the full analysis: **tell the
user the desk is running first**, it can take up to two minutes on a heavy wallet. Never fire a
second call while one is in flight. A result saying the analysis is still running is not a
failure: wait about 30 seconds and call again **once**; it answers from cache.

1. **The hook** — `get_wallet_analysis` (default parts). Lead with the verdict in one line, then
   the score and archetype, then the dimensions worst-first: each has a `score` and a `line` that
   says what was measured — quote the line, it is the evidence. Then the flags. From `overview`:
   `track` (net, win rate, profit factor, trades), `drawdown` (`dd_pct` of equity, and
   `in_drawdown` now), `rank`, and `labels` where Senpi has them. `book_summary` gives the account
   value and how much of it is at work.
2. **What's urgent** — `get_wallet_positions`. Read each `status` as written: `PROTECTED`,
   `PARTIAL`, `UNPROTECTED`, `UNKNOWN`, or `NO_POSITIONS` for the book. `protected_by` says what
   covers it: a stop resting on Hyperliquid (`hyperliquid_stop`) or Senpi's own ratchet stop
   (`senpi_stop`). Give each position's liquidation distance against its daily range: a 3%
   distance on a coin that moves 5% a day is the finding.
   - **`UNKNOWN` means the orders or Senpi's stops could not be read — never say "unprotected" or
     "nothing to protect" over it.** A dex whose positions could not be read is named, not counted
     as empty.
   - Senpi's ratchet stops don't rest on Hyperliquid's book; they are read only for the signed-in
     user's own strategy wallets. `senpi_stops: "not_signed"` or `"unread"` means they weren't
     readable here, so an `UNPROTECTED` position on a Senpi strategy wallet may still be covered in
     Senpi — say so.
3. **The money** — the `leaks` part (in the default read): `costs` is the waterfall, gross →
   fees → funding → net; then `leaks` ranked by dollar impact, each with its `evidence` and
   `counterfactual` (what the same trades would have kept), and `recoverable` is the one figure
   that does not double count. Quote the counterfactuals as measured on this wallet's own trades,
   never as a promise.
4. **The rest, on request** — one part at a time: `performance` (the per-coin table, long against
   short, holds, execution), `strategy` (what the book does, its fingerprint and statements),
   `context` (today's market by asset class, the funding regime, the record by regime), `smart`
   (the positions against the proven and hot cohorts), `market` (each open position's fit with
   trend and funding), `edge` (best and worst setups, the measured rules).
5. **Going deeper** — `replay` (the worst 7-day window and its trades), `funding` (the next 30
   days at today's rates), `windows` (the last 30 days against the 60 before).
   - **Two or more wallets** ("compare these", "which of these is the better trader") →
     `quant_desk_compare`: the side-by-side numbers and what separates them, in third person. Say
     each wallet's window. For one wallet against a benchmark, pick the benchmark from
     `find_top_traders` with a `size_band`.
   - **Live matches** ("what fits me today", "where do my patterns line up with the market") →
     the `scout` part. Process only: a match is a setup that fits how this trader wins, never a
     call to buy a coin.

## Voice

- Someone else's wallet is "they"; the user's own book is "you". The tools do not choose — the
  `subject` field says which (`address` or `own_senpi_book`).
- Numbers and labels exactly as returned: a dimension `line`, a flag, a leak's `evidence`. Round
  dollars to the nearest dollar and percentages to one decimal when you restate them.
- Warnings in `overview.meta.warnings` are part of the answer: a coverage line, a truncated
  history, a cohort that could not be read.

## The data behind the desk

- The trades the desk scored → `get_wallet_closed_trades` (same `address`; `last` or a `coin`).
- The P&L and equity curve, flows and drawdown as series → `get_wallet_pnl_history` (same
  `address` and `window_days`); the desk's drawdown figure comes from this series.

## Framing

- Quote `analysis_as_of`; the desk describes the window analyzed, not a prediction. Informational
  only.
- Closed trades come from Senpi's trade history where Senpi has indexed the wallet, otherwise from
  Hyperliquid's public fills; `overview.meta.sources.trades` says which. A coverage line means the
  trade-level reads cover less than the wallet's whole volume — say so next to the numbers it
  affects.
- `not_a_trader` (the desk doesn't score this address: a vault, a known market maker, or a book
  trading more coins than the desk reads; the field names which) and `no_activity` (no perp trades
  and no open positions in the window) are answers, not errors: say which, plainly.
- Findings stay descriptive: what the book shows and what it cost. Never prescribe a trade, a size,
  a leverage or a stop price. Setting stops, fixing a leak in a live strategy or deploying one
  happens in the user's own Senpi account at senpi.ai — on a wallet the user custodies, they set
  stops on Hyperliquid themselves.
