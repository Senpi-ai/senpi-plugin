# The scanner contract

`scanners/scan.py` exports one function, `scan(inputs, ctx)`. The runtime on the user's agent
calls it every `interval_seconds`. It reads data, scores it, and returns a list of signals. The
runtime sizes, places and exits every trade.

## Rules

- **Exactly two arguments:** `def scan(inputs, ctx):`.
- **One pass.** No `while True`, no `sleep`, no threads, no background work.
- **Read only.** Senpi data comes from `ctx.senpi_mcp.call_tool(name, args)`. Every tool that
  changes anything (opening, closing or editing a position, cancelling an order, creating or
  updating a strategy, moving funds, stop edits) raises `PermissionError`. Do not open files.
- **Outside APIs.** The scanner may read an outside API over HTTPS with `urllib.request`, with a
  `timeout`, when every host it calls is listed in `strategy.yaml` under `network.hosts`. Live,
  every other host is blocked. Only read: never send the strategy's signals or the user's data
  out. Do not shell out (`subprocess`) or use `socket` directly.
- **Return a list.** On any error, return `[]` or the signals you already have. Returning anything
  else, or raising, throws the whole tick away.
- **Pure math in `scoring.py`.** No reads and no clock there; `scan.py` passes values in.
- **Bounded work.** The whole tick must finish inside `timeout_seconds`. A tick that runs over is
  killed on every tick, so the strategy never trades. Each read can take up to 30 seconds before
  it fails. Keep a tick in the tens of reads: fetch each asset once, read board-wide data once per
  tick rather than once per asset, and pass `limit` for the rows you need.

## `inputs`

The scanner's `inputs:` map from `runtime.yaml`, as a plain dict. Read with `.get` and a default:

```python
min_score = float(inputs.get("minScore", 4))
assets = inputs.get("assets", ["BTC", "ETH"])
```

## `ctx`

`ctx` is frozen: you cannot set or add anything on it.

| Member | What it is |
|---|---|
| `ctx.senpi_mcp.call_tool(name, args)` | the only way to read data. Tools and keys: [scanner-tools.md](scanner-tools.md) |
| `ctx.state` | memory between ticks, or `None` when `state_history_max_count` is 0 |
| `ctx.wallet` | this strategy's wallet address |
| `ctx.scanner_name` | the scanner's `name` |
| `ctx.interval_seconds` | the tick cadence |
| `ctx.dry_run` | `True` during validation, `False` in a real run |
| `ctx.set_summary(text)` | one line about this tick, at most 300 characters; optional |

There is no `ctx.call_tool`, no `ctx.inputs`, no `ctx.now` and no logger. To log, use
`print(..., file=sys.stderr)`.

### `ctx.state`

| Call | Returns |
|---|---|
| `ctx.state.last()` | the newest record (a dict) or `None` |
| `ctx.state.recent(n)` | the last `n` records, oldest first |
| `len(ctx.state)` | how many records are kept |
| `ctx.state.append(record)` | adds a record; it must be a dict |

- State moves forward only on a clean tick. If the tick raises or times out, the append is undone.
- A record is stored as JSON: no sets, tuples, datetimes or non-string keys. An `int` key comes
  back as a string.
- Guard every use: `if ctx.state is not None:`.

### `ctx.dry_run`

A scanner that returns early (outside a session, before a warm-up, on a weekday check) is correct in
a real run. But a validation tick that reads nothing proves nothing and is reported as UNPROVEN.
Let `ctx.dry_run` skip the gate:

```python
if not in_session(now) and not ctx.dry_run:
    return []
```

## Responses

`call_tool` returns the tool's JSON. It can also return a plain string or a list when the tool
answered with text. A non-empty string passes `if not resp:` and then fails on `.get`, killing the
tick. Check the type:

```python
resp = ctx.senpi_mcp.call_tool("market_get_asset_data", {"asset": asset, "candle_intervals": ["4h"]})
if not isinstance(resp, dict):
    continue
data = resp.get("data", resp)
```

Most numbers arrive as strings. Read every number through `_f`:

```python
def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d
```

