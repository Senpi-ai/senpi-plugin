# Findings and refusals

Every finding carries `code`, `severity`, `stage`, `file`, `line`, `what`, `why` and `fix`. The
`fix` is computed against your actual package: apply it first. The tables below are the short form.

- A code starting `E_` is an error. At upload, any error means nothing was stored. At validation,
  any error makes the verdict FAIL.
- A code starting `W_` is a warning. The package still runs; read it and fix what it points at.
- If the same code comes back after two attempts to fix it, stop editing. Tell the user what is
  blocking in the finding's own `what` and `fix` words.
- A code not on this page: follow its `what`, `why` and `fix`.

## Upload refusals

The call is refused before the package is checked. The tool error message starts with the code.

| Code | Cause | Do this |
|---|---|---|
| `E_PACKAGE_TOO_LARGE` | more than 40 files or more than 512 KB in all | drop files you do not need; shorten long files |
| `E_PACKAGE_FILE` | a file over 128 KB, not UTF-8 text, with a NUL byte, or with an extension other than `.py` `.yaml` `.yml` `.json` `.md` `.txt` | fix that file |
| `E_PACKAGE_PATH` | a path that is absolute, has `..`, has a part starting with `.`, has other characters, or appears twice | use plain relative paths like `scanners/scan.py` |
| `E_PACKAGE_LAYOUT` | no `strategy.yaml` at the root, or not exactly one `runtime.yaml` | flatten to one instance |
| `E_PACKAGE_NOT_FOUND` | no package with that id on the user's agent (replaced or removed) | upload the files again and use the new id |
| `E_PACKAGE_BUSY` | another validation is running on the agent | call again in a minute |
| `E_PACKAGE_NOT_VALIDATED` | (starting simulations) the package's last validation failed | fix, upload, validate to PASS |
| `E_RUNTIME_TOO_OLD` | the user's agent does not know these tools yet | tell the user it needs an update; do not retry in a loop |
| `INVALID_REQUEST` | malformed arguments | fix the call |

Starting simulations with a `package_id` the agent no longer has answers that the package is not on
the box: upload the files again and use the new id.

## The recipe (static)

| Code | Cause | Do this |
|---|---|---|
| `E_VALIDATE_YAML_SYNTAX` | `runtime.yaml` does not parse | fix the YAML at the line given |
| `E_VALIDATE_SCHEMA` | a field breaks the schema (wrong type, out of range, removed name) | fix the field named; see [runtime-yaml.md](runtime-yaml.md) |
| `E_VALIDATE_DUP_SCANNER_NAME` | two scanners share a name | rename one |
| `E_VALIDATE_DUP_ACTION_NAME` | two actions share a name | rename one |
| `E_VALIDATE_PROMPT_PLACEHOLDER` | an action prompt names a placeholder nothing supplies | use `decision_mode: rule` and drop the prompt |
| `E_VALIDATE_EXIT_PRESET` | the exit block is missing or invalid | copy a preset from [dsl-presets.yaml](dsl-presets.yaml) |
| `E_VALIDATE_NO_DSL_EXIT` | no DSL exit block | add `exit: {engine: dsl, dsl_preset: ...}` and a position tracker |
| `E_VALIDATE_UNSIZED` | an entry action with no way to size a trade | add `strategy.margin_pct`, or emit `marginPct` from the scanner |
| `E_VALIDATE_UNGATED` | an entry action with no `risk.guard_rails` | add the block ([exits-and-risk.md](exits-and-risk.md)) |
| `E_VALIDATE_ENTRYPOINT_MISSING` | the scanner's `entrypoint` file is not in the package | upload `scanners/scan.py` or fix `path` / `entrypoint` |
| `E_VALIDATE_UNRESOLVABLE_SCANNER_PATH` | the scanner `path` cannot be resolved | use `./scanners` |
| `E_VALIDATE_MARGIN_PCT_FRACTION` | `strategy.margin_pct` below 1, read as a percent | write `20` for 20% |
| `E_VALIDATE_LIMIT_OPEN_UNSUPPORTED` | entry `order_type: LIMIT` | use `FEE_OPTIMIZED_LIMIT` or `MARKET` |
| `E_VALIDATE_LLM_NO_MODEL` | an action in `llm` mode with no model | use `decision_mode: rule` |
| `E_VALIDATE_WALLET_UNBOUND` | the wallet the manifest expects is not the one the recipe binds | `strategy.wallet: "${<ID>_WALLET}"`, no `instances:` |
| `E_VALIDATE_SCANNER_ENABLED` | a scanner entry has an `enabled` key | delete the key |
| `E_VALIDATE_PACKAGE_ID_CASE` | the `strategy.yaml` id has capitals | lowercase it |
| `E_VALIDATE_NO_RECIPE`, `E_VALIDATE_AMBIGUOUS_RECIPE` | no runtime file, or more than one | one `runtime.yaml` at the root |
| `E_VALIDATE_UNREADABLE_MANIFEST` | `strategy.yaml` does not load | `id` and `version` present, no `simulation` key, valid YAML |
| `E_VALIDATE_INSTANCE_DIR_COLLISION` | two instances in one folder | flat package, no `instances:` |

