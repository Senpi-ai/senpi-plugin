# Senpi — AI Quant

Senpi is an AI quant engineer for Hyperliquid. This plugin connects your AI assistant — Claude, ChatGPT, Codex, Cursor, Grok Bot, Grok Build or Hermes Agent — to **your own Senpi agent**, so you can ask it what's moving, run a signals sweep, score any wallet with the Quant Desk, research traders, and work through a strategy, from the app you already use.

The agent runs on your Senpi account. This plugin only delivers your messages to it and returns its replies.

## What it does

- **Market Pulse** — a cross-asset read of the day's structure
- **Signals** — ranked market anomalies from Senpi's detector library
- **Smart Money Radar** — where the proven cohort sits against the crowd
- **Trader Research** — due diligence on any Hyperliquid wallet
- **Quant Desk** — scores a book, finds the leaks, prices the fixes
- **Strategy Discovery / Authoring** — pick from the template catalog, or build one
- **Portfolio, Trade Coaching, Account** — your own book and plan

Everything above works without depositing funds.

## Safeguards

- **Every trade or fund movement the agent proposes pauses for your approval**, one action at a time. An unanswered approval expires and the action is denied.
- **No tool here can withdraw funds.** Deposits and withdrawals happen only on senpi.ai or in the Senpi app, behind MFA.
- The agent can move funds only between your own Senpi wallets, and only with your approval.
- You can revoke any connected app in one click from Senpi → Connectors.

## What this plugin runs, sends, and fetches

- **Runs:** nothing on your machine. There are no scripts, hooks, or local servers.
- **Sends:** the messages you address to your Senpi agent, to `https://agents.senpi.ai/mcp` over HTTPS, authenticated by OAuth 2.0 with your Senpi login. Nothing else leaves your assistant.
- **Fetches:** the agent's replies, pending approvals, and session lists from the same server.

Privacy policy: <https://senpi.ai/privacy> · Terms: <https://senpi.ai/terms> · Support: <https://resources.senpi.ai/support>

## Install

Every route ends on the same Senpi sign-in, where you choose whether to grant chat access (the agent can act, with your approval) or read-only access. Manage or disconnect any time at Senpi → Connectors.

### Claude Code

```bash
claude plugin marketplace add Senpi-ai/senpi-plugin
claude plugin install senpi-agent@senpi
```

Then `/mcp` inside Claude Code to sign in. Server only, without the skill: `claude mcp add --transport http --scope user senpi-agent https://agents.senpi.ai/mcp`.

### Claude (claude.ai and Claude Desktop)

Add the plugin from **Customize → Plugins**, or add the connector directly with the URL `https://agents.senpi.ai/mcp` and sign in.

### ChatGPT

Senpi is listed as **Senpi — AI Quant**. Or, in Developer Mode: Plugins → **+** → **Create MCP app**, server URL `https://agents.senpi.ai/mcp`, authentication OAuth.

On ChatGPT and Codex the plugin is **research-only**: each workflow is its own tool (Market Pulse, signals, smart-money positioning, trader research, Quant Desk, portfolio and trade review, strategy recommendations), and nothing can place a trade, deploy a strategy or move funds; those are done in the Senpi app.

### Codex CLI

```bash
codex plugin marketplace add Senpi-ai/senpi-plugin
codex plugin add senpi-agent@senpi
codex mcp login senpi-agent
```

### Cursor and Grok Bot

Grok Bot installs connectors from the [Cursor Marketplace](https://cursor.com/marketplace). Install **Senpi — AI Quant** there, then complete the Senpi sign-in when prompted. Until the listing is live, add the server to `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "senpi-agent": { "url": "https://agents.senpi.ai/mcp" } } }
```

### Grok (grok.com) and Grok Build

- **grok.com:** Connectors → **New Connector** → **Custom** → paste `https://agents.senpi.ai/mcp` and complete sign-in.
- **Grok Build:** install **senpi-agent** from the [xAI plugin marketplace](https://github.com/xai-org/plugin-marketplace) once the catalog entry is live.

### Hermes Agent

```bash
hermes plugins install senpi
hermes plugins enable senpi-agent
```

Until the catalog entry is live, install from this repository instead: `hermes plugins install Senpi-ai/senpi-plugin --no-enable`, then `hermes plugins enable senpi-agent`. Your first message to the agent opens the Senpi sign-in in your browser; approve it, then run `/reload-mcp` or start a new session so the tools load. Ask the agent to call `read_senpi_guide` first.

The trade gate is Senpi's, server-side: every position or strategy action pauses for your allow-once through `resolve_approval`, and an unanswered approval is denied. Hermes does not add a prompt of its own before `ask_agent`; if you want one, declare the server yourself in `~/.hermes/config.yaml` with `trust: untrusted` (a server in `config.yaml` overrides the plugin's).

Server only, without the skill: `hermes mcp install senpi` once the MCP catalog entry is live, or add `https://agents.senpi.ai/mcp` under `mcp_servers` in `~/.hermes/config.yaml` with OAuth.

### Anything else that speaks MCP

Server URL `https://agents.senpi.ai/mcp`, Streamable HTTP transport, OAuth 2.0 (the MCP authorization spec, with discovery documents at `/.well-known/oauth-protected-resource/mcp`).

## What's in this repo

| Path | For |
|---|---|
| `plugin.json`, `mcp.json` | Source of truth — the [Agent Plugins](https://agent-plugins.org) standard, which is also what Hermes Agent installs as a portable package; ChatGPT metadata under `extensions["com.openai"]` |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code plugin + marketplace (generated) |
| `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` | Codex CLI and ChatGPT desktop (generated) |
| `.cursor-plugin/plugin.json` | Cursor / Grok Bot marketplace listing (generated) |
| `.grok-plugin/plugin.json` | Grok Build — xAI plugin marketplace (generated) |
| `.mcp.json` | The MCP server, for Claude Code, Cursor, Grok Build and Codex (generated) |
| `skills/senpi-agent/SKILL.md` | Teaches the assistant how to work with the agent: statuses, approvals, money rules |
| `assets/` | Logo for directory listings |

Edit `plugin.json` or `mcp.json`, then run `python3 scripts/build-manifests.py`; CI fails if the generated copies are stale.

## License

Apache-2.0. See [LICENSE](LICENSE).
