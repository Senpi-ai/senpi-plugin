---
name: senpi-quant-desk
description: >-
  Quant Desk — score a Hyperliquid wallet with the Senpi connector: a 0-100 quant score with six
  explained dimensions, archetype and verdict, leaks priced in dollars, an exchange-level
  protection audit, rank and drawdown. Use for "run quant desk", "run AI quant", "score my
  trading", "rate my trading", "find leaks", "where am I leaking money", "analyze my wallet",
  "score this trader 0x…", "what should I fix first". Calls get_quant_scorecard. Works on any
  address without sign-in; the user's own book needs Senpi sign-in. Read-only.
---

# Quant Desk

One tool: `get_quant_scorecard`, with optional `trader_address` (0x…) and `window_days` (default
30, max 90). It runs the full analysis server-side and returns the finished scorecard — never try
to recompute or re-derive the score yourself.

- **An address given** → that wallet is scored from public data; no sign-in needed.
- **No address** → the signed-in user's own wallet; `AUTH_REQUIRED` means they haven't connected
  their Senpi account in this app — point them to the connector sign-in, then call again.
- "Run quant desk on my wallet 0x…" → pass that address. Treat it as the user's own book when they
  say it is theirs; as research when they're analyzing someone else ("score this trader").

## Timing — read before calling

The analysis walks every fill, funding payment and candle in the window, so **a fresh run takes up
to a minute**. Tell the user the desk is running before you call. **Never fire a second call while
one is in flight.** If the call times out, wait a few seconds and retry **once** — the finished
analysis is cached server-side for ten minutes, so the retry usually returns instantly.

## Presenting the scorecard

Stage it, don't dump it:

1. **The number first**: quant score, archetype, verdict — that's what they came for.
2. **What's urgent**: the protection audit — unprotected coins, liquidation distances. Say plainly
   that protection shown is **exchange-level only** (resting stops on Hyperliquid); Senpi ratchet
   stops are not visible to this tool, so a position may be protected in Senpi without showing here.
3. **The money**: leaks with their counterfactual dollars, and `recoverable_usd`.
4. On request: the six dimensions (each has a `line` explaining its score — a `null` score means
   not enough data, say so), rank, drawdown, the strategy read.

- Quote the `as_of` timestamp and keep the informational-only framing; the score describes the
  window analyzed, not a prediction.
- `wallet_used` / `wallets_available` present means the user has several wallets and this scored
  the first — name which one, and that the others can be scored by passing their address.
- `NOT_A_TRADER` means no perp activity in the window — an answer, not an error. `TIMEOUT` and
  `ALREADY_RUNNING` are retryable (once, after a pause); `BAD_INPUT` is not.
- Findings stay descriptive: point at what the book shows, never prescribe a trade, size or
  leverage. Fixing leaks, setting stops and deploying strategies happen in the user's own Senpi
  account at senpi.ai.
