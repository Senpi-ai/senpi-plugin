---
name: senpi-quant-desk
description: >-
  Quant Desk — read a Hyperliquid wallet like a quant with the Senpi connector: a 0-100 quant score
  with six explained dimensions, archetype and verdict, the protection audit of the live book, the
  P&L waterfall and leaks priced in dollars, the strategy read, market fit, smart-money comparison
  and where the edge is. Use for "run quant desk", "run AI quant", "score my trading", "rate my
  trading", "find leaks", "where am I leaking money", "analyze my wallet", "score this trader 0x…",
  "is my book protected?". Calls quant_desk_overview, quant_desk_protection, quant_desk_leaks,
  quant_desk_section, quant_desk_deep, quant_desk_my_wallets, quant_desk_compare and quant_desk_find. Works on any address without
  sign-in; the user's own book needs Senpi sign-in. Read-only.
---

# Quant Desk

Every number comes from the desk's tools, computed server-side. Never recompute, estimate or
re-derive a score, a P&L figure or a leak yourself — relay what the tools return.

## Whose book

- **An address given** (`address: 0x…`) → that wallet; no sign-in needed.
- **No address** → the signed-in user's own book (all their Senpi strategy wallets, read as one).
  An `auth_required` result means they haven't connected Senpi in this app — point them to the
  connector sign-in, then call again.
- "find me traders to analyse" / no address and no own book → `quant_desk_find`; ask the size band first (a $9k book and a $9M book teach different lessons), then the window — relay the candidates with their numbers, then run the desk on the one they pick.
- "My wallets" / "which of my wallets" → `quant_desk_my_wallets` first; it lists them largest first.
- Treat an address as the user's own when they say it is theirs; as research when they're reading
  someone else ("score this trader").
- `window_days` is optional: 7 to 90, default 90.

## Run it in stages

Stage it, don't dump it. Each stage after the first reads the cached analysis and is instant.

1. **The hook** — `quant_desk_overview`: the score, archetype, verdict, flags and the top
   findings. This call does the full analysis: **tell the user the desk is running first**, it can
   take up to a minute. Never fire a second call while one is in flight; if it times out, wait a few
   seconds and retry **once** (the finished analysis is cached for ten minutes).
2. **What's urgent** — `quant_desk_protection`: each open position's distance to liquidation and
   whether a stop covers it. Read each status as written: `PROTECTED`, `PARTIAL`, `UNPROTECTED`,
   `UNKNOWN`, or `NO_POSITIONS` for the book. `protected_by` says what covers it: a stop resting on
   Hyperliquid (`hyperliquid_stop`) or Senpi's own ratchet stop (`senpi_stop`).
   - **`UNKNOWN` means the orders or Senpi's stops could not be read — never say "unprotected" or
     "nothing to protect" over it.** A dex whose positions could not be read is named, not counted
     as empty.
   - Senpi's ratchet stops don't rest on Hyperliquid's book; they are read only for the signed-in
     user's own strategy wallets. `senpi_stops: "not_signed"` means they weren't readable here, so
     an `UNPROTECTED` position on a Senpi strategy wallet may still be covered in Senpi — say so.
3. **The money** — `quant_desk_leaks`: gross → fees → funding → net, then the leaks ranked by dollar
   impact, each with its counterfactual.
4. **The rest, on request** — `quant_desk_section` with `strategy`, `context`, `performance`,
   `smart`, `market`, `edge` or `scout`.
5. **Going deeper** — `quant_desk_deep` with a mode the user picks (`protect`, `smart`, `replay`,
   `funding`, `regime`, `compare`, `rules`, `strategy`, `scout`).
   - **Two or more wallets** ("compare these", "which of these is the better trader") → `quant_desk_compare`: the side-by-side table and what separates them, in third person. Say each wallet's window. For one wallet against a benchmark, pick the benchmark from `quant_desk_find`.
   - **Live matches** ("what fits me today", "where do my patterns line up with the market") → `quant_desk_section` with `scout`, or `quant_desk_deep` with `scout`. Process only: a match is a setup that fits how this trader wins, never a call to buy a coin — relay that line as written.

Each tool returns structured data and the section's own text: relay that text, keeping its numbers
and labels exactly.

## Framing

- Quote `analysis_as_of`; the desk describes the window analyzed, not a prediction. Informational
  only.
- Closed trades come from Senpi's trade history where Senpi has indexed the wallet, otherwise from
  Hyperliquid's public fills; the result says which. A coverage line means the trade-level reads
  cover less than the wallet's whole volume — say so next to the numbers it affects.
- `not_a_trader` (the desk doesn't score this address: a vault, a known market maker, or a book
  trading more coins than the desk reads; the field names which) and `no_activity` (no perp trades
  and no open positions in the window) are answers, not errors: say which, plainly.
- Findings stay descriptive: what the book shows and what it cost. Never prescribe a trade, a size,
  a leverage or a stop price. Setting stops, fixing a leak in a live strategy or deploying one
  happens in the user's own Senpi account at senpi.ai — on a wallet the user custodies, they set
  stops on Hyperliquid themselves.
