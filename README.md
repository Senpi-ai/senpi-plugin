# Senpi — AI Quant

Senpi is an AI quant engineer for Hyperliquid. This plugin connects your AI assistant — Claude, ChatGPT, Codex, Cursor, Grok Bot, Grok Build or Hermes Agent — to Senpi's research tools: what's moving and why, ranked market signals, smart-money positioning, trader due diligence, the strategy catalog, and your own portfolio and trade history.

Every tool is read-only. Trading, funding and strategy deployment happen in your Senpi account at [senpi.ai](https://senpi.ai) — never through this plugin.

## What it does

| Workflow | Tools |
|---|---|
| **Market Pulse** — cross-asset read: momentum, funding regime, open-interest shifts, smart-money lean | `get_market_pulse` |
| **Signals** — ranked, non-obvious market developments from Senpi's detectors | `scan_market_signals` |
| **Asset Signal** — one asset: its signals card, with price, daily move, funding and open interest | `read_asset_signal` |
| **Smart Money Radar** — the proven cohort's positioning, what the cohorts did over a window, and recent large moves | `get_smart_money_positioning`, `get_smart_money_flow`, `get_whale_moves` |
| **Trader Research** — rank Hyperliquid traders by window and metric, and who a wallet is | `find_top_traders`, `get_wallet_profile` |
| **Wallet History** — any wallet's closed trades, paged with totals, and its P&L, account value, flows and drawdown over a window | `get_wallet_closed_trades`, `get_wallet_pnl_history` |
| **Market Data** — instrument specs, one asset's candles, order book, open interest and funding, funding extremes across the market | `list_instruments`, `get_asset_market_data`, `get_funding` |
| **4h Leaderboard** — the live board: ranking, coin concentration, one trader's row and positions | `get_leaderboard` |
| **Quant Desk** — read any wallet like a quant: 0-100 quant score, six dimensions, the live book's protection, priced leaks, deep dives, side by side | `get_wallet_analysis`, `get_wallet_positions`, `compare_wallets` (and `find_top_traders` with a size band, `get_my_portfolio` for your wallets) |
| **Strategy Discovery** — browse Senpi's strategy template catalog by goal and risk | `browse_strategy_catalog`, `get_catalog_strategy` |
| **Plans & Pricing** — Senpi's live plan catalog: prices, credits, points multipliers | `get_subscription_plan_catalog` |
| **Portfolio & Trade Review** — your own book, your closed trades reviewed whole, and your ratchet-stop timeline; the wallet-history tools read your own wallets when given no address | `get_my_portfolio`, `get_wallet_closed_trades`, `get_my_stop_events` |
| **Account Status** — your plan, remaining credits, points and rank, fee, referral earnings | `get_account_status` |

Every tool runs through your connected Senpi account: the connector asks you to sign in to Senpi when you add it. The market, research and catalog tools read public data; the portfolio, trade-review and account tools read only your own account.

## Safeguards

- **Read-only by construction.** This server exposes no tool that can place, change or close a trade, deploy a strategy, or move funds. There is nothing to approve because nothing can act.
- Every result carries an `as_of` timestamp and is informational — not financial advice.
- Portfolio tools return data only for the account that signed in via OAuth.
- You can revoke any connected app in one click from Senpi → Connectors.

## What this plugin runs, sends, and fetches

- **Runs:** nothing on your machine. There are no scripts, hooks, or local servers.
- **Sends:** tool calls to `https://open-mcp.senpi.ai/mcp` over HTTPS. Sign-in is OAuth 2.0 with your Senpi login and happens once, when you add the connector; every tool runs through it, and the account tools read only that account. Nothing else leaves your assistant.
- **Fetches:** market data, trader statistics, strategy catalog entries, and — when you are signed in — your own portfolio and trade history.

Privacy policy: <https://senpi.ai/privacy> · Terms: <https://senpi.ai/terms> · Support: <https://resources.senpi.ai/support>

## Install

Sign-in is OAuth 2.0 with your Senpi login and happens once, when you add the connector. Manage or disconnect any time at Senpi → Connectors.

### Claude Code

```bash
claude plugin marketplace add Senpi-ai/senpi-plugin
claude plugin install senpi-agent@senpi
```

Then `/mcp` inside Claude Code to sign in. Server only, without the skills: `claude mcp add --transport http --scope user senpi-agent https://open-mcp.senpi.ai/mcp`.

### Claude (claude.ai and Claude Desktop)

Add the plugin from **Customize → Plugins**, or add the connector directly with the URL `https://open-mcp.senpi.ai/mcp` and sign in.

### ChatGPT

Senpi is listed as **Senpi — AI Quant**. Or, in Developer Mode: Plugins → **+** → **Create MCP app**, server URL `https://open-mcp.senpi.ai/mcp`, authentication OAuth.

### Codex CLI

```bash
codex plugin marketplace add Senpi-ai/senpi-plugin
codex plugin add senpi-agent@senpi
codex mcp login senpi-agent
```

### Cursor and Grok Bot

Grok Bot installs connectors from the [Cursor Marketplace](https://cursor.com/marketplace). Install **Senpi — AI Quant** there, then complete the Senpi sign-in when prompted. Until the listing is live, add the server to `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "senpi-agent": { "url": "https://open-mcp.senpi.ai/mcp" } } }
```

### Grok (grok.com) and Grok Build

- **grok.com:** Connectors → **New Connector** → **Custom** → paste `https://open-mcp.senpi.ai/mcp` and complete sign-in.
- **Grok Build:** install **senpi-agent** from the [xAI plugin marketplace](https://github.com/xai-org/plugin-marketplace) once the catalog entry is live.

### Hermes Agent

```bash
hermes plugins install senpi
hermes plugins enable senpi-agent
```

Until the catalog entry is live, install from this repository instead: `hermes plugins install Senpi-ai/senpi-plugin --no-enable`, then `hermes plugins enable senpi-agent`. The first call of any tool opens the Senpi sign-in in your browser — approve it, then run `/reload-mcp` or start a new session so the tools load.

Server only, without the skills: `hermes mcp install senpi-agent` once the MCP catalog entry is live, or add `https://open-mcp.senpi.ai/mcp` under `mcp_servers` in `~/.hermes/config.yaml` with OAuth. Every tool on this server is read-only, so no trust gate is needed.

### Anything else that speaks MCP

Server URL `https://open-mcp.senpi.ai/mcp`, Streamable HTTP transport, OAuth 2.0 (the MCP authorization spec, with discovery documents at `/.well-known/oauth-protected-resource/mcp`).

## What's in this repo

| Path | For |
|---|---|
| `plugin.json`, `mcp.json` | Source of truth — the [Agent Plugins](https://agent-plugins.org) standard, which is also what Hermes Agent installs as a portable package; ChatGPT metadata under `extensions["com.openai"]` |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code plugin + marketplace (generated) |
| `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Codex CLI and ChatGPT desktop (generated) |
| `.cursor-plugin/plugin.json` | Cursor / Grok Bot marketplace listing (generated) |
| `.grok-plugin/plugin.json` | Grok Build — xAI plugin marketplace (generated) |
| `.mcp.json` | The MCP server, for Claude Code, Cursor, Grok Build and Codex (generated) |
| `skills/` | One skill per workflow: market pulse, signals, smart money, trader research, quant desk, strategy discovery, portfolio, trade review, account status, and "why did X move" |
| `assets/` | Logo for directory listings |

Edit `plugin.json` or `mcp.json`, then run `python3 scripts/build-manifests.py`; CI fails if the generated copies are stale.

## License

Apache-2.0. See [LICENSE](LICENSE).
