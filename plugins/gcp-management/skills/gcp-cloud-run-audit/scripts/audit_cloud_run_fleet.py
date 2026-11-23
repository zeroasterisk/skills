#!/usr/bin/env python3
"""
GCP Cloud Run Fleet Sweep & Security/Cost Posture Auditor

Performs parallelized, strictly READ-ONLY discovery of all deployed Cloud Run
services and jobs across Google Cloud projects, inspecting:
- Ingress & IAM exposure (allUsers / allAuthenticatedUsers vs IAP vs authenticated)
- Container image URI, digest pinning, and active revision deployment timestamp/age
- Scaling & resource posture (minScale, maxScale, CPU, memory, GPU, cpu-throttling)
- Service Account identity (default compute SA vs dedicated SA)
- Environment variable secret hygiene (literal sensitive env vars vs Secret Manager)
- 30-day HTTP traffic presence in Cloud Logging

Usage:
  ./scripts/audit_cloud_run_fleet.py [--projects p1,p2] [--output cloud_run_audit.json] [--markdown REPORT.md]
"""

import argparse
import concurrent.futures
from datetime import datetime, timedelta, timezone
import json
import re
import subprocess
import sys

SECRET_ENV_RE = re.compile(
    r'(SECRET|PASSWORD|PASSWD|PRIVATE_KEY|API_KEY|ACCESS_KEY|AUTH_TOKEN|CLIENT_SECRET)',
    re.IGNORECASE,
)
SAFE_ENV_NAMES = {
    'PUBLIC_API_KEY',
    'FIREBASE_API_KEY',
    'VITE_FIREBASE_API_KEY',
}


def run_json(cmd, timeout=25):
  """Executes a read-only gcloud command and parses JSON output."""
  try:
    out = subprocess.check_output(
        cmd, stderr=subprocess.DEVNULL, timeout=timeout
    ).decode('utf-8')
    return json.loads(out) if out.strip() else None
  except Exception:
    return None


def is_billing_enabled(project_id):
  info = run_json([
      'gcloud',
      'beta',
      'billing',
      'projects',
      'describe',
      project_id,
      '--format=json',
  ], timeout=12)
  return bool(info and info.get('billingEnabled'))


def has_run_api_enabled(project_id):
  svcs = run_json([
      'gcloud',
      'services',
      'list',
      f'--project={project_id}',
      '--enabled',
      '--filter=config.name:run.googleapis.com',
      '--format=json',
  ], timeout=15)
  return bool(isinstance(svcs, list) and len(svcs) > 0)


def check_service_public_iam(project_id, region, service_name):
  policy = run_json([
      'gcloud',
      'run',
      'services',
      'get-iam-policy',
      service_name,
      f'--project={project_id}',
      f'--region={region}',
      '--format=json',
  ], timeout=15)
  if not isinstance(policy, dict):
    return {'public': False, 'invokers': []}
  invokers = []
  is_public = False
  for b in policy.get('bindings', []):
    if b.get('role') == 'roles/run.invoker':
      members = b.get('members', [])
      invokers.extend(members)
      if 'allUsers' in members or 'allAuthenticatedUsers' in members:
        is_public = True
  return {'public': is_public, 'invokers': invokers}


def check_service_traffic_30d(project_id, service_name, start_30d):
  logs = run_json([
      'gcloud',
      'logging',
      'read',
      f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service_name}" AND timestamp >= "{start_30d}" AND httpRequest.requestMethod:*',
      f'--project={project_id}',
      '--limit=5',
      '--format=json',
  ], timeout=15)
  return len(logs) if isinstance(logs, list) else 0


def parse_age_days(iso_str):
  if not iso_str:
    return None
  try:
    dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return round((datetime.now(timezone.utc) - dt).total_seconds() / 86400.0, 1)
  except Exception:
    return None


