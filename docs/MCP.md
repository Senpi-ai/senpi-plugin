# Senpi — AI Quant: MCP server reference

Setup, authentication, tool-by-tool inputs and classification, response format, errors and limits for Senpi's hosted MCP server. Generated from the server's tool registry as deployed in production.

> **Read-only by construction: 22 tools, all Read. No Write tools. No Sensitive writes.**
> No tool can place, change or cancel a trade order, deploy a strategy, move funds, or change settings. Every tool is registered with `readOnlyHint: true` and `destructiveHint: false`, and every response carries `meta.action_type: "read"`. Trading happens in the Senpi app at [senpi.ai](https://senpi.ai), never through this server.

## Connection

| | |
|---|---|
| Endpoint | `https://mcp.senpi.ai/mcp` — Streamable HTTP. Production environment. |
| Authentication | OAuth 2.0 authorization code with PKCE (`S256`). Public client: no client secret. No dynamic client registration. |
| Authorization server | `https://senpi-auth-service.prod.senpi.ai` |
| Authorize URL | `https://senpi-auth-service.prod.senpi.ai/oauth/authorize` |
| Token URL | `https://senpi-auth-service.prod.senpi.ai/oauth/token` |
| Revocation URL | `https://senpi-auth-service.prod.senpi.ai/oauth/revoke` |
| Scopes | `agent:read` (required for every tool) · `offline_access` (refresh token) |
| Resource metadata | `https://mcp.senpi.ai/.well-known/oauth-protected-resource/mcp`. An unauthenticated request gets `401` with `WWW-Authenticate: Bearer resource_metadata="…", scope="agent:read"`. |
| Revoking access | The user disconnects any connected app in one click at Senpi → Connectors; tokens stop working when revoked. |

## Permissions and data

- **Public-data tools** read Hyperliquid market data, Senpi's market signals and smart-money cohorts, and any public Hyperliquid wallet.
- **Account tools** — `get_my_portfolio`, `get_account_status`, `get_my_stop_events` — read only the signed-in user's own Senpi account. The wallet-history tools also read the user's own wallets when called with no address.
- **Catalog tools** read Senpi's published strategy template catalog.
- No tool changes data, account state or permissions, and none acts on the user's behalf.

## Tool classification

Every tool is **Read** and **not sensitive**, with no side effects.

| Tool | Title | Data | Class |
|---|---|---|---|
| [`get_market_pulse`](#get_market_pulse) | Market pulse | Public data | Read |
| [`scan_market_signals`](#scan_market_signals) | Scan market signals | Public data | Read |
| [`read_asset_signal`](#read_asset_signal) | Asset signal | Public data | Read |
| [`get_smart_money_positioning`](#get_smart_money_positioning) | Smart money positioning | Public data | Read |
| [`get_whale_moves`](#get_whale_moves) | Whale moves | Public data | Read |
| [`find_top_traders`](#find_top_traders) | Find top traders | Public data | Read |
| [`get_wallet_profile`](#get_wallet_profile) | Wallet profile | Public data | Read |
| [`browse_strategy_catalog`](#browse_strategy_catalog) | Browse the strategy catalog | Senpi catalog | Read |
| [`get_catalog_strategy`](#get_catalog_strategy) | Catalog strategy | Senpi catalog | Read |
| [`get_my_portfolio`](#get_my_portfolio) | My Senpi portfolio | Your account | Read |
| [`get_account_status`](#get_account_status) | My Senpi status | Your account | Read |
| [`get_wallet_closed_trades`](#get_wallet_closed_trades) | Wallet closed trades | Public data | Read |
| [`list_instruments`](#list_instruments) | Instruments | Public data | Read |
| [`get_asset_market_data`](#get_asset_market_data) | Asset market data | Public data | Read |
| [`get_funding`](#get_funding) | Funding | Public data | Read |
| [`get_leaderboard`](#get_leaderboard) | 4h leaderboard | Public data | Read |
| [`get_smart_money_flow`](#get_smart_money_flow) | Smart money flow | Public data | Read |
| [`get_my_stop_events`](#get_my_stop_events) | My stop events | Your account | Read |
| [`get_wallet_pnl_history`](#get_wallet_pnl_history) | Wallet P&L history | Public data | Read |
| [`get_wallet_analysis`](#get_wallet_analysis) | Wallet analysis (Quant Desk) | Public data | Read |
| [`get_wallet_positions`](#get_wallet_positions) | Wallet positions | Public data | Read |
| [`compare_wallets`](#compare_wallets) | Compare wallets (Quant Desk) | Public data | Read |

## Response format

Every tool returns the same envelope. Success:

```json
{
  "success": true,
  "data": { "…tool fields…": "…",
            "as_of": "2026-11-17T15:04:05.000Z",
            "disclosure": "Informational only, not financial advice." },
  "meta": { "tool": "get_market_pulse", "action_type": "read",
            "timestamp": "2026-11-17T15:04:05.000Z", "request_id": "…" }
}
```

Failure:

```json
{
  "success": false,
  "error": { "code": "INVALID_ARGUMENT", "message": "…", "retryable": false },
  "meta":  { "tool": "…", "action_type": "read", "timestamp": "…", "request_id": "…" }
}
```

- **Freshness:** every result carries `as_of`.
- **Partial results:** a source that could not be read is named in `sources_unavailable`; the rest of the result is still returned.
- **Size:** a result cut to fit the response budget carries `response_truncated: true` and names what was cut, with how many rows, in `response_omitted`.
- **Paging:** a result with `next_offset` has more; the same call with `offset` set to it returns the next page.

## Errors and status handling

| Code | Meaning | Retry |
|---|---|---|
| `INVALID_ARGUMENT` | An input is missing, malformed or out of range. | No |
| `NOT_FOUND` | The requested asset, wallet or strategy does not exist. | No |
| `UNAUTHENTICATED` | The call carried no connector token. The user reconnects Senpi. | No |
| `PERMISSION_DENIED` | The connection was not granted `agent:read`. The user reconnects to grant it. | No |
| `NOT_CONFIGURED` | A data source is not enabled on this deployment. | No |
| `UNAVAILABLE` | An upstream source is temporarily unavailable, or the read timed out. | Yes |
| `INTERNAL` | Unexpected error. | Yes |

A non-retryable error's message ends *"This error is deterministic. Do not retry with the same arguments."* Because no tool writes, retrying a read never duplicates an action.

## Limits

- **Per call:** 45-second timeout. A call that runs out returns `UNAVAILABLE`, retryable.
- **Response size:** 40 KB per result; past it the largest list is trimmed and flagged as above.
- **Quant Desk** (`get_wallet_analysis`, `get_wallet_positions`, `compare_wallets`): up to 5 fresh analyses per user at once, 4 running server-wide, 16 queued, 120 seconds per analysis. Past a bound, a fresh analysis is refused immediately and can be retried; cached analyses are still returned.
- **Upstream throttling:** Hyperliquid rate limits are absorbed by the server, which retries up to 6 times with at most a 20-second wait.
- The connector applies no other per-user request quota.

## Server instructions

Sent to the host at initialization, verbatim:

> Senpi's read-only research connector for Hyperliquid perpetuals, for a user signed in to Senpi. Market tools (pulse, signals, asset signal, smart-money positioning, whale moves, top traders) and the strategy catalog read public data. Account tools (portfolio, closed trades with no address, account status) read only the user's own Senpi account. Quant Desk tools read any Hyperliquid address from public data, or the user's own Senpi strategy wallets as one book. Nothing here trades, moves funds or changes settings. Every result carries as_of; a source that could not be read is named in sources_unavailable. A result cut to fit the response size carries response_truncated: true and names what was cut, with how many rows, in response_omitted. A result with a next_offset has more: the same call with offset set to it returns the next page. Results are informational only, not financial advice.

## Tool reference

### `get_market_pulse`

**Market pulse** · Read · not sensitive · no side effects · Public data

The market's day as data: every crypto perp and every builder-dex equity, index, commodity and FX instrument with its daily move (previous close to mark), grouped with each group's average; the cross-asset reads (gold, the dollar, VIX, dispersion) each with a label; the day's classification (risk_on, risk_off, mixed); the market-wide funding regime; and the biggest movers by size with volume, funding sign and open-interest trend. The 4h board is get_leaderboard and its momentum events get_whale_moves. Read-only public market data.

No inputs.

### `scan_market_signals`

**Scan market signals** · Read · not sensitive · no side effects · Public data

Every read of the Senpi detector sweep: funding extremes, open-interest spikes, momentum and flow anomalies, each with an asset, a type and a strength; rows from the trade feed come first, then the news feed, each in its own order and each with its own strength (trade score; social score for news); not_measured names the sources the sweep couldn't read: a source not measured is not one that found nothing. Optional signal_type filter and limit (omit it for the whole sweep). Read-only public market data.

| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Maximum signals to return. Omit for every read of the sweep (the feed holds at most a dozen). — range 1–100 |
| `signal_type` | string | Only signals of this type (as returned in each signal’s type field). Omit for all types. |

### `read_asset_signal`

**Asset signal** · Read · not sensitive · no side effects · Public data

One asset's Senpi Signals card: its summary, its signals (each with type, strength and the read behind it), whether it is in the signals universe and what was not measured, with the card's as_of and stale flag — the one-asset counterpart of scan_market_signals. Takes one asset symbol such as BTC or xyz:GOLD. Its market data is get_asset_market_data, the cohorts' positioning get_smart_money_positioning, the 4h board get_leaderboard. Read-only public market data.

| Parameter | Type | Description |
|---|---|---|
| `asset` **required** | string | Asset symbol (uppercase like BTC, ETH; prefixed like xyz:GOLD for HIP-3 assets). |

### `get_smart_money_positioning`

**Smart money positioning** · Read · not sensitive · no side effects · Public data

Where smart money leans: the proven cohort Senpi Signals' cards count (the refresher's last good read of every >= $1M wallet, holders of at least $1,000; smart_cohort names the source and its as_of, and falls back to the tool's own ranking sample, saying so, when that read is unavailable) against a crowd sample ($10k..$100k), each coin's net bias (net/gross, -1..+1) with member counts; smart_leaning lists the coins where at least 5 proven traders lean past 0.40, divergences where the two cohorts sit on opposite sides or 0.50 apart. With an asset, both cohorts' read on that one coin with the 20 largest member positions and positions_total. Cached two minutes (computed_at). Read-only public data about public wallets.

| Parameter | Type | Description |
|---|---|---|
| `asset` | string | Only positions in this asset (BTC, xyz:GOLD). Omit for the whole book of the cohort. |

### `get_whale_moves`

**Whale moves** · Read · not sensitive · no side effects · Public data

The 4h board's momentum events (tier crossings by top traders), one per trader — its newest, preferring one that names its positions — newest first, up to 8 (truncated says more traders moved; traders counts them, events_read the events behind). Each move: trader_id, tier_label, delta_pnl, top_positions, detected_at. These are 4h P&L tier crossings, not position opens or closes. Optional asset and window in hours (default 4, the board's window; max 168). The read holds the newest 200 events: when read_cut_at_limit is true the moves cover only back to oldest_event_read, not the whole window (events_in_window is the board's count). Unavailable, not empty, when the board is down. Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `asset` | string | Only moves in this asset (BTC, xyz:GOLD). Omit for all assets. |
| `window_hours` | integer | How far back to look, in hours (default 4, the board's window; max 168). — default `4`; range 1–168 |

### `find_top_traders`

**Find top traders** · Read · not sensitive · no side effects · Public data

Ranked public Hyperliquid perp traders over a time window (default monthly) with sort options (ROI by default; PnL, win rate, drawdown and more) and a limit (default 20, max 1000) — or, with size_band, candidates by Hyperliquid account value (5k-10k, 10k-25k, 25k-100k, 100k-1m, whales) that actually trade (window volume of at least $250k), the most profitable over the window first, or the worst with losers; each with account value, PnL, ROI, volume and turnover. A null max drawdown or ROI means not computed, never zero; generated_at is the ranking's time. With shortlist, a copyability ranking instead: the 7-day ROI, 30-day ROI and 30-day realized PnL rankings blended by address (seen_in names each ranking and rank; one ranking when window or sort_by is given), the top 20 of the pool read for their current book and ordered for copyability: no blowup risk first, then mirrorable now (good and partial alike), the fewest flags (high turnover and critical margin weigh most), reliability, the rankings seen in, the consistency score. Each row has the track record (roi_pct, pnl_usd and win_rate_pct from the first ranking it is seen in), reliability, mirrorability (the share of the book a mirror would open now: positions within 5% of the trader's entry on the side slippage is gated on, as a fit of good, partial, poor or unknown), book, min_mirror_budget (a rough margin floor to open that book at Hyperliquid's $12 position minimum, never below $10), net_exposure, momentum from the 4h board (the top 10; unknown below them) and flags; pool counts the blended traders and enriched the rows read. A book that could not be read is unknown, never flat. A ranking, the books or the momentum that could not be read is named in sources_unavailable (ranking:7d_hot, ranking:30d_return, ranking:30d_realized, trader_states, momentum:<address>): the blend lacks that view, or those rows' fit or momentum is unknown. Flags: thin_track_record (under 5 closed trades or 7 active days), choppy_consistency, blowup_risk (max drawdown at or below -83%), roi_pnl_conflict (positive ROI, negative PnL), high_turnover (over 8 trades a day), infrequent_trader (under 0.2), dormant (no trade in over 30 days), critical_margin_usage (over 90%) or high_margin_usage (over 80%), currently_in_drawdown (net unrealized loss), concentrated_book (one position over 60% of the notional), single_position, no_open_positions (a read, empty book). Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Maximum traders to return (default 20, max 1000; max 50 with size_band). — default `20`; range 1–1000 |
| `losers` | boolean | With size_band: the least profitable first, often the instructive read. — default `false` |
| `shortlist` | boolean | Rank for copyability instead: three rankings blended (7-day ROI, 30-day ROI, 30-day realized PnL; one ranking when window or sort_by is given), the top 20 read for their current book and ordered by how much of it a mirror could open now, with flags; limit is per ranking. Not with size_band. — default `false` |
| `size_band` | string | Candidates by Hyperliquid account value instead of Senpi's ranking: accounts in this size bracket that actually trade (window volume of at least $250k), the most profitable over the window first — the read behind the Quant Desk's find. — one of: `5k-10k`, `10k-25k`, `25k-100k`, `100k-1m`, `whales` |
| `sort_by` | string | Ranking metric (ignored with size_band: that ranks by P&L within the band). — one of: `roi`, `return_on_investment`, `pnl`, `profit_and_loss`, `realized_pnl`, `unrealized_pnl`, `win_rate`, `max_drawdown`, `gain_to_pain`, `trader_age`; default `"roi"` |
| `window` | string | Ranking window (with size_band: weekly, monthly or all_time). — one of: `daily`, `weekly`, `monthly`, `all_time`; default `"monthly"` |

### `get_wallet_profile`

**Wallet profile** · Read · not sensitive · no side effects · Public data

Who a Hyperliquid wallet is, for 1 to 5 addresses: Senpi's ranking row over the window (default all_time: the whole record, as a vet reads it) with its track-record stats and trader labels, and the closed-trade count; found says whether Senpi knows the wallet. With vet, each wallet also carries the copyability read of its current book: reliability (solid, ok, choppy, thin, or unknown when Senpi has no row), book (open positions, longs, shorts, net bias, top assets), mirrorability (the share of the book's notional within 5% of the trader's entry on the side a mirror's slippage is gated on, and a fit of good, partial, poor or unknown), min_mirror_budget (a rough margin floor to open that book at Hyperliquid's $12 position minimum, never below $10; null when nothing would open), net_exposure, momentum (hot, cold, flat or unknown from the 4h board) and flags. A book that could not be read is unknown with a null book, never flat. Flags: thin_track_record (under 5 closed trades or 7 active days), choppy_consistency, blowup_risk (max drawdown at or below -83%), roi_pnl_conflict (positive ROI, negative PnL), high_turnover (over 8 trades a day), infrequent_trader (under 0.2), dormant (no trade in over 30 days), critical_margin_usage (over 90%) or high_margin_usage (over 80%), currently_in_drawdown (net unrealized loss), concentrated_book (one position over 60% of the notional), single_position, no_open_positions (a read, empty book). A read that fails is named in sources_unavailable; the rest stands. Its live book is get_wallet_positions, its trades get_wallet_closed_trades, its 4h momentum get_leaderboard, and a scored comparison compare_wallets. Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `addresses` **required** | array of string | 1 to 5 Hyperliquid wallet addresses. — up to 5 items |
| `vet` | boolean | Also read each wallet's current book for copyability: reliability, book summary, mirrorability, the minimum budget to mirror it, net exposure, 4h momentum and flags. — default `false` |
| `window` | string | Track-record window (default all_time: the whole record, as a vet reads it). — one of: `daily`, `weekly`, `monthly`, `all_time`; default `"all_time"` |

### `browse_strategy_catalog`

**Browse the strategy catalog** · Read · not sensitive · no side effects · Senpi catalog

Senpi's public strategy catalog as cards, one per variant family (a card lists its variants), in alphabetical order or ranked by a plain-words goal (weighted over each strategy's tags, asset classes, tagline, name, archetype and thesis; a risk word or a horizon word like intraday-horizon counts most), with risk level, direction, horizon, leverage cap, minimum budget and up to 4 declared assets (none for a strategy that scans the whole universe). assets (tickers or classes), direction (long drops short-only strategies, short the reverse) and exclude (copy_trading, crypto, equities, dca, shorting) narrow the catalog: a named ticker keeps the strategies that trade it and the configurable ones that take any coin, and when none is left it widens once to the ticker's class and keeps only strategies that trade that class (widened lists the classes, otherwise null; an xyz: ticker widens to the xyz classes). Each card carries asset_match (0 to 2: how many of the stated assets it covers; it orders ties) and caveats (plain notes: a configurable strategy, extra alts, a short side, a split across wallets, a minimum budget above budget_usd, which never filters). unmet lists the constraints that left nothing; warnings, a ticker no strategy declares. matching counts the strategies that passed the filters. limit defaults to 8; raise it when the user asks to see more or the whole catalog (truncated says when more exist; next_offset pages through the rest). Read live from senpi-skills' catalog (reread every 15 minutes; catalog_as_of and catalog_stale say how fresh). Read-only catalog data; nothing is deployed or funded.

| Parameter | Type | Description |
|---|---|---|
| `assets` | array of string | Assets the user wants to trade: tickers (SOL, DOGE, xyz:NVDA) or a class (btc_eth, major_alts, universe_crypto, xyz_equities, commodities, fx, indices, pre_ipo; words like btc, stocks, gold or forex map to one). Keeps strategies that trade the named ticker, or any coin for a configurable one; a ticker no strategy trades widens to its class. — up to 20 items |
| `budget_usd` | number | What the user has to put in, in USD. Never filters: a strategy whose minimum budget is above it carries a caveat. |
| `direction` | string | long drops short-only strategies, short drops long-only ones (default any). — one of: `long`, `short`, `any` |
| `exclude` | array of string (copy_trading, crypto, equities, dca, shorting) | Kinds to leave out: copy_trading, crypto, equities, dca, shorting (no strategy that can short). |
| `goal` | string | What the user wants from a strategy, in plain words (max 300 chars). Used to rank matches. |
| `limit` | integer | Maximum cards to return (default 8). Raise it when the user asks to see more or the whole catalog; truncated says when more exist. — default `8`; range 1–500 |
| `offset` | integer | Paging: start at this card (next_offset from the previous page). A page holds what fits the response; next_offset is null on the last page. — default `0`; range 0– |
| `risk` | string | Only strategies with this declared risk level. — one of: `conservative`, `moderate`, `aggressive` |

### `get_catalog_strategy`

**Catalog strategy** · Read · not sensitive · no side effects · Senpi catalog

One catalog strategy in detail: entry logic, markets, sizing and risk limits. Live performance is not part of the catalog. Takes strategy_id from browse_strategy_catalog. Read-only catalog data.

| Parameter | Type | Description |
|---|---|---|
| `strategy_id` **required** | string | Catalog id from browse_strategy_catalog (for example "athena"). |

### `get_my_portfolio`

**My Senpi portfolio** · Read · not sensitive · no side effects · Your account

The signed-in user's own Senpi account: balances, open positions and running strategies, and wallets — the saved read-only wallets and Senpi strategy wallets, one list ordered by Hyperliquid account value, each usable as the address of the wallet tools. Strategy wallets holding $0 are counted in empty_wallets, not listed. The wallets come a page at a time: next_offset pages the rest, null on the last page. money: three separate pools that never mix — the main wallet's idle cash (main_wallet.idle_usd: Hyperliquid perps and spot USDC and EVM stablecoins), idle_in_strategies_usd (free margin inside strategy wallets, not in a position) and deployed_in_positions_usd — grand_total_usd, and reconciles against the account total (null when a strategy wallet could not be read: strategy_wallets_unread). strategy_groups: one entry per strategy, which is all its wallets (grouped by the package it was created from; name_source says whether name is the strategy's own name or, for an unnamed one, its package; kind is mirror, a copy-trade of copied_trader with no runtime or mandate of its own, or custom): totals, each wallet's balance and positions, flat_wallets (the wallets with nothing open: waiting, not idle money), closed_record over each wallet's last 50 closes (record, newest close, hours since it; the five newest with entry and exit price) and mandate (the catalog template's declared job; null for a strategy not made from one). quiet_strategies: a funded strategy whose newest close is 48 hours old or more. Whether a strategy's runtime is running or why it has not traded lives on the user's own machine and is not here. Read-only.

| Parameter | Type | Description |
|---|---|---|
| `offset` | integer | Paging the wallets list: start at this wallet (next_offset from the previous page); next_offset is null on the last page. — default `0`; range 0– |

### `get_account_status`

**My Senpi status** · Read · not sensitive · no side effects · Your account

The signed-in user's standing across Senpi: current plan and renewal date, remaining AI credits for the cycle, Senpi points with rank, the Senpi trading fee as the backend reports it, and unclaimed referral earnings. Sources that cannot be read are named in sources_unavailable. Read-only.

No inputs.

### `get_wallet_closed_trades`

**Wallet closed trades** · Read · not sensitive · no side effects · Public data

Closed Hyperliquid trades, newest first: each with coin, side, entry and exit price, size, leverage, open and close time, realized PnL (gross, before fees), fees, net PnL (after fees; funding is not included) and whether it was a liquidation. With an address (public data): one page per call (up to 200) over a window in days (default 30, max 365) or the last N, an optional coin and an offset, with the page's totals and paging (total_count, has_more, next_offset). With no address: the signed-in user's whole book — every Senpi strategy wallet (active, paused and closed), every saved wallet and the Senpi main wallet — each paged to the window start, with totals over every trade in the window (count; gross PnL, fees and net PnL after fees; wins, losses and win rate on net; the largest wins and losses by net), the trades a page at a time (each page holds what fits; next_offset pages the rest from the same read), and truncated_wallets for any wallet whose closes ran past the 2,000 read. wallets lists the wallets with a trade in the window or a failed or cut read; wallets_read counts every wallet read and wallets_without_trades the quiet ones. A wallet whose history could not be read is named (wallets_omitted), never counted as $0. review: true adds, on each trade, exit — from the trade's Senpi ratchet-stop record on the user's own strategy wallets: terminal SL_TRIGGERED (with tier_number and high_water_roe), CLOSED_OFF_LADDER (the position went away by another route: the runtime, the agent or the user, never "you closed it"), LIQUIDATED, ADL, UNKNOWN (no record: the mechanism is not known) or NOT_A_STRATEGY_WALLET — and if_held (the dollars holding from the exit to now would have added or given back: context, never a grade); and review.timing (exits_ahead, exits_held_higher, if_all_held_to_now_usd, by asset class), review.exit_mix (closes by terminal overall, by asset class and by strategy, and the premature exits: a tier 1 or 2 lock on a high-water ROE of 5% or less) and review.book_vs_market (the 4h board's 12 biggest movers, which of them the book traded and on which side, and the gaps). The review is of the Senpi-managed wallets: review.senpi_totals are their totals, and a saved wallet's closes (traded by hand) are counted apart in review.saved_wallets and review.scope, never in the timing or the exit mix. Each wallet listed also carries its own wins, losses, gross, fees and net over the window. The close reason a strategy's runtime records, blocked signals and failed orders live on the user's machine and are not here. Read-only.

| Parameter | Type | Description |
|---|---|---|
| `address` | string | A Hyperliquid wallet address (public data). Omit for the signed-in user's own wallets. — pattern `^0x[a-fA-F0-9]{40}$` |
| `coin` | string | Only trades in this coin (BTC, xyz:GOLD). |
| `last` | integer | Only the N most recent closed trades ("the last 20 trades"), whatever the window; also the page size (default 50, max 200), with offset for the next page. — range 1–200 |
| `offset` | integer | Paging: skip this many newest trades (next_offset from the previous page). — default `0`; range 0– |
| `review` | boolean | Add the trade review: each trade's exit (from its Senpi ratchet record, own book only) and its hold-to-now counterfactual, plus review.timing, review.exit_mix and review.book_vs_market over every trade in hand. — default `false` |
| `window_days` | integer | How many days back (default 30, max 365). — default `30`; range 1–365 |

### `list_instruments`

**Instruments** · Read · not sensitive · no side effects · Public data

Hyperliquid's instruments as reference data: exact name and casing (xyz:GOLD for a builder dex), dex, size decimals, maximum leverage, isolated-only and delisted flags. Optional query (substring, case-insensitive), dex, include_delisted and limit; total_matched and truncated report the cut. Specs only — prices and funding are get_asset_market_data's. Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `dex` | string | Only this dex: "main" or a builder dex such as xyz. Omit for every dex. |
| `include_delisted` | boolean | false drops delisted instruments. — default `true` |
| `limit` | integer | Maximum rows (default 50, max 500); total_matched and truncated report the cut. — default `50`; range 1–500 |
| `query` | string | Only names containing this, case-insensitive, with or without the dex prefix (btc, gold, xyz:gol). |

### `get_asset_market_data`

**Asset market data** · Read · not sensitive · no side effects · Public data

One asset's price history and depth: the live context (mark, previous day's close and the daily move, hourly funding and its annualized rate, open interest, day volume), candles for the intervals asked (each over its own lookback: 1m 2h, 15m 1d, 1h 7d, 4h 30d, 1d 90d; candle_limit keeps the newest N), the order book (20 levels a side) when include_book is true, and the open-interest velocity read where the service has one. Takes one asset symbol such as BTC or xyz:GOLD. Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `asset` **required** | string | Asset symbol (uppercase like BTC, ETH; prefixed like xyz:GOLD for a builder dex). |
| `candle_limit` | integer | Keep only the newest N candles of each interval (max 180). Omit for the whole lookback. — range 1–180 |
| `include_book` | boolean | Include the order book, 20 levels a side. — default `false` |
| `intervals` | array of string (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d, 3d, 1w, 1M) | Candle intervals to read, each over its own lookback (default ["1h"]; [] for no candles). — up to 14 items |

### `get_funding`

**Funding** · Read · not sensitive · no side effects · Public data

Funding for one asset or the whole market: with an asset, its hourly funding rate over the last 7 days and its annualized extremes and persistence as the service measures them; without one, every asset whose funding clears min_annualized_pct (default 20%) for at least min_persistence_hours. Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `asset` | string | One asset (BTC, xyz:GOLD): its hourly rates over 7 days and its extremes. Omit for the market-wide extremes. |
| `include_history` | boolean | true keeps each extreme's 24-hour hourly history (funding_history_24h); off by default, the persistence fields carry the read. — default `false` |
| `limit` | integer | Extremes to return, the largest absolute annualized rate first (default 20, max 100); assets_total says how many qualified. — default `20`; range 1–100 |
| `min_annualized_pct` | number | Minimum absolute annualized funding rate to count as extreme (default 20). — default `20`; range 0– |
| `min_persistence_hours` | number | Minimum hours the extreme has held in one direction (default 0). — default `0`; range 0– |

### `get_leaderboard`

**4h leaderboard** · Read · not sensitive · no side effects · Public data

The 4h board: the ranking of the top traders by unrealized gain in the window (limit, default 20) and where their gains concentrate by coin; with a trader, that wallet's row and the positions behind its gain. concentration.movers: up to 5 markets climbing the board right now (rank past 10, at least 10 traders, a rising 15-minute share, the 4h price agreeing with the side). concentration.rotations: markets that just jumped the board, scored with Penguin's rotation scorer against an earlier read (score, reasons, rank_jump, prev_rank); concentration.rotation_baseline says how old that read is: band LIVE (<= 5 min), WIDE (<= 30 min, a longer window than Penguin's), or NONE, TOOFRESH or STALE (not scored: no rotations, never "none jumped"; a read a couple of minutes later scores them). UNAVAILABLE when the board is down, never an empty ranking. Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `concentration_limit` | integer | Concentration rows, the most crowded first (default 20, max 100); rows_total says how many there are. — default `20`; range 1–100 |
| `limit` | integer | Ranking rows (default 20, max 100). — default `20`; range 1–100 |
| `trader` | string | With a wallet: its row on the board and the positions behind its gain. — pattern `^0x[a-fA-F0-9]{40}$` |

### `get_smart_money_flow`

**Smart money flow** · Read · not sensitive · no side effects · Public data

What the smart-money cohorts did, not where they sit: positions opened, added to, trimmed, closed and flipped over a window (latest, 1h, 4h, 24h), per asset and cohort (proven, crowd, apex, whale), with the net flow in USD and the divergences between cohorts, from Senpi's position snapshots; include_events adds the newest wallet moves of $10k or more behind it (at most 50: events_cut_at_limit says they are a sample of the window, not all of it). age_s says how old the read is. For where the cohorts sit now, use get_smart_money_positioning. Read-only public data.

| Parameter | Type | Description |
|---|---|---|
| `asset` | string | Only this asset (BTC, xyz:GOLD). Omit for every asset. |
| `cohort` | string | Only this cohort. Omit for every cohort. — one of: `proven`, `crowd`, `apex`, `whale`, `all` |
| `include_events` | boolean | Also return the newest wallet moves of $10k or more in the same window, asset and cohort. — default `false` |
| `limit` | integer | Markets to return (default 20, max 50). — default `20`; range 1–50 |
| `window` | string | The window the changes are summed over (default 1h); latest is the last snapshot interval only. — one of: `latest`, `1h`, `4h`, `24h`; default `"1h"` |

### `get_my_stop_events`

**My stop events** · Read · not sensitive · no side effects · Your account

The signed-in user's Senpi ratchet-stop timeline: each event (a tier trigger, a lock move, an arm or a stop) with its strategy, wallet, asset, type, details and time, newest first, across the account's strategies or one strategy_id, optionally since a time. Each strategy also carries by_type, the count of every event read for it by type (every event, past dsl-engine's 100 a read; capped marks a strategy with more than 2,000, whose count is then a floor), and total_events counts them all. Events come a page at a time, newest first: next_offset pages the rest, null on the last page. A strategy closed before since is left out and counted (strategies_closed_before_since). A strategy whose events could not be read is named, not empty. Read-only.

| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Most events in one page, newest first across the strategies (default 100, max 500); a page holds what fits the response. — default `100`; range 1–500 |
| `offset` | integer | Paging: start at this event (next_offset from the previous page); next_offset is null on the last page. — default `0`; range 0– |
| `since` | string | ISO 8601 time; only events at or after it. |
| `strategy_id` | string | Only this strategy's events. Omit for every strategy of the account. |

### `get_wallet_pnl_history`

**Wallet P&L history** · Read · not sensitive · no side effects · Public data

A Hyperliquid wallet's P&L and account-value series over a window (7 to 90 days, default 30), its net flows per interval (deposits, withdrawals and transfers netted, from Hyperliquid's own series), and its drawdown — on a unified or portfolio-margin account measured against the whole account's value, not the perps-only series. account_value and equity are Hyperliquid's own series, what the account held; equity_ex_flows (and its summary) is that series less the window's net flows, the return base, and return_on_avg_equity is the ledger's net P&L over its average. Takes an address (public data); omit it for the signed-in user's own wallets, one series each, a page at a time (next_offset pages the rest, null on the last page); wallets_omitted names any of them not read, and strategies_closed_before_window counts those that closed before the window. Read-only.

| Parameter | Type | Description |
|---|---|---|
| `address` | string | A Hyperliquid wallet address (public data). Omit for the signed-in user's own wallets. — pattern `^0x[a-fA-F0-9]{40}$` |
| `offset` | integer | Paging the signed-in user's own wallets: start at this wallet (next_offset from the previous page); next_offset is null on the last page. — default `0`; range 0– |
| `window_days` | integer | The window in days (7 to 90, default 30). — default `30`; range 7–90 |

### `get_wallet_analysis`

**Wallet analysis (Quant Desk)** · Read · not sensitive · no side effects · Public data

The Quant Desk as data, for a Hyperliquid wallet (an address, public data; addresses, two to ten wallets read together as one combined book, subject.kind combined_book, subject.mine true when any of the user's own wallets (strategy, saved or main) is among them, false otherwise, null when the account could not be read; or none for the signed-in user's own strategy wallets as one book) over a window of 7 to 90 days: one cached analysis, the parts asked for. overview (0–100 quant score on six dimensions with the measurements behind each as numbers, the archetype and the verdict as facts, flags, track record, equity and drawdown, rank, Senpi's labels, the book's summary) and leaks (the P&L waterfall and the leaks as kind, dollars and measures, costs, timing) by default. What the wallet holds is book_summary.account_value (the whole account when the portfolio is readable, else the perps clearinghouse value, account_value_perps); equity.start/end/avg are the return base — the account's value series less the window's net flows — not what it holds; rank.leaderboard_account_value is the stats leaderboard's lagging snapshot; performance (per-coin, long/short, holds, execution), strategy (what the book does, its fingerprint), context (today's market, the funding regime, the record by regime), smart (positions against the cohorts), market (each open position's fit), edge (best and worst setups, the measured rules), scout (live matches), replay (the worst 7-day window), funding (the next 30 days at today's rates) and windows (the last 30 days against the 60 before) on request; "all" is every part but replay. No sentences: the words are the skill's; present the fields. A heavy wallet takes up to two minutes the first time and answers from cache after. Read-only.

| Parameter | Type | Description |
|---|---|---|
| `address` | string | A Hyperliquid wallet address (public data). Omit to read the user's own Senpi book (every strategy wallet as one desk). — pattern `^0x[a-fA-F0-9]{40}$` |
| `addresses` | array of string | Two to ten Hyperliquid wallet addresses read together as one combined book. Not with address. — up to 10 items |
| `include` | array of string (overview, leaks, performance, strategy, context, smart, market, edge, scout, replay, funding, windows, all) | Which parts of the analysis to return (default ["overview", "leaks"]; "all" is every part but replay, which reads hourly candles). Every part is the full view; the list only trims the response. |
| `window_days` | integer | Analysis window in days (default 90, 7 to 90). — default `90`; range 7–90 |

### `get_wallet_positions`

**Wallet positions** · Read · not sensitive · no side effects · Public data

A Hyperliquid wallet's live book as data, read from the clearinghouse and the order book (never fills, so it answers in seconds): each open position with entry, mark, size, leverage, notional, unrealized P&L, margin used, liquidation price and distance, the coin's average daily range (daily_range_pct), margin at risk, and its protection — resting reduce-only stops on Hyperliquid (full, partial or none), Senpi's own stops on the signed-in user's strategy wallets — with a status per position (PROTECTED, PARTIAL, UNPROTECTED, or UNKNOWN when orders or Senpi stops could not be read, never UNPROTECTED by default) and the book's: account_value, margin utilization and withdrawable for the whole account when the portfolio is readable (account_value_basis whole_account; account_value_perps beside it), else the perps clearinghouse alone (basis perps) — the same figures get_wallet_analysis's book_summary carries; spot_balances, the wallet's non-zero Hyperliquid spot holdings (token, total, the part on hold, cost), and spot_value_usd, the whole account's value less its perps value (both null when spot or the portfolio was not read). Takes an address (public data), addresses (two to ten wallets as one combined book, subject.kind combined_book) or none for the signed-in user's own book. Wallets with nothing open are summed in flat_wallets (count and account value), not listed; the rest come largest first, a page at a time: next_offset pages the rest, null on the last page. Read-only.

| Parameter | Type | Description |
|---|---|---|
| `address` | string | A Hyperliquid wallet address (public data). Omit to read the user's own Senpi book (every strategy wallet as one desk). — pattern `^0x[a-fA-F0-9]{40}$` |
| `addresses` | array of string | Two to ten Hyperliquid wallet addresses read together as one combined book. Not with address. — up to 10 items |
| `offset` | integer | Paging the wallets list: start at this wallet (next_offset from the previous page); next_offset is null on the last page. — default `0`; range 0– |

### `compare_wallets`

**Compare wallets (Quant Desk)** · Read · not sensitive · no side effects · Public data

Two to five Hyperliquid wallets side by side, each run through the Quant Desk over the window (default 90 days): per wallet the hook (quant score, archetype and verdict as facts, rank with the stats leaderboard's leaderboard_account_value — a lagging snapshot, not the live book — equity as the return base (the value series less the window's net flows, not what the wallet holds), drawdown, track: ledger net, trades, win rate, profit factor, taker share, cost ratio), and separation — each metric's value per wallet, which wallet is best and worst at it, and the spread. No rendered text. Public data; a wallet not analysed before takes up to a minute, and one still running at the call's deadline is marked pending for a second call. Read-only.

| Parameter | Type | Description |
|---|---|---|
| `addresses` **required** | array of string | Two to five Hyperliquid wallet addresses to put side by side (public data). — up to 5 items |
| `window_days` | integer | Analysis window in days (default 90, 7 to 90). — default `90`; range 7–90 |

---

*Informational only, not financial advice. © Senpi Inc.*
