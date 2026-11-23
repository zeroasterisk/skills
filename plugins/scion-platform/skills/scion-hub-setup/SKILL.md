---
name: scion-hub-setup
description: Bootstrap, upgrade, and reconcile self-hosted Scion Hub deployments on GCE, including clean database resets, selective container image builds (claude, antigravity, opencode), headless super-admin JWT derivation, Vertex AI global region configuration, broker quota ceilings, and global agent-team template imports.
license: Apache-2.0
compatibility: Requires python3, gcloud, jq, curl, and bash.
metadata:
  author: ghchinoy
  version: "1.1.0"
---

# Scion Hub Bootstrap, Upgrade & Reconciliation (`scion-hub-setup`)

This skill provides an end-to-end operational guide and idempotent Python reconciliation script for standing up, upgrading, or reconciling a self-hosted Scion Hub instance (combo Hub + Runtime Broker + Web UI) on Google Cloud Compute Engine (GCE).

---

## 1. Prerequisites

1. **`gcloud` CLI authenticated** with access to the target GCP project and GCE instance.
2. **Passphrase-less SSH key for non-interactive GCE automation**:
   If `~/.ssh/google_compute_engine` is passphrase-protected, generate an ephemeral key so non-interactive `gcloud compute ssh` commands do not hang on passphrase prompts:
   ```bash
   ssh-keygen -t ed25519 -f /tmp/gce_tmp_key -N "" -q
   ```
3. **Local checkout of `GoogleCloudPlatform/scion`** (`./scripts/starter-hub/gce-start-hub.sh`).

---

## 2. Helper Scripts

- [`scripts/hub-reconcile.py`](scripts/hub-reconcile.py) — Idempotent Python reconciliation script that executes on the Hub VM (or via SSH stdin) to:
  1. Ensure the bootstrap admin user exists in `~/.scion/hub.db` and holds the `super-admin` system role binding (`role_bindings`).
  2. Deterministically derive the HS256 `user_signing_key` from `SCION_SERVER_SESSION_SECRET` (`~/.scion/hub.env`) and mint a 365-day CLI JWT token.
  3. Configure `server-config` operational defaults (`default_harness_config`, `default_template`).
  4. Create the per-broker `max_agents_per_broker` entitlement binding (e.g. `100` or `200`, overriding the upstream default ceiling of `12`).
  5. Set Hub-scoped Vertex AI `global` region environment variables (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_REGION=global`, `GOOGLE_CLOUD_LOCATION=global`, `CLOUD_ML_REGION=global`, `ANTHROPIC_VERTEX_PROJECT_ID`).
  6. Update global harness configs (`claude` → `claude-opus-5-5@default`, `antigravity` → `Gemini 3.8 Flash (Medium)`, `opencode`), write their `config.yaml` files, and optionally prune unused seeded harness configs.
  7. Batch-import all 13 global `agent-team` templates (`coordinator`, `eng-manager`, `developer`, `code-reviewer`, `architect`, `investigator`, `qa-tester`, `test-engineer`, `doc-writer`, `researcher`, `security-auditor`, `release-notes`, `web-builder`).

---

## 3. End-to-End Reconciliation Workflow

### Phase 1: Hub Server Upgrade & Optional Clean Database Reset

1. **Back up the existing SQLite database and point the VM's checkout to upstream**:
   ```bash
   CLOUDSDK_CORE_PROJECT=<gcp-project> gcloud compute ssh scion@<vm-name> \
     --zone=<zone> --ssh-key-file=/tmp/gce_tmp_key --command='
       cp ~/.scion/hub.db ~/.scion/hub.db.bak-$(date +%Y%m%d) || true
       cd /home/scion/scion && git remote set-url origin https://github.com/GoogleCloudPlatform/scion.git
     '
   ```
2. **Deploy the latest `main` build** (add `--reset-db` only when wiping an unused/drifted database):
   ```bash
   CLOUDSDK_CORE_PROJECT=<gcp-project> PROJECT_ID=<gcp-project> \
     HUB_NAME=<hub-short-name> CERT_DOMAIN=<hub-domain> HUB_DOMAIN=<hub-domain> \
     ./scripts/starter-hub/gce-start-hub.sh --full --reset-db --branch main
   ```

---

### Phase 2: Build & Push Harness Container Images

Build `core-base`, `scion-base`, and the desired agent harnesses (`claude`, `antigravity`, `opencode`) directly on the GCE VM and push to Artifact Registry:

```bash
CLOUDSDK_CORE_PROJECT=<gcp-project> gcloud compute ssh scion@<vm-name> \
  --zone=<zone> --ssh-key-file=/tmp/gce_tmp_key --command='
    cd /home/scion/scion
    for target in core-base scion-base claude antigravity opencode; do
      ./image-build/scripts/build-images.sh \
        --registry us-central1-docker.pkg.dev/<gcp-project>/scion \
        --target "$target" \
        --push
    done
  '
```

---

### Phase 3: Run Idempotent Hub Reconciliation (`hub-reconcile.py`)

Pipe [`scripts/hub-reconcile.py`](scripts/hub-reconcile.py) over SSH to bootstrap the admin user, derive the CLI token, configure quotas, environment variables, harness configs, and global `agent-team` templates:

```bash
CLOUDSDK_CORE_PROJECT=<gcp-project> gcloud compute ssh scion@<vm-name> \
  --zone=<zone> --ssh-key-file=/tmp/gce_tmp_key \
  --command='python3 - --admin-email ghchinoy@gmail.com --gcp-project <gcp-project> --registry us-central1-docker.pkg.dev/<gcp-project>/scion --broker-ceiling 100 --prune-unused-harnesses' \
  < ./scripts/hub-reconcile.py
```

Save the emitted `SCION_ADMIN_TOKEN=<jwt>` in `~/.scion/credentials.json` under both `"https://<hub-domain>"` and `"https://<hub-domain>/"`.

---

### Phase 4: Verify Agent Service Account IAM Bindings

Ensure the Hub VM's service account (`<vm-sa>@<gcp-project>.iam.gserviceaccount.com`) holds `roles/iam.serviceAccountTokenCreator` on each agent runner service account so the Hub can mint GCP tokens for agent containers:

```bash
for SA in scion-agent-runner@<gcp-project>.iam.gserviceaccount.com sa-scion-warmup@<gcp-project>.iam.gserviceaccount.com; do
  gcloud iam service-accounts add-iam-policy-binding "$SA" \
    --project="<gcp-project>" \
    --member="serviceAccount:<vm-sa>@<gcp-project>.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --condition=None \
    --quiet
done
```
