---
name: senpi-signals
description: >-
  Scan Hyperliquid markets for ranked anomalies with the Senpi connector. Use for "scan the market
  for signals", "any anomalies?", "what's unusual today?", "where's the momentum?" — requests for a
  ranked sweep rather than a general overview. Calls scan_market_signals, then read_asset_signal
  and get_asset_market_data on the top hits. For the overall read use get_market_pulse
  (senpi-market-pulse). Funding extremes are get_funding and whale movements are
  get_whale_moves (senpi-smart-money), not this skill.
---

# Signals

Three steps, in order.

1. `scan_market_signals`. Optional `signal_type` (filter to one detector type) and `limit` — omit
   it: the sweep holds a dozen reads at most and the default returns all of them. The `trade` feed
   comes first in its own order (by trade score), then the `news` feed (by social score); each row
   says which `feed` it is from. A read can appear once in each feed; keep both. The result also
   carries `not_measured` (the sources the sweep couldn't read), `coverage` and `signals_stale`.
2. For the top two or three signals by strength, `read_asset_signal` with that `asset`: the card
   (`summary`, `signals`, `in_universe`, `not_measured`, `signals_as_of`, `signals_stale`).
3. For each of those assets, `get_asset_market_data` with `asset` and `intervals` `["1h", "1d"]`:
   the daily move, funding and open interest behind the signal.

If the sweep returns one or two signals, follow those; if none, say so and stop.

Two questions are not this skill. "Funding extremes?" → `get_funding` (no asset: every asset whose
funding clears the threshold). "Whale movements?" → `get_whale_moves` (senpi-smart-money). Route
them there and do not scan.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown. For
  example, "open interest surge" and "extreme funding", not `oi_surge` or `funding_extreme`; "not
  measured: funding", not `not_measured`; "in Senpi's tradeable universe", not `in_universe: true`.
- Two sections, in this order, each ranked in its own feed's order, one line per row (asset, type,
  strength). Never merge them or drop a row because the other section has it:
  - **Tradeable dislocations, for building ideas** — the trade rows.
  - **Market news, for content** — the news rows (strength here is the social score).
  Don't bury the ranking in prose. Omit a section that has no rows.
- Then the not-measured line, only when `not_measured` is non-empty: "Not measured this run:" and the
  sources in plain words (e.g. the 4h leaderboard). A source not measured is not one that found
  nothing: never say "nothing there" about it.
- Then, only when `signals_stale` is true: say the reading is from `signals_as_of`, that it is older
  than usual, and that the Senpi backend is behind.
- Then one short paragraph per followed asset, from its card (the summary, the signals, whether it
  is `in_universe`; say what `not_measured` lists, and that a card with `signals_stale: true` is old) and its market
  data (the daily move, funding, open interest).
- If the user asked about a specific kind of signal, pass `signal_type` when a matching type exists
  in the results; otherwise scan once and filter in your answer, saying so.
- `truncated: true` only happens when a `limit` was passed; call again without one.
- Quote the call's `as_of` (the call time) and each card's `signals_as_of` (when its signals were read; the top-level `as_of` is not that). A signal is an observation, not a recommendation — never present one as a trade
  instruction.

## How every run ends: one question

After the sections and a few sentences, end with one question and nothing after it: "Want to act on
any of these?" Offer a single trade on one read, or four strategies the user can look at in the
catalog (see senpi-strategy-discover; `get_catalog_strategy` for details):

- Signals Hunter: trades these smart-money signals on an hourly clock. It runs its own scan, so its
  reads are close to this feed but not identical, and its score floor is higher, so it acts on fewer.
- Puffin: the same engine, one position at a time, higher risk and reward: one stop-out is about
  19-23% of the account, and a round trip costs roughly 0.8-0.9% of the wallet in fees. Offer it only
  when the user asks for size or the aggressive one.
- Athena: a hedge-fund style strategy built on these smart-money signals.
- Hyperfeed momentum strategies (such as Penguin for crypto, Pelican for all assets): these chase
  live Hyperfeed rotations, a different source from the smart-money reads above, so say so; they do
  not trade what was just read.

Offer all four each time. These are strategies to explore, not something this connector places or
starts: the catalog is read-only and deploying happens in senpi.ai. A single trade on a read takes the
side the read names (a funding extreme names no side, so it is never a one-trade setup). Never promise
results or call a strategy proven. If the user says no or doesn't answer, stop; don't repeat the offer.
Keep the question out of anything written for public posting, which stays observation-only.

## Follow-ups to offer

- Another asset in the list → `read_asset_signal` and `get_asset_market_data` on it.
- Who is driving it → `get_whale_moves` with that asset, or the cohorts' lean from
  `get_smart_money_positioning` (senpi-smart-money).
- Funding across the market → `get_funding`.
