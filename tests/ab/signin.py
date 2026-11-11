#!/usr/bin/env python3
"""Signs side B in to the dev connector without a browser.

    signin.py <privy-token-file> <out-token-file>

Runs dev auth-service's OAuth code flow (Claude Code's client, PKCE) and
approves it with the dev Privy token, as senpi-web's consent page does, then
writes the connector access token (15 minutes) to <out-token-file>, mode 600.
run.sh calls it before each side-B question, so a headless run never depends
on a keychain sign-in that has expired.

curl, not urllib: dev's Cloudflare refuses Python's default client.
"""
import base64, hashlib, json, os, re, secrets, subprocess, sys, tempfile, urllib.parse

AS = os.environ.get("SENPI_AUTH_URL", "https://senpi-auth-service.dev.senpi.ai")
RES = os.environ.get("OPEN_MCP_DEV_URL", "https://senpi-agent-bridge.dev.senpi.ai/connector/mcp")
CID = "https://claude.ai/oauth/claude-code-client-metadata"
RED = "http://127.0.0.1:53682/callback"
JAR = tempfile.mkstemp(suffix=".jar")[1]


def req(url, data=None, headers=None, method=None):
    """One request, no redirects followed: (status, headers, body)."""
    cmd = ["curl", "-s", "-b", JAR, "-c", JAR, "-D", "-", "-o", "-", "-X", method or ("POST" if data else "GET"), url]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if data:
        cmd += ["--data-binary", "@-"]
    out = subprocess.run(cmd, input=data, capture_output=True).stdout.decode(errors="replace")
    head, _, body = out.partition("\r\n\r\n")
    lines = head.split("\r\n")
    status = int(lines[0].split()[1]) if lines and len(lines[0].split()) > 1 else 0
    hdrs = {l.split(":", 1)[0].strip().title(): l.split(":", 1)[1].strip() for l in lines[1:] if ":" in l}
    return status, hdrs, body


def main():
    privy = open(sys.argv[1]).read().strip()
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    q = urllib.parse.urlencode({"response_type": "code", "client_id": CID, "redirect_uri": RED, "scope": "agent:read",
                                "code_challenge": challenge, "code_challenge_method": "S256", "state": "ab", "resource": RES})
    status, h, body = req(f"{AS}/oauth/authorize?{q}")
    m = re.search(r"(?:interaction/|uid=)([A-Za-z0-9_-]{8,})", h.get("Location", ""))
    if not m:
        sys.exit(f"authorize {status}: no interaction ({body[:200]})")
    status, h, body = req(f"{AS}/oauth/interaction/{m.group(1)}/decision", json.dumps({"allow": True}).encode(),
                          {"Authorization": "Bearer " + privy, "Content-Type": "application/json", "Origin": AS}, "POST")
    if status != 200:
        sys.exit(f"decision {status}: {body[:200]} (is the Privy token expired?)")
    url = json.loads(body)["redirectTo"]
    for _ in range(6):
        status, h, body = req(url)
        url = urllib.parse.urljoin(url, h.get("Location", ""))
        if url.startswith(RED):
            break
    code = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("code", [None])[0]
    if not code:
        sys.exit(f"no code: {url[:160]}")
    status, h, body = req(f"{AS}/oauth/token", urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": code, "redirect_uri": RED, "client_id": CID,
        "code_verifier": verifier, "resource": RES}).encode(), {"Content-Type": "application/x-www-form-urlencoded"}, "POST")
    tok = json.loads(body).get("access_token") if body.startswith("{") else None
    if not tok:
        sys.exit(f"token {status}: {body[:200]}")
    fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, tok.encode())
    os.close(fd)


if __name__ == "__main__":
    try:
        main()
    finally:
        os.unlink(JAR)
