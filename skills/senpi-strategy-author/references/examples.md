# Two whole packages

Both are flat, single-instance packages, trimmed from strategies in Senpi's catalog. Each block is
one file: upload it with the path in its heading. Copy the shape, then write your own idea.

---

## 1. `index-trend`: follow the stronger stock-index trend

Trades two index instruments. Each tick it measures each index's 4-day move, picks the larger one
past a floor, and trades in its direction. One position at a time. Exit: `let_winners_run`.

### `strategy.yaml`

```yaml
schema_version: 1
id: index-trend
version: "1.0.0"
catalog:
  name: "Index Trend"
  belief_plain: "Trades the S&P 500 and XYZ 100 indices in the direction of whichever has the bigger 4-day move, and lets the winner run."
requires:
  runtime: ">=3.0.0"
```

### `runtime.yaml`

```yaml
name: index-trend-main
group: index-trend
version: 1.0.0
description: >
  Trades xyz:SP500 and xyz:XYZ100. Every 5 minutes it measures each index's move over the last
  24 four-hour candles (4 days), picks the larger move past 1.5%, and goes long on a rise or short
  on a fall. Score 3, plus 2 for a move of 4% or more, plus 1 when 4h volume is rising. One
  position at a time, 20% of the free balance at 3x. Exits on a stop 8% ROE below entry and
  a ladder that starts locking gains at +20% ROE.

strategy:
  wallet: "${INDEX_TREND_WALLET}"
  slots: 1
  default_leverage: 3
  trading_risk: conservative

scanners:
  - name: position_tracker
    type: position_tracker
    interval_seconds: 10
  - name: index_trend_signals
    type: external_scanner
    path: ./scanners
    entrypoint: scan.py
    interval_seconds: 300
    timeout_seconds: 180
    default_signal_validity_seconds: 1800
    state_history_max_count: 100
    inputs:
      whitelist: ["xyz:SP500", "xyz:XYZ100"]
      trendLookbackBars: 24
      minTrendPct: 1.5
      strongTrendPct: 4.0
      minScore: 4
      marginPct: 20
      leverage: 3
      maxLeverage: 5
      recentSignalTtlSeconds: 240
    signal_data_schema:
      score: { type: number }
      direction: { type: string }
      trendPct: { type: number }
      volumeTrendPct: { type: number }
      reasons: { type: array }

actions:
  - name: position_tracker_action
    action_type: POSITION_TRACKER
    decision_mode: rule
    scanners: [position_tracker]
  - name: index_trend_entry
    action_type: OPEN_POSITION
    decision_mode: rule
    scanners: [index_trend_signals]
    params:
      order_type: FEE_OPTIMIZED_LIMIT
      fee_optimized_limit_options:
        ensure_execution_as_taker: true
        execution_timeout_seconds: 30
    context:
      - type: signal
        scanner: index_trend_signals

exit:
  engine: dsl
  interval_seconds: 60
  dsl_preset:                       # let_winners_run, unchanged
    phase1:
      enabled: false
      max_loss_pct: 8.0
      retrace_threshold: 8
      consecutive_breaches_required: 1
    phase2:
      enabled: true
      tiers:
        - { trigger_pct: 20,  lock_hw_pct: 25 }
        - { trigger_pct: 30,  lock_hw_pct: 40 }
        - { trigger_pct: 50,  lock_hw_pct: 60 }
        - { trigger_pct: 75,  lock_hw_pct: 75 }
        - { trigger_pct: 100, lock_hw_pct: 85 }

risk:
  data_retention_seconds: 345600
  guard_rails:
    daily_loss_limit_pct: 12
    max_entries_per_day: 2
    bypass_max_entries_per_day_on_profit: false
    max_consecutive_losses: 3
    cooldown_seconds: 5400
    drawdown_halt_pct: 20
    drawdown_reset_on_day_rollover: false
    per_asset_cooldown_seconds: 21600
```

### `scanners/scoring.py`

