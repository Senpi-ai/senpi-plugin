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
  compare_wallets for two to five wallets side by side. The user's own book needs their Senpi
  sign-in; any other address is public data. Read-only.
---

# Quant Desk

Every number comes from the desk's tools. Never recompute, estimate or
re-derive a score, a P&L figure or a leak yourself — relay what the tools return. The tools return
data only; the words are yours, and this file says how to put them.

Quant Desk reads — a 0-100 score, leaks, protection, the side-by-side, candidates to run the desk
on, live matches — are this skill's; a plain ranked list of traders or a metrics-only comparison
stays with `senpi-trader-research` (`find_top_traders`, `get_wallet_profile`).

## Two tools

- `get_wallet_analysis` — one analysis, returned by parts (`include`):
  `overview` and `leaks` by default; `performance`, `strategy`, `context`, `smart`, `market`,
  `edge`, `scout`, `replay`, `funding` and `windows` on request; `["all"]` is every part but
  `replay`. Ask for what the question needs: the default for a first read, one part for a
  follow-up. Every part is the full view — the list only trims the response.
- `get_wallet_positions` — the live book, read in seconds without the trade history: each open
  position with entry, mark, leverage, liquidation price and distance, margin used and at risk,
  the coin's average daily range (`daily_range_pct`), its stops and a protection `status`; per
  wallet, `account_value`, margin utilization and withdrawable for the whole account
  (`account_value_basis` says `whole_account` or `perps`; `account_value_perps` sits beside).

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
failure: wait about 30 seconds and call again **once**.

