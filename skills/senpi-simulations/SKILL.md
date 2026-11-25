---
name: senpi-simulations
description: >-
  Run, watch and rank the signed-in user's Senpi simulations with the Senpi connector. Use for
  "run 5 variations of hawk as simulations", "test 10 versions of this strategy", "how are my
  simulations doing?", "which simulation is winning?", "show my best simulations", "find the
  winners", "stop the losers", "stop every simulation in this group", "resume my paused
  simulation", "what would 20 simulations cost?", "take my simulation live". Calls get_catalog_strategy, create_simulations, list_my_simulations, get_my_simulation, quote_simulations,
  stop_simulations and resume_simulation. A strategy package the user or you wrote goes through
  senpi-strategy-author first (write, upload, validate), then runs here by its package_id.
  "Best" means the highest return unless the user names another measure: call list_my_simulations
  with sort "return" (the connector's default sort is Sharpe). Running simulations are "running", never "live" (real money).
  Never start a simulation without the user's yes to that exact batch: call quote_simulations
  with the exact strategy or from_simulation_id or package_id, variants, budget_usd and group_name
  you will start, show every variant and the credits an hour and a day, ask whether to start
  exactly this, and end your turn. A message that changes the batch ("deploy them with $500
  each", "swap it in", "replace X with the improved one", "drop its leverage and start it") is a
  change, not a yes: quote the new batch, show it, ask again. Call create_simulations only after
  a yes to the latest quote, with the same arguments and its quote_id.
  Simulations trade virtual money and use the user's Senpi credits. Nothing here trades real money,
  moves funds or takes a strategy live. Before answering "take my simulation live", call
  get_strategy_package with its simulation_id: an uploaded package goes live only after the user
  approves it in the Senpi app or their Senpi agent chat.
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
2. **How many.** Exactly the number the user asked for. When they named no number, propose the
   strategy as it is plus two to four variations, and start only the ones they say yes to. Never
   add a variant they did not say yes to, a base included: when they ask for 3, the batch has 3.
3. **The variants.** Vary what the user asked about. When they named no setting, pick what tests
   the strategy, one change per variant: its scoring (the entry score), a scanner threshold, its
   entry management (cooldown, size, leverage, never above the catalog's `leverage_max`) or its exit
   management (stop, trailing, profit lock). Keep each far enough from the strategy's own value to
   show a difference, and say in plain words what it tests ("pickier entries: score 7 instead of
   5"). Each variant is a `settings` map applied over the strategy's own, with a short `label` that
   says what it changes (`lev3`, `score7`).
4. **Setting keys.** Use only keys you have read for this strategy. For a catalog strategy, read
   `get_catalog_strategy` before you show the batch: its `settings` lists every key a variant can
   change, with the strategy's own value. Show each variant's exact values, and after the yes start
   the whole batch in one `create_simulations`. A running simulation's `settings`
   (`get_my_simulation`) or a group's `settings_diff` (`list_my_simulations`) work too. Never guess
   a key. Only when `get_catalog_strategy` answers `settings_unavailable` and the user has no
   simulation of the strategy: make the first of the count the strategy as it is (empty
   `settings`), start that one alone after the yes, read its settings once it has an id, then
   start the rest with `from_simulation_id`. If a change you showed has no key, say so instead of
   picking another.
5. **`budget_usd`.** One budget for the whole batch, so the variants compare: the user's figure,
   else $1,000 (leave `budget_usd` out). Above the maximum, the refusal names it. Hyperliquid refuses an order under $10,
   and a strategy's order shrinks with its leverage, so a variant at lower leverage can order under
   $10 and never trade. Each variant needs `min_budget` × `leverage_max` ÷ its leverage, rounded up
   to a whole dollar (hawk: $15 × 5 ÷ 3 = $25 for a 3x variant). When the budget is lower than
   that, say which variants may never trade and the budget they need.
6. **`idempotency_key`.** A new key for each batch the user asks for. Reuse a key only to retry the
   same batch or to check its progress: the same key never starts a variant twice.
7. **The group.** Leave `group_name` out unless the user names a group: the batch then joins the
   strategy's own group (`hawk`), which is the name the user will use to find or stop it later.

### Show the batch, then start it on a yes

Before any `create_simulations`, call `quote_simulations` with the exact `strategy` (or
`from_simulation_id` or `package_id`), `variants`, `budget_usd` and `group_name` you will start. It
answers a `quote_id`. Show the user every variant of the count, in one message:

- each variant: its label and what it changes from the strategy as it is (or "the strategy as it
  is"), and the budget each starts with;
- the cost an hour and a day, and how long their credits last;
- that a strategy which waits for a breakout, like hawk, can go hours without a trade.

Then ask whether to start exactly this, and end your turn. Start nothing until the user says yes. On
the yes, call `create_simulations` with the same arguments and that `quote_id`.

A message that changes the batch is a change, not a yes, even when it reads as an order: "deploy
them with $500 each", "swap it in for the current one", "replace the old one with the improved
one", "drop its leverage and start it". Quote the new batch, show it, ask, and end your turn. Only
a yes after the new quote starts it. The yes covers this batch only: the next batch is quoted and
shown again, while calling again with the same key to check progress or retry needs no new yes.

When `create_simulations` refuses for a missing or changed quote, do what the refusal says: quote
again, show, ask. Never start the batch another way.

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

- "Best", "winning" and "the winners" mean the highest return, unless the user names another
  measure, such as Sharpe, drawdown or win rate: then sort by that one. Always pass the sort: with
  none, the connector ranks by Sharpe.
- Across strategies: `list_my_simulations {group_by: strategy, sort: return}` returns one row per
  group with its best variant by return and how many variants matched.
- Inside one group: `list_my_simulations {group_id, sort: return}`. Other sorts: `sharpe`,
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
with $500"), first find out whether it runs a strategy the user uploaded:
1. Find the simulation's id with `list_my_simulations` if you don't have it.
2. Call `get_strategy_package {simulation_id}`. An answer with a package id means uploaded code.

- **Uploaded:** it can go live after the user approves it in the Senpi app or their Senpi agent
  chat. Say to ask their Senpi agent there to take it live and approve it; the approval lists the
  hosts the strategy declared. Claude and ChatGPT can't take it live or approve it.
- **No package id:** say to open the simulation in Senpi and press Take it live.
- **Not found** (a stopped simulation no longer runs on the agent): say that a strategy the user
  uploaded goes live after they approve it in Senpi, and any other is taken live from its page in
  Senpi.

Give no link and call no other tool. Placing trades, funding a strategy and moving money also
happen only in the user's Senpi account.

## Presenting the result

- Write for the user, not about the tools. Never name a tool, argument or response field, and never
  quote a raw code or enum value: say "your agent's box is full", not `BOX_FULL`. The one exception
  is the `message` of a create, which is already written for the user. Simulation ids, group names,
  variant labels and coin symbols may be shown.
- Quote figures as returned, with when they were read. A source named in `sources_unavailable`
  "couldn't be read right now"; never fill it in.
- Every figure is simulated: never call simulated P&L money the user made.
- A simulation that is running is "running", never "live": "live" means a strategy trading real
  money.
