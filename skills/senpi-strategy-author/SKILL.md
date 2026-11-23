---
name: senpi-strategy-author
description: >-
  Write the user's own Senpi strategy as a package, put it on their Senpi agent and run it as
  simulations, with the Senpi connector. Use for "write me a strategy that fades funding spikes",
  "turn this idea into a strategy and test 3 versions", "fix my strategy, it failed", "show me
  the strategy I uploaded yesterday". Calls upload_strategy_package, validate_strategy_package,
  get_strategy_package, list_my_strategy_packages and create_simulations with a package_id.
  Simulations trade virtual money and use the user's Senpi credits. An uploaded strategy runs only
  as simulations: it never trades real money, here or in the Senpi app.
---

# Write a strategy package

A strategy is a small package of files: a manifest, one runtime file and a Python scanner. You
write the files, upload them to the user's own Senpi agent, fix what the upload reports, prove
the scanner runs, and then start simulations of it. The runtime on the agent owns everything
operational: it calls the scanner on a timer, sizes each trade, places it, and runs the exit.
Your code only reads data and says what it would trade.

This skill does not pick a catalog strategy for the user (senpi-strategy-discover does) and does
not run simulations of catalog strategies (senpi-simulations does). It never takes a strategy
live.

## When to use it

- The user describes a trading idea and wants it built and tested.
- The user wants changes to a package they or you wrote earlier.
- A simulation of an uploaded package trades nothing, or fails, and needs a fix.

Ask what the strategy should trade, what signal it acts on, long, short or both, and how risky it
may be, when the user has not said. Ask only what is missing. Then build.

## The package: flat, one instance

```
strategy.yaml          # id, version, a short catalog block
runtime.yaml           # the runtime file: scanners, entry action, exit, risk
scanners/scan.py       # def scan(inputs, ctx) -> list[dict]
scanners/scoring.py    # optional: pure math, no reads
```

- Exactly one `runtime.yaml`, at the root. No `instances:` list, no instance folders.
- `strategy.yaml` `id`: lowercase letters, digits and hyphens, at most 24 characters. It is the
  strategy id the upload answers with.
- `runtime.yaml`: `name: <id>-main`, `group: <id>`, and `strategy.wallet: "${<ID>_WALLET}"`: the
  id in capitals, hyphens as underscores, as the whole value. A lowercase or partial
  placeholder is refused.
- Write a plain-words `description` in `runtime.yaml`: what it trades, the signal, when it enters
  and how it exits. The user sees it later.
- Paths are relative, no folder or file name starts with a dot, and only `.py`, `.yaml`, `.yml`,
  `.json`, `.md` and `.txt` files. No `__init__.py` in `scanners/`.
- At most 40 files, 128 KB per file and 512 KB in all.

Details and every rule: [references/package-layout.md](references/package-layout.md). Every
`runtime.yaml` field with its unit: [references/runtime-yaml.md](references/runtime-yaml.md).
Two whole packages to copy from: [references/examples.md](references/examples.md).

## The scanner contract

`scan(inputs, ctx)` runs on the user's agent, not in this conversation.

- It is called once per tick. It reads, scores and returns a list of signals. No loops, no
  sleep, no threads, no file writes, no network calls of its own.
- `inputs` is the scanner's `inputs:` map from `runtime.yaml`. Put every tunable there.
- Read data only with `ctx.senpi_mcp.call_tool(name, args)`. There is no `ctx.call_tool`.
- Remember things between ticks with `ctx.state` (`last()`, `recent(n)`, `append(dict)`). Set
  `state_history_max_count` above 0 or `append` raises.
- A gate that returns early (outside a session, during warm-up) must still read when
  `ctx.dry_run` is true. A tick that reads nothing cannot be proven.
- Each signal is `{"asset", "direction": "LONG"|"SHORT", "marginPct", "leverage", "data"}`.
  `marginPct` is a percent of the free balance in (0, 100]: 10 means 10%. `marginPct` and
  `leverage` go at the top level, never inside `data`.
- Every key in `data` must be declared in `signal_data_schema`, and every declared key is
  required unless it says `required: false`. Put the score in `data`.
- A stop computed in the scanner does nothing. The only stop is the exit preset in
  `runtime.yaml`.
- On any error, return `[]`. Guard every response with `isinstance(resp, dict)` before `.get`.

Full contract and a skeleton: [references/scanner-contract.md](references/scanner-contract.md).

## Scanner tools are the agent's tools, not yours

