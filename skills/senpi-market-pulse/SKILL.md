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

One tool call answers this: `get_market_pulse` (no arguments). It returns trending markets, the
funding regime, open-interest velocity, the lean of recent large-trader moves, and
`sources_unavailable` naming any section that could not be read this run.

## Presenting the result

- Lead with the one-line read: what kind of day it is (risk-on, risk-off, mixed) based on the
  funding regime and the lean — then the two or three movers that matter.
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
