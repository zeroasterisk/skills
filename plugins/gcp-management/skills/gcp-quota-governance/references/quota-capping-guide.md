# Google Cloud Quotas & Spend Capping Guide

This reference provides technical guidance on how to enforce **hard caps, rate limits, and auto-scaling constraints** on Google Cloud Platform and Vertex AI.

---

## 1. Cloud Quotas API (`gcloud beta quotas`)

Google Cloud Quotas API allows declaring downward quota preferences. Unlike quota increases (which require manual approval), **quota decreases are fulfilled immediately**.

### Key Quota IDs for Vertex AI (`aiplatform.googleapis.com`)

| Quota ID | Metric Description | Dimensions |
| :--- | :--- | :--- |
| `OnlinePredictionRequestsPerMinutePerProjectPerRegion` | Online prediction requests/min in a region | `region` |
| `GenerateContentRequestsPerMinutePerProjectPerRegionPerBaseModel` | Gemini/Multimodal request rate per model | `base_model`, `region` |
| `GlobalOnlinePredictionTokensPerMinutePerBaseModel` | Global token throughput per minute | `base_model` |
| `OnlinePredictionInputTokensPerMinutePerRegionPerBaseModel` | Input token rate per minute | `base_model`, `region` |
| `AnthropicMaasConcurrentBatchPredictionJobs` | Concurrent Claude batch prediction jobs | None (Project-wide) |

---

## 2. Command Syntax for Setting Quota Caps

### A. Cap Regional Online Prediction Requests (Vertex AI / Claude)
```bash
gcloud beta quotas preferences create \
  --service=aiplatform.googleapis.com \
  --project=<PROJECT_ID> \
  --quota-id=OnlinePredictionRequestsPerMinutePerProjectPerRegion \
  --dimensions=region=us-central1 \
  --preferred-value=50 \
  --allow-high-percentage-quota-decrease
```
*Effect:* Any requests exceeding 50 requests/min in `us-central1` return HTTP 429 `RESOURCE_EXHAUSTED` instead of incurring billing fees.

### B. Cap Specific Model Request Rates (e.g. Gemini 1.5 Pro)
```bash
gcloud beta quotas preferences create \
  --service=aiplatform.googleapis.com \
  --project=<PROJECT_ID> \
  --quota-id=GenerateContentRequestsPerMinutePerProjectPerRegionPerBaseModel \
  --dimensions=base_model=gemini-1.5-pro,region=us-central1 \
  --preferred-value=10 \
  --allow-high-percentage-quota-decrease
```

---

## 3. Cloud Run Service Scaling Constraints

Cloud Run defaults to a maximum of 100 container instances. To prevent runaway costs during traffic spikes, enforce explicit instance caps:

```bash
# Cap service to 2 maximum instances
gcloud run services update <SERVICE_NAME> \
  --project=<PROJECT_ID> \
  --region=<REGION> \
  --max-instances=2 \
  --concurrency=80
```

---

## 4. Quota Reversion & Resetting

To remove a custom quota preference and restore default provider quotas:

```bash
gcloud beta quotas preferences create \
  --service=aiplatform.googleapis.com \
  --project=<PROJECT_ID> \
  --quota-id=<QUOTA_ID> \
  --dimensions=<DIMENSIONS> \
  --preferred-value=-1
```
*(`-1` indicates reset to default/unlimited).*
