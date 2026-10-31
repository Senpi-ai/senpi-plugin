---
name: senpi-smart-money
description: >-
  Read where top Hyperliquid traders sit with the Senpi connector. Use for "what's smart money
  doing?", "are the whales long or short?", "smart money on ETH?", "big moves lately?", "who's
  buying?". Calls get_smart_money_positioning (the cohort's current lean) and get_whale_moves
  (recent large opens/closes). Public wallets, read-only.
---

# Smart Money Radar

Two tools:

- `get_smart_money_positioning` — the proven cohort's current book: long share by value, long vs
  short trader counts, top positions. Optional `asset` narrows to one market.
- `get_whale_moves` — recent large opens and closes, newest first. Optional `asset`,
  `window_hours` (max 168), `min_notional_usd`.

## Presenting the result

- Lead with the lean: "the cohort is X% long by value" (or the counts when value is thin), then
  the standout positions or moves.
- `positions_sampled: 0` with an asset filter means the cohort simply holds none of it — say that
  plainly; it is an answer, not an error.
- Attribute moves to addresses, not names, unless the result carries a name. These are public
  wallets; never speculate about identities.
- Quote `as_of`; positioning can be hours old by the time the user acts. No advice: describe the
  positioning, don't tell the user to copy it.

## Follow-ups to offer

- Depth on one trader → `compare_traders` or `find_top_traders` (senpi-trader-research).
- Depth on one asset → `get_asset_brief`.
