---
name: senpi-strategy-discover
description: >-
  Help the user explore Senpi's public strategy catalog with the Senpi connector. Use for "what
  strategies does Senpi have?", "recommend a strategy for a choppy market", "something low-risk",
  "what's in the catalog?", "details on Athena". Calls browse_strategy_catalog and get_catalog_strategy, with get_my_portfolio
  (the user's budget and holdings, when signed in) and get_asset_market_data (why now).
  Read-only catalog: nothing is deployed, funded, or started from here — that happens in senpi.ai.
---

# Strategy Discovery

Four tools; the last two are optional context:

- `browse_strategy_catalog` — the catalog as cards, one per variant family (a card's `variants` lists
  its siblings — offer those only through the parent), in neutral alphabetical order, or ranked
  for the user's `goal` (plain words, max 300 chars); optional `risk`
  (conservative/moderate/aggressive) and the constraints below. `limit` defaults to 8 — raise it when the user asks to see
  more or the whole catalog ("list everything" → `limit: 500`); `truncated: true` says more exist,
  `families` and `total_in_catalog` say how many. With `risk`, `assets`, `direction` or `exclude`,
  `matching` is how many fit them; `total_in_catalog` is still the whole catalog — never call the
  match "the catalog". A page holds only what fits in one response:
  for the whole catalog, call again with `offset` set to the page's `next_offset` until it comes
  back null, then present every family. Don't re-ask with different goals or risks to fill gaps.
  Before you say "all N", count the families you actually list: the count must equal `families`.
  If it doesn't (a page you didn't read, or entries you grouped away), list the missing ones or say
  plainly how many you're showing of how many — never claim the whole catalog over a shorter list.
- `get_catalog_strategy` — one entry in full by `strategy_id`: thesis, archetype, direction,
  leverage cap, minimum budget, declared risk level.
- `get_my_portfolio` — the signed-in user's balance and holdings (see below).
- `get_asset_market_data` — one coin's market read, for "why now" (see below).

## Turn the user's words into constraints

Pass what the user states as arguments, not as goal text. Leave out anything they did not say.

- Coins or markets they want to trade → `assets`: tickers as they name them (`SOL`, `DOGE`,
  `xyz:NVDA`) or a class word (`btc_eth`, `major_alts`, `universe_crypto`, `xyz_equities`,
  `commodities`, `fx`, `indices`, `pre_ipo`; "stocks", "gold" and "forex" map to one). A ticker no
  strategy trades widens once to its class when nothing else would be left: `widened` says so (name
  the class in words and say it is a broader fit, not an exact one). When the ticker was an `xyz:`
  one, `widened` lists several xyz classes: call it "other markets on Senpi's equities, commodities
  and FX venue" or "other xyz markets", plainly, never one class.
- "Long only", "no shorting", "I want to short" → `direction` `long` or `short`; "no shorts at
  all" → `exclude` `shorting` too.
- "Not copy trading", "no crypto", "no stocks", "not DCA" → `exclude` with `copy_trading`,
  `crypto`, `equities`, `dca`.
- What they have to put in ("I have $500") → `budget_usd`. It never removes anything: a strategy
  whose minimum is above it carries a caveat, and you say so ("needs at least $X, below that it
  runs degraded").
- The mood, the market or the style ("choppy market", "low-risk", "intraday") stays in `goal`; a
  stated risk appetite also goes in `risk`.

Each card carries `caveats` (plain notes — say them, they are why a fit is not exact) and
`asset_match` (how many of the stated assets it covers; a higher one is the closer fit). If nothing
matched, `unmet` lists the constraints that left nothing: say which one to relax and offer the
search again without it, rather than a bare "nothing found". `warnings` names a ticker no strategy
declares: tell the user it is not covered by a fixed strategy.

## Budget and holdings (only when the user is signed in)

When the user's own account is in play ("what fits me", "with what I have", a budget not stated),
read `get_my_portfolio` once: their balance sets `budget_usd`, and the coins they already hold are a
reason to prefer a strategy that trades them, or one that does not pile onto the same book. Use the
balance the user named over the one read. If that read fails or they are not signed in, carry on
without a budget or holdings and say so once.

## Why now

For the top three results, say why now, from the market. Each card lists up to four `assets`:
take up to two of those coins and read `get_asset_market_data` with `asset`, `intervals` `["4h"]`
and `candle_limit` `8`. Read three things and say them plainly: the 24-hour change, whether
funding is positive (longs pay) or negative (shorts pay), and the 4-hour trend. The trend needs at
least four closes: compare the last close with the close six candles before it (the seventh from
the end; the oldest one if fewer) — up when it is more than 1.5% higher, down when more than 1.5%
lower, otherwise flat. Say what that means for the strategy's style (a trend-follower likes a
clear trend; a fader likes a stretched one). A card with no assets trades the whole universe: say
that, and give no single-coin "why now" for it. Read each coin once across the cards: a coin
already read for an earlier card (BTC or ETH, say) is not read or described again. A coin that cannot be read is left out; never make
up a number. This is context for the choice, not a signal to act on.

## What this data is — and isn't

- Entries are **declared template metadata** (what the strategy does, its risk posture, its
  minimum budget). Tracked live performance is not in this result — never invent a return number,
  and say so if the user asks for one.
- The catalog has a version (`catalog_version`, `catalog_updated`); quote it when the user asks
  how current the list is.
  The catalog is read live from senpi-skills and reread every 15 minutes: `catalog_as_of` is when
  it was last confirmed current, and `catalog_stale: true` means the last refresh failed and this
  is the last good copy — say so if the user is choosing on the latest entries.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown.
- Two or three fits beat ten: name, one-line belief, risk level, minimum budget, and why it
  matches the user's goal.
- Always end with the honest boundary: reviewing, funding, and starting a strategy happen in the
  user's Senpi account at senpi.ai — this conversation can inform the choice but not execute it.
  Never imply you deployed anything.
