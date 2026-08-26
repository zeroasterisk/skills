# GCP Project Decommissioning & Cleanup Checklist

This checklist guides the safe, permanent shutdown of retired or duplicate Google Cloud projects without unintended data loss or blocker errors.

---

## 1. Pre-Decommissioning Discovery

Before shutting down a project, verify the following:
- [ ] **No Active HTTP Traffic:** Confirm 30-day request log query returns zero incoming requests:
  ```bash
  gcloud logging read 'timestamp >= "YYYY-MM-DDT00:00:00Z" AND httpRequest.requestMethod:*' --project=<PROJECT_ID> --limit=5
  ```
- [ ] **Storage Backup:** Verify Cloud Storage buckets do not contain critical archives:
  ```bash
  gcloud storage ls --project=<PROJECT_ID>
  ```
- [ ] **Firestore / Datastore Backup:** Export database if records must be retained:
  ```bash
  gcloud firestore export gs://<BACKUP_BUCKET>/backups/<PROJECT_ID> --project=<PROJECT_ID>
  ```

---

## 2. Check & Remove Project Liens

Projects linked to certain Google services (e.g., Dialogflow CX/ES agents, Firebase associations) may have **liens** placed on them that prevent deletion.

### Check for Active Liens:
```bash
gcloud alpha resource-manager liens list --project=<PROJECT_ID>
```

### If a Lien Exists:
```text
Example error:
A lien to prevent deletion was placed on the project by [You cannot delete this project because it is linked with a Dialogflow agent...].
```
1. Delete the Dialogflow agent or linked service via the web console.
2. Or delete the lien directly if safe:
   ```bash
   gcloud alpha resource-manager liens delete <LIEN_NAME> --project=<PROJECT_ID>
   ```

---

## 3. Unlink Billing vs. Project Deletion

### Option A: Unlink Billing ($0 Cost, Retain Configuration)
If you want to keep the project configuration without incurring any costs:
```bash
gcloud beta billing projects unlink <PROJECT_ID>
```
*Note: Unlinked projects immediately stop paid compute, but retain IAM, APIs, and resource definitions.*

### Option B: Permanent Deletion
To completely remove the project and clean up console dropdowns:
```bash
gcloud projects delete <PROJECT_ID> --quiet
```
*(Note: GCP provides a 30-day recovery window during which a project can be undeleted via `gcloud projects undelete <PROJECT_ID>` before permanent erasure).*
