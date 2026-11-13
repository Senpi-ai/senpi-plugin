#!/usr/bin/env python3
"""Build the plugin archive from this repository.

Default layout, "codex": the one archive that installs in both Claude and
ChatGPT, a single senpi-agent/ folder holding

  .claude-plugin/plugin.json   Claude's manifest
  .codex-plugin/plugin.json    OpenAI's manifest (mcpServers -> ./.mcp.json),
                               with the review cases under extensions["com.openai"]
  .mcp.json                    the server, shared by both
  skills/ assets/ README.md LICENSE

.mcp.json keeps Claude's transport spelling ("http", which OpenAI's plugin docs
use too) and adds OpenAI's sign-in hint from mcp.json
(extensions["com.openai"].auth: CIMD, since the auth service has registration
off). Claude ignores the hint. The repo's own .mcp.json is not changed: Cursor
and Grok Build read it as it is. This is the archive to upload to OpenAI's
portal and to ChatGPT desktop.

--layout portable: the Agent Plugins package (plugin.json, mcp.json, skills/,
assets/, README.md, LICENSE at the archive root, exactly one manifest). Do not
install this one in ChatGPT desktop: its loader rejects the sign-in block in the
portable mcp.json ("unknown field extensions") and drops the server.

Usage: python3 scripts/package.py [--mcp-url URL] [--layout codex|portable] [output.zip]
  --mcp-url  point the archive at another server (the dev connector); codex layout only
"""
import argparse, json, pathlib, re, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = {".DS_Store", "Thumbs.db", "desktop.ini"}
EPOCH = (1980, 1, 1, 0, 0, 0)  # fixed, so the same tree always builds the same archive


def tree(folder):
    """Every file under ROOT/folder, as paths relative to ROOT, sorted."""
    base = ROOT / folder
    return sorted(p.relative_to(ROOT).as_posix() for p in base.rglob("*")
                  if p.is_file() and p.name not in SKIP and "__MACOSX" not in p.parts)


def write(z, name, data):
    info = zipfile.ZipInfo(name, EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, data)


def codex_members(mcp_url):
    codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
    codex["mcpServers"] = "./.mcp.json"  # as OpenAI's plugin docs declare it
    portable = json.loads((ROOT / "mcp.json").read_text())["mcpServers"]
    servers = {}
    for name, s in json.loads((ROOT / ".mcp.json").read_text())["mcpServers"].items():
        s = dict(s)
        if "extensions" in portable.get(name, {}):
            s["extensions"] = portable[name]["extensions"]
        if mcp_url:
            s["url"] = mcp_url
        servers[name] = s
    members = {
        ".claude-plugin/plugin.json": (ROOT / ".claude-plugin/plugin.json").read_bytes(),
        ".codex-plugin/plugin.json": (json.dumps(codex, indent=2, ensure_ascii=False) + "\n").encode(),
        ".mcp.json": (json.dumps({"mcpServers": servers}, indent=2) + "\n").encode(),
    }
    for path in tree("skills") + tree("assets") + ["README.md", "LICENSE"]:
        members[path] = (ROOT / path).read_bytes()
    return {f"senpi-agent/{k}": v for k, v in members.items()}


def portable_members():
    return {path: (ROOT / path).read_bytes()
            for path in ["plugin.json", "mcp.json", "README.md", "LICENSE"] + tree("skills") + tree("assets")}


def check_codex(names, read):
    need = ["senpi-agent/.claude-plugin/plugin.json", "senpi-agent/.codex-plugin/plugin.json", "senpi-agent/.mcp.json"]
    missing = [n for n in need if n not in names]
    if missing:
        sys.exit(f"missing: {missing}")
    for m in need[:2]:
        for ref in re.findall(r'"\./([^"]+)"', read(m).decode()):
            ref = ref.rstrip("/")
            if not any(n == f"senpi-agent/{ref}" or n.startswith(f"senpi-agent/{ref}/") for n in names):
                sys.exit(f"{m} names ./{ref}, which is not in the archive")
    skills = sorted(n.split("/")[2] for n in names if re.fullmatch(r"senpi-agent/skills/[^/]+/SKILL\.md", n))
    urls = [s["url"] for s in json.loads(read("senpi-agent/.mcp.json"))["mcpServers"].values()]
    return f"{len(skills)} skills, server {', '.join(urls)}"


def check_portable(names, read):
    manifests = [n for n in names if "plugin.json" in n or "marketplace" in n]
    if manifests != ["plugin.json"]:
        sys.exit(f"expected one manifest, found {manifests}")
    cases = json.loads(read("plugin.json"))["extensions"]["com.openai"]["review"]["test_cases"]
    for group in cases.values():
        for case in group:
            extra = set(case) - {"description", "prompt", "tools_triggered", "expected_behavior"}
            if extra:
                sys.exit(f"test case has keys OpenAI rejects: {extra}")
    return f"{len(names)} files, single manifest, test cases clean"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mcp-url", default="")
    ap.add_argument("--layout", choices=["codex", "portable"], default="codex")
    ap.add_argument("output", nargs="?")
    a = ap.parse_args()
    if a.layout == "portable" and a.mcp_url:
        sys.exit("--mcp-url applies to the codex layout only")
    version = json.loads((ROOT / "plugin.json").read_text())["version"]
    default = f"dist/senpi-agent-{version}.zip" if a.layout == "codex" else f"dist/senpi-agent-{version}-portable.zip"
    out = pathlib.Path(a.output or default)
    if not out.is_absolute():
        out = pathlib.Path.cwd() / out
    out.parent.mkdir(parents=True, exist_ok=True)

    members = codex_members(a.mcp_url) if a.layout == "codex" else portable_members()
    out.unlink(missing_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        for name in sorted(members):
            write(z, name, members[name])

    with zipfile.ZipFile(out) as z:
        names = sorted(z.namelist())
        summary = (check_codex if a.layout == "codex" else check_portable)(names, z.read)
    print(f"{out}: {summary}")


if __name__ == "__main__":
    main()
