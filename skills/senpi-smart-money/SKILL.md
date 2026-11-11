---
name: senpi-smart-money
description: >-
  Read where top Hyperliquid traders sit with the Senpi connector. Use for "what's smart money
  doing?", "are the whales long or short?", "smart money on ETH?", "big moves lately?", "who's
  buying?", "whale movements?", "what did smart money do today?". Calls get_smart_money_positioning (the cohort's
  current lean), get_smart_money_flow (what the cohorts did over a window) and get_whale_moves
  (top traders whose 4h P&L crossed a tier). Public wallets, read-only.
---

# Smart Money Radar

Three tools:

- `get_smart_money_positioning` — two cohorts: the **smart** cohort, the proven tier (lifetime
  realized ≥ $1M) that Senpi Signals' cards count, and a **crowd** sample (150 wallets with
  $10k–$100k realized); a holder is a position of at least $1,000. Returns `smart_leaning` — the
  coins where at least 5 proven traders lean past a net bias of 0.40 (`bias` is net/gross in
  −1..+1, with `members`, `n_long`, `n_short`, `net_usd`), strongest first — and `divergences`,
  where the two cohorts sit on opposite sides or 0.50 apart. Optional `asset` adds `smart` and
  `crowd` reads on that one coin, with the members' positions. `cohorts` names each cohort and its
  size; when the signals cohort can't be read, the smart cohort falls back to a 150-wallet sample
  of the ranking and its definition says so — mention that, since holder counts then differ from
  the asset card's.
- `get_smart_money_flow` — what the cohorts **did**, not where they sit: positions opened, added
  to, trimmed, closed and flipped over a `window` (`latest`, `1h`, `4h`, `24h`; default 1h), per
  asset and cohort (`proven`, `crowd`, `apex`, `whale`), with `net_usd` per asset and the
  `divergences` between cohorts; `include_events: true` adds the newest wallet moves of $10k or
  more behind the flow. Quote `age_s`: the read is a snapshot, and says how old. "Smart money is
  short ETH" is positioning; "smart money sold ETH this afternoon" is flow — use the right one.
  The per-asset totals are summed **across all cohorts**; one cohort's own moves come only from
  the events — pass `include_events: true` and group them by cohort before saying what the
  proven cohort, or the whales, did. The events are the newest 50 at most: when
  `events_cut_at_limit` is true they are a sample of the window, so say "among the latest moves",
  never a cohort's total for the window. Not every deployment offers this tool: when it is not in
  your tool list, answer a "what did they do" question with `get_whale_moves` (top traders whose
  4h P&L crossed a tier — not trades) and say the per-cohort flow is not available here.
- `get_whale_moves` — the 4h board's momentum events, one per trader (its newest that names
  `top_positions`), newest first, up to 8. Each is a top trader whose 4h P&L crossed a tier
  (`tier_label`, `delta_pnl`), with the positions they held — **not** an open or a close: never
  say a whale opened or closed anything from it. Optional `asset`, `window_hours` (default 4, the
  board's own window; max 168). When `read_cut_at_limit` is true the moves only reach back to
  `oldest_event_read`: say the span they cover, not the whole window.

## The full read, in order

For "what's smart money doing?", "where are the whales leaning?" and "smart money vs the crowd", run
these in order and narrate each block as it returns. Each block names its population and window
("proven traders' open positions", "the 4h board's winners"), and the two populations are never
merged: the proven cohort (positioning, over its whole record) and the 4h board (whoever is winning
the last four hours, survivors included) are regularly on opposite sides of the same coin.

1. **Headline lean.** `get_smart_money_positioning`: where the proven traders (lifetime realized
   ≥ $1M) are net-leaning now, with how many of them — "N proven traders, net X% short ETH" — set
   against the crowd sample ($10k–$100k realized). Open with the cohort's size from `cohorts`:
   "all N proven wallets" (the whole proven tier, not a sample of it). Every holder count and
   dollar total is out of that base, so a reader comparing against another read knows why the
   numbers are larger.
2. **Smart vs the crowd.** The divergences from the same read: who is on which side, how lopsided,
   how many wallets. Lead with the cases on opposite sides. This is the core signal.
3. **Near-term flow.** `get_smart_money_flow` with `window: "4h"`: are the cohorts adding or
   unwinding? Then `get_leaderboard` (`limit: 5`, `concentration_limit: 8`) for the 4h board's
   winners: does the board confirm the lean or fight it? A "confirms or fights" verdict compares two
   populations, so state both. If flow is not in your tool list, use `get_whale_moves` for this step
   and say the per-cohort flow isn't available here.
4. **Bottom line.** One paragraph: where the proven money sits, where it splits from the crowd,
   whether the last four hours back it, and a "what to watch" line.

An asset question ("smart money on ETH?") passes `asset` to positioning and flow and skips the 4h
board. A narrow ask ("who's long what?") runs only the block it needs. Fail open: if a later read
fails or is unavailable, say once, in plain words, that the layer couldn't be read right now, and
finish the answer with what you have.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown.
- Lead with the lean: the top `smart_leaning` rows as "N proven traders, net X% short ETH", then
  any divergence — the proven cohort against the crowd is the core signal.
- An empty `smart_leaning` means no coin clears the 5-member / 0.40 bar right now — say that; it
  is an answer, not an error. With an `asset`, `small_sample: true` means fewer than 5 members
  hold it: report the positions, don't call it a lean.
- A cohort's read on one asset is thin when fewer than 20 of its wallets hold it, or one wallet
  holds more than half of its gross: say how many wallets that is and how much the largest holds,
  report the positions, and don't call that cohort's direction or compare it with the other
  cohort's. The crowd is a 150-wallet sample, so its read on one coin is often thin.
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