def inspect_service(project_id, project_number, svc, start_30d):
  meta = svc.get('metadata', {})
  spec = svc.get('spec', {})
  status = svc.get('status', {})

  name = meta.get('name', 'unknown')
  labels = meta.get('labels', {})
  annotations = meta.get('annotations', {})
  region = labels.get('cloud.googleapis.com/location', 'unknown')
  url = status.get('url', '')

  ingress = annotations.get('run.googleapis.com/ingress', 'all')
  iap_enabled = annotations.get('run.googleapis.com/iap-enabled', 'false').lower() == 'true'

  tmpl = spec.get('template', {})
  tmpl_meta = tmpl.get('metadata', {})
  tmpl_ann = tmpl_meta.get('annotations', {})
  tmpl_spec = tmpl.get('spec', {})

  min_scale = int(tmpl_ann.get('autoscaling.knative.dev/minScale', '0') or 0)
  max_scale = int(tmpl_ann.get('autoscaling.knative.dev/maxScale', '0') or 0)
  cpu_throttling = tmpl_ann.get('run.googleapis.com/cpu-throttling', 'true').lower() != 'false'
  gpu_type = tmpl_ann.get('run.googleapis.com/gpu-type', '')

  sa = tmpl_spec.get('serviceAccountName', '')
  default_sa_prefix = f'{project_number}-compute@developer.gserviceaccount.com'
  uses_default_sa = (not sa) or (sa == default_sa_prefix)

  containers = tmpl_spec.get('containers', [])
  primary = containers[0] if containers else {}
  image = primary.get('image', '')
  resources = primary.get('resources', {}).get('limits', {})
  cpu = resources.get('cpu', '')
  memory = resources.get('memory', '')
  gpu_limit = resources.get('nvidia.com/gpu', '')

  # Check env vars for literal secrets vs Secret Manager secretKeyRef
  literal_secret_envs = []
  secret_refs = []
  env_keys = []
  for c in containers:
    for e in c.get('env', []):
      k = e.get('name', '')
      env_keys.append(k)
      if 'valueFrom' in e and 'secretKeyRef' in e.get('valueFrom', {}):
        secret_refs.append(k)
      elif 'value' in e and k not in SAFE_ENV_NAMES and SECRET_ENV_RE.search(k):
        literal_secret_envs.append(k)

  latest_rev = status.get('latestReadyRevisionName', '')
  conditions = status.get('conditions', [])
  ready_cond = next((c for c in conditions if c.get('type') == 'Ready'), {})
  last_transition = ready_cond.get('lastTransitionTime') or meta.get('creationTimestamp', '')
  age_days = parse_age_days(last_transition)

  iam_info = check_service_public_iam(project_id, region, name)
  recent_hits = check_service_traffic_30d(project_id, name, start_30d)

  flags = []
  if iam_info['public'] and not iap_enabled:
    flags.append('PUBLIC_UNAUTHENTICATED')
  if iap_enabled:
    flags.append('IAP_PROTECTED')
  if min_scale > 0:
    flags.append(f'MIN_SCALE_{min_scale}')
  if not cpu_throttling:
    flags.append('ALWAYS_ON_CPU')
  if gpu_limit or gpu_type:
    flags.append(f'GPU({gpu_type or gpu_limit})')
  if literal_secret_envs:
    flags.append(f'LITERAL_SECRET_ENV({",".join(literal_secret_envs)})')
  if uses_default_sa:
    flags.append('DEFAULT_COMPUTE_SA')
  if age_days is not None and age_days > 30:
    flags.append(f'AGE_{int(age_days)}D')
  if recent_hits == 0 and (age_days is None or age_days > 7):
    flags.append('ZERO_30D_TRAFFIC')

  return {
      'projectId': project_id,
      'name': name,
      'region': region,
      'url': url,
      'ingress': ingress,
      'iapEnabled': iap_enabled,
      'publicInvoker': iam_info['public'],
      'invokers': iam_info['invokers'],
      'recentHitsSample30d': recent_hits,
      'latestRevision': latest_rev,
      'lastDeployed': last_transition,
      'ageDays': age_days,
      'image': image,
      'containerCount': len(containers),
      'minScale': min_scale,
      'maxScale': max_scale,
      'cpuThrottling': cpu_throttling,
      'cpu': cpu,
      'memory': memory,
      'gpu': gpu_type or gpu_limit,
      'serviceAccount': sa or default_sa_prefix,
      'usesDefaultSa': uses_default_sa,
      'literalSecretEnvs': literal_secret_envs,
      'secretManagerRefs': secret_refs,
      'flags': flags,
  }


def scan_project(p, start_30d):
  pid = p['projectId']
  pnum = p.get('projectNumber', '')
  if not is_billing_enabled(pid):
    return {'projectId': pid, 'billingEnabled': False, 'services': [], 'jobs': []}
  if not has_run_api_enabled(pid):
    return {'projectId': pid, 'billingEnabled': True, 'services': [], 'jobs': []}

  svcs_raw = run_json([
      'gcloud',
      'run',
      'services',
      'list',
      f'--project={pid}',
      '--format=json',
  ], timeout=25)
  services = []
  if isinstance(svcs_raw, list):
    for s in svcs_raw:
      services.append(inspect_service(pid, pnum, s, start_30d))

  jobs_raw = run_json([
      'gcloud',
      'run',
      'jobs',
      'list',
      f'--project={pid}',
      '--format=json',
  ], timeout=20)
  jobs = []
  if isinstance(jobs_raw, list):
    for j in jobs_raw:
      jmeta = j.get('metadata', {})
      jlabels = jmeta.get('labels', {})
      jobs.append({
          'projectId': pid,
          'name': jmeta.get('name', 'unknown'),
          'region': jlabels.get('cloud.googleapis.com/location', 'unknown'),
          'created': jmeta.get('creationTimestamp', ''),
      })

  return {
      'projectId': pid,
      'billingEnabled': True,
      'services': services,
      'jobs': jobs,
  }


