#!/usr/bin/env bash
# Runs each question through side A (senpi-skills → full MCP on dev) and side B
# (this plugin → open-mcp on dev), back to back, headless. Each run's full
# stream goes to <out>/<id>.<side>.jsonl; the answer and the tool calls it made
# go to <out>/<id>.<side>.json. judge.py then scores the pairs.
#
#   run.sh [-o out-dir] [-s "A B"|A|B] [-q id,id,...]
#
# Both sides need SENPI_AUTH_TOKEN_FILE (a dev Privy token; ~/.senpi-dev-token by
# default, valid an hour). Side A passes it to the senpi-skills engines; side B
# trades it for a connector token before each question (signin.py).
#
# The runs are read-only by construction: the only tools allowed are the skills,
# file reads, python3 (the senpi-skills engines) and the plugin's MCP server.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
BUILD=${AB_OUT:-"$HOME/.cache/senpi-ab"}
OUT="$HERE/out/$(date +%Y%m%d-%H%M)"; SIDES="A B"; ONLY=""
while getopts "o:s:q:" f; do case $f in o) OUT=$OPTARG;; s) SIDES=$OPTARG;; q) ONLY=$OPTARG;; esac; done
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
[ -d "$BUILD/A" ] || "$HERE/build.sh" "$BUILD" >/dev/null

TOKEN_FILE=${SENPI_AUTH_TOKEN_FILE:-"$HOME/.senpi-dev-token"}
MCP_A=${SENPI_MCP_URL:-https://mcp.dev.senpi.ai/mcp}
ALLOW_A="Skill,Read,Glob,Grep,Bash(python3:*),Bash(cd:*)"
ALLOW_B="Skill,Read,Glob,Grep,mcp__senpi-tok"
SYS="You are being run headless for a test. Answer the question fully in your final message with every number, name and label the tools returned. Never ask a clarifying question; never ask whether to continue; never stop at a plan. If a tool fails, say which tool and what it returned."

run_one() {  # id side question
  local id=$1 side=$2 q=$3 raw="$OUT/$1.$2.jsonl"
  # B: only the senpi-dev server, by explicit config (its OAuth sign-in is keyed by name+URL,
  # so the keychain token from the one-time interactive sign-in is used). Arrays start
  # non-empty: bash 3 + set -u.
  local env=(AB_SIDE="$2") allow=$ALLOW_B mcpflag=(--strict-mcp-config --mcp-config "$BUILD/senpi-dev.mcp.json" --max-turns 40)
  if [ "$side" = A ]; then
    env=(SENPI_MCP_URL="$MCP_A"); allow=$ALLOW_A; mcpflag=(--strict-mcp-config --max-turns 40)   # no MCP servers at all on A
    [ -r "$TOKEN_FILE" ] && env+=(SENPI_AUTH_TOKEN="$(cat "$TOKEN_FILE")")
  fi
  if [ "$side" = B ]; then
    # A fresh connector token per run (signin.py: the dev OAuth flow approved with the
    # Privy token), sent as a header on a server named senpi-tok: the name keeps Claude
    # Code from reusing an expired keychain sign-in held for senpi-dev.
    local tok="$OUT/.tok.$id" cfg="$OUT/.mcp.$id.json"
    python3 "$HERE/signin.py" "$TOKEN_FILE" "$tok" || { echo "$id B: sign-in failed" >&2; return 0; }
    (umask 077; printf '{"mcpServers":{"senpi-tok":{"type":"http","url":"%s","headers":{"Authorization":"Bearer %s"}}}}' \
      "${OPEN_MCP_DEV_URL:-https://senpi-agent-bridge.dev.senpi.ai/connector/mcp}" "$(cat "$tok")" > "$cfg")
    mcpflag=(--strict-mcp-config --mcp-config "$cfg" --max-turns 40)
  fi
  local t0=$(date +%s)
  (cd "$BUILD" && env "${env[@]}" claude -p "$q" \
      --plugin-dir "$BUILD/$side" --setting-sources project \
      --append-system-prompt "$SYS" \
      --allowedTools "$allow" "${mcpflag[@]}" --no-session-persistence \
      --output-format stream-json --verbose < /dev/null > "$raw" 2> "$OUT/$id.$side.err") || true   # </dev/null: claude -p would eat the questions on stdin
  [ "$side" = B ] && rm -f "$OUT/.tok.$id" "$OUT/.mcp.$id.json"   # the token never outlives its run
  python3 - "$raw" "$OUT/$id.$side.json" "$id" "$side" "$q" $(( $(date +%s) - t0 )) <<'EOF'
import json, sys
raw, dst, qid, side, q, secs = sys.argv[1:7]
answer, tools, cost, texts = "", [], None, []
for line in open(raw):
    try: m = json.loads(line)
    except ValueError: continue
    if m.get("type") == "assistant":
        for b in m.get("message", {}).get("content", []):
            # A skill that answers in stages (the quant desk) writes one message per stage:
            # the answer is every message, not just the last one.
            if b.get("type") == "text" and b.get("text", "").strip():
                texts.append(b["text"].strip())
            if b.get("type") == "tool_use":
                i = b.get("input", {})
                tools.append({"tool": b["name"], "input": i if b["name"] != "Bash" else {"command": i.get("command", "")[:300]}})
    elif m.get("type") == "result":
        answer = m.get("result") or ""; cost = m.get("total_cost_usd")
if len(texts) > 1:
    answer = "\n\n".join(texts)
json.dump({"id": qid, "side": side, "question": q, "seconds": int(secs), "cost_usd": cost,
           "tools": tools, "answer": answer}, open(dst, "w"), indent=1)
print(f"{qid:12s} {side}  {secs:>4}s  {len(tools):>2} tool calls  {len(answer):>5} chars" + ("" if answer else "  ← EMPTY ANSWER"))
EOF
}

# questions.json is a list of {id, auth, skill, question}; one tab-separated row each.
python3 -c 'import json, sys
for r in json.load(open(sys.argv[1])):
    print("\t".join([r["id"], r["auth"], r["skill"], r["question"]]))' "$HERE/questions.json" |
while IFS=$'\t' read -r id auth skill q; do
  [ -n "$ONLY" ] && [[ ",$ONLY," != *",$id,"* ]] && continue
  for side in $SIDES; do run_one "$id" "$side" "$q"; done
done
echo "→ $OUT"
