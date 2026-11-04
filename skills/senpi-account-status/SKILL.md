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

- Lead with what they asked; don't dump every section for a single question.
- **Fee**: quote `fee.percent` (and `fee.bps` when present) exactly as returned — `0` means a
  paid plan pays no Senpi trading fee (Hyperliquid's own exchange fees still apply). Never state
  a rate the data didn't return.
- **Credits**: report `remaining_usd` and `cycle_end` as returned. Do not compute "low credits"
  percentages or burn projections — the app's own meter and notifications are the source of truth
  for that judgment, and top-ups make simple ratios misleading. For the exact live figure, point
  at the meter in the app header or senpi.ai/settings/subscription.
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
- **Credits are not money**: they can't be traded, withdrawn or deposited into a strategy. A
  shrinking meter is usage (messages and tool turns), never a trading loss.
- **Payment is web-only** (senpi.ai/settings/subscription); the app links out to it.
- Changing, upgrading or cancelling a plan, and claiming referral rewards, happen in the user's
  own Senpi account — never through this connector, which is read-only.
