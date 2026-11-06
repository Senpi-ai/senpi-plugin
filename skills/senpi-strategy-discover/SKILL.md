---
name: senpi-strategy-discover
description: >-
  Help the user explore Senpi's public strategy catalog with the Senpi connector. Use for "what
  strategies does Senpi have?", "recommend a strategy for a choppy market", "something low-risk",
  "what's in the catalog?", "details on Athena". Calls browse_strategy_catalog and get_catalog_strategy.
  Read-only catalog: nothing is deployed, funded, or started from here — that happens in senpi.ai.
---

# Strategy Discovery

Two tools:

- `browse_strategy_catalog` — the catalog as cards, one per variant family (a card's `variants` lists
  its siblings — offer those only through the parent), in neutral alphabetical order, or ranked
  for the user's `goal` (plain words, max 300 chars); optional `risk`
  (conservative/moderate/aggressive). `limit` defaults to 8 — raise it when the user asks to see
  more or the whole catalog ("list everything" → `limit: 500`); `truncated: true` says more exist,
  `families` and `total_in_catalog` say how many. With `risk`, `matching` is how many fit that
  risk level; `total_in_catalog` is still the whole catalog — never call the match "the
  catalog". A page holds only what fits in one response:
  for the whole catalog, call again with `offset` set to the page's `next_offset` until it comes
  back null, then present every family. Don't re-ask with different goals or risks to fill gaps.
- `get_catalog_strategy` — one entry in full by `strategy_id`: thesis, archetype, direction,
  leverage cap, minimum budget, declared risk level.

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
