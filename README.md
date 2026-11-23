# Senpi — AI Quant

Senpi is an AI quant engineer for Hyperliquid. This plugin connects your AI assistant — Claude, ChatGPT, Codex, Cursor, Grok Bot, Grok Build or Hermes Agent — to Senpi's research tools: what's moving and why, ranked market signals, smart-money positioning, trader due diligence, the strategy catalog, and your own portfolio and trade history. It also runs simulations: variations of a strategy that trade with virtual money on your own Senpi agent, so you can find the ones that work.

Simulations use your Senpi credits. Nothing in this plugin trades real money, moves funds or takes a strategy live: those happen in your Senpi account at [senpi.ai](https://senpi.ai).

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
| **Simulations** — start variations of a strategy on virtual money, watch them, rank them to find the winners, stop the losers | `create_simulations`, `list_my_simulations`, `get_my_simulation`, `quote_simulations`, `stop_simulations`, `resume_simulation` |

Every tool runs through your connected Senpi account: the connector asks you to sign in to Senpi when you add it. The market, research and catalog tools read public data; the portfolio, trade-review, account and simulation tools read only your own account. Three tools change something: `create_simulations` and `resume_simulation` start simulations, and `stop_simulations` stops them. Every other tool is read-only.

## Example prompts

- "What's moving the markets today?"
- "Scan the market for anomalies"
- "What is smart money doing on ETH?"
- "Who were the best traders this week? Compare the top two."
- "Run Quant Desk on 0x…" with any Hyperliquid wallet address
- "How is my portfolio doing?" once you have signed in to Senpi
- "Run 5 variations of hawk as simulations and tell me which is doing best after an hour"
- "Which of my simulations are winning? Stop the rest."

## Safeguards

- **No real money.** This server exposes no tool that can place, change or close a real trade, take a strategy live, or move funds. Simulations trade with virtual money.
- **Two limits on simulations: your credits and your agent's box.** A simulation starts only while your credits cover the next hour of everything running. Simulations run on your Senpi agent's box, which grows from 4 to 8 to 16 GB to fit them; past that, the rest don't start. Nothing else caps how many you run.
- **No grace period.** When your credits run out, every simulation and strategy stops and your agent pauses.
- **Taking a simulation live happens in the Senpi app only:** open the simulation in Senpi and press Take it live. The assistant can't do it for you.
- **Every tool says what it does.** Each carries `readOnlyHint`, `destructiveHint` and `openWorldHint`. The three simulation writes are marked not read-only, and `stop_simulations` is marked destructive, so your assistant can ask before it runs them.
- Every result carries an `as_of` timestamp and is informational — not financial advice.
- Portfolio tools return data only for the account that signed in via OAuth.
- You can revoke any connected app in one click from Senpi → Connectors.

## What this plugin runs, sends, and fetches

- **Runs:** nothing on your machine. The plugin has no hooks and no local server, and no skill runs a script.
- **Sends:** tool calls to `https://mcp.senpi.ai/mcp` over HTTPS. Sign-in is OAuth 2.0 with your Senpi login and happens once, when you add the connector; every tool runs through it, and the account tools read only that account. Nothing else leaves your assistant.
- **Fetches:** market data, trader statistics, strategy catalog entries, and — when you are signed in — your own portfolio, trade history and simulations.
- **Changes:** only your own simulations, and only when your assistant calls `create_simulations`, `stop_simulations` or `resume_simulation`.

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

The plugin declares its server `trust: untrusted`, so Hermes itself asks before any tool call that can change something, such as starting or stopping a simulation.

Server only, without the skills: `hermes mcp install senpi` once the MCP catalog entry is live, or add `https://mcp.senpi.ai/mcp` under `mcp_servers` in `~/.hermes/config.yaml` with OAuth. Three tools on this server start or stop simulations; every other tool is read-only.

### Anything else that speaks MCP

Server URL `https://mcp.senpi.ai/mcp`, Streamable HTTP transport, OAuth 2.0 (the MCP authorization spec, with discovery documents at `/.well-known/oauth-protected-resource/mcp`).

## Troubleshooting

- **No sign-in prompt, or the Senpi tools are missing:** reconnect the connector. In Claude Code run `/mcp`; in Claude, open the plugin's Connectors tab; in other apps, disconnect Senpi in the connector settings and add it again.
- **"Couldn't be read right now" in an answer:** one data source did not respond for that read. The rest of the answer stands; ask again in a minute.
- **"This connection was not granted simulation access":** the connection was made before simulations, or without them. Disconnect Senpi, add it again and approve the access Senpi asks for when you sign in.
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
| `skills/` | One skill per workflow: market pulse, signals, smart money, trader research, quant desk, strategy discovery, portfolio, trade review, account status, simulations, and "why did X move" |
| `assets/` | Logo for directory listings |

`main` holds only the plugin and is what the Claude plugin directory reads. The `release` branch is `main` plus the maintainer scripts (regenerate the generated manifests from `plugin.json` and `mcp.json`, build the archive) and the `package` workflow, which builds the prod and dev archives for OpenAI and ChatGPT on every push to `release`. To ship: merge `main` into `release` and take the archive from that run. The A/B test harness lives on the `ab-harness` branch.

## License

Apache-2.0. See [LICENSE](LICENSE).
