---
name: senpi-market-pulse
description: >-
  Read the Hyperliquid market as a whole with the Senpi connector. Use for "what's moving the
  markets today?", "how are markets?", "market overview", "what's the regime?", "anything happening
  in crypto perps?" — any cross-market question that names no single asset. Calls get_market_pulse.
  Also for funding: "funding extremes?", "which coins pay the most funding?", "what's funding on
  ETH?" — calls get_funding. For one asset's signals, use read_asset_signal instead; for ranked
  anomalies, scan_market_signals (senpi-signals).
---

# Market Pulse

One tool call answers this: `get_market_pulse` (no arguments). It reads the whole market's day:

- `groups` — every crypto perp and every xyz equity, index, commodity and FX instrument with its
  daily move (`change_pct`, previous day's close to now), grouped (`crypto`, `semis_memory`,
  `indices`, `commodities`, …) with each group's `avg_change_pct`; `group_order` lists them.
  `missing: true` on a row means the instrument wasn't listed, not that it was flat.
- `signals` — the cross-asset reads: `gold`, `dxy` and `vix` each with a `read` label, `dispersion`
  (is the index calm while a sector breaks?), `day_classification` (`risk_on` / `risk_off` /
  `mixed`, from how many groups moved more than ±0.5%), and the `funding_regime`.
- `movers` — the biggest moves by size, each with `volume_usd`, `funding` sign and `oi_trend`.
- `sources_unavailable` names any read that failed.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown.
- Lead with the one-line read: the `day_classification` label and the group averages behind it
  (crypto vs. equities vs. commodities) — then the two or three movers that matter, with their
  conviction (volume, funding, OI trend).
- Then the confirmation checklist as returned: gold, dollar, VIX, dispersion — quote the `read`
  labels; they are the engine's, not yours to recompute.
- The groups are *today*. Where the money is *right now* is the 4h board, `get_leaderboard`: read
  it when the user asks who is winning now, and keep the two apart — a red 4h board on a green
  day is rotation inside the day, not a contradiction.
- Quote figures as returned; the result's `as_of` says when the read was taken — say it when the
  user may act on the data.
- If `sources_unavailable` is non-empty, say which section is missing rather than presenting a
  partial read as complete.
- Keep the disclosure honest: this is information, not advice. Never promise returns or tell the
  user to trade.

## Funding questions

"Which coins pay the most funding?", "funding extremes?" or one coin's funding is `get_funding`,
not the pulse. With no `asset` it returns `extremes`: every asset whose annualized funding clears
`min_annualized_pct` (default 20%) for at least `min_persistence_hours`, with its direction, trend
and how long it has persisted. With an `asset` it adds that coin's hourly rates over 7 days and
their average, annualized.

- Who pays comes from the sign of each row's current hourly rate (`current_funding_1h`): positive
  means longs pay shorts, negative means shorts pay longs. The annualized figure is a size with no
  sign, and `funding_direction` names the side that collects (`SHORT` on a positive rate) — never
  read it as the side that pays.
- Lead with the ranked list: asset, annualized rate, who pays whom, and how long it has held. Say
  how many assets cleared the threshold and what the threshold was.
- A high rate on a thin builder-dex market is not the same as one on BTC: say which venue an
  asset trades on when it is a builder-dex one (`xyz:` and the like).
- Funding is a cost or an income for holding a position, not a signal to trade: never present a
  high rate as a reason to take the other side.

## Follow-ups to offer

- A mover caught their eye → `read_asset_signal` on it.
- "Anything unusual?" → `scan_market_signals`.
- "What are the big traders doing?" → `get_smart_money_positioning` or `get_whale_moves`.
- The exact name of an instrument ("is gold listed?", "what's the ticker?") → `list_instruments`
  (`query`, `dex`); a builder-dex asset is prefixed, like `xyz:GOLD`.
- One coin's candles, order book, open interest and funding → `get_asset_market_data` (`asset`,
  `intervals` such as `["1h", "1d"]`, `include_book`).
- The 4h board itself, a trader's row and the positions behind their gain → `get_leaderboard`.
