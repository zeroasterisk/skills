#!/usr/bin/env python3
"""Connector for the Plushcap MCP server (Streamable HTTP + JSON-RPC).

Plushcap is an EXTERNAL remote MCP server, not a workspace MCP server, so it is
reached over HTTP rather than through call_mcp_tool.

Usage:
  python3 scripts/plushcap_mcp.py tools/list
  python3 scripts/plushcap_mcp.py tools/call '{"name":"get_trends_data","arguments":{"weeks":8}}'

Auth: reads PLUSHCAP_API_KEY from the environment, else from a `.env` file next
to the skill root (one level up from this script). Never commit the key.

Note: a browser User-Agent is required. Plushcap sits behind Cloudflare, which
returns "error 1010 / browser_signature_banned" for default library UAs.
"""
import os, sys, json, urllib.request, urllib.error

URL = os.environ.get("PLUSHCAP_MCP_URL", "https://mcp.plushcap.com/mcp")
PROTO = "2025-06-18"
_session = {"id": None}


def load_key():
    key = os.environ.get("PLUSHCAP_API_KEY", "").strip()
    if key:
        return key
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    try:
        with open(env_path) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("PLUSHCAP_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return ""


KEY = load_key()


def post(payload, notify=False):
    data = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + KEY,
        "MCP-Protocol-Version": PROTO,
        "User-Agent": os.environ.get(
            "PLUSHCAP_UA",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        ),
    }
    if _session["id"]:
        headers["Mcp-Session-Id"] = _session["id"]
    req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=90)
    except urllib.error.HTTPError as e:
        print("HTTP_ERROR", e.code, e.read().decode(errors="replace"), file=sys.stderr)
        raise
    sid = resp.headers.get("mcp-session-id") or resp.headers.get("Mcp-Session-Id")
    if sid:
        _session["id"] = sid
    raw = resp.read().decode(errors="replace")
    if notify:
        return None
    if "text/event-stream" in resp.headers.get("Content-Type", ""):
        raw = "\n".join(ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:"))
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def main():
    if not KEY:
        print("ERROR: set PLUSHCAP_API_KEY (env) or put it in <skill>/.env", file=sys.stderr)
        sys.exit(2)
    init = post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": PROTO, "capabilities": {},
                            "clientInfo": {"name": "cowork", "version": "1.0"}}})
    try:
        info = init["result"]["serverInfo"]
        print("CONNECTED:", info.get("name"), info.get("version"), file=sys.stderr)
    except Exception:
        print("INIT:", json.dumps(init)[:400], file=sys.stderr)
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, notify=True)
    method = sys.argv[1] if len(sys.argv) > 1 else "tools/list"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    print(json.dumps(post({"jsonrpc": "2.0", "id": 2, "method": method, "params": params}), indent=2))


if __name__ == "__main__":
    main()
