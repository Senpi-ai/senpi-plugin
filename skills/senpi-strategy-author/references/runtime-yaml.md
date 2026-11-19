# `runtime.yaml` fields

One `runtime.yaml` is one strategy on one wallet: the scanners it runs, the action that opens
trades, the exit, and the risk limits. Unknown top-level keys are accepted and ignored, so a
misspelled key does nothing and says nothing. Copy names from this page.

All durations are integer **seconds**, except the exit time cuts, which are **minutes**.

## A complete file

```yaml
name: funding-fade-main
group: funding-fade
version: 1.0.0
description: >
  Shorts majors whose longs pay extreme funding, sized at 15% of the free balance at 3x.
  Exits on a trailing stop that only locks gains; no time-based exit.

strategy:
  wallet: "${FUNDING_FADE_WALLET}"
  slots: 2
  default_leverage: 3
  trading_risk: moderate

scanners:
  - name: position_tracker
    type: position_tracker
    interval_seconds: 10
  - name: funding_fade_signals
    type: external_scanner
    path: ./scanners
    entrypoint: scan.py
    interval_seconds: 300
    timeout_seconds: 120
    default_signal_validity_seconds: 600
    state_history_max_count: 50
    inputs:
      assets: ["BTC", "ETH", "SOL"]
      minAnnualizedPct: 50
      marginPct: 15
      leverage: 3
    signal_data_schema:
      score: { type: number }
      fundingAnnualizedPct: { type: number }
      reasons: { type: array, required: false }

actions:
  - name: position_tracker_action
    action_type: POSITION_TRACKER
    decision_mode: rule
    scanners: [position_tracker]
  - name: funding_fade_entry
    action_type: OPEN_POSITION
    decision_mode: rule
    scanners: [funding_fade_signals]
    params:
      order_type: FEE_OPTIMIZED_LIMIT
      fee_optimized_limit_options: { ensure_execution_as_taker: true, execution_timeout_seconds: 30 }
    context:
      - { type: signal, scanner: funding_fade_signals }

exit:
  engine: dsl
  interval_seconds: 30
  dsl_preset:            # a preset copied from dsl-presets.yaml
    phase1: { enabled: false, max_loss_pct: 6.0, retrace_threshold: 6, consecutive_breaches_required: 1 }
    phase2:
      enabled: true
      tiers:
        - { trigger_pct: 5,  lock_hw_pct: 30 }
        - { trigger_pct: 10, lock_hw_pct: 50 }
        - { trigger_pct: 15, lock_hw_pct: 65 }
        - { trigger_pct: 25, lock_hw_pct: 80 }
        - { trigger_pct: 40, lock_hw_pct: 90 }

risk:
  data_retention_seconds: 259200
  guard_rails:
    daily_loss_limit_pct: 15
    drawdown_halt_pct: 25
    max_consecutive_losses: 3
    cooldown_seconds: 3600
    per_asset_cooldown_seconds: 7200
    max_entries_per_day: 5
```

## Top level

| Field | Required | Notes |
|---|---|---|
| `name` | yes | `<id>-main` for a flat package |
| `group` | for packages | `<id>`; simulations are grouped under it by default |
| `version` | no | metadata only |
| `description` | no, but write it | plain words: what it trades, the signal, entry, exit |
| `strategy` | yes | below |
| `scanners` | yes when an action reads signals | below |
| `actions` | yes to trade | below |
| `exit` | yes in practice | a package without a DSL exit is refused at validation |
| `risk` | yes in practice | an entry action without `risk.guard_rails` is refused at validation |

Never put `dsl_preset` at the top level: it belongs under `exit:`. Leave `notifications` out.

## `strategy`

| Field | Unit / values | Notes |
|---|---|---|
| `wallet` | `"${<ID>_WALLET}"` | required; whole value, upper case |
| `slots` | count | most positions open at once |
| `margin_pct` | percent, > 0 and ≤ 100 | fallback size when a signal carries no `marginPct`. `20` is 20%; `0.2` is 0.2% |
| `margin_per_slot` | USD | fixed fallback size |
| `default_leverage` | multiplier | used when a signal carries no `leverage` |
| `trading_risk` | `conservative` \| `moderate` \| `aggressive` | |

Sizing order: the signal's `marginPct`, then `margin_pct`, then `margin_per_slot`. Do not put
`enabled` here; it is ignored.

## `scanners`

Every scanner needs a unique `name` and a `type`. Always include the position tracker when there is
an exit:

```yaml
- { name: position_tracker, type: position_tracker, interval_seconds: 10 }
```

Built-in scanners take `interval_seconds` of at least 7.

### `external_scanner` (your code)

