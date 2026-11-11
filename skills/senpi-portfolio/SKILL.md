---
name: senpi-portfolio
description: >-
  Show the signed-in user their own Senpi account with the Senpi connector. Use for "my portfolio",
  "my balance", "my positions", "my strategies", "how am I doing?" — and for their stops: "did any
  of my stops trigger?", "my ratchet-stop events", "did my stop fire?". Calls get_my_portfolio,
  get_wallet_positions (what a saved wallet or a strategy holds, and its stops) and
  get_my_stop_events. Reads only the connected user's own account. Read-only — nothing here
  trades, moves funds, or changes the account.
---

# Portfolio

The main tool is `get_my_portfolio` (no arguments); `get_wallet_positions` reads one wallet's live
book where the sections below call for it. Returns the user's balances, open positions, running
strategies, the money map (`money`), one entry per strategy (`strategy_groups`), and `wallets` — their saved read-only wallets and Senpi strategy wallets, largest by
Hyperliquid account value first, each usable as the `address` of the wallet tools (the Quant Desk,
closed trades, P&L history). "Which of my wallets…" reads from that list. Strategy wallets holding
$0 (closed strategies, mostly) are counted in `empty_wallets`, not listed: give the count when you
list the wallets ("plus 51 empty strategy wallets"), never call them missing. The list comes a page
at a time: while `next_offset` is set, call again with `offset` set to it, and read every page
before you present the list as complete.

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
  the user runs none. The money map and the strategy groups need that list too: when it is
  missing they are unknown, never empty.

## The money map — three pools that never mix

Every dollar of the user's Senpi money sits in exactly one pool (`money`), and the most common
mistake is mixing them:

| Pool | What it is |
|---|---|
| The main wallet's idle cash (`main_wallet.idle_usd`) | Truly free: Hyperliquid perps and spot USDC plus stablecoins on EVM chains. Only the Hyperliquid part can fund a strategy; the EVM stablecoins don't move in on their own. |
| Idle inside strategies (`idle_in_strategies_usd`) | Free margin inside a strategy wallet, not in a position: waiting for a signal. |
| Deployed (`deployed_in_positions_usd`) | Margin backing open positions. |

- **Always say where idle money is**: "$X idle in your main wallet, free to deploy or withdraw" is
  a different statement from "$Y sitting in strategy wallets waiting for signals". Never call the
  second one free cash.
- The grand total is the three pools added up. When `reconciles` is false, the pools and the
  account total disagree: quote both figures and say part of the money couldn't be placed, never
  pick one. When `strategy_wallets_unread` names a wallet, its money is missing from the pools:
  say the pools are incomplete and leave `reconciles` unmentioned.
- A strategy wallet's crypto and equities views share one free balance; the pools already count
  it once. Never add the two views yourself.
- The saved wallets the user trades by hand are not part of these pools. Show them in the wallet
  list, never inside the three pools.
- **Show what each saved wallet holds, not only its value.** For each saved wallet (up to five,
  largest first) call `get_wallet_positions` with its address: list its open positions, and its
  spot holdings (each token and amount, with what the spot holdings are worth together). A wallet
  with neither holds cash: say so.
- **Give one book total.** After the pools: "Your whole book is $X: $Y managed by Senpi and $Z in
  wallets you added, which Senpi can read but not trade." Keep the two parts visibly apart; never
  fold the saved wallets into the Senpi total.

## A strategy is all its wallets

`strategy_groups` has one entry per strategy. A strategy can run on several wallets (a long book
and a short book, a core and a ballast); they are the legs of one design, never separate
strategies. Present and judge each group as one strategy, with its wallets as detail.

- **Names.** Most strategies have no name of their own. When `name_source` is `package`, the
  name shown is the package the strategy was made from, not its name: say "your Spider strategy",
  and tell two of them apart by wallet. When it is null the strategy is unnamed: call it by its
  wallet.
- **Copy-trades and directly placed positions.** A strategy whose `kind` is `mirror` copies one
  trader (`copied_trader`): say whom it copies. That, and any strategy with no package (or the
  package `senpi-trade`), is a copy-trade or positions the user or their agent placed directly.
  Each is its own entry. They have no runtime and no mandate by design: never call one "not
  running", unprotected for lack of a runtime, or off-mandate, and never say its mandate lives
  on the user's machine.