```python
"""Pure index-trend math: no reads, no clock."""


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def trend_strength(closes, lookback):
    """Percent change of the latest close against the close `lookback` bars earlier."""
    if not closes or len(closes) <= lookback:
        return None
    ref = closes[-(lookback + 1)]
    if ref <= 0:
        return None
    return (closes[-1] - ref) / ref * 100.0


def pick_strongest(strength_by_asset, min_pct):
    """(asset, strength) with the largest move of at least min_pct, or None."""
    best, best_mag = None, -1.0
    for asset, strength in strength_by_asset.items():
        if strength is None or abs(strength) < min_pct:
            continue
        if abs(strength) > best_mag:
            best, best_mag = (asset, strength), abs(strength)
    return best


def volume_trend(candles, lookback=6):
    """Percent change of mean volume, last half against first half of the last `lookback` candles."""
    if len(candles) < lookback:
        return 0.0
    vols = [_f(c.get("v")) for c in candles[-lookback:]]
    half = lookback // 2
    earlier = sum(vols[:half]) / half
    if earlier <= 0:
        return 0.0
    return (sum(vols[-half:]) / half - earlier) / earlier * 100.0


def build_thesis(asset, strength, candles, inputs):
    min_pct = _f(inputs.get("minTrendPct"), 1.5)
    strong_pct = _f(inputs.get("strongTrendPct"), 4.0)
    if strength is None or abs(strength) < min_pct:
        return None
    vol = volume_trend(candles)
    score = 3
    reasons = [f"{asset}_4d_{strength:+.1f}%"]
    if abs(strength) >= strong_pct:
        score += 2
        reasons.append("strong_trend")
    if vol > 15:
        score += 1
        reasons.append(f"volume_rising_{vol:+.0f}%")
    return {
        "direction": "LONG" if strength > 0 else "SHORT",
        "score": score,
        "reasons": reasons,
        "trend_pct": round(strength, 2),
        "volume_trend_pct": round(vol, 2),
    }
```

### `scanners/scan.py`

```python
import sys
import time

import scoring


def _candles_4h(ctx, asset):
    try:
        resp = ctx.senpi_mcp.call_tool("market_get_asset_data", {
            "asset": asset,
            "candle_intervals": ["4h"],
            "include_funding": False,
            "include_order_book": False,
        })
    except Exception as exc:
        print(f"[index-trend] {asset} read failed: {exc!r}", file=sys.stderr)
        return []
    if not isinstance(resp, dict):
        return []
    data = resp.get("data", resp)
    if not isinstance(data, dict):
        return []
    candles = data.get("candles") or {}
    return candles.get("4h") or []


def scan(inputs, ctx):
    now = time.time()
    whitelist = inputs.get("whitelist", [])
    lookback = int(scoring._f(inputs.get("trendLookbackBars"), 24))
    min_pct = scoring._f(inputs.get("minTrendPct"), 1.5)
    min_score = scoring._f(inputs.get("minScore"), 4)
    margin_pct = min(scoring._f(inputs.get("marginPct"), 20), 100.0)
    leverage = min(scoring._f(inputs.get("leverage"), 3), scoring._f(inputs.get("maxLeverage"), 5))
    ttl = scoring._f(inputs.get("recentSignalTtlSeconds"), 240)

    last = (ctx.state.last() or {}) if ctx.state is not None else {}
    recent = {k: v for k, v in dict(last.get("recent", {})).items() if now - v < ttl * 4}

    candles_by_asset, strength_by_asset = {}, {}
    for asset in whitelist:
        if now - recent.get(asset, 0) < ttl:
            continue
        candles = _candles_4h(ctx, asset)
        if len(candles) <= lookback:
            continue
        closes = [scoring._f(c.get("c")) for c in candles]
        candles_by_asset[asset] = candles
        strength_by_asset[asset] = scoring.trend_strength(closes, lookback)

    out = []
    picked = scoring.pick_strongest(strength_by_asset, min_pct)
    if picked is not None:
        asset, strength = picked
        th = scoring.build_thesis(asset, strength, candles_by_asset[asset], inputs)
        if th is not None and th["score"] >= min_score:
            recent[asset] = now
            out.append({
                "asset": asset,
                "direction": th["direction"],
                "marginPct": margin_pct,
                "leverage": leverage,
                "data": {
                    "score": float(th["score"]),
                    "direction": th["direction"],
                    "trendPct": float(th["trend_pct"]),
                    "volumeTrendPct": float(th["volume_trend_pct"]),
                    "reasons": th["reasons"],
                },
            })

    ctx.set_summary(f"{len(strength_by_asset)} indices read, {len(out)} signal")
    if ctx.state is not None:
        try:
            ctx.state.append({"recent": recent})
        except Exception as exc:
            print(f"[index-trend] state append failed: {exc!r}", file=sys.stderr)
    return out
```

