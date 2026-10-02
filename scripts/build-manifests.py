#!/usr/bin/env python3
"""Derive every host-specific manifest from the portable ones.

Source of truth: plugin.json (Agent Plugins schema; OpenAI metadata under
extensions["com.openai"]) and mcp.json. Generated so they never drift:

  .claude-plugin/plugin.json        Claude Code (+ Anthropic directory listing fields)
  .claude-plugin/marketplace.json   Claude Code marketplace (install as senpi-agent@senpi)
  .codex-plugin/plugin.json         Codex CLI / ChatGPT desktop (interface at top level)
  .agents/plugins/marketplace.json  Codex / ChatGPT marketplace index
  .cursor-plugin/plugin.json        Cursor / Grok Bot marketplace (plated logo + MCP path)
  .grok-plugin/plugin.json          Grok Build — xAI plugin marketplace
  .mcp.json                         Claude Code, Cursor, Grok Build, Codex (mcpServers only)

.mcp.json spells the remote transport as "http": Claude Code's loader and the
Anthropic directory validator accept http|sse|ws only. The root mcp.json keeps
the Agent Plugins spelling ("streamable-http") for hosts that read the standard.

Run after editing plugin.json or mcp.json:  python3 scripts/build-manifests.py
Pass --check to fail (exit 1) if any committed copy is stale. CI runs --check.
"""
import json, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
plugin = json.loads((root / "plugin.json").read_text())
mcp = json.loads((root / "mcp.json").read_text())
iface = plugin["extensions"]["com.openai"]["interface"]
common = {k: plugin[k] for k in ("name", "version", "description", "author", "homepage", "repository", "license", "keywords") if k in plugin}
# Asset paths come from plugin.json only, so this script names no image file
# (the directory validator holds a plugin whose scripts name bundled images).
logo = iface["logo"]
plated_logo = plugin["extensions"]["ai.senpi"]["platedLogo"]  # Cursor wants a plated 1:1 logo

def claude_mcp(servers):
    out = {}
    for name, s in servers.items():
        t = s.get("type", "streamable-http")
        c = {"type": {"streamable-http": "http", "http": "http", "sse": "sse"}[t], "url": s["url"]}
        if s.get("headers"):
            c["headers"] = s["headers"]
        out[name] = c
    return out

outputs = {
    root / ".claude-plugin" / "plugin.json": {
        **common,
        "displayName": iface["displayName"],
        "icon": logo,
        # The homepage sits behind a Cloudflare challenge that automated checks may not pass;
        # the README is the public documentation the directory can fetch.
        "documentationUrl": "https://github.com/Senpi-ai/senpi-plugin#readme",
        "supportUrl": iface["supportURL"],
        "privacyPolicyUrl": iface["privacyPolicyURL"],
        "termsOfServiceUrl": iface["termsOfServiceURL"],
        "skills": "./skills/",
        "mcpServers": "./.mcp.json",
    },
    root / ".claude-plugin" / "marketplace.json": {
        "name": "senpi",
        "description": plugin["description"],
        "owner": {"name": plugin["author"]["name"], "url": plugin["author"].get("url", "")},
        "plugins": [{
            "name": plugin["name"],
            "source": "./",
            "displayName": iface["displayName"],
            "description": iface["shortDescription"],
            "version": plugin["version"],
            "author": {"name": plugin["author"]["name"]},
            "homepage": plugin["homepage"],
            "license": plugin["license"],
            "category": "finance",
            "keywords": plugin["keywords"],
        }],
    },
    root / ".codex-plugin" / "plugin.json": {**common, "skills": "./skills/", "interface": iface},
    root / ".agents" / "plugins" / "marketplace.json": {
        "name": "senpi",
        "interface": {"displayName": iface["displayName"]},
        "plugins": [{
            "name": plugin["name"],
            "source": {"source": "local", "path": "./"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": iface["category"],
        }],
    },
    root / ".cursor-plugin" / "plugin.json": {**common, "logo": plated_logo, "skills": "./skills/", "mcpServers": "./.mcp.json"},
    root / ".grok-plugin" / "plugin.json": {**common, "skills": "./skills/", "mcpServers": "./.mcp.json"},
    root / ".mcp.json": {"mcpServers": claude_mcp(mcp["mcpServers"])},
}

check = "--check" in sys.argv
stale = []
for path, data in outputs.items():
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if check:
        if not path.exists() or path.read_text() != text:
            stale.append(str(path.relative_to(root)))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print("wrote", path.relative_to(root))
if check and stale:
    print("stale generated manifests (run scripts/build-manifests.py):", ", ".join(stale))
    sys.exit(1)
