# Senpi — AI Quant

Senpi is an AI quant engineer for Hyperliquid. This plugin connects your AI assistant — Claude, ChatGPT, Codex, Cursor, Grok Bot, Grok Build or Hermes Agent — to Senpi's research tools: what's moving and why, ranked market signals, smart-money positioning, trader due diligence, the strategy catalog, and your own portfolio and trade history.

Every tool is read-only. Trading, funding and strategy deployment happen in your Senpi account at [senpi.ai](https://senpi.ai) — never through this plugin.

## What it does

| Workflow | Tools |
|---|---|
| **Market Pulse** — cross-asset read: momentum, funding regime, open-interest shifts, smart-money lean | `get_market_pulse` |
| **Signals** — ranked anomalies from Senpi's detectors, with the card and market data behind the top hits | `scan_market_signals`, `read_asset_signal`, `get_asset_market_data` |
| **Asset Signal** — one asset: its signals card, with price, daily move, funding and open interest | `read_asset_signal` |
| **Smart Money Radar** — the proven cohort's positioning, what the cohorts did over a window, and recent large moves | `get_smart_money_positioning`, `get_smart_money_flow`, `get_whale_moves` |
| **Trader Research** — rank Hyperliquid traders by window and metric, and who a wallet is | `find_top_traders`, `get_wallet_profile` |
| **Wallet History** — any wallet's closed trades, paged with totals, and its P&L, account value, flows and drawdown over a window | `get_wallet_closed_trades`, `get_wallet_pnl_history` |
| **Market Data** — instrument specs, one asset's candles, order book, open interest and funding, funding extremes across the market | `list_instruments`, `get_asset_market_data`, `get_funding` |
| **4h Leaderboard** — the live board: ranking, coin concentration, one trader's row and positions | `get_leaderboard` |
| **Quant Desk** — read any wallet like a quant: 0-100 quant score, six dimensions, the live book's protection, priced leaks, deep dives, side by side | `get_wallet_analysis`, `get_wallet_positions`, `compare_wallets` (and `find_top_traders` with a size band, `get_my_portfolio` for your wallets) |
| **Strategy Discovery** — browse Senpi's strategy template catalog by goal and risk | `browse_strategy_catalog`, `get_catalog_strategy` |
| **Portfolio & Trade Review** — your own book, your closed trades reviewed whole with your equity path and your stop events; the wallet-history tools read your own wallets when given no address | `get_my_portfolio`, `get_wallet_closed_trades`, `get_wallet_pnl_history`, `get_my_stop_events` |
| **Account Status** — your plan, remaining credits, points and rank, fee, referral earnings | `get_account_status` |

Every tool runs through your connected Senpi account: the connector asks you to sign in to Senpi when you add it. The market, research and catalog tools read public data; the portfolio, trade-review and account tools read only your own account.

## Example prompts

- "What's moving the markets today?"
- "Scan the market for anomalies"
- "What is smart money doing on ETH?"
- "Who were the best traders this week? Compare the top two."
- "Run Quant Desk on 0x…" with any Hyperliquid wallet address
- "How is my portfolio doing?" once you have signed in to Senpi

## Safeguards

- **Read-only by construction.** This server exposes no tool that can place, change or close a trade, deploy a strategy, or move funds. There is nothing to approve because nothing can act.
- Every result carries an `as_of` timestamp and is informational — not financial advice.
- Portfolio tools return data only for the account that signed in via OAuth.
- You can revoke any connected app in one click from Senpi → Connectors.

## What this plugin runs, sends, and fetches

- **Runs:** nothing on your machine. The plugin has no hooks and no local server, and no skill runs a script.
- **Sends:** tool calls to `https://mcp.senpi.ai/mcp` over HTTPS. Sign-in is OAuth 2.0 with your Senpi login and happens once, when you add the connector; every tool runs through it, and the account tools read only that account. Nothing else leaves your assistant.
- **Fetches:** market data, trader statistics, strategy catalog entries, and — when you are signed in — your own portfolio and trade history.

Privacy policy: <https://senpi.ai/privacy> · Terms: <https://senpi.ai/terms> · Support: <https://senpi.ai/resources/support> · X: [@senpi_ai](https://x.com/senpi_ai)

## Install

Sign-in is OAuth 2.0 with your Senpi login and happens once, when you add the connector. Manage or disconnect any time at Senpi → Connectors.

### Claude Code

```bash
claude plugin marketplace add Senpi-ai/senpi-plugin
claude plugin install senpi-agent@senpi
```

Then `/mcp` inside Claude Code to sign in. Server only, without the skills: `claude mcp add --transport http --scope user senpi-agent https://mcp.senpi.ai/mcp`.

### Claude (claude.ai and Claude Desktop)

Add the plugin from **Customize → Plugins**, or add the connector directly with the URL `https://mcp.senpi.ai/mcp` and sign in.

### ChatGPT

Senpi is listed as **Senpi — AI Quant**. Or, in Developer Mode: Plugins → **+** → **Create MCP app**, server URL `https://mcp.senpi.ai/mcp`, authentication OAuth.

### Codex CLI

```bash
codex plugin marketplace add Senpi-ai/senpi-plugin
codex plugin add senpi-agent@senpi
codex mcp login senpi-agent
```

### Cursor and Grok Bot

Grok Bot uses your Cursor plugins and connectors. Install **Senpi — AI Quant** from the [Cursor Marketplace](https://cursor.com/marketplace), then complete the Senpi sign-in when prompted. Until the listing is live, add the server to `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "senpi-agent": { "url": "https://mcp.senpi.ai/mcp" } } }
```

### Grok (grok.com) and Grok Build

- **grok.com:** Connectors → **New Connector** → **Custom** → paste `https://mcp.senpi.ai/mcp` and complete sign-in.
- **Grok Build:** install **senpi-agent** from the [xAI plugin marketplace](https://github.com/xai-org/plugin-marketplace) once the catalog entry is live.

### Hermes Agent

```bash
hermes plugins install senpi
hermes plugins enable senpi-agent
```

Until the catalog entry is live, install from this repository instead: `hermes plugins install Senpi-ai/senpi-plugin --no-enable`, then `hermes plugins enable senpi-agent`. The first call of any tool opens the Senpi sign-in in your browser — approve it, then run `/reload-mcp` or start a new session so the tools load.

Server only, without the skills: `hermes mcp install senpi-agent` once the MCP catalog entry is live, or add `https://mcp.senpi.ai/mcp` under `mcp_servers` in `~/.hermes/config.yaml` with OAuth. Every tool on this server is read-only, so no trust gate is needed.

### Anything else that speaks MCP

Server URL `https://mcp.senpi.ai/mcp`, Streamable HTTP transport, OAuth 2.0 (the MCP authorization spec, with discovery documents at `/.well-known/oauth-protected-resource/mcp`).

## Troubleshooting

- **No sign-in prompt, or the Senpi tools are missing:** reconnect the connector. In Claude Code run `/mcp`; in Claude, open the plugin's Connectors tab; in other apps, disconnect Senpi in the connector settings and add it again.
- **"Couldn't be read right now" in an answer:** one data source did not respond for that read. The rest of the answer stands; ask again in a minute.
- **Signed in, but your portfolio is empty:** the account tools read only the Senpi account you signed in with. Check that it is the account that holds your strategies.
- **To remove access:** Senpi → Connectors, then revoke the app.

More fixes, including for connectors in Claude and ChatGPT, are on the [support page](https://senpi.ai/resources/support).

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

This branch holds only the plugin. The maintainer tools that regenerate the generated manifests from `plugin.json` and `mcp.json` and build the archive for Claude and ChatGPT live on the `tooling` branch, and the A/B test harness that compares these skills with the originals lives on the `ab-harness` branch.

## License

Apache-2.0. See [LICENSE](LICENSE).