- **Totals** cover every wallet of the strategy. A total that is null means a wallet couldn't be
  read: say so, never $0.
- **A wallet with no open position** (`flat_wallets`, by address) in a multi-wallet strategy is its
  other book waiting for its signal. It is not idle money to move elsewhere, and never "dead money".
- **Protection.** Say what protects each strategy, from its record: its stop-loss and take-profit
  percentages (empty means none is set: "no stop-loss or take-profit is set on this strategy"),
  and for a copy-trade its copy multiplier. For a strategy holding positions, each position's own
  stop is in `get_wallet_positions` for its wallet (protected, partly, unprotected, or unknown
  when it couldn't be read): read it and say it. Never call a strategy unprotected because it has
  no runtime.
- **The closed record** covers each wallet's last 50 closes: quote the record, the win rate and the
  newest close as given, never a rate worked out from the recent sample. List the newest closes
  with their entry and exit price beside the result. Say "has not closed a
  trade in X hours", never "has not traded": an entry taken since the last close is invisible
  here. A strategy in `quiet_strategies` that is holding positions is fully allocated, not stuck.
- **The mandate** is the template's declared job, from Senpi's catalog. Lead each strategy with
  that job in the user's words, then judge whether it is behaving the way that job says, with the
  positions as evidence. Never judge a hedge, a market-neutral or an all-weather book by whether
  it caught this week's move, and never call a selective strategy with nothing open "dead": it is
  flat, waiting for its setup. When the mandate is null, the strategy wasn't made from a catalog
  template: unless it is a copy-trade or a directly placed position (above), its declared job lives in its own setup
  on the user's machine. Say the mandate isn't visible from here and judge cautiously on
  behaviour.

## A verdict for each strategy, and the user's options

End each strategy with one plain verdict line and the number behind it: doing its job, flat and
waiting, or the largest drag on the book ("the largest loss in your book: down $4.86 of the $10
it was funded with, on four closes, all losers"). Then list the options the user has in the Senpi
app, without choosing for them: for a copy-trade, lowering the multiplier, setting a stop-loss,
copying someone else or stopping; for any other strategy, pausing it, closing it, or adding to it.
Listing options is not advice: never say which to take, and never suggest a trade.

## What this connector can't see

Whether a strategy's runtime is actually running, why a running strategy hasn't opened a position,
the signals it skipped, and a self-written strategy's own description all live in the runtime on
the user's machine. When the user asks "is it running?" or "why hasn't it traded?", say what the
account shows (funded, positions, last close) and that the runtime's own status isn't visible from
this connector; their Senpi agent can read it. Never say a strategy is running, or broken, on that
evidence alone.
- Quote figures exactly as returned with `as_of`. Never extrapolate value, promise performance, or
  advise a trade. Deposits, withdrawals, and any change to positions or strategies happen in the
  Senpi app, not here.

## My stops

- "What did my stops do?", "did my ratchet trigger?", "why did my position close?" →
  `get_my_stop_events`: the account's ratchet-stop timeline, newest first — each event with its
  strategy, wallet, asset, `event_type` (a tier trigger, a lock move, an arm, a stop) and `details`.
  `strategy_id` narrows to one strategy, `since` to a time. The events come a page at a time:
  each strategy's `by_type` counts all of them, so a summary needs no further page; to list them,
  follow `next_offset` (call again with `offset` set to it) until it is null. A strategy in
  `sources_unavailable` could not be read: its events are missing, not absent.
- **Scope what an empty timeline proves.** It is Senpi's ratchet-stop record only. No events in
  the window means "no Senpi ratchet stop acted on your strategies since Monday", never "none of
  your stops fired" or "no stop closed anything": a stop resting on Hyperliquid's book, a manual
  close or a liquidation leaves no event here, and this connector can't see how a position
  closed. When the user asks why a position closed or whether "a stop" fired, say what the
  ratchet record shows and that other exits aren't visible from here.

## Follow-ups to offer

- "How did I trade?" → `get_wallet_closed_trades` with no address (senpi-improve-trades).
- A position's market → `read_asset_signal`.
- "My closed trades" one page at a time, per wallet → `get_wallet_closed_trades` with no address;
  "how has my equity moved" → `get_wallet_pnl_history` with no address (one series per wallet).