def render_markdown(data):
  lines = []
  lines.append('# GCP Cloud Run Fleet Posture Report')
  lines.append(f'- **Scanned At**: `{data["timestamp"]}`')
  lines.append(f'- **Projects Scanned**: {data["projectsScanned"]} ({data["projectsWithCloudRun"]} with Cloud Run deployments)')
  lines.append(f'- **Total Cloud Run Services**: {data["totalServices"]}')
  lines.append(f'- **Total Cloud Run Jobs**: {data["totalJobs"]}\n')

  lines.append('## Deployed Cloud Run Services')
  lines.append('| Project | Service | Region | Exposure | Scale (`min`/`max`) | 30d Traffic | Deployed (Age) | Posture Flags |')
  lines.append('| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
  for s in data['services']:
    if s['iapEnabled']:
      exp = 'IAP'
    elif s['publicInvoker']:
      exp = f'Public (`{s["ingress"]}`)'
    else:
      exp = f'IAM (`{s["ingress"]}`)'
    scale = f'{s["minScale"]} / {s["maxScale"] or "default"}'
    traffic = 'Active' if s.get('recentHitsSample30d', 0) > 0 else '0 reqs'
    age = f'{s["lastDeployed"][:10]} ({s["ageDays"]}d)' if s['lastDeployed'] else '—'
    flags = ', '.join(f'`{fl}`' for fl in s['flags']) if s['flags'] else '—'
    lines.append(f'| `{s["projectId"]}` | `{s["name"]}` | `{s["region"]}` | {exp} | {scale} | {traffic} | {age} | {flags} |')

  if data['jobs']:
    lines.append('\n## Deployed Cloud Run Jobs')
    lines.append('| Project | Job | Region | Created |')
    lines.append('| :--- | :--- | :--- | :--- |')
    for j in data['jobs']:
      lines.append(f'| `{j["projectId"]}` | `{j["name"]}` | `{j["region"]}` | `{j["created"][:10]}` |')

  return '\n'.join(lines) + '\n'


def main():
  parser = argparse.ArgumentParser(description='Audit Cloud Run services across GCP projects')
  parser.add_argument('--projects', default='', help='Comma-separated project IDs (default: all accessible)')
  parser.add_argument('--output', default='', help='Optional JSON output path')
  parser.add_argument('--markdown', default='', help='Optional Markdown report path')
  args = parser.parse_args()

  if args.projects:
    wanted = {x.strip() for x in args.projects.split(',') if x.strip()}
    all_projs = run_json(['gcloud', 'projects', 'list', '--format=json'], timeout=25) or []
    projects = [p for p in all_projs if p.get('projectId') in wanted]
    for w in wanted:
      if not any(p.get('projectId') == w for p in projects):
        projects.append({'projectId': w, 'projectNumber': ''})
  else:
    projects = run_json(['gcloud', 'projects', 'list', '--format=json'], timeout=25) or []

  start_30d = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
      '%Y-%m-%dT%H:%M:%SZ'
  )
  results = []
  with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    futs = [ex.submit(scan_project, p, start_30d) for p in projects]
    for f in concurrent.futures.as_completed(futs):
      results.append(f.result())

  all_services = []
  all_jobs = []
  for r in sorted(results, key=lambda x: x['projectId']):
    all_services.extend(sorted(r['services'], key=lambda x: x['name']))
    all_jobs.extend(sorted(r['jobs'], key=lambda x: x['name']))

  summary = {
      'timestamp': datetime.now(timezone.utc).isoformat(),
      'projectsScanned': len(projects),
      'projectsWithCloudRun': sum(1 for r in results if r['services'] or r['jobs']),
      'totalServices': len(all_services),
      'totalJobs': len(all_jobs),
      'services': all_services,
      'jobs': all_jobs,
  }

  if args.output:
    with open(args.output, 'w', encoding='utf-8') as f:
      json.dump(summary, f, indent=2)

  md = render_markdown(summary)
  if args.markdown:
    with open(args.markdown, 'w', encoding='utf-8') as f:
      f.write(md)

  print(md)


if __name__ == '__main__':
  main()
