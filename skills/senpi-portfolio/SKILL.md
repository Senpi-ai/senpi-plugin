---
name: senpi-portfolio
description: >-
  Show the signed-in user their own Senpi account with the Senpi connector. Use for "my portfolio",
  "my balance", "my positions", "my strategies", "how am I doing?". Calls get_my_portfolio.
  Reads only the connected user's own account. Read-only — nothing here trades, moves funds, or
  changes the account.
---

# Portfolio

One tool: `get_my_portfolio` (no arguments). Returns the user's balances, open positions, running
strategies, and `wallets` — their saved read-only wallets and Senpi strategy wallets, largest by
Hyperliquid account value first, each usable as the `address` of the wallet tools (the Quant Desk,
closed trades, P&L history). "Which of my wallets…" reads from that list.

## Presenting the result

- Lead with total balance, then positions (asset, side, size, PnL if present), then running
  strategies with their status.
- `strategies: null` means that section could not be read this run — say so instead of implying
  the user runs none.
- Quote figures exactly as returned with `as_of`. Never extrapolate value, promise performance, or
  advise a trade. Deposits, withdrawals, and any change to positions or strategies happen in the
  Senpi app, not here.

## My stops

- "What did my stops do?", "did my ratchet trigger?", "why did my position close?" →
  `get_my_stop_events`: the account's ratchet-stop timeline, newest first — each event with its
  strategy, wallet, asset, `event_type` (a tier trigger, a lock move, an arm, a stop) and `details`.
  `strategy_id` narrows to one strategy, `since` to a time. A strategy in `sources_unavailable`
  could not be read: its events are missing, not absent.

## Follow-ups to offer

- "How did I trade?" → `get_wallet_closed_trades` with no address (senpi-improve-trades).
- A position's market → `read_asset_signal`.
- "My closed trades" one page at a time, per wallet → `get_wallet_closed_trades` with no address;
  "how has my equity moved" → `get_wallet_pnl_history` with no address (one series per wallet).
