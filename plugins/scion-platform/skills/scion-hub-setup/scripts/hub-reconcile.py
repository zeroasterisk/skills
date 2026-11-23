#!/usr/bin/env python3
"""hub-reconcile.py — Idempotent Scion Hub bootstrap and configuration reconciler.

Runs directly on a Scion Hub host (with access to ~/.scion/hub.db, ~/.scion/hub.env,
and http://localhost:8080) to:
  1. Ensure the bootstrap admin user exists and holds the 'super-admin' role binding.
  2. Derive the HS256 user_signing_key from SCION_SERVER_SESSION_SECRET and mint a 365-day CLI JWT.
  3. Set operational defaults (default_harness_config=claude, default_template=default).
  4. Configure the max_agents_per_broker entitlement ceiling on the Hosted Broker.
  5. Configure Hub-scoped Vertex AI global region environment variables.
  6. Reconcile harness-configs (claude, antigravity, opencode) and optionally prune unused ones.
  7. Import global agent-team templates from GitHub.
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
import uuid


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile Scion Hub configuration.")
    parser.add_argument("--admin-email", required=True, help="Admin user email (e.g. ghchinoy@gmail.com)")
    parser.add_argument("--admin-name", default="Admin", help="Admin display name")
    parser.add_argument("--gcp-project", required=True, help="GCP project ID for Vertex AI (e.g. ghchinoy-genai-sa)")
    parser.add_argument("--registry", required=True, help="Container registry prefix (e.g. us-central1-docker.pkg.dev/ghchinoy-genai-sa/scion)")
    parser.add_argument("--broker-ceiling", type=int, default=100, help="max_agents_per_broker ceiling (default: 100)")
    parser.add_argument("--claude-model", default="claude-opus-5-5@default", help="Default model for claude harness")
    parser.add_argument("--antigravity-model", default="Gemini 3.8 Flash (Medium)", help="Default model for antigravity harness")
    parser.add_argument("--templates-url", default="https://github.com/ghchinoy/agent-team/tree/main/templates", help="GitHub URL for global templates")
    parser.add_argument("--prune-unused-harnesses", action="store_true", help="Delete seeded harness configs other than claude, antigravity, opencode")
    parser.add_argument("--hub-url", default="http://localhost:8080", help="Local Hub API base URL")
    args = parser.parse_args()

    db_path = os.path.expanduser("~/.scion/hub.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cur.execute("SELECT id FROM users WHERE email = ?", (args.admin_email,))
    row = cur.fetchone()
    if row:
        user_id = row["id"]
        cur.execute("UPDATE users SET role = ?, status = ? WHERE id = ?", ("admin", "active", user_id))
        conn.commit()
    else:
        user_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO users (id, email, display_name, role, status, created, last_login) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, args.admin_email, args.admin_name, "admin", "active", now_str, now_str),
        )
        conn.commit()

    cur.execute("SELECT id FROM role_definitions WHERE name = ? AND scope_type = ?", ("super-admin", "system"))
    rd_row = cur.fetchone()
    if rd_row:
        cur.execute(
            "INSERT OR IGNORE INTO role_bindings (id, role_definition_id, principal_type, principal_id, scope_type, scope_id, created_by, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), rd_row["id"], "user", user_id, "system", "", "admin-api", now_str),
        )
        conn.commit()

    cur.execute("SELECT scope_id FROM secrets WHERE key = ?", ("user_signing_key",))
    srow = cur.fetchone()
    hub_id = srow["scope_id"] if srow else ""

    cur.execute("SELECT id, name, status FROM runtime_brokers")
    brokers = [dict(r) for r in cur.fetchall()]
    broker_id = brokers[0]["id"] if brokers else None
    conn.close()

    shared_secret = ""
    hub_env_path = os.path.expanduser("~/.scion/hub.env")
    if os.path.exists(hub_env_path):
        with open(hub_env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("SCION_SERVER_SESSION_SECRET=") or line.startswith("SESSION_SECRET="):
                    shared_secret = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not shared_secret:
        raise RuntimeError("SCION_SERVER_SESSION_SECRET not found in ~/.scion/hub.env")

    signing_key = hashlib.sha256(f"scion-hub-signing-key:user_signing_key:{shared_secret}".encode()).digest()
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    claims = {
        "iss": "scion-hub",
        "sub": user_id,
        "aud": ["scion-hub-api"],
        "iat": now,
        "nbf": now,
        "exp": now + 365 * 86400,
        "jti": uuid.uuid4().hex,
        "uid": user_id,
        "email": args.admin_email,
        "name": args.admin_name,
        "role": "admin",
        "type": "cli",
        "client": "cli",
    }
    hdr_b64 = b64url(json.dumps(header, separators=(",", ":")).encode())
    clm_b64 = b64url(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{hdr_b64}.{clm_b64}"
    sig = hmac.new(signing_key, signing_input.encode("ascii"), hashlib.sha256).digest()
    token = f"{signing_input}.{b64url(sig)}"
    print(f"SCION_ADMIN_TOKEN={token}")

    def api(method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            args.hub_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}

    api("PUT", "/api/v1/admin/server-config", {
        "agent_defaults": {"default_template": "default", "default_harness_config": "claude"}
    })

    limits = api("GET", "/api/v1/admin/limits")
    for item in limits.get("items", []):
        if item["name"] == "max_agents_per_broker" and broker_id:
            lid = item["id"]
            ents = api("GET", f"/api/v1/admin/limits/{lid}/entitlements").get("items", [])
            existing = next((e for e in ents if e.get("subjectId") == broker_id and e.get("scopeId") == broker_id), None)
            payload = {
                "subjectType": "user",
                "subjectId": broker_id,
                "scopeType": "broker",
                "scopeId": broker_id,
                "value": args.broker_ceiling,
            }
            if existing:
                api("PUT", f"/api/v1/admin/entitlements/{existing['id']}", payload)
            else:
                api("POST", f"/api/v1/admin/limits/{lid}/entitlements", payload)

    hub_env = {
        "GOOGLE_CLOUD_PROJECT": args.gcp_project,
        "GOOGLE_CLOUD_REGION": "global",
        "GOOGLE_CLOUD_LOCATION": "global",
        "CLOUD_ML_REGION": "global",
        "ANTHROPIC_VERTEX_PROJECT_ID": args.gcp_project,
    }
    for k, v in hub_env.items():
        api("PUT", f"/api/v1/env/{k}", {
            "value": v,
            "scope": "hub",
            "scopeId": hub_id,
            "injectionMode": "always",
        })

    hcs = api("GET", "/api/v1/harness-configs").get("harnessConfigs", [])
    desired_hcs = {
        "claude": {
            "harness": "claude",
            "image": f"{args.registry}/scion-claude:latest",
            "user": "scion",
            "model": args.claude_model,
            "auth_selected_type": "vertex-ai",
        },
        "antigravity": {
            "harness": "antigravity",
            "image": f"{args.registry}/scion-antigravity:latest",
            "user": "scion",
            "model": args.antigravity_model,
            "auth_selected_type": "vertex-ai",
        },
        "opencode": {
            "harness": "opencode",
            "image": f"{args.registry}/scion-opencode:latest",
            "user": "scion",
            "model": "",
            "auth_selected_type": "",
        },
    }
    existing_by_name = {h["name"]: h for h in hcs}
    for name, cfg in desired_hcs.items():
        h_type = cfg["harness"]
        h_img = cfg["image"]
        h_usr = cfg["user"]
        h_mod = cfg["model"]
        h_auth = cfg["auth_selected_type"]
        yaml_lines = [f"harness: {h_type}", f"image: {h_img}", f"user: {h_usr}"]
        if h_mod:
            yaml_lines.append(f'model: "{h_mod}"')
        if h_auth:
            yaml_lines.append(f"auth_selected_type: {h_auth}")
        yaml_content = "\n".join(yaml_lines) + "\n"

        if name in existing_by_name:
            hid = existing_by_name[name]["id"]
        else:
            created = api("POST", "/api/v1/harness-configs", {
                "name": name,
                "slug": name,
                "harness": h_type,
                "scope": "global",
                "config": {
                    "harness": h_type,
                    "image": h_img,
                    "user": h_usr,
                    "model": h_mod,
                    "authSelectedType": h_auth,
                },
            })
            hid = created.get("harnessConfig", created)["id"]

        api("PUT", f"/api/v1/harness-configs/{hid}/files/config.yaml", {"content": yaml_content})
        hc_full = api("GET", f"/api/v1/harness-configs/{hid}")
        hc_full["harness"] = h_type
        hc_full["config"] = {
            "harness": h_type,
            "image": h_img,
            "user": h_usr,
            "model": h_mod,
            "authSelectedType": h_auth,
        }
        api("PUT", f"/api/v1/harness-configs/{hid}", hc_full)

    if args.prune_unused_harnesses:
        for h in hcs:
            if h["name"] not in desired_hcs:
                try:
                    api("DELETE", f"/api/v1/harness-configs/{h['id']}?deleteFiles=true")
                except urllib.error.HTTPError:
                    pass

    if args.templates_url:
        res_tpl = api("POST", "/api/v1/resources/import", {
            "kind": "template",
            "sourceUrl": args.templates_url,
            "scope": "global",
            "overwrite": True,
            "force": True,
        })
        print("Imported global templates:", json.dumps(res_tpl))


if __name__ == "__main__":
    main()