| Field | Required | Unit / values | Notes |
|---|---|---|---|
| `path` | yes | folder | `./scanners` |
| `entrypoint` | yes | file | `scan.py`; must exist |
| `interval_seconds` | no (30) | seconds, integer > 0 | how often `scan()` runs |
| `timeout_seconds` | no (= interval) | seconds, integer > 0 | the whole tick's budget; a tick past it is killed, every time |
| `default_signal_validity_seconds` | **yes** | seconds, integer > 0 | how long a signal stays valid |
| `state_history_max_count` | no (0) | count, integer ≥ 0 | records kept in `ctx.state`; 0 disables it |
| `inputs` | no | map | passed to `scan()` as its first argument |
| `signal_data_schema` | **yes** | map, not empty | one entry per `data` key: `{ type, required? }` |

`type` is one of `string`, `number`, `boolean`, `object`, `array`. A key is required unless it says
`required: false`.

Refused on an external scanner: `interval`, `params`, `config`, `outputs`, `blocked_assets`,
`depends_on`. Never add `enabled` to any scanner entry: it is ignored, so a scanner marked
`enabled: false` still runs.

### Inputs and simulation settings

The upload answers a `settings` map: the only keys a simulation variant may change. It holds the
plain values (numbers, strings, true/false) of `strategy`, of the entry action's `params`, of
`exit` and `risk`, and of the entry scanner and its `inputs` as `scanner.inputs.<name>`. Lists and
maps inside `inputs` are not settings, and neither is an input whose name contains `key`, `token`,
`secret`, `password`, `auth` or `webhook`. So make every value the user may want to vary a plain
number or string in `inputs`.

## `actions`

| Field | Values | Notes |
|---|---|---|
| `name` | unique | |
| `action_type` | `OPEN_POSITION` \| `CLOSE_POSITION` \| `POSITION_TRACKER` | |
| `decision_mode` | `rule` \| `llm` \| `none` | always write `rule`. Left out, it means `none`, and `none` on an entry action opens nothing |
| `scanners` | list of scanner names | the scanners whose signals this action takes |
| `params.order_type` | `MARKET` \| `FEE_OPTIMIZED_LIMIT` | never `LIMIT` for an entry |
| `params.fee_optimized_limit_options` | `ensure_execution_as_taker` (bool), `execution_timeout_seconds` (1-300) | only with `FEE_OPTIMIZED_LIMIT` |
| `context` | `- { type: signal, scanner: <name> }` | |

`llm` mode needs a model and a prompt; do not use it in an uploaded package.

Every external scanner must be listed by an action. A close is never a `direction`: the entry
action refuses anything but `LONG` and `SHORT`. To close on a signal, add a second scanner that emits
the open position's asset and side, and a `CLOSE_POSITION` action listing only that scanner.

## `exit`

| Field | Unit / values | Notes |
|---|---|---|
| `engine` | `dsl` | |
| `interval_seconds` | seconds, 5-3600 (30) | how often the exit checks positions |
| `order_type` | `MARKET` \| `FEE_OPTIMIZED_LIMIT` | how exits are placed |
| `fee_optimized_limit_options` | as on the entry | |
| `dsl_preset` | map | copy one from `dsl-presets.yaml` |

### `dsl_preset`

| Key | Fields | Unit |
|---|---|---|
| `phase1` | `enabled`, `max_loss_pct` (> 0, ≤ 100), `retrace_threshold` (> 0), `consecutive_breaches_required` (integer ≥ 1) | ROE % |
| `phase2` | `enabled`, `tiers` | |
| each tier | `trigger_pct` (> 0), `lock_hw_pct` (0-100) | ROE % |
| `hard_timeout` | `enabled`, `interval_in_minutes` (> 0) | minutes |
| `weak_peak_cut` | `enabled`, `interval_in_minutes` (> 0), `min_value` (> 0) | minutes, ROE % |
| `dead_weight_cut` | `enabled`, `interval_in_minutes` (> 0) | minutes |

- Tiers must be in strictly rising `trigger_pct` order.
- Time cuts sit at the preset root, beside `phase1` and `phase2`, never inside `phase1`.
- `max_loss_pct` is the stop from entry whether or not `phase1` is enabled.
- Any other key inside `dsl_preset` is refused.

## `risk`

| Field | Unit / values |
|---|---|
| `data_retention_seconds` | seconds, 3600-604800 |
| `guard_rails.daily_loss_limit_pct` | percent, ≥ 0 |
| `guard_rails.drawdown_halt_pct` | percent, 0-100 |
| `guard_rails.drawdown_reset_on_day_rollover` | true / false (false) |
| `guard_rails.max_entries_per_day` | integer ≥ 1 |
| `guard_rails.bypass_max_entries_per_day_on_profit` | true / false (false) |
| `guard_rails.max_consecutive_losses` | integer ≥ 1 |
| `guard_rails.cooldown_seconds` | seconds, ≥ 60 |
| `guard_rails.per_asset_cooldown_seconds` | seconds, ≥ 300 |

Any other key directly under `risk` is refused. The old `cooldown_minutes`,
`per_asset_cooldown_minutes` and `data_retention_hours` are refused. What each limit does:
[exits-and-risk.md](exits-and-risk.md).
