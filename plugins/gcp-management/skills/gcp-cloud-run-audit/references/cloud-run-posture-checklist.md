# Cloud Run Fleet Posture Checklist & Remediation Reference

## 1. Exposure & Authentication Posture

| Posture Flag | Meaning | Recommended Action |
| :--- | :--- | :--- |
| `PUBLIC_UNAUTHENTICATED` | `allUsers` or `allAuthenticatedUsers` holds `roles/run.invoker` and IAP is disabled. | Confirm the service is intentionally public. For internal tools, remove `allUsers` and enable Cloud Run native IAP (`--iap`). |
| `IAP_PROTECTED` | `run.googleapis.com/iap-enabled: "true"` is set. | Verify IAM `roles/iap.httpsResourceAccessor` is scoped to authorized users/groups. |

```bash
# Remove public unauthenticated access from an internal Cloud Run service
gcloud run services remove-iam-policy-binding <SERVICE> \
  --region=<REGION> \
  --project=<PROJECT_ID> \
  --member="allUsers" \
  --role="roles/run.invoker"
```

---

## 2. Scaling, GPU & Idle Cost Guardrails

| Posture Flag | Meaning | Cost Impact & Action |
| :--- | :--- | :--- |
| `MIN_SCALE_<N>` | `autoscaling.knative.dev/minScale` is $\ge 1$. | Keeps $N$ instances warm 24/7. Keep `minScale=1` only for latency-critical gateways or keepalive loops; scale to `0` for dev/staging or low-traffic services. |
| `ALWAYS_ON_CPU` | `run.googleapis.com/cpu-throttling: "false"` | Bills for CPU throughout the full instance lifetime rather than only during request processing. Required only when background goroutines/threads run between requests. |
| `GPU(...)` | Attached NVIDIA L4 or RTX PRO 6000 GPU. | Always pair GPU services with `--min-instances=0` (scale-to-zero) and a strict `--max-instances` cap (`1–3`) unless serving continuous production traffic. |

```bash
# Reset a service to scale-to-zero and request-scoped CPU billing
gcloud run services update <SERVICE> \
  --region=<REGION> \
  --project=<PROJECT_ID> \
  --min-instances=0 \
  --cpu-throttling
```

---

## 3. Identity, Secrets & Runtime Freshness

- **`LITERAL_SECRET_ENV(...)`**: Migrate sensitive literal environment variables to Google Cloud Secret Manager:
  ```bash
  gcloud run services update <SERVICE> \
    --region=<REGION> \
    --project=<PROJECT_ID> \
    --update-secrets=<ENV_NAME>=<SECRET_NAME>:latest
  ```
- **`DEFAULT_COMPUTE_SA`**: Replace the default Compute Engine service account (`<project-number>-compute@developer.gserviceaccount.com`, which often carries broad Editor permissions) with a dedicated, least-privilege service account:
  ```bash
  gcloud run services update <SERVICE> \
    --region=<REGION> \
    --project=<PROJECT_ID> \
    --service-account=<DEDICATED_SA>@<PROJECT_ID>.iam.gserviceaccount.com
  ```
- **`AGE_<N>D` (Runtime CVE Drift)**: When a base runtime security release drops (such as Node.js `v22.23.4` / `v24.22.1` on October 21, 2026), any Node-based Cloud Run revision deployed prior to that date should be rebuilt (`--no-cache` or updated base digest) and redeployed.
