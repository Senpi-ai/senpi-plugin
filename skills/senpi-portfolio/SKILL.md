---
name: senpi-portfolio
description: >-
  Show the signed-in user their own Senpi account with the Senpi connector. Use for "my portfolio",
  "my balance", "my positions", "my strategies", "how am I doing?". Calls get_my_portfolio.
  Reads only the connected user's own account. Read-only — nothing here trades, moves funds, or
  changes the account.
---

# Portfolio

One tool: `get_my_portfolio` (no arguments). Returns the user's balances, open positions, and
running strategies.

## Presenting the result

- Lead with total balance, then positions (asset, side, size, PnL if present), then running
  strategies with their status.
- `strategies: null` means that section could not be read this run — say so instead of implying
  the user runs none.
- Quote figures exactly as returned with `as_of`. Never extrapolate value, promise performance, or
  advise a trade. Deposits, withdrawals, and any change to positions or strategies happen in the
  Senpi app, not here.

## Follow-ups to offer

- "How did I trade?" → `review_my_trades` (senpi-improve-trades).
- A position's market → `get_asset_brief`.
