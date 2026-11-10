---
name: senpi-account-status
description: >-
  The user's standing across Senpi, and Senpi's plans and pricing, with the Senpi connector. Use
  for "how many points do I have?", "what's my rank?", "what are my fees?", "my referral rewards",
  "what plan am I on?", "how many credits do I have left?", "what plans are there?", "how much does
  Senpi cost?", "what do I get on Pro?". Calls get_account_status (the user's own account) and
  get_subscription_plan_catalog (public). Read-only.
---

# Senpi Account Status

Two tools, routed by what the question is about:

- **The user's own standing** → `get_account_status`. Returns: current plan with renewal date, remaining AI credits for
  the cycle, points (total, base/perp split, multiplier, rank and rank change), the Senpi trading
  fee, unclaimed referral earnings, and account basics.
- **Plans and pricing** → `get_subscription_plan_catalog`. The catalog is read live from
  the same feed the app's paywall renders, so quote it as returned — never from memory, and never
  from this file. Plans closed to new subscribers don't appear.

## Presenting the data

- Write for the user, not about the tools. Never name a tool, argument or response field, never show
  a field as `key: value`, and never quote a raw code or enum value (snake_case labels, error codes,
  request ids): say in plain words what was read and what it found. A failed read is "couldn't be
  read right now", not its error. Wallet addresses, strategy ids and coin symbols may be shown.
- Lead with what they asked; don't dump every section for a single question.
- **Fee**: quote `fee.percent` (and `fee.bps`, in basis points: 3 bps = 0.03%) exactly as
  returned — `0` means a paid plan pays no Senpi trading fee (Hyperliquid's own exchange fees
  still apply). A fee with `unknown_reason` means the fee couldn't be confirmed (the plan
  couldn't be read alongside it): say so, never that they pay nothing. Never state a rate the
  data didn't return.
- **Credits**: report `remaining_usd` and `cycle_end` as returned — the live balance is readable
  here, so give the figure rather than sending the user to the app. Do not compute "low credits"
  percentages or burn projections — the app's own meter and notifications are the source of truth
  for that judgment, and top-ups make simple ratios misleading. Credit top-ups exist; for how to
  buy one, point at the app header meter or senpi.ai/settings/subscription, and never quote a
  top-up price or size from memory.
- **Referral**: `unclaimed_usdc > 0` is claimable — in the Senpi app, not here. Referrals pay 15%
  of a referred friend's monthly Senpi spend for their first 12 months.
- A source named in `sources_unavailable` is unknown, not zero — say so rather than reporting
  empty values.

## Rules with no API behind them (policy, quote as-is)

- **Tiers carry no benefit right now**: no fee change, nothing unlocked. Don't bring tiers up,
  never suggest reaching or keeping one; if asked, say tiers carry no benefit right now. Points
  still accrue at the plan multiplier and still set leaderboard rank.
- **A lapsed plan pauses everything**: when a trial or plan expires, a renewal fails, or the
  cycle's credits run out, the agent and every strategy on it pause — no scans, no new entries,
  no stop moves. Open positions stay open; a stop already resting on the exchange still triggers;
  funds stay withdrawable. Never tell a user a subscription is not needed.
- **What spends credits**: every message the user sends and every tool turn the agent runs. Long
  threads cost more, because the whole conversation is re-sent each turn: a fresh thread is cheaper
  than a long one. Scheduled check-ins the agent runs for the user (a recurring monitor of a
  strategy, say) are the usual silent drain — each firing is a full model turn.
- **A running strategy spends no credits**: its runtime ticks without a model call. That is not the
  same as needing no plan — the strategy runs on the agent, and a lapsed plan pauses both.
- **Chat is not free**: every turn spends credits, including the turn that asks what a turn cost.
  Never say "chatting is free" or "that cost nothing".
- **Credits are not money**: they can't be traded, withdrawn or deposited into a strategy. A
  shrinking meter is usage (messages and tool turns), never a trading loss.
- **Billing is a 30-day rolling cycle** from the user's own start date, never a calendar month.
  The plan's own credits land in full at the start of the cycle and expire at its end (no rollover).
  Purchased top-ups are separate: each keeps its own expiry and is not cleared at renewal.
- **Every plan includes every model.** Plans differ on credits and points rate, never on model
  access, so a cheaper plan never locks anyone out of the better model.
- **Upgrading is instant**, any day: the new plan's credits land immediately and the cycle restarts.
  **Downgrading or cancelling takes effect at the next renewal**, never mid-cycle, with benefits kept
  until then. There are no refunds for the unused part of a cycle.
- **The free trial lasts 14 days** from when the user deploys their agent, and is one-time. Never
  quote a credit figure for the trial: the starting amount has changed more than once, and the
  user's subscription page is the only source. When it ends or runs out, the agent and its
  strategies pause, but open positions are **not** auto-closed and funds are untouched.
- **Plan prices and credit sizes come only from the plan catalog**, read live — never from memory
  or this file.
- **Payment is web-only** (senpi.ai/settings/subscription); the app links out to it.
- Changing, upgrading or cancelling a plan, and claiming referral rewards, happen in the user's
  own Senpi account — never through this connector, which is read-only.
