---
name: senpi-signals
description: >-
  Scan Hyperliquid markets for ranked anomalies with the Senpi connector. Use for "scan the market
  for signals", "any anomalies?", "what's unusual today?", "funding extremes?", "where's the
  momentum?", "whale movements?" — requests for a ranked sweep rather than a general overview.
  Calls scan_market_signals. For the overall read use get_market_pulse (senpi-market-pulse).
---

# Signals

One tool call: `scan_market_signals`. Optional `signal_type` (filter to one detector type) and
`limit` (max 20). Signals come ranked by strength.

## Presenting the result

- List the top signals with asset, type, and strength; one line each, strongest first. Don't bury
  the ranking in prose.
- If the user asked about a specific kind (funding, OI, whales), pass `signal_type` when a matching
  type exists in the results; otherwise scan once and filter in your answer, saying so.
- `truncated: true` means more signals exist than the limit; offer to fetch more.
- Quote `as_of`. A signal is an observation, not a recommendation — never present one as a trade
  instruction.

## Follow-ups to offer

- Depth on one signal's asset → `get_asset_brief`.
- Who is driving it → `get_whale_moves` with that asset.
