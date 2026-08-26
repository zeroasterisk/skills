---
name: ai-pop-publisher
description: Sub-skill for publishing compiled AI Pop web player assets (web/dist) to a public hosting endpoint (Firebase Hosting or GCS static website bucket) and verifying liveness.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# AI Pop Publisher

This skill deploys compiled web player static assets (`web/dist`) to a public hosting endpoint and returns the live URL.

## Supported Deployment Targets

The skill supports multi-tier hosting adapters:

- **Tier 1 (Primary): Firebase Hosting** (`target: "firebase"`)
  - Provides clean HTTPS URLs, CDN edge distribution, and single-command SPA routing.
- **Tier 1 (Fallback / Direct GCS): GCS Static Website Bucket** (`target: "gcs"`)
  - Direct sync to a public static-website-configured GCS bucket (`storage.googleapis.com/<bucket>/<slug>/index.html`).
- **Tier 2 (Extensible): Third-Party Static Hosts** (`target: "vercel" | "cloudflare" | "netlify"`)
  - CLI adapters for external static site hosting services.

## Instructions

1. **Verify Build Output:**
   * Confirm `web/dist/index.html` exists and is non-empty.
   * Verify all bundled assets (`.js`, `.css`, `.mp3`, `.png`) are present in `web/dist/assets/`.

2. **Resolve Deployment Strategy:**
   * Read target from request context or environment (`AIPOP_DEPLOY_TARGET`).
   * Default strategy: Try **Firebase Hosting** first if `firebase.json` or `FIREBASE_TOKEN`/service account key is available; otherwise fall back to **GCS Static Website Bucket** using `AIPOP_RESULTS_BUCKET` or `GENMEDIA_BUCKET`.

3. **Deploy - Strategy A: Firebase Hosting:**
   * Ensure `firebase.json` exists in `web/` or project root configured to point `public` to `dist`.
   * Run deployment command:
     ```bash
     firebase deploy --only hosting --non-interactive
     ```
   * Extract the published Hosting URL (e.g. `https://<site-id>.web.app`).

4. **Deploy - Strategy B: GCS Static Website Bucket:**
   * Derive a unique URL path slug using artist name and timestamp (e.g. `velvet-decibels-20260813`).
   * Sync static assets to the public results bucket:
     ```bash
     gcloud storage rsync -r web/dist/ gs://<bucket_name>/<artist-slug>/
     ```
   * Construct the public HTTPS web URL: `https://storage.googleapis.com/<bucket_name>/<artist-slug>/index.html`.

5. **Liveness Verification:**
   * Issue a HTTP HEAD request to the published URL (`curl -s -I <URL>`).
   * Confirm response status code is `200 OK`.

6. **Return Deliverable:**
   * Output a structured JSON response and human-readable summary with the verified live URL.