Settings this upload returns include `strategy.slots`, `strategy.default_leverage`,
`scanner.interval_seconds`, `scanner.inputs.minTrendPct`, `scanner.inputs.strongTrendPct`,
`scanner.inputs.marginPct`, `exit.dsl_preset.phase1.max_loss_pct` and
`risk.guard_rails.max_entries_per_day`. `whitelist` is a list, so it is not a setting.

---

## 2. `crowd-fade`: fade an exhausted 4-hour crowd

Watches four majors on the 4-hour board. When a coin has moved 3% or more in four hours, at least
30 of the board's leaders are on that side and still adding, and market-wide funding does not
contradict the fade, it trades the other way. Exit: `mean_reversion`.

The board ranks whoever gained most in the last four hours. That is momentum, not smart money, and
the description says so.

### `strategy.yaml`

```yaml
schema_version: 1
id: crowd-fade
version: "1.0.0"
catalog:
  name: "Crowd Fade"
  belief_plain: "When a major coin has run hard and the traders winning the last four hours all pile onto that side, it bets on the unwind."
requires:
  runtime: ">=3.0.0"
```

### `runtime.yaml`

```yaml
name: crowd-fade-main
group: crowd-fade
version: 1.0.0
description: >
  Fades crowded 4-hour moves on BTC, ETH, SOL and HYPE. Reads the 4-hour leaderboard (the traders
  winning the last four hours: momentum, not a proven cohort) and the market-wide funding regime
  every 3 minutes. Trades against the leaders' side when price moved 3% or more their way in four
  hours, at least 30 leaders hold it, their share is still rising over 15 minutes, and funding
  does not contradict the fade. 30% of the free balance at 7x, one position at a time. Exits on the
  mean_reversion ladder: stop 6% ROE below entry, first lock at +5% ROE, out within 48 hours.

strategy:
  wallet: "${CROWD_FADE_WALLET}"
  slots: 1
  default_leverage: 7
  trading_risk: conservative

scanners:
  - name: position_tracker
    type: position_tracker
    interval_seconds: 10
  - name: crowd_fade_signals
    type: external_scanner
    path: ./scanners
    entrypoint: scan.py
    interval_seconds: 180
    timeout_seconds: 120
    default_signal_validity_seconds: 360
    state_history_max_count: 0
    inputs:
      assets: ["BTC", "ETH", "SOL", "HYPE"]
      leaderboardLimit: 100
      minTraderCount: 30
      minMove4hPct: 3.0
      minConcentrationPct: 15
      minScore: 6
      marginPct: 30
      leverage: 7
    signal_data_schema:
      score: { type: number }
      leadersSide: { type: string }
      move4hPct: { type: number }
      traderCount: { type: number }
      regime: { type: string }
      reasons: { type: array }

actions:
  - name: position_tracker_action
    action_type: POSITION_TRACKER
    decision_mode: rule
    scanners: [position_tracker]
  - name: crowd_fade_entry
    action_type: OPEN_POSITION
    decision_mode: rule
    scanners: [crowd_fade_signals]
    params:
      order_type: FEE_OPTIMIZED_LIMIT
      fee_optimized_limit_options:
        ensure_execution_as_taker: true
        execution_timeout_seconds: 60
    context:
      - type: signal
        scanner: crowd_fade_signals

exit:
  engine: dsl
  interval_seconds: 30
  dsl_preset:                       # mean_reversion, unchanged
    hard_timeout:
      enabled: true
      interval_in_minutes: 2880
    weak_peak_cut:
      enabled: true
      interval_in_minutes: 120
      min_value: 2.0
    phase1:
      enabled: false
      max_loss_pct: 6.0
      retrace_threshold: 6
      consecutive_breaches_required: 1
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
    max_entries_per_day: 3
    bypass_max_entries_per_day_on_profit: false
    max_consecutive_losses: 3
    cooldown_seconds: 3600
    drawdown_halt_pct: 25
    drawdown_reset_on_day_rollover: false
    per_asset_cooldown_seconds: 7200
```

### `scanners/scoring.py`

