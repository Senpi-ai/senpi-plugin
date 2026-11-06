#!/usr/bin/env bash
# Builds the archive OpenAI's "New Plugin" upload accepts: exactly one plugin
# manifest at the archive root. The generated host manifests (.claude-plugin/,
# .codex-plugin/, .cursor-plugin/, .grok-plugin/, .agents/) and the marketplace
# files must stay out — with them the uploader refuses the zip as "Expected a
# single plugin archive". Their test_cases schema also allows no extra keys
# (a `notes` field was rejected with "Extra inputs are not permitted").
#
# Usage: ./scripts/package-openai.sh [output.zip]
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import json; print(json.load(open('plugin.json'))['version'])")
OUT="${1:-senpi-agent-${VERSION}-openai.zip}"

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
cp plugin.json mcp.json README.md LICENSE "$STAGE/"
cp -R skills assets "$STAGE/"

rm -f "$OUT"
(cd "$STAGE" && zip -q -r - .) > "$OUT"

python3 - "$OUT" <<'EOF'
import json, sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
names = [n for n in z.namelist() if not n.endswith('/')]
manifests = [n for n in names if 'plugin.json' in n or 'marketplace' in n]
assert manifests == ['plugin.json'], f"expected one manifest, found {manifests}"
p = json.loads(z.read('plugin.json'))
for group in p['extensions']['com.openai']['review']['test_cases'].values():
    for case in group:
        extra = set(case) - {'description', 'prompt', 'tools_triggered', 'expected_behavior'}
        assert not extra, f"test case has keys OpenAI rejects: {extra}"
print(f"{sys.argv[1]}: {len(names)} files, single manifest, test cases clean")
EOF
