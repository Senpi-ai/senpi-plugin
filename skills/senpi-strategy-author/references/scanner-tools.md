# Tools a scanner can call

These run on the user's Senpi agent, called from `scan()` as
`ctx.senpi_mcp.call_tool(name, args)`. They are **not** the tools you have in this conversation:
the names, arguments and answers differ. You cannot call them from here to look at an answer, so
use only what this page lists. A tool, argument or key that is not here is a guess, and a guess
runs cleanly and trades nothing.

## The answer envelope

Every tool answers:

```json
{ "success": true, "data": { ... }, "meta": { "tool": "...", "timestamp": "..." } }
```

Read `data` with a fallback, and check types first:

```python
resp = ctx.senpi_mcp.call_tool(name, args)
if not isinstance(resp, dict):
    return []                      # or skip this read
data = resp.get("data", resp)
```

Numbers in market and account answers are usually **strings** (`"62469.0"`). Read them through
`_f()` (see [scanner-contract.md](scanner-contract.md)). Times named `t`, `T` and `time` are epoch
milliseconds; `timestamp` at the top of `data`, `startTime` and `lastTradeTimestamp` are epoch
seconds.

## Market data

### `market_get_asset_data`

One asset: candles, live context, open-interest change.

| Argument | Type | Notes |
|---|---|---|
| `asset` | string, required | exact name: `BTC`, `xyz:SP500` |
| `candle_intervals` | list | from `1m` `3m` `5m` `15m` `30m` `1h` `2h` `4h` `8h` `12h` `1d` `3d` `1w` `1M`; default `["1h"]`; `[]` for none |
| `candle_limit` | integer | newest N candles per interval, at most 180 |
| `include_funding` | bool | default true; set false unless you read funding |
| `include_order_book` | bool | default true; set false unless you read the book |
| `dex` | string | inferred from the `xyz:` prefix; leave it out |

Answer, under `data`:

- `candles`: map from interval to a list, oldest first, of
  `{t, T, s, i, o, h, l, c, v, n}`: open time, close time (ms), symbol, interval, open, high, low,
  close, volume, trade count. The close is `c`; there is no `close` key.
- `asset_context`: `markPx`, `midPx`, `oraclePx`, `prevDayPx`, `funding` (hourly rate),
  `openInterest` (in coins), `dayNtlVlm` (24h volume, USD), `dayBaseVlm`, `premium`, `impactPxs`.
- `oi_velocity`: `current_oi`, `oi_change_pct_5m`, `oi_change_pct_15m`, `oi_change_pct_1h`,
  `oi_change_pct_4h`, `oi_trend`, `oi_acceleration`. It can be `null`; treat that as unknown, not
  flat.
- `asset`, `max_leverage`, `only_isolated`, `margin_modes`, `margin_mode`.

A candle has closed when `_f(c["t"]) / 1000 + candle_seconds <= time.time()` (`4h` is 14400). A
series can come back shorter than asked: check `len()`.

### `market_list_instruments`

Every tradeable perp, with live context. The source of exact names.

| Argument | Type | Notes |
|---|---|---|
| `fields` | list | from `name` `sz_decimals` `max_leverage` `is_delisted` `only_isolated` `margin_modes` `margin_mode` `context`; pass only what you read |
| `include_delisted` | bool | pass `false` |
| `limit` | integer | 1-500 |
| `query` | string | names containing it, e.g. `btc`, `xyz:` |
| `dex` | string | empty for the main and `xyz` lists together |

Answer: `data.instruments`, a list of rows with `name` and the fields asked for. `context` holds
the same keys as `asset_context` above, as strings. Also `data.count`, `data.total_matched`,
`data.truncated`. There is no `row["volume"]`: 24h volume is `row["context"]["dayNtlVlm"]`, and
open interest in USD is `openInterest × markPx`.

### `market_get_prices`

| Argument | Type | Notes |
|---|---|---|
| `assets` | list of strings | leave out for all |
| `dex` | string | `xyz` for the `xyz:` list |

Answer: `data.prices`, a map from name to mid price as a string; `data.count`.

### `market_get_funding_history`

Funding extremes and how long they have lasted.

| Argument | Type | Notes |
|---|---|---|
| `asset` | string | one asset; leave out for every asset with extreme funding |
| `min_annualized_pct` | number | default 20; ignored when `asset` is given |
| `min_persistence_hours` | number | default 0 |

Answer: `data.data`, a list of rows: `asset`, `current_funding_1h` (hourly rate),
`funding_annualized_pct`, `funding_direction` (the side that **collects**: `LONG` when the rate is
negative), `persistence_hours`, `persistence_started_at`, `funding_trend` (`INTENSIFYING`,
`STABLE`, `DECAYING`), `funding_history_24h` (list of `{timestamp, rate_1h}`). Note the list is at
`data["data"]`, not `data` itself.

### `market_get_funding_regime`

No arguments (`{}`). Answer under `data`: `regime` (`LONG_CROWDED`, `SHORT_CROWDED` or `NEUTRAL`;
`LONG_CROWDED` means longs pay), `long_funding_assets`, `short_funding_assets`,
`avg_funding_annualized`, `extreme_funding_count`, `regime_duration_hours`, `timestamp`.

### `market_get_cross_asset_flows`

| Argument | Type | Notes |
|---|---|---|
| `leader_asset` | string | default `BTC` |
| `min_move_pct` | number | default 2 |
| `window` | string | default `"4h"` |

