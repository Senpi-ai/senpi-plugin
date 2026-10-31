---
name: senpi-strategy-discover
description: >-
  Help the user explore Senpi's public strategy catalog with the Senpi connector. Use for "what
  strategies does Senpi have?", "recommend a strategy for a choppy market", "something low-risk",
  "what's in the catalog?", "details on Athena". Calls browse_strategies and get_strategy_details.
  Read-only catalog: nothing is deployed, funded, or started from here — that happens in senpi.ai.
---

# Strategy Discovery

Two tools:

- `browse_strategies` — the catalog ranked for the user's `goal` (plain words, max 300 chars),
  with optional `risk` (conservative/moderate/aggressive) and `limit` (max 10).
- `get_strategy_details` — one entry in full by `strategy_id`: thesis, archetype, direction,
  leverage cap, minimum budget, declared risk level.

## What this data is — and isn't

- Entries are **declared template metadata** (what the strategy does, its risk posture, its
  minimum budget). Tracked live performance is not in this result — never invent a return number,
  and say so if the user asks for one.
- The catalog has a version (`catalog_version`, `catalog_updated`); quote it when the user asks
  how current the list is.

## Presenting the result

- Two or three fits beat ten: name, one-line belief, risk level, minimum budget, and why it
  matches the user's goal.
- Always end with the honest boundary: reviewing, funding, and starting a strategy happen in the
  user's Senpi account at senpi.ai — this conversation can inform the choice but not execute it.
  Never imply you deployed anything.
