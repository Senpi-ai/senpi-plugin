---
name: senpi-portfolio
description: >-
  Show the signed-in user their own Senpi account with the Senpi connector. Use for "my portfolio",
  "my balance", "my positions", "my strategies", "how am I doing?" — and for their stops: "did any
  of my stops trigger?", "my ratchet-stop events", "did my stop fire?". Calls get_my_portfolio and
  get_my_stop_events. Reads only the connected user's own account. Read-only — nothing here
  trades, moves funds, or changes the account.
---

# Portfolio

One tool: `get_my_portfolio` (no arguments). Returns the user's balances, open positions, running
strategies, and `wallets` — their saved read-only wallets and Senpi strategy wallets, largest by
Hyperliquid account value first, each usable as the `address` of the wallet tools (the Quant Desk,
closed trades, P&L history). "Which of my wallets…" reads from that list.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown. For
  example, "I checked your stop history since Monday", not `get_my_stop_events` with `since`; "your
  strategy wallets couldn't be read", not `sources_unavailable`.
- Lead with total balance, then positions (asset, side, size, PnL if present), then running
  strategies with their status. **When `total_complete` is false, the total is a floor**: some
  read behind it failed and counted as $0 — say "at least $X; part of the balance couldn't be read
  right now", never present it as the finished total. When `perps_and_spot_same_money` is true
  (a unified or portfolio-margin account), the perps and spot figures in the portfolio are the
  same money: quote the total, never add the two. `account_mode` is the Hyperliquid margin mode of
  the user's main wallet, not the state of their Senpi account: `disabled` or `default` is a
  standard account (perps and spot kept apart) and nothing is wrong. Don't mention it unless the
  user asks; it only tells you whether perps and spot are the same money.
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
