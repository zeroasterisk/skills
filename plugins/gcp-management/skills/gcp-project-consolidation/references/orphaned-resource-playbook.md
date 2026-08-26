# Orphaned Cloud Resource Detection & Elimination Playbook

This playbook provides actionable steps to detect and eliminate dormant assets that silently accumulate monthly billing charges.

---

## 1. Persistent Disks on Terminated / Stopped VMs

### The Problem:
Stopping or terminating a Compute Engine VM (`gcloud compute instances stop`) **only stops the hourly CPU/RAM compute charge**.  
**Attached persistent disks continue to incur monthly $/GB storage fees!**

### Detection:
```bash
# List all disks and check if they are in use by active VMs
gcloud compute disks list --project=<PROJECT_ID> --format="table(name,sizeGb,zone,users)"
```

### Elimination:
```bash
# Delete persistent disk
gcloud compute disks delete <DISK_NAME> --zone=<ZONE> --project=<PROJECT_ID> --quiet
```
*(Note: If billing is disabled on the project, you cannot mutate disks via Compute Engine API. In that case, deleting the project via `gcloud projects delete` will automatically destroy all attached disks).*

---

## 2. Unassigned Static IP Addresses

### The Problem:
Google Cloud charges an hourly fee for **reserved static external IP addresses that are not attached to a running VM or forwarding rule**.

### Detection:
```bash
gcloud compute addresses list --project=<PROJECT_ID> --filter="status:RESERVED"
```

### Elimination:
```bash
gcloud compute addresses delete <ADDRESS_NAME> --region=<REGION> --project=<PROJECT_ID> --quiet
```

---

## 3. Idle Cloud SQL Instances

### The Problem:
Cloud SQL instances incur continuous hourly compute and storage charges even when idle or receiving zero queries.

### Detection:
```bash
gcloud sql instances list --project=<PROJECT_ID>
```

### Action:
```bash
# Stop instance (can be restarted later)
gcloud sql instances patch <INSTANCE_NAME> --activation-policy=NEVER --project=<PROJECT_ID>
```

---

## 4. Unused Cloud Storage Buckets

### The Problem:
Forgotten buckets containing multi-gigabyte logs, build artifacts, or stale database backups incur monthly storage fees.

### Detection:
```bash
gcloud storage buckets list --project=<PROJECT_ID>
```

### Elimination:
```bash
# Recursively delete bucket and all objects
gcloud storage rm -r gs://<BUCKET_NAME>
```
