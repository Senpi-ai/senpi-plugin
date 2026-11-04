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

- `get_smart_money_positioning` — two cohorts read from the all-time realized-PnL ranking: the
  **smart** cohort (lifetime realized ≥ $1M, sampled to 150 wallets) and the **crowd** ($10k–$100k
  realized). Returns `smart_leaning` — the coins where at least 5 proven traders lean past a net
  bias of 0.40 (`bias` is net/gross in −1..+1, with `members`, `n_long`, `n_short`, `net_usd`),
  strongest first — and `divergences`, where the two cohorts sit on opposite sides or 0.50 apart.
  Optional `asset` adds `smart` and `crowd` reads on that one coin, with the members' positions.
  `cohorts` says how many wallets each sample holds.
- `get_whale_moves` — the 4h board's momentum events, one per trader (its `sent` event, which
  names `top_positions`, over newer blocked repeats), `sent` first, up to 8. Optional `asset`,
  `window_hours` (default 4, the board's own window; max 168).

## Presenting the result

- Lead with the lean: the top `smart_leaning` rows as "N proven traders, net X% short ETH", then
  any divergence — the proven cohort against the crowd is the core signal.
- An empty `smart_leaning` means no coin clears the 5-member / 0.40 bar right now — say that; it
  is an answer, not an error. With an `asset`, `small_sample: true` means fewer than 5 members
  hold it: report the positions, don't call it a lean.
- A momentum event's `blocked` decision means the alert wasn't pushed — the tier crossing is
  still the signal. `get_whale_moves` returns `UNAVAILABLE` when the board is down, never an
  empty list in its place.
- Attribute moves to addresses, not names, unless the result carries a name. These are public
  wallets; never speculate about identities.
- Quote `as_of`; positioning can be hours old by the time the user acts. No advice: describe the
  positioning, don't tell the user to copy it.

## Follow-ups to offer

- Depth on one trader → `compare_traders` or `find_top_traders` (senpi-trader-research).
- Depth on one asset → `get_asset_brief`.
