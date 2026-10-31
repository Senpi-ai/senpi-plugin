---
name: senpi-improve-trades
description: >-
  Review the signed-in user's own closed Hyperliquid trades with the Senpi connector. Use for
  "review my trades", "how did I trade this month?", "where am I losing money?", "what should I
  fix?", "my win rate?". Calls review_my_trades. Requires Senpi sign-in; anonymous calls return
  auth_required. Read-only.
---

# Trade Review

One tool: `review_my_trades` with `window_days` (default 30, max 90). Returns trade count, net
realized PnL, total fees, win rate, and the largest wins and losses in the window.

## Auth

- `AUTH_REQUIRED` means the user hasn't connected their Senpi account in this app — point them to
  the connector sign-in, then call again.

## Presenting the review

- Lead with the net number after fees, then the shape: win rate, how concentrated the PnL is in
  the largest wins/losses.
- The honest readings this data supports: fee drag (fees vs net PnL), asymmetry (are losses larger
  than wins), concentration (one trade carrying the month). Say what the data shows — and say what
  it cannot show (entries/exits quality needs per-trade inspection that isn't in this summary).
- `trades_count: 0` with wallets reviewed means no closed trades in the window — an answer, not an
  error.
- Coaching stays descriptive: point at patterns in their own record, never prescribe a trade, size,
  or leverage. Changes to how they trade happen in their own decisions and Senpi app settings.