1. **The hook** — `get_wallet_analysis` (default parts). The tool returns numbers and labels; you
   write the sentences from them, and every figure you quote names the measure it comes from.
   Lead with the verdict in one line, then the score and archetype, then the dimensions
   worst-first, then the flags.
   - **Verdict** — `verdict.strength_kind` picks the opening clause:
     - `edge` → "Real edge — profit factor {`profit_factor`} on {`trades`} trades"
     - `payoff` → "Winners run — {`payoff_ratio`}× payoff"
     - `win_rate` → "Picks well — {`win_rate`} win rate"
     - `ledger_up` → "Net {`ledger_net`} on the ledger over the window (open book and funding included)"
     - `ledger_down` → "Down {`ledger_net`} on the ledger over the window (open book and funding included)"
     - `net_positive` → "Net positive — {`net`} realized over the window"
     - `none` → "No edge shows up in this window"

     Then join only the one clause `weak_kind` names (absent: none of them), so the sentence says
     what the engine said, in the same order of precedence:
     - `underwater` → `underwater {unrealized, pct_of_equity, unprotected, unprotected_unread,
       positions}`: "the open book is ${|unrealized|} under water ({pct_of_equity} of equity),
       {unprotected} of {positions} positions unprotected" (`unrealized` is a negative number: quote
       its magnitude; and {unprotected_unread} unread, when above zero; unread is never
       "unprotected").
     - `liquidation` → `nearest_liquidation`: "{coin} {side} sits {liq_distance_pct}% from
       liquidation at {leverage}×", with its `protection` (`FULL` a full stop, `PARTIAL` a partial
       stop, `NONE` no stop, empty: orders the desk could not read).
     - `weakest` → "{dimension} scores {score}", then `measures[lead]` of that dimension (the
       finding below). Say "and" rather than "but" after `ledger_down` or `none`.

     The "but"/"and" joins whichever clause is said. `thin: true` → "only {trades} closed trades,
     too thin to grade". With none of these, say nothing in the record is leaking badly.
   - **Dimensions** — each has `score` (0-100) and `measures`. Quote the score, then the
     `lead` finding, then the other measures below that are present; a key that is absent was not
     measured, so leave it out. **`measures.lead` names the measure behind the line the desk
     chose**: quote `measures[lead]` as that dimension's finding (with the measures it sits
     beside). `lead: null` means nothing to flag for that dimension; say so. Order dimensions
     worst score first. `judged: false` with a null score means the desk could not score it: say so
     and quote only what was measured, never a score.
     - **Units.** These keys are fractions; multiply by 100 when you show them: `chased_share`,
       `give_back_median`, `dd_pct`, `current_dd_pct`, `margin_utilization`, `cost_ratio`,
       `cost_drag`, `taker_share`, `win_rate`, `long_share`, `largest_share`,
       `funding_pct_of_equity_yr`, `pct_of_equity`, `losers_that_were_green`,
       `mfe_median_winners`, `fee_rate_taker`, `fee_rate_maker`. Everything else is shown as
       returned: `liq_distance_pct` and `daily_range_pct` are already percentages; multiples
       (`hold_ratio`, `payoff_ratio`, `profit_factor`, `loser_to_winner_size`,
       `exposure_over_equity`), counts, hours and dollars go as they are.
     - **Signs.** Quote money as a magnitude and say the direction in words: `ledger_net` negative
       is "down $X"; `funding` and `worst_coin_funding` negative is "paid $X", positive is
       "collected $X"; `funding_per_day` negative means the book pays that much a day, positive
       that it collects; `unrealized` (under water) and `chased_realized` are negative numbers:
       say "$X under water" and "lost $X"; `liquidation_loss` is a loss whatever its sign. Never
       print "down -$X".
     - `naked` and `unread` are lists of coins; the count is their length (as a `lead`, name the
       coins).
     - `timing` — `chased_share` of `n` entries came after a ≥3% move (`chased_n`), run at
       `chased_pf` against `calm_pf` before the move (either can be very large when there were few losses; say so rather than quoting an absurd figure); `give_back_median` of a winner's peak given
       back; `entry_lag_h` hours after the whale cohort's flow turns (negative: ahead of it).
     - `risk` — `naked` (unprotected coins) and `unread` (coins whose stops could not be read) out
       of `open_positions`; `nearest_liquidation`; `hold_ratio` (`hold_losers_h` against
       `hold_winners_h`); `liquidations` costing `liquidation_loss`; `margin_utilization`;
       `dd_pct` drawdown over `days`; `ledger_net`.
     - `cost` — `cost_ratio` (`fees` plus paid `funding` against `gross_realized` and
       `gross_income`), or, when the window has no gross to compare, `cost_drag` (costs against the
       `cost_drag_basis` net result); `net`, `ledger_net`, `taker_share`.
     - `sizing` — `size_cv` and `size_max_over_median`; `loser_to_winner_size` (losers sized that
       many times winners, over `losers_sized` and `winners_sized`); `big_positions` (`n` of them,
       `winners` of which won); `exposure_over_equity`; `largest_share`; `complete_trades`.
     - `consistency` — `trades`, `win_rate`, `profit_factor` (`"Infinity"`: no losing trade),
       `payoff_ratio`.
     - `market_fit` — `with_market` against `against` positions (`against_positions`: coin, side,
       trend); `net_exposure`; `funding_per_day` and `funding_pct_of_equity_yr` on `account_value`;
       `positions`.
   - **Archetype** — `archetype` is facts, not a label. Say it as `style` + `bias` + `trader_type`:
     `style` (`aggressive`, `balanced` or `careful`), `bias` (`long` becomes "long-only", `short`
     "short-only"; empty means none), then the `trader_type` noun, e.g. "careful opportunist" or
     "aggressive long-only momentum chaser". Then describe how they trade from the inputs:
     `max_leverage`, `exposure_over_equity`, `margin_utilization`, `hold_winners_h` and
     `hold_losers_h` (`hold_median_h` over `complete_trades`), `pre24_median`, `trades_per_day`
     over `active_days`, `chased_share`, `long_share`. `trader_type` `thin record` or `early days`
     (`thin_record: true`) means too few closed trades: lead with "thin record — {`trades`}
     closed trades, {`fills`} fills" (or "early days — {`trades`} closed trades") and do not
     characterize their style beyond what the numbers show.
   - **The rest of `overview`** — `track` (net, win rate, profit factor, trades), `drawdown`
     (`dd_pct` of equity, and `in_drawdown` now), `rank`, and `labels` where Senpi has them. What
     the wallet holds is `book_summary.account_value` (the whole account when readable, else the
     perps value — see `account_value_perps`); quote that as its account value. `equity.start/end/avg`
     are the return base — the value series less the window's net flows — not what it holds, and
     `rank.leaderboard_account_value` is the stats leaderboard's lagging snapshot. Name which one
     you quote; never call two of them "account value" in one answer.
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
   fees → funding → net; then `leaks` ranked by dollar impact. Each leak has a `kind`, `usd`,
   `unpriced`, `window` and `measures`; write one line from the kind and its measures:
   - `taker_fees` — "{`taker_share`} of volume crossed the spread as a taker: {`fees_exec`} in fees
     on {`volume`} at {`fee_rate_taker`} taker / {`fee_rate_maker`} maker"
   - `funding_paid` — "paid {`funding`} in funding over {`days`} days; {`worst_coin`} alone cost
     {`worst_coin_funding`}" (say so when it exceeds the net, other coins having collected funding
     back), "the book pays {|`funding_per_day`|}/day at today's rates" when `funding_per_day` is
     negative, otherwise "the book collects {`funding_per_day`}/day", and when priced "holds past 24h
     paid {`paid_after_24h`}: {`funding_saved`} of funding plus {`exit_effect`} from closing
     earlier"
   - `open_past_24h` — "across {`complete_trades`} complete trades, the ones still open at 24h gave
     back more than they added from there on"
   - `hold_ratio` — "losers held {`hold_ratio`}× longer than winners: median {`hold_losers_h`}h
     against {`hold_winners_h`}h over {`complete_trades`} complete trades"
   - `give_back` — "winners give back a median {`give_back_median`} of their peak (they reach
     {`mfe_median_winners`} before exit); {`losers_that_were_green`} of losers were green first"
   - `give_back_unmeasured` — "no complete trade closed green, but {`n`} of them were in profit
     first"
   - `chased_entries` — "{`chased_n`} of {`n`} entries came after a ≥3% move and lost
     ${|`chased_realized`|} at profit factor {`chased_pf`}, against {`calm_pf`} when entering before
     the move" (`chased_realized` is negative when they lost; say "made" only if it is positive)
   - `liquidations` — "{`liquidations`} liquidation(s) cost {`liquidation_loss`}"
   - `oversized` — "{`n`} positions were sized over 1.5× the median winner; {`losers`} of them lost
     money, and capping them at the median winner ({`median_winner`}) would have kept {`usd`}"

   `usd` is what the same trades would have kept, measured on this wallet's own trades over the
   `window` — never a promise. `unpriced: true` means the pattern is measured, not priced: quote
   its measures and give no dollar figure. `gross` (on `open_past_24h`, `give_back`,
   `give_back_unmeasured`, `oversized`) is the gain before the offsetting cost, and `usd` is the
   net. `recoverable` is the one figure that does not double count. Never add the leaks' `usd`
   together yourself.