Candle times `t` and `T` are epoch **milliseconds**; `time.time()` is seconds.

If any read in a tick failed, even one your code caught, and the tick returns `[]`, the tick is
thrown away and state does not move. That is safe; it only means the next tick starts from the
same memory.

## The signal

Return a list of dicts, one per trade you want:

| Key | Required | Notes |
|---|---|---|
| `asset` | yes | the exact instrument name, e.g. `BTC`, `xyz:SP500` |
| `direction` | yes | `LONG` or `SHORT`. Anything else is refused |
| `marginPct` | no | top level. Percent of the free balance, in (0, 100]: `10` is 10%. Out of range drops the signal |
| `leverage` | no | top level. A positive number |
| `data` | no | checked against `signal_data_schema` |
| `valid_for_seconds` | no | a positive integer, or leave it out to use `default_signal_validity_seconds`. Any other value drops the signal |
| `signal_type` | no | a label |

- `marginPct` and `leverage` are the only sizing keys. Any other top-level key is dropped and the
  size falls back to the recipe's margin.
- `data` must match `signal_data_schema` exactly: an undeclared key, a missing required key, or a
  wrong type drops the signal. A `bool` is not a `number`.
- Put the score in `data`. It is the record of why the trade was taken.
- `data` records; it never instructs. A `stop_price` or `take_profit` in `data` does nothing. The
  only stop is the exit preset (see [exits-and-risk.md](exits-and-risk.md)).
- Do not set `valid_until`, `produced_at` or `signal_id`; the runtime owns them.
- Read `marginPct` from `inputs` as a constant. If you compute it, clamp it with `min(pct, 100.0)`.
- Emit one signal for "one best trade", or all that qualify and let `slots` cap them.
- The universe comes from the thesis: a list in `inputs` or an explicit filter. Never let a loose
  score condition widen it to every coin on the venue.

## Skeleton

```python
import sys
import time

import scoring


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _read(ctx, name, args):
    try:
        resp = ctx.senpi_mcp.call_tool(name, args)
    except Exception as exc:
        print(f"[scan] {name} failed: {exc!r}", file=sys.stderr)
        return None
    return resp if isinstance(resp, dict) else None


def scan(inputs, ctx):
    now = time.time()
    assets = inputs.get("assets", [])
    min_score = _f(inputs.get("minScore"), 5.0)
    margin_pct = min(_f(inputs.get("marginPct"), 10.0), 100.0)
    leverage = _f(inputs.get("leverage"), 3.0)

    last = (ctx.state.last() or {}) if ctx.state is not None else {}
    seen = dict(last.get("seen", {}))

    out = []
    for asset in assets:
        resp = _read(ctx, "market_get_asset_data", {
            "asset": asset, "candle_intervals": ["4h"],
            "include_funding": False, "include_order_book": False,
        })
        if resp is None:
            continue
        candles = (resp.get("data", resp) or {}).get("candles", {}).get("4h", []) or []
        thesis = scoring.score(asset, candles, inputs)
        if thesis is None or thesis["score"] < min_score:
            continue
        seen[asset] = now
        out.append({
            "asset": asset,
            "direction": thesis["direction"],
            "marginPct": margin_pct,
            "leverage": leverage,
            "data": {"score": float(thesis["score"]), "reasons": thesis["reasons"]},
        })

    if ctx.state is not None:
        try:
            ctx.state.append({"seen": seen})
        except Exception as exc:
            print(f"[scan] state append failed: {exc!r}", file=sys.stderr)
    return out
```

With this `runtime.yaml` scanner block:

```yaml
state_history_max_count: 50
signal_data_schema:
  score: { type: number }
  reasons: { type: array }
```

## Before you upload

- Every tool name, argument and response key is in [scanner-tools.md](scanner-tools.md).
- Every ticker was checked with `list_instruments`.
- Every `data` key is declared, with the right type.
- Every early return honours `ctx.dry_run`.
- Every name is assigned before any branch that reads it. A name used on a path that runs before
  its assignment fails the first time that path runs, which can be days later.
- Read your scoring against a case you know: a clear uptrend must score long, a clear downtrend
  short.
