---
name: senpi-market-pulse
description: >-
  Read the Hyperliquid market as a whole with the Senpi connector. Use for "what's moving the
  markets today?", "how are markets?", "market overview", "what's the regime?", "anything happening
  in crypto perps?" — any cross-market question that names no single asset. Calls get_market_pulse.
  For one asset, use get_asset_brief instead; for ranked anomalies, scan_market_signals
  (senpi-signals).
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
- `smart_money` — the 4h board layer: `status`, `concentration` (where the top traders' gains sit),
  `top_traders`, and `momentum_events` (one per trader, newest first, with `top_positions`).
  `null` means the board could not be read this run; it is not "no activity".
- `sources_unavailable` names any read that failed.

## Presenting the result

- Lead with the one-line read: the `day_classification` label and the group averages behind it
  (crypto vs. equities vs. commodities) — then the two or three movers that matter, with their
  conviction (volume, funding, OI trend).
- Then the confirmation checklist as returned: gold, dollar, VIX, dispersion — quote the `read`
  labels; they are the engine's, not yours to recompute.
- The 4h layer is where the money is *right now*; the groups are *today*. Keep them apart: a red
  4h board on a green day is rotation inside the day, not a contradiction.
- Quote figures as returned; the result's `as_of` says when the read was taken — say it when the
  user may act on the data.
- If `sources_unavailable` is non-empty, say which section is missing rather than presenting a
  partial read as complete.
- Keep the disclosure honest: this is information, not advice. Never promise returns or tell the
  user to trade.

## Follow-ups to offer

- A mover caught their eye → `get_asset_brief` on it.
- "Anything unusual?" → `scan_market_signals`.
- "What are the big traders doing?" → `get_smart_money_positioning` or `get_whale_moves`.