4. **The rest, on request** — one part at a time: `performance` (the per-coin table, long against
   short, holds, execution), `strategy` (what the book does: its fingerprint and families, as
   measured fields — describe them in your own words; no wording comes with them), `context`
   (today's market by asset class, the funding regime, the record by regime), `smart` (the
   positions against the proven and hot cohorts), `market` (each open position's fit with trend and
   funding; the book's stance comes as `stance`, `btc` and `median_funding_bp_8h`, in basis points
   per 8 hours), `edge` (best and worst setups, the measured rules).
5. **Going deeper** — `replay` (the worst 7-day window and its trades), `funding` (the next 30
   days at today's rates), `windows` (the last 30 days against the 60 before).
   - **Two or more wallets** ("compare these", "which of these is the better trader") →
     `compare_wallets`: per wallet the hook (score, archetype, verdict, rank, equity, drawdown,
     track) — the verdict and archetype are facts, read as in step 1 — and `separation`: each
     metric's value per wallet, which is best and worst at it, and the spread (`lower_is_better`
     says which way). Lead with the metrics that separate them most, in third person, and say each
     wallet's window and `analysed` count; a wallet marked `pending` is still running — call again
     in about 30 seconds. For one wallet against a benchmark, pick the benchmark from
     `find_top_traders` with a `size_band`.
   - **Live matches** ("what fits me today", "where do my patterns line up with the market") →
     the `scout` part. Process only: a match is a setup that fits how this trader wins, never a
     call to buy a coin.

## Voice

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown. For
  example, "Senpi stops were read", not `senpi_stops: read`; "a real edge", not
  `strength_kind: edge`; "no stop on it", not `naked`.
- Someone else's wallet is "they"; the user's own book is "you". The tools do not choose — the
  `subject` field says which (`address` or `own_senpi_book`).
- Numbers exactly as returned, and labels in their plain meaning: a measure, a flag, a leak's
  dollars. Round dollars to the nearest dollar and percentages to one decimal when you restate them.
  Never recompute a score or a dollar figure — relay it, and name the measure each number comes
  from.
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