## The code (import)

| Code | Cause | Do this |
|---|---|---|
| `E_VALIDATE_SYNTAX` | a `.py` file under the scanner folder does not compile, even one never imported | fix it or remove it |
| `E_VALIDATE_IMPORT_FAILED` | importing `scan.py` raised | the finding names the file and line; usually a missing file or a bad import |
| `E_VALIDATE_SCAN_MISSING` | no `scan` function | define `def scan(inputs, ctx):` |
| `E_VALIDATE_SCAN_NOT_CALLABLE` | `scan` is not a function | make it one |
| `E_VALIDATE_SCAN_BAD_ARITY` | `scan` does not take exactly `(inputs, ctx)` | fix the signature |
| `E_VALIDATE_IMPORT_TIMEOUT` | importing never finished | remove work at module level |
| `W_VALIDATE_SCANNERS_IS_PACKAGE` | an `__init__.py` in the scanner folder | delete it; import siblings by name |
| `W_VALIDATE_SHADOWS_STDLIB` | a file named like a standard module | rename it |
| `W_VALIDATE_NON_MCP_SOURCE` | data fetched outside `ctx.senpi_mcp` | read only through `ctx.senpi_mcp.call_tool` |

## The live tick

| Code | Cause | Do this |
|---|---|---|
| `E_VALIDATE_TICK_EXCEPTION` | the tick raised | fix the line in the finding |
| `E_VALIDATE_TICK_TIMEOUT` | the tick ran past `timeout_seconds` | cut reads per tick ([scanner-contract.md](scanner-contract.md)) |
| `E_VALIDATE_TICK_UNRESPONSIVE` | the tick stopped responding | look for a loop or a blocking call |
| `E_VALIDATE_TICK_UNPROVEN` | a clean tick that read nothing: verdict UNPROVEN | let `ctx.dry_run` skip the early return the finding names |
| `E_VALIDATE_EGRESS_BLOCKED` | the scanner tried to send data out | remove it |
| `E_VALIDATE_MCP_PERMISSION` | the scanner called a tool that changes something | remove the call; the runtime trades |
| `E_VALIDATE_MCP_TOOL_ERROR` | every read failed | check tool names and arguments against [scanner-tools.md](scanner-tools.md) |
| `E_VALIDATE_UNKNOWN_MCP_TOOL` | a tool that does not exist | use a name from [scanner-tools.md](scanner-tools.md) |
| `E_VALIDATE_UNKNOWN_TICKER` | a read named an instrument the venue does not carry | check it with `list_instruments`; use the exact name |
| `E_VALIDATE_UNIVERSE_NOT_LIVE` | a ticker written in the package is not live | replace or remove it |
| `E_VALIDATE_SIGNAL_REJECTED` | a signal the runtime would refuse | fix the key the finding names: `direction`, `marginPct`, or a `data` key against `signal_data_schema` |
| `W_VALIDATE_SUPPRESSED_EXCEPTION` | an exception was raised and caught | fix the cause; a caught error looks healthy in a real run |
| `W_VALIDATE_MCP_TOOL_ERROR` | some reads failed | check the failing tool and arguments |
| `W_VALIDATE_UNUSED_MCP_RESPONSE` | a response was fetched and none of it read | the code reads keys the answer does not have |
| `W_VALIDATE_MISSING_RESPONSE_KEY` | it emitted nothing having read keys no row carried | fix the key names against [scanner-tools.md](scanner-tools.md) |
| `W_VALIDATE_STRING_NUMERICS` | numbers arrived as text | read them through `_f()` |
| `W_VALIDATE_NO_SIGNALS_EMITTED` | a clean tick emitted nothing | fine for a quiet market; on a new scanner, check every key it reads |
| `W_VALIDATE_SIGNALS_WITHOUT_READS` | signals emitted having read nothing | signals must come from data |
| `W_VALIDATE_NO_EXTERNAL_SCANNERS` | no scanner of your own | add the `external_scanner` |
| `W_VALIDATE_MARGIN_PCT_SUSPICIOUS` | a signal's `marginPct` below 1 | write `10` for 10% |
| `W_VALIDATE_UNIVERSE_UNCHECKED` | the ticker check could not read the package | fix the package error reported with it |

## Not the package

These say the environment failed, not the code. Do not edit the package for them. Validate again
later, and if it repeats, tell the user.

`W_VALIDATE_UNIVERSE_UNAVAILABLE`, `E_VALIDATE_NO_CREDENTIALS`, `E_VALIDATE_ENV_MISSING_SDK`,
`E_VALIDATE_IMPORT_HARNESS_FAILED`, `W_VALIDATE_PROOF_NOT_RECORDED`.

## Proof

| Code | Cause | Do this |
|---|---|---|
| `E_VALIDATE_NO_PROOF` | this exact package was never validated | validate it |
| `E_VALIDATE_CONTENT_CHANGED` | the files changed since the last PASS | validate the new package |
| `E_VALIDATE_RUNTIME_VERSION_CHANGED` | the agent's runtime was updated since the PASS | validate again |