Answer under `data`: `leader` with `asset`, `move_pct`, `direction`, `move_started_at`,
`sm_aligned`; `laggards`, a list that is empty until the leader moves enough; `timestamp`. The
keys of a laggard row are not listed here: do not read them.

## The 4-hour board

The board ranks whoever gained most in the last four hours. It is momentum, not smart money: the
traders at the top are there because the move already happened. Say "4h leaders" in every text the
user reads, never "smart money".

### `leaderboard_get_markets`

| Argument | Type | Notes |
|---|---|---|
| `limit` | number | top traders to aggregate, 1-500, default 100 |

Answer: `data.markets.markets`, a list of rows: `token`, `dex`, `direction` (**lower case**:
`long`, `short`), `max_leverage`, `pct_of_top_traders_gain`, `contribution_pct_change_15m`,
`contribution_pct_change_1h`, `contribution_pct_change_4h`, `token_price_change_pct_15m`,
`token_price_change_pct_1h`, `token_price_change_pct_4h`, `day_notional_volume`, `trader_count`,
`is_dominant_direction`. A token can appear once per side. Also `data.markets.source_trader_count`,
`window`, `timestamp`. These numbers are already numbers.

### `leaderboard_get_top`

| Argument | Type | Notes |
|---|---|---|
| `limit` | number | 1-500, default 20; no paging |

Answer: `data.leaderboard.data`, a list of rows: `rank`, `trader_id` (the address),
`unrealized_pnl`, `pnl_percentage`, `ath_delta`, `top_markets`, `trader_tags`. Also
`data.leaderboard.window`, `data.leaderboard.total_traders`.

## Proven traders

### `discovery_get_top_traders`

Ranked by track record over a window.

| Argument | Type | Notes |
|---|---|---|
| `time_frame` | string, required | `DAILY` `WEEKLY` `MONTHLY` `ALL_TIME` |
| `limit` | integer | 1-1000, default 20 |
| `offset` | integer | paging |
| `sort_by` | string | `RETURN_ON_INVESTMENT` (default) `PROFIT_AND_LOSS` `PROFIT_AND_LOSS_REALIZED` `PROFIT_AND_LOSS_UNREALIZED` `WIN_RATE` `MAX_DRAWDOWN` `GAIN_TO_PAIN_RATIO` `TRADER_AGE` |
| `bias` | string | `LONG` `SHORT` `ALL` |
| `consistency` | list | `ELITE` `RELIABLE` `STREAKY` `CHOPPY` |
| `activity_labels` | list | `DEGEN` `ACTIVE` `TACTICAL` `PATIENT` |
| `risk_labels` | list | `CONSERVATIVE` `BALANCED` `AGGRESSIVE` `SNIPER` |
| `open_position_filter` | bool | only traders with an open position |
| `addresses` | list | up to 100 |

Answer: `data.traders`, a list of rows: `address`, `returnOnInvestment`, `profitAndLoss`,
`realizedProfitAndLoss`, `unRealizedProfitAndLoss`, `winRate`, `maxDrawdown`, `gainToPainRatio`,
`traderAgeSeconds`, `lastTradeTimestamp`, `longVolume`, `shortVolume`, `averageLeverageUsed`,
`tcsLabel`. Also `data.count`.

### `discovery_get_trader_state`

What traders hold now. One call takes up to 50 addresses: batch them, never one call per trader.

| Argument | Type | Notes |
|---|---|---|
| `trader_addresses` | list | `0x` + 40 hex each, at most 50 |
| `include_position_age` | bool | adds `startTime` and `durationInSeconds` |
| `latest` | bool | fresh data instead of cached |

Answer: `data.traders`, a list with `address`, `openPositions`, `marginSummary`, `withdrawable`,
`marginPercentage`. Each open position: `coin`, `szi` (signed size: above 0 is long, below 0 is
short), `entryPx`, `positionValue`, `unrealizedPnl`, `leverage` (`{type, value}`), `marginUsed`,
`returnOnEquity`, `liquidationPx`, and with position age `startTime`, `durationInSeconds`. Take the
side from the sign of `szi`, never from the sign of the profit.

## This strategy's account

### `strategy_get_clearinghouse_state`

| Argument | Type | Notes |
|---|---|---|
| `strategy_wallet` | string, required | pass `ctx.wallet` |

Answer: `data.main` and `data.xyz`, each with `assetPositions` (a list of
`{type, position: {coin, szi, entryPx, ...}}`), `marginSummary` (`accountValue`,
`totalMarginUsed`, `totalNtlPos`, `totalRawUsd`), `withdrawable`, `time`. `main` and `xyz` are two
views of one account: never add their account values. The runtime already sizes trades and limits
open positions; do not read this to size, and do not stop the scan when it reads empty.

## Never call

Any tool that changes something raises `PermissionError`: `create_position`, `close_position`,
`edit_position`, `cancel_order`, `send_usdc`, `transfer_spot_to_perps`, `strategy_create`,
`strategy_create_custom_strategy`, `strategy_close`, `strategy_close_positions`,
`strategy_update`, `strategy_pause`, `strategy_top_up`, `strategy_withdraw_funds`,
`strategy_bridge_funds_from_hyperliquid_to_evm`, `ratchet_stop_add`, `ratchet_stop_edit`,
`ratchet_stop_delete`, `user_claim_referral_rewards`.
