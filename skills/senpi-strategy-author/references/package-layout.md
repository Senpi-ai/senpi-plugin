# Package layout

A package is the files of one strategy, uploaded together. The upload takes them as a list of
`{path, content}` pairs; `content` is the file's full text.

## The flat layout

```
strategy.yaml          # the manifest
runtime.yaml           # the one runtime file
scanners/scan.py       # exports scan(inputs, ctx)
scanners/scoring.py    # optional pure helpers, imported as `import scoring`
```

- One `runtime.yaml`, at the root. The runtime builds the single instance, named `main`, from it.
- No `instances:` list in `strategy.yaml` and no instance folders. A package with more than one
  runtime file, or none, is refused.
- The scanner folder is the one `runtime.yaml` names in the scanner's `path` (`./scanners`).
  Files in it import each other by module name: `import scoring`.
- Extra files are allowed (a `README.md`, a `notes.txt`). They are stored and never run.

## Limits checked on upload

| Rule | Limit | Refusal |
|---|---|---|
| Number of files | 1 to 40 | `E_PACKAGE_TOO_LARGE` |
| Total size | 512 KB | `E_PACKAGE_TOO_LARGE` |
| One file | 128 KB, UTF-8 text, no NUL byte | `E_PACKAGE_FILE` |
| Extension | `.py` `.yaml` `.yml` `.json` `.md` `.txt` | `E_PACKAGE_FILE` |
| Path | relative; matches `^[A-Za-z0-9_][A-Za-z0-9_./-]{0,127}$`; no `..`; no leading `/`; no part starting with `.`; no duplicates | `E_PACKAGE_PATH` |
| Layout | `strategy.yaml` at the root and exactly one `runtime.yaml` | `E_PACKAGE_LAYOUT` |

## `strategy.yaml`

```yaml
schema_version: 1
id: funding-fade               # REQUIRED
version: "1.0.0"               # REQUIRED, quoted
catalog:                       # optional; short and honest
  name: "Funding Fade"
  belief_plain: "Shorts coins whose longs are paying extreme funding, and covers on the unwind."
requires:
  runtime: ">=3.0.0"
```

- `id` and `version` are required.
- `id` is lowercase letters, digits and hyphens. A capital letter is refused at validation.
- Keep `id` at most 24 characters. A simulation runs as `<id>-main-simulation`, and that must fit
  in 40 characters.
- Never add a `simulation:` key. The same package runs as a simulation or live; the package does
  not choose.
- Never add `instances:` for a flat package.

## Linkage in `runtime.yaml`

| Field | Value | Why |
|---|---|---|
| `name` | `<id>-main` | the runtime id of the one instance |
| `group` | `<id>` | ties the runtime to the package; simulations are grouped under it by default |
| `strategy.wallet` | `"${<ID>_WALLET}"` | the id in capitals with `_` for `-`, plus `_WALLET` |

The wallet value must be exactly one `${...}` placeholder, upper case (`A-Z`, `0-9`, `_`) and
nothing else in the string. `"${funding_fade_wallet}"` and `"pre${FUNDING_FADE_WALLET}"` are
refused. Never write an address.

## Python files

- Use the Python standard library only.
- Do not name a file after a standard-library module (`signal.py`, `random.py`, `json.py`): it
  shadows that module for everything imported after it.
- Do not add `__init__.py` to the scanner folder. It turns the folder into a package and invites
  relative imports that fail at run time.
- Do no work at module level beyond constants and function definitions. Module code runs when the
  file is imported, and an import that does not finish is a failure.
- Every file under the scanner folder must compile, even one nothing imports.

## One package per strategy id

- Uploading the same files again returns the same `package_id` and the stored result.
- A clean upload with the same `id` and different files replaces the earlier package. The
  answer's `replaced` names the old `package_id`, which stops working.
- An upload with any error-level finding stores nothing. The previous clean package of that id
  stays.
- The agent keeps up to 20 strategy ids and 10 MB of packages. Past that, the least recently
  uploaded other strategy is removed and must be uploaded again to be used.
- Simulations already started run from their own copy; replacing or removing the upload does not
  touch them.
