---
name: senpi-smart-money
description: >-
  Read where top Hyperliquid traders sit with the Senpi connector. Use for "what's smart money
  doing?", "are the whales long or short?", "smart money on ETH?", "big moves lately?", "who's
  buying?", "what did smart money do today?". Calls get_smart_money_positioning (the cohort's
  current lean), get_smart_money_flow (what the cohorts did over a window) and get_whale_moves
  (recent large opens/closes). Public wallets, read-only.
---

# Smart Money Radar

Three tools:

- `get_smart_money_positioning` — two cohorts read from the all-time realized-PnL ranking: the
  **smart** cohort (lifetime realized ≥ $1M, sampled to 150 wallets) and the **crowd** ($10k–$100k
  realized). Returns `smart_leaning` — the coins where at least 5 proven traders lean past a net
  bias of 0.40 (`bias` is net/gross in −1..+1, with `members`, `n_long`, `n_short`, `net_usd`),
  strongest first — and `divergences`, where the two cohorts sit on opposite sides or 0.50 apart.
  Optional `asset` adds `smart` and `crowd` reads on that one coin, with the members' positions.
  `cohorts` says how many wallets each sample holds and names them: this is a 150-wallet sample
  of the proven tier with every position counted, not the signals card's whole tier that
  `read_asset_signal` reads, so the two tools' holder counts differ by design.
- `get_smart_money_flow` — what the cohorts **did**, not where they sit: positions opened, added
  to, trimmed, closed and flipped over a `window` (`latest`, `1h`, `4h`, `24h`; default 1h), per
  asset and cohort (`proven`, `crowd`, `apex`, `whale`), with `net_usd` per asset and the
  `divergences` between cohorts; `include_events: true` adds the newest wallet moves of $10k or
  more behind the flow. Quote `age_s`: the read is a snapshot, and says how old. "Smart money is
  short ETH" is positioning; "smart money sold ETH this afternoon" is flow — use the right one.
  The per-asset totals are summed **across all cohorts**; one cohort's own moves come only from
  the events — pass `include_events: true` and group them by cohort before saying what the
  proven cohort, or the whales, did.
- `get_whale_moves` — the 4h board's momentum events, one per trader (its newest that names
  `top_positions`), newest first, up to 8. Optional `asset`, `window_hours` (default 4, the
  board's own window; max 168).

## Presenting the result

- Lead with the lean: the top `smart_leaning` rows as "N proven traders, net X% short ETH", then
  any divergence — the proven cohort against the crowd is the core signal.
- An empty `smart_leaning` means no coin clears the 5-member / 0.40 bar right now — say that; it
  is an answer, not an error. With an `asset`, `small_sample: true` means fewer than 5 members
  hold it: report the positions, don't call it a lean.
- `get_whale_moves` returns `UNAVAILABLE` when the board is down, never an empty list in its
  place.
- Attribute moves to addresses, not names, unless the result carries a name. These are public
  wallets; never speculate about identities.
- Quote `as_of`; positioning can be hours old by the time the user acts. No advice: describe the
  positioning, don't tell the user to copy it.

## Follow-ups to offer

- Depth on one trader → `get_wallet_profile` or `find_top_traders` (senpi-trader-research).
- Depth on one asset → `read_asset_signal`.
- The 4h board's ranking and where its gains concentrate, or one trader's positions behind a
  momentum event → `get_leaderboard` (`trader` for the wallet).
