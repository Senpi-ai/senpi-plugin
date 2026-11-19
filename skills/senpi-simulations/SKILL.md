---
name: senpi-simulations
description: >-
  Run, watch and rank the signed-in user's Senpi simulations with the Senpi connector. Use for
  "run 5 variations of hawk as simulations", "test 10 versions of this strategy", "how are my
  simulations doing?", "which simulation is winning?", "find the winners", "stop the losers",
  "stop every simulation in this group", "resume my paused simulation", "what would 20 simulations
  cost?". Calls create_simulations, list_my_simulations, get_my_simulation, quote_simulations,
  stop_simulations and resume_simulation. Simulations trade virtual money and use the user's Senpi
  credits. Nothing here trades real money, moves funds or takes a strategy live.
---

# Simulations

A simulation runs one strategy on the user's own Senpi agent with simulated dollars: it reads the
same markets and takes the same signals as the live strategy would, and no real money moves. Each
running simulation uses Senpi credits every hour. A **group** holds the variations of one strategy;
a **variant** is one simulation in it, with its own settings.

Two limits decide how many run, nothing else:

- **Credits.** A simulation starts only while the user's credits cover the next hour of everything
  already running plus the new ones. When credits run out, every simulation and strategy stops and
  the agent pauses. There is no grace period.
- **The agent's box.** Simulations run on the user's Senpi agent, which grows from 4 to 8 to 16 GB
  to fit them. Past 16 GB the rest don't start (BOX_FULL).

## Run a batch

1. **The strategy.** A catalog id from `browse_strategy_catalog` (for example `hawk`), or one of the
   user's running simulations as `from_simulation_id`: its variations join its group.
2. **The variants.** One entry per simulation, each a `settings` map applied over the strategy's
   own, and a short `label` that says what it changes (`lev3`, `score7`). Use only setting keys you
   have read for this strategy: a simulation's `settings` (`get_my_simulation`) or a group's
   `settings_diff` (`list_my_simulations`). Never guess a key. When none is known, start the
   strategy as it is (empty `settings`), read its settings once it has an id, and start the
   variations from it with `from_simulation_id`. Vary what the user asked about; when they named
   nothing, vary one or two settings across a small range around the strategy's own value, and
   tell them what each variant changes.
3. **`budget_usd`.** The simulated dollars each starts with: the user's figure, else the strategy's
   minimum budget from `get_catalog_strategy`.
4. **`idempotency_key`.** A new key for each batch the user asks for. Reuse a key only to retry the
   same batch or to check its progress: the same key never starts a variant twice.
5. **The cost, when asked.** `quote_simulations` answers what a batch would cost per hour and per
   day and how long the user's credits last, without starting anything. It is optional: a batch
   never needs a quote first.

### Relay the answer as given

`create_simulations` answers once the agent has accepted the batch. Its `message` is written for
the user: relay it as is, with its numbers, and don't round, soften or drop any part of it. It says
how many started of how many asked, which ones did not start and why, what the simulations now use
an hour, and how long the credits last.

- **A partial answer is the normal answer at a limit.** `not_started` lists each variant that did
  not start with its reason: `BOX_FULL` (the agent's box is at its largest size), `insufficient_credits`
  (the credits don't cover the next hour), `invalid` (a setting the strategy doesn't have, or a
  repeated label: its detail says which) or `failed`. Say which ones and why, in plain words. Never
  start them again on your own: room on the box comes from stopping other simulations, and credits
  are added in the Senpi app. An `invalid` variant can be fixed and started in a new batch with a
  new key.
- **They start one after another.** A started variant's id is empty until its deploy creates it.
  Call `create_simulations` again with the same `idempotency_key` to read each one's progress and
  id; nothing new starts.
- **The agent is starting or waking** (`provisioning`, `waking`): nothing was created yet. Say so,
  and call again with the same key after the time it gives.
- **Refused**: relay the reason as given (no plan, plan lapsed, out of credits, and the like). Plans
  and credits are handled in the user's Senpi account; give no link.

## Watch them

- `list_my_simulations {group_id}` follows one batch; with no filter it lists every simulation,
  and `totals` counts them by status with the credits a day they use.
- `get_my_simulation {id, include: [positions, closed]}` is one simulation in full: its open
  positions (entry and mark, size, leverage, margin, liquidation price, unrealized P&L, funding
  since open, fees so far) and its closed ones (entry and exit, realized P&L, fees, funding, why it
  closed). Funding paid is negative.
- You can't wait for results. When the user asks for "after an hour", start the batch, say when the
  results start to mean something, and rank when they ask again.

## Find the winners

- Across strategies: `list_my_simulations {group_by: strategy, sort: sharpe}` returns one row per
  group with its best variant on the sort and how many variants matched.
- Inside one group: `list_my_simulations {group_id, sort: sharpe}`. Other sorts: `return`,
  `max_drawdown` (smallest first), `win_rate`, `profit_factor`, `trades`, `credits_per_day`.
- Say what the winner changes from the group's base (`settings_diff`), with its return, Sharpe,
  drawdown and trade count. Simulations with too few trades to rank come last; `min_trades` leaves
  them out. A variant with a handful of trades has not shown anything yet: say so instead of
  naming it a winner.
- A ranking is a record of simulated results, not advice and not a promise of live returns.

## Stop the losers

- `stop_simulations {ids}` (up to 200) or `stop_simulations {group_id}` (every queued, running or
  paused simulation of the group). Stopping is final: a stopped simulation keeps its record but
  never runs again. Stop what the user named. When they ask to stop "the losers", list the ones you
  would stop and why, and stop them once they agree.
- Relay what was stopped, what could not be stopped and why, and the credits a day saved. Stopping
  something already stopped is not an error.
- `resume_simulation {id}` is for a paused simulation (paused when credits ran out, for example).
  It is admitted like a new one. A refusal for credits means credits are added in the Senpi app.

## Taking a simulation live

Not here. When the user wants to run a simulation with real money ("take my best simulation live
with $500"), say: open the simulation in Senpi and press Take it live. Give no link and call no
tool. Placing trades, funding a strategy and moving money also happen only in the user's Senpi
account.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, and never
  quote a raw code or enum value: say "your agent's box is full", not `BOX_FULL`. The one exception
  is the `message` of a create, which is already written for the user. Simulation ids, group names,
  variant labels and coin symbols may be shown.
- Quote figures as returned, with when they were read. A source named in `sources_unavailable`
  "couldn't be read right now"; never fill it in.
- Every figure is simulated: never call simulated P&L money the user made.
