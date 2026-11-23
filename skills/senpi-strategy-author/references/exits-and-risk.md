# Exits and risk

## Units first

`max_loss_pct`, `retrace_threshold`, `trigger_pct`, `lock_hw_pct` and `weak_peak_cut.min_value` are
**ROE %**: percent of the margin, not of the price. The price move is the ROE divided by the
leverage.

| ROE | at 3x | at 5x | at 10x |
|---|---|---|---|
| 6% | 2.0% of price | 1.2% | 0.6% |
| 8% | 2.7% | 1.6% | 0.8% |
| 20% | 6.7% | 4% | 2% |

Always say a stop to the user in price terms at the strategy's leverage. A stop that is a small
price move sits inside normal noise and stops winners out before they run. Lower the leverage
before you tighten the stop.

## Pick a preset by horizon

Copy one preset's `dsl_preset` block from [dsl-presets.yaml](dsl-presets.yaml) into
`exit.dsl_preset`. Change at most one field.

| Preset | For | Stop from entry | First lock | Time cuts |
|---|---|---|---|---|
| `let_winners_run` | trend, breakout, momentum, following traders | 8% ROE | at +20%, keeps 25% of the best | none |
| `balanced` (default) | general, unsure | 8% ROE | at +10%, keeps 30% | flat-and-fading cut at 6h; outer bound 72h |
| `mean_reversion` | fading spikes, range trades | 6% ROE | at +5%, keeps 30% | flat-and-fading cut at 2h; outer bound 48h |
| `scalp` | fast in and out | 5% ROE | at +5%, keeps 50% | flat-since-entry cut at 45m; outer bound 90m |
| `parabolic_runner` | an identified parabolic move only | 18% ROE | at +30%, keeps 30% | outer bound 14 days |

Time cuts belong to the horizon, not to the preset:

| Meant to be out in | `weak_peak_cut` | timed closes |
|---|---|---|
| minutes to an hour | yes | short; the cut defines the hold |
| within the day | yes, 60 minutes or more | 60 minutes or more |
| days | no | nothing under 48 hours |
| weeks | no | nothing under 5 days |

`balanced` carries a 6-hour cut. For a strategy that holds for days, take `let_winners_run` or turn
the cuts off. Keep `weak_peak_cut.min_value` below the first tier's `trigger_pct`, or the cut can
close a trade that already locked profit.

## How the exit works

- **Stop from entry.** `max_loss_pct` closes the trade when it has lost that much ROE.
- **Locks.** Once the trade's ROE reaches a tier's `trigger_pct`, the stop moves to
  `best ROE so far × lock_hw_pct / 100`. The highest tier reached applies. Below the first trigger
  nothing is locked.
- **The stop follows the best price**, not the current one. It only moves up for a long and down for
  a short. Nothing is sold on the way up; a lock only sets where a reversal closes the trade.
- **Every close is a full close.**

Say it to the user in plain words before you name a preset:

> Your stop moves up as the price moves your way (down for a short). As the trade gains it follows
> behind and locks in more of the gain. It never sells while the trade is still going your way.

Then the ladder as outcomes, starting where the trade is now. For `let_winners_run` at 5x:

> - Below +20% ROE nothing is locked yet; the stop is 8% ROE below entry, a 1.6% price move.
> - At +20% your stop moves to +5%. From there the trade can't lose money.
> - At +50% your stop moves to +30%.
> - At +100% your stop moves to +85%.

Add a line for each time cut the chosen preset has.

### Check the ladder before you build it

Offer a concrete alternative, never just a warning:

- **First lock above about +40% ROE:** most trades never reach it, so nothing is ever locked.
  Offer `balanced`, which starts at +10%.
- **`lock_hw_pct: 0`:** exits flat and still pays fees. Never ship one.
- **Locks that shrink as triggers rise:** almost always a typo. Read it back.
- **Preset against the idea:** a fader on `let_winners_run`, a multi-day trend on `scalp`.

If the user keeps their choice after you explain it, build what they asked for.

## A stop from the scanner does not bind

The only stop a position has is the preset's. A `stop_price` in the signal's `data` is recorded and
ignored. To express a structural stop, convert it to ROE at the leverage and set `max_loss_pct`:

```
LONG:  max_loss_pct = (1 - stop_price / entry_price) × leverage × 100
SHORT: max_loss_pct = (stop_price / entry_price - 1) × leverage × 100
```

The preset is one value for the whole strategy. A stop that changes per trade cannot be expressed;
size the preset to the widest stop the idea tolerates and tell the user.

## Risk limits (`risk.guard_rails`)

They are checked before every new entry. Closes are never blocked. A package with an entry action and
no `guard_rails` block is refused.

| Limit | What it does | When it resets |
|---|---|---|
| `daily_loss_limit_pct` | stops new entries after the day's loss passes this percent | 00:00 UTC; stays stopped until then even if the day recovers |
| `drawdown_halt_pct` | stops new entries after a drawdown from the profit peak passes this percent | never by itself, unless `drawdown_reset_on_day_rollover: true` (then at 00:00 UTC) |
| `max_consecutive_losses` + `cooldown_seconds` | after that many losing trades in a row, pauses entries for the cooldown. Needs both fields | after the cooldown |
| `per_asset_cooldown_seconds` | no new entry on an asset closed less than this long ago | when the time passes |
| `max_entries_per_day` | at most this many entries per UTC day | 00:00 UTC |
| `bypass_max_entries_per_day_on_profit` | lets entries past the cap while the day is in profit | |

`max_entries_per_day` is a ceiling, not a pace: the whole allowance can fire minutes after 00:00 UTC.
If a risk reading fails, entries pause; there is no permissive fallback.

A sensible start, to tune to the style:

```yaml
risk:
  data_retention_seconds: 259200
  guard_rails:
    daily_loss_limit_pct: 15
    drawdown_halt_pct: 25
    drawdown_reset_on_day_rollover: false
    max_consecutive_losses: 3
    cooldown_seconds: 3600
    per_asset_cooldown_seconds: 14400
    max_entries_per_day: 5
    bypass_max_entries_per_day_on_profit: false
```

Faders and fast strategies want a shorter `per_asset_cooldown_seconds` and more entries a day;
strategies that hold for days want the opposite.

## Sizing

- The signal's `marginPct` is a percent of the free balance in (0, 100]. `strategy.margin_pct` is the
  fallback in the same unit. `0.2` means 0.2%, not 20%.
- `slots` caps how many positions are open at once.
- In a simulation, `budget_usd` is the simulated balance the strategy starts with. Very small
  margins can fall under the exchange's minimum order and open nothing.
