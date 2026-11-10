---
name: senpi-market-pulse
description: >-
  Read the Hyperliquid market as a whole with the Senpi connector. Use for "what's moving the
  markets today?", "how are markets?", "market overview", "what's the regime?", "anything happening
  in crypto perps?" — any cross-market question that names no single asset. Calls get_market_pulse,
  then get_leaderboard and get_whale_moves (the last 4 hours) and scan_market_signals (a short
  signals brief). Also for funding: "funding extremes?", "which coins pay the most funding?", "what's funding on
  ETH?" — calls get_funding. For one asset's signals, use read_asset_signal instead; for ranked
  anomalies, scan_market_signals (senpi-signals).
---

# Market Pulse

The full read is four layers in a fixed order (below); a narrow ask runs the first only. The first
is `get_market_pulse` (no arguments). It reads the whole market's day:

- `groups` — every crypto perp and every xyz equity, index, commodity and FX instrument with its
  daily move (`change_pct`, previous day's close to now), grouped (`crypto`, `semis_memory`,
  `indices`, `commodities`, …) with each group's `avg_change_pct`; `group_order` lists them.
  `missing: true` on a row means the instrument wasn't listed, not that it was flat.
- `signals` — the cross-asset reads: `gold`, `dxy` and `vix` each with a `read` label, `dispersion`
  (is the index calm while a sector breaks?), `day_classification` (`risk_on` / `risk_off` /
  `mixed`, from how many groups moved more than ±0.5%), and the `funding_regime`.
- `movers` — the biggest moves by size, each with `volume_usd`, `funding` sign and `oi_trend`.
- `sources_unavailable` names any read that failed.

## The full read, in order

For "what's moving the markets today?", "market overview", "how are markets?" and the like, run these
in order and narrate each layer as it returns:

1. **The day.** `get_market_pulse`. Narrate: the macro picture (the day's character and the one tell
   behind it), the indices, the epicenter (where the action is, and its gradient), the divergence
   (what is not moving with the crowd), commodities and macro (gold, dollar, VIX as confirmation),
   crypto (majors, funding regime, volume character), other notables, and a bottom line with an
   explicit "what to watch" list of levels and triggers.
2. **Last 4 hours.** `get_leaderboard` (`limit: 5`, `concentration_limit: 8`) and `get_whale_moves`.
   Narrate a "Last 4 hours" block: which markets carry the winners' gains (the share of the gains
   and how many traders), the top traders, and up to 8 momentum events, one per trader. Label it the
   4h board, or "the last four hours' winners" — never "smart money": this is whoever is winning now,
   survivors included, while smart money is the proven cohort (senpi-smart-money), and the two are
   often on opposite sides of the same coin. Say which population each statement is about. A
   momentum event is a trader's 4h P&L crossing a tier; give the trader, tier and size, and never
   guess its markets or say it was an open or a close.
3. **Senpi Signals, in brief.** `scan_market_signals` (`limit: 3`). Narrate a "Senpi Signals, in
   brief" block: the three top reads, one line each, from the scan as it stands.
4. **A catalyst, when one is needed.** When a mover is unusually large or unexplained, run at most
   one web search for the reason and say it is a search result, not Senpi data. Skip it otherwise.
5. **Close** with "What do you want to do next?" and three numbered offers, the last block of the
   answer: (1) the full signals scan, (2) Quant Desk on their wallet, (3) one asset's card (the
   asset's signal read). Keep it to these three.

A narrow ask ("how's gold?", "what's the dollar doing?") runs step 1 only and answers what was asked.
Fail open: if a later read fails or is unavailable, say once, in plain words, that the layer couldn't
be read right now, and carry on with the rest — never stall or retry in a loop. A missing change is
a dash, never 0%.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown.
- Lead with the one-line read: the `day_classification` label and the group averages behind it
  (crypto vs. equities vs. commodities) — then the two or three movers that matter, with their
  conviction (volume, funding, OI trend). Say the label in words — a "risk-on day", a "risk-off
  day", a "mixed day" — and let it stand: it counts how many groups moved, so never call a risk-on
  day "mixed" because one group fell; say which group went against it ("a risk-on day led by
  equities, while crypto fell"). A null label means too few groups were read to call the day: say
  so, don't pick one.
- Then the confirmation checklist as returned: gold, dollar, VIX, dispersion — quote the `read`
  labels; they are the engine's, not yours to recompute.
- The groups are *today*. Where the money is *right now* is the 4h board (step 2): keep the two
  apart — a red 4h board on a green day is rotation inside the day, not a contradiction. When the
  user asks only who is winning now, run step 2 alone.
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
- "Want the full signals scan?" → `scan_market_signals` at its default size (senpi-signals).
- Quant Desk on their wallet → `get_wallet_analysis` (senpi-quant-desk).
- "What are the big traders doing?" → `get_smart_money_positioning` or `get_whale_moves`
  (senpi-smart-money).
- The exact name of an instrument ("is gold listed?", "what's the ticker?") → `list_instruments`
  (`query`, `dex`); a builder-dex asset is prefixed, like `xyz:GOLD`.
- One coin's candles, order book, open interest and funding → `get_asset_market_data` (`asset`,
  `intervals` such as `["1h", "1d"]`, `include_book`).
- The 4h board itself, a trader's row and the positions behind their gain → `get_leaderboard`.
