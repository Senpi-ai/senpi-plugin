# Changelog

## 0.5.1 — 2026-11-13

- Skills: the reads the original Senpi skills make — the full market read (the day, the last four hours, signals in brief), the staged Quant Desk, copy-trade vetting, catalog filters, and the portfolio's money map and strategy groups.
- Account status no longer lists plans or prices. A question about plans gets a link to senpi.ai/pricing, and the skill links to no payment page.
- OpenAI review cases: exactly five positive and three negative, written for a demo account with no strategies. The Codex manifest carries them.
- README: example prompts and a troubleshooting section. Support is at senpi.ai/resources/support.
- Repository: `scripts/package.py` replaces the two shell packaging scripts and builds the same archives. The A/B test harness moved to the `ab-harness` branch.

## 0.5.0 — 2026-11-06

- The plugin points at Senpi's read-only research server, `https://mcp.senpi.ai/mcp`, and ships ten skills: market pulse, signals, smart money, trader research, Quant Desk, strategy discovery, portfolio, trade review, account status, and why Senpi.
- No trading, approval or messaging tools.

## 0.4.0 — 2026-10-19

- Research first: every workflow has its own tool.

## 0.3.0 — 2026-10-02

- First release: one plugin for Claude Code, Claude, ChatGPT, Codex, Cursor, Grok Bot and Grok Build.
