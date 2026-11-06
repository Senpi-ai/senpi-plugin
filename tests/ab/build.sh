#!/usr/bin/env bash
# Builds the two plugin directories the A/B run loads, one per side:
#   A  the senpi-skills read skills (hidden-engine Python → the full MCP on dev)
#   B  this plugin, with .mcp.json pointed at the dev open-mcp
# Usage: build.sh <out-dir>   (defaults to $AB_OUT or ./.build)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PLUGIN=$(cd "$HERE/../.." && pwd)
SKILLS=${SENPI_SKILLS:-"$PLUGIN/../senpi-skills"}
# Outside the repo: senpi-plugin's own .mcp.json (the prod URL) is a project MCP config
# that Claude Code would load for any cwd inside the repo, beside the plugin's dev one.
OUT=${1:-${AB_OUT:-"$HOME/.cache/senpi-ab"}}
DEV_URL=${OPEN_MCP_DEV_URL:-https://senpi-agent-bridge.dev.senpi.ai/connector/mcp}

rm -rf "$OUT/A" "$OUT/B"; mkdir -p "$OUT/A/skills" "$OUT/B"

# A: the nine read skills, copied (tests and caches left out), under their own plugin name.
mkdir -p "$OUT/A/.claude-plugin"
cat > "$OUT/A/.claude-plugin/plugin.json" <<'EOF'
{"name": "senpi-skills", "version": "ab", "description": "A/B control: senpi-skills read skills on the full MCP", "skills": "./skills/"}
EOF
for s in quant-desk senpi-account-status senpi-improve-trades senpi-market-pulse senpi-portfolio \
         senpi-signals senpi-smart-money senpi-strategy-discover senpi-trader-research; do
  rsync -a --exclude tests --exclude __pycache__ "$SKILLS/$s/" "$OUT/A/skills/$s/"
done

# B: this plugin's skills, without its MCP server: a plugin-dir server is "dynamically
# configured" and its OAuth sign-in is not persisted, so headless runs stay anonymous.
# The dev connector is a local-scope server of $OUT instead (run.sh registers it), whose
# sign-in the keychain keeps: tools come up as mcp__senpi-dev__<tool>.
rsync -a --exclude .git --exclude tests --exclude .mcp.json "$PLUGIN/" "$OUT/B/"
python3 - "$OUT/B/.claude-plugin/plugin.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1])); d.pop("mcpServers", None)
json.dump(d, open(sys.argv[1], "w"), indent=2)
EOF

echo "A: $OUT/A  ($(ls "$OUT/A/skills" | wc -l | tr -d ' ') skills → \$SENPI_MCP_URL)"
echo "B: $OUT/B  (skills only; server senpi-dev → $DEV_URL, local scope of $OUT)"
printf '{"mcpServers":{"senpi-dev":{"type":"http","url":"%s"}}}\n' "$DEV_URL" > "$OUT/senpi-dev.mcp.json"
(cd "$OUT" && claude mcp get senpi-dev >/dev/null 2>&1 || claude mcp add --transport http --scope local senpi-dev "$DEV_URL" >/dev/null)  # for the interactive sign-in