The scanner calls the Senpi tools that run on the user's agent: `market_get_asset_data`,
`market_list_instruments`, `leaderboard_get_markets`, `discovery_get_top_traders` and others.
Their names, arguments and answers differ from the tools you have in this conversation. Use only
the tools, arguments and response keys listed in
[references/scanner-tools.md](references/scanner-tools.md). Never write a tool name, argument or
key from memory: a wrong one runs cleanly and trades nothing.

Check every ticker the package names with `list_instruments` before you write it. Use the exact
name it returns (`xyz:SP500`, not `SP500`).

## Exits and risk

Copy one exit preset from [references/dsl-presets.yaml](references/dsl-presets.yaml) into
`exit.dsl_preset` and change at most one field. Pick it by how long a trade should last. Add
a `risk.guard_rails` block: a package without one is refused. `max_loss_pct` and every tier are
in ROE (percent of margin), not percent of price. How to choose and explain them:
[references/exits-and-risk.md](references/exits-and-risk.md).

## The loop

1. **Write** the package.
2. **Upload** every file with `upload_strategy_package {files: [{path, content}]}`. Always send
   the whole package, not just the file you changed.
   - `stored: true`: keep the `package_id` and the `settings` map. Read the warnings.
   - `stored: false`: nothing was kept. Each finding has `code`, `file`, `line`, `what`, `why`
     and `fix`. Apply the fix and upload again.
   - A refusal whose message starts with `[E_PACKAGE_...]`: fix the files as it says.
   - The agent is waking or starting: send the same files again after the time it gives.
3. **Stop rule.** If the same finding code comes back after two attempts to fix it, stop editing.
   Tell the user what is blocking, in the finding's own `what` and `fix` words, and let them
   decide.
4. **Validate** with `validate_strategy_package {package_id}`. The first call starts one live
   tick and answers `status: running`. Call again with the same `package_id` until `status` is
   `done`. `interrupted` means call again: a new run starts.
   - `PASS`: the code loads, a real tick ran, it read live data, and its signals would be
     accepted. Only PASS means it runs.
   - `UNPROVEN` is not a pass. The tick read nothing. Usually a gate that ignores `ctx.dry_run`.
   - `FAIL`: fix each finding, upload again (a new `package_id`), validate the new id.
   - A PASS with a "no signals emitted" warning on a new scanner: check every key the code reads
     against [references/scanner-tools.md](references/scanner-tools.md).
   - Another validation is running on the agent: wait and call again.
   The same stop rule applies.
5. **Simulate** with `create_simulations {package_id, variants, budget_usd, idempotency_key}`.
   Each variant's `settings` may use only keys from the `settings` map the upload returned, with
   values of the same type. A variant with empty `settings` runs the package as written.
   `budget_usd` is the user's figure; ask for one if they gave none. Leave `group_name` out: the
   batch joins the package's own group. Then follow senpi-simulations: relay its `message` as
   given, and watch and rank the same way.

Uploads and validations are limited per hour. Fix with thought, not by retrying.

Finding codes and what to do about each: [references/findings.md](references/findings.md).

A PASS proves the strategy runs, not that its logic is right. Read your own math against a known
case before you call it done.

## Changing a package

A package is never edited in place. Change the files, upload the whole package again and validate
the new `package_id`. A clean upload replaces the earlier package of the same strategy id; the old
`package_id` stops working. Simulations already running keep their own copy.

## In a new conversation

You have no copy of the files. `list_my_strategy_packages` lists the user's packages with their
last verdict. `get_strategy_package {strategy_id}` (or `package_id`, or `simulation_id` for the
copy a simulation runs, settings applied) answers the file list and `settings`. Add `path` to read
one file; when the answer has a `next_offset`, call again with that `offset` for the next page.
Read every file before you change any of them.

## Going live

An uploaded strategy never goes live, from this conversation or from the Senpi app. Senpi runs
code written outside Senpi only as simulations, and its simulations have no Take it live. When the
user wants real money on one, say exactly that: this strategy stays a simulation. Do not send them
to the app to take it live, give no link and call no tool. A strategy from Senpi's catalog can be
taken live in the Senpi app.

## Presenting the result

- Write for the user. Never name a tool, argument, response field or file path, and never quote a
  raw code: say "the strategy reads no data outside its trading hours", not `E_VALIDATE_TICK_UNPROVEN`.
  The `what`, `why` and `fix` text of a finding is already written for people: quote it when you
  stop.
- Say what you built in a few lines: what it trades, the signal, the exit in price terms at its
  leverage, and the risk limits.
- Say what each simulation variant changes. Package ids, strategy ids, simulation ids and variant
  labels may be shown.
- Every simulated figure is simulated. Never call it money the user made.
