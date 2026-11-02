# Senpi — AI Quant

Senpi is an AI quant engineer for Hyperliquid. This plugin connects your AI assistant — Claude, ChatGPT, Codex, Cursor, Grok Bot, Grok Build or Hermes Agent — to Senpi's research tools: what's moving and why, ranked market signals, smart-money positioning, trader due diligence, the strategy catalog, and your own portfolio and trade history.

Every tool is read-only. Trading, funding and strategy deployment happen in your Senpi account at [senpi.ai](https://senpi.ai) — never through this plugin.

## What it does

| Workflow | Tools | Needs sign-in |
|---|---|---|
| **Market Pulse** — cross-asset read: momentum, funding regime, open-interest shifts, smart-money lean | `get_market_pulse` | No |
| **Signals** — ranked, non-obvious market developments from Senpi's detectors | `scan_market_signals` | No |
| **Asset Brief** — one asset: price, 7-day move, funding, open interest, active signals | `get_asset_brief` | No |
| **Smart Money Radar** — the proven cohort's positioning and recent large moves | `get_smart_money_positioning`, `get_whale_moves` | No |
| **Trader Research** — rank Hyperliquid traders by window and metric, compare side by side | `find_top_traders`, `compare_traders` | No |
| **Quant Desk** — score any wallet: 0-100 quant score, six dimensions, priced leaks, protection audit | `get_quant_scorecard` | Only for your own book |
| **Strategy Discovery** — browse Senpi's strategy template catalog by goal and risk | `browse_strategies`, `get_strategy_details` | No |
| **Portfolio & Trade Review** — your own book, and your closed trades aggregated | `get_my_portfolio`, `review_my_trades` | Yes |

The market and research tools work without a Senpi account. The two portfolio tools answer only for your own connected account; without sign-in they return a clear "sign in to Senpi" response instead of data.

## Safeguards

- **Read-only by construction.** This server exposes no tool that can place, change or close a trade, deploy a strategy, or move funds. There is nothing to approve because nothing can act.
- Every result carries an `as_of` timestamp and is informational — not financial advice.
- Portfolio tools return data only for the account that signed in via OAuth.
- You can revoke any connected app in one click from Senpi → Connectors.

## What this plugin runs, sends, and fetches

- **Runs:** nothing on your machine. There are no scripts, hooks, or local servers.
- **Sends:** tool calls to `https://agents.senpi.ai/connector/mcp` over HTTPS. Sign-in is OAuth 2.0 with your Senpi login, and is only required for the portfolio tools. Nothing else leaves your assistant.
- **Fetches:** market data, trader statistics, strategy catalog entries, and — when you are signed in — your own portfolio and trade history.

Privacy policy: <https://senpi.ai/privacy> · Terms: <https://senpi.ai/terms> · Support: <https://resources.senpi.ai/support>

## Install

Signing in is optional and only unlocks the portfolio tools. Manage or disconnect any time at Senpi → Connectors.

### Claude Code

```bash
claude plugin marketplace add Senpi-ai/senpi-plugin
claude plugin install senpi-agent@senpi
```

Then `/mcp` inside Claude Code to sign in. Server only, without the skills: `claude mcp add --transport http --scope user senpi-agent https://agents.senpi.ai/connector/mcp`.

### Claude (claude.ai and Claude Desktop)

Add the plugin from **Customize → Plugins**, or add the connector directly with the URL `https://agents.senpi.ai/connector/mcp` and sign in.

### ChatGPT

Senpi is listed as **Senpi — AI Quant**. Or, in Developer Mode: Plugins → **+** → **Create MCP app**, server URL `https://agents.senpi.ai/connector/mcp`, authentication OAuth.

### Codex CLI

```bash
codex plugin marketplace add Senpi-ai/senpi-plugin
codex plugin add senpi-agent@senpi
codex mcp login senpi-agent
```

### Cursor and Grok Bot

Grok Bot installs connectors from the [Cursor Marketplace](https://cursor.com/marketplace). Install **Senpi — AI Quant** there, then complete the Senpi sign-in when prompted. Until the listing is live, add the server to `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "senpi-agent": { "url": "https://agents.senpi.ai/connector/mcp" } } }
```

### Grok (grok.com) and Grok Build

- **grok.com:** Connectors → **New Connector** → **Custom** → paste `https://agents.senpi.ai/connector/mcp` and complete sign-in.
- **Grok Build:** install **senpi-agent** from the [xAI plugin marketplace](https://github.com/xai-org/plugin-marketplace) once the catalog entry is live.

### Hermes Agent

```bash
hermes plugins install senpi
hermes plugins enable senpi-agent
```

Until the catalog entry is live, install from this repository instead: `hermes plugins install Senpi-ai/senpi-plugin --no-enable`, then `hermes plugins enable senpi-agent`. The market tools work right away; asking about your own portfolio opens the Senpi sign-in in your browser — approve it, then run `/reload-mcp` or start a new session so the tools load.

Server only, without the skills: `hermes mcp install senpi` once the MCP catalog entry is live, or add `https://agents.senpi.ai/connector/mcp` under `mcp_servers` in `~/.hermes/config.yaml` with OAuth. Every tool on this server is read-only, so no trust gate is needed.

### Anything else that speaks MCP

Server URL `https://agents.senpi.ai/connector/mcp`, Streamable HTTP transport, OAuth 2.0 (the MCP authorization spec, with discovery documents at `/.well-known/oauth-protected-resource/connector/mcp`).

## What's in this repo

| Path | For |
|---|---|
| `plugin.json`, `mcp.json` | Source of truth — the [Agent Plugins](https://agent-plugins.org) standard, which is also what Hermes Agent installs as a portable package; ChatGPT metadata under `extensions["com.openai"]` |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code plugin + marketplace (generated) |
| `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Codex CLI and ChatGPT desktop (generated) |
| `.cursor-plugin/plugin.json` | Cursor / Grok Bot marketplace listing (generated) |
| `.grok-plugin/plugin.json` | Grok Build — xAI plugin marketplace (generated) |
| `.mcp.json` | The MCP server, for Claude Code, Cursor, Grok Build and Codex (generated) |
| `skills/` | One skill per workflow: market pulse, signals, smart money, trader research, quant desk, strategy discovery, portfolio, trade review, and "why did X move" |
| `assets/` | Logo for directory listings |

Edit `plugin.json` or `mcp.json`, then run `python3 scripts/build-manifests.py`; CI fails if the generated copies are stale.

## License

Apache-2.0. See [LICENSE](LICENSE).
