#!/usr/bin/env bash
# Builds the one plugin archive that installs in both Claude and ChatGPT: a
# single senpi-agent/ folder holding
#
#   .claude-plugin/plugin.json   Claude's manifest
#   .codex-plugin/plugin.json    OpenAI's manifest (mcpServers -> ./.mcp.json)
#   .mcp.json                    the server, shared by both
#   skills/ assets/ README.md LICENSE
#
# .mcp.json keeps Claude's transport spelling ("http", which OpenAI's plugin
# docs use too) and adds OpenAI's sign-in hint from mcp.json
# (extensions["com.openai"].auth: CIMD, since the auth service has
# registration off). Claude ignores the hint. The repo's own .mcp.json is not
# changed: Cursor and Grok Build read it as it is.
#
# Usage: ./scripts/package-plugin.sh [--mcp-url URL] [output.zip]
#   --mcp-url  point the archive at another server (the dev connector)
set -euo pipefail
cd "$(dirname "$0")/.."

MCP_URL=""
if [[ "${1:-}" == "--mcp-url" ]]; then
  MCP_URL="${2:?--mcp-url needs a URL}"
  shift 2
fi
VERSION=$(python3 -c "import json; print(json.load(open('plugin.json'))['version'])")
OUT="${1:-dist/senpi-agent-${VERSION}.zip}"
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
P="$STAGE/senpi-agent"
mkdir -p "$P/.claude-plugin" "$P/.codex-plugin"
cp .claude-plugin/plugin.json "$P/.claude-plugin/"
cp -R skills assets README.md LICENSE "$P/"

python3 - "$P" "$MCP_URL" <<'EOF'
import json, sys
p, url = sys.argv[1], sys.argv[2]

codex = json.load(open(".codex-plugin/plugin.json"))
codex["mcpServers"] = "./.mcp.json"  # as OpenAI's plugin docs declare it
open(f"{p}/.codex-plugin/plugin.json", "w").write(json.dumps(codex, indent=2, ensure_ascii=False) + "\n")

servers = {}
portable = json.load(open("mcp.json"))["mcpServers"]
for name, s in json.load(open(".mcp.json"))["mcpServers"].items():
    s = dict(s)
    if "extensions" in portable.get(name, {}):
        s["extensions"] = portable[name]["extensions"]
    if url:
        s["url"] = url
    servers[name] = s
open(f"{p}/.mcp.json", "w").write(json.dumps({"mcpServers": servers}, indent=2) + "\n")
EOF

rm -f "$OUT"
(cd "$STAGE" && zip -q -X -r - senpi-agent) > "$OUT"

python3 - "$OUT" <<'EOF'
import json, re, sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
names = set(z.namelist())
need = ["senpi-agent/.claude-plugin/plugin.json", "senpi-agent/.codex-plugin/plugin.json", "senpi-agent/.mcp.json"]
missing = [n for n in need if n not in names]
if missing:
    sys.exit(f"missing: {missing}")
for m in need[:2]:
    for ref in re.findall(r'"\./([^"]+)"', z.read(m).decode()):
        ref = ref.rstrip("/")
        if not any(n == f"senpi-agent/{ref}" or n.startswith(f"senpi-agent/{ref}/") for n in names):
            sys.exit(f"{m} names ./{ref}, which is not in the archive")
skills = sorted(n.split("/")[2] for n in names if re.fullmatch(r"senpi-agent/skills/[^/]+/SKILL\.md", n))
url = [s["url"] for s in json.loads(z.read("senpi-agent/.mcp.json"))["mcpServers"].values()]
print(f"{sys.argv[1]}: {len(skills)} skills, server {', '.join(url)}")
EOF