```python
"""Pure crowd-fade math: no reads, no clock."""


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def regime_confirms(fade_direction, regime):
    """True when funding shows the crowd on the side we fade, False when it shows the opposite,
    None when neutral or unknown."""
    if regime in (None, "NEUTRAL"):
        return None
    if fade_direction == "SHORT":
        return regime == "LONG_CROWDED"
    return regime == "SHORT_CROWDED"


def score_fade(row, regime, inputs):
    """One board row -> a fade candidate, or None when any gate fails."""
    side = str(row.get("direction", "")).upper()
    if side not in ("LONG", "SHORT"):
        return None
    traders = int(_f(row.get("trader_count")))
    min_traders = int(_f(inputs.get("minTraderCount"), 30))
    if traders < min_traders:
        return None
    move = _f(row.get("token_price_change_pct_4h"))
    min_move = _f(inputs.get("minMove4hPct"), 3.0)
    if abs(move) < min_move:
        return None
    if (side == "LONG" and move < 0) or (side == "SHORT" and move > 0):
        return None
    if _f(row.get("contribution_pct_change_15m")) <= 0:
        return None

    fade = "SHORT" if side == "LONG" else "LONG"
    confirms = regime_confirms(fade, regime)
    if confirms is False:
        return None

    score = 4
    reasons = [f"leaders_{side.lower()}_{traders}", f"move_4h_{move:+.1f}%"]
    if _f(row.get("pct_of_top_traders_gain")) >= _f(inputs.get("minConcentrationPct"), 15):
        score += 2
        reasons.append("concentrated")
    if traders >= 2 * min_traders:
        score += 1
        reasons.append("deep_crowd")
    if abs(move) >= 2 * min_move:
        score += 1
        reasons.append("overextended")
    if confirms:
        score += 2
        reasons.append(f"funding_{regime.lower()}")
    return {"direction": fade, "score": score, "leaders_side": side,
            "move": move, "traders": traders, "reasons": reasons}
```

### `scanners/scan.py`

```python
import sys

import scoring


def _read(ctx, name, args):
    try:
        resp = ctx.senpi_mcp.call_tool(name, args)
    except Exception as exc:
        print(f"[crowd-fade] {name} failed: {exc!r}", file=sys.stderr)
        return None
    return resp if isinstance(resp, dict) else None


def _board(ctx, limit):
    resp = _read(ctx, "leaderboard_get_markets", {"limit": limit})
    if resp is None:
        return []
    data = resp.get("data", resp)
    markets = data.get("markets") if isinstance(data, dict) else None
    rows = markets.get("markets") if isinstance(markets, dict) else None
    return rows if isinstance(rows, list) else []


def _regime(ctx):
    resp = _read(ctx, "market_get_funding_regime", {})
    if resp is None:
        return None
    data = resp.get("data", resp)
    return data.get("regime") if isinstance(data, dict) else None


def scan(inputs, ctx):
    assets = set(inputs.get("assets", []))
    min_score = scoring._f(inputs.get("minScore"), 6)
    margin_pct = min(scoring._f(inputs.get("marginPct"), 30), 100.0)
    leverage = scoring._f(inputs.get("leverage"), 7)

    rows = _board(ctx, int(scoring._f(inputs.get("leaderboardLimit"), 100)))
    regime = _regime(ctx)

    # A coin can appear once per side: keep the side holding the larger share of the leaders' gains.
    best = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("dex"):
            continue
        token = row.get("token")
        if token not in assets:
            continue
        share = scoring._f(row.get("pct_of_top_traders_gain"))
        if token not in best or share > scoring._f(best[token].get("pct_of_top_traders_gain")):
            best[token] = row

    out = []
    for token, row in best.items():
        c = scoring.score_fade(row, regime, inputs)
        if c is None or c["score"] < min_score:
            continue
        out.append({
            "asset": token,
            "direction": c["direction"],
            "marginPct": margin_pct,
            "leverage": leverage,
            "data": {
                "score": float(c["score"]),
                "leadersSide": c["leaders_side"],
                "move4hPct": float(c["move"]),
                "traderCount": float(c["traders"]),
                "regime": regime or "UNKNOWN",
                "reasons": c["reasons"],
            },
        })

    out.sort(key=lambda s: s["data"]["score"], reverse=True)
    ctx.set_summary(f"{len(best)} of {len(assets)} coins on the board, {len(out)} to fade")
    return out
```

This scanner keeps no memory, so `state_history_max_count` is 0; the runtime's
`per_asset_cooldown_seconds` stops it re-entering a coin it just closed. In a calm market most ticks
emit nothing, and validation answers PASS with a "no signals emitted" warning: that is expected
here.
