#!/usr/bin/env python3
"""
GCP & Firebase Portfolio Audit Script

Performs parallelized, strictly READ-ONLY discovery across Google Cloud and Firebase projects:
- Project & Billing account status
- Week-over-Week Spend Velocity & Trend Analysis (via BigQuery Billing Export)
- Billing Budgets & Threshold Alert configurations
- Compute Engine VMs, Persistent Disks, Cloud Run, App Engine, Cloud Functions, GCS Buckets, Static IPs
- 30-day Cloud Logging HTTP/API traffic detection
- Firebase Services (Firestore DBs, Registered Apps, Hosting Domains)

Output:
- Saves detailed JSON to gcp_audit_results.json
- Prints summary table to stdout

Usage:
  python3 audit_portfolio.py [--output gcp_audit_results.json]
"""

import argparse
import concurrent.futures
from datetime import datetime, timedelta, timezone
import json
import os
import subprocess
import sys


def run_cmd(cmd, timeout=15):
  """Executes a shell command and returns parsed JSON or raw string."""
  try:
    out = subprocess.check_output(
        cmd, stderr=subprocess.DEVNULL, timeout=timeout
    ).decode('utf-8')
    return json.loads(out)
  except Exception:
    return None


def query_bigquery_billing():
  """Queries itemized 30-day spend from BigQuery billing export if available."""
  sql = """
  SELECT
    IFNULL(project.id, "Shared / Unassigned") AS project_id,
    service.description AS service_description,
    ROUND(SUM(cost), 2) AS gross_cost_usd,
    ROUND(SUM(cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost_usd
  FROM
    `simple-node-001.billingexport.gcp_billing_export_v1_00615D_35664D_BF0DF0`
  WHERE
    _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY
    project_id, service_description
  HAVING
    gross_cost_usd > 0 OR net_cost_usd > 0
  ORDER BY
    net_cost_usd DESC
  """
  try:
    out = subprocess.check_output(
        ['bq', 'query', '--use_legacy_sql=false', '--format=json', sql],
        stderr=subprocess.DEVNULL,
        timeout=20,
    ).decode('utf-8')
    return json.loads(out)
  except Exception:
    return []


def query_bigquery_trends():
  """Queries Week-over-Week spend velocity (last 7 days vs previous 7 days) for high-cost projects."""
  sql = """
  SELECT
    IFNULL(project.id, "Shared / Unassigned") AS project_id,
    service.description AS service_description,
    ROUND(SUM(CASE WHEN _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) THEN cost ELSE 0 END), 2) AS cost_last_7d,
    ROUND(SUM(CASE WHEN _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY) AND _PARTITIONTIME < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) THEN cost ELSE 0 END), 2) AS cost_prev_7d
  FROM
    `simple-node-001.billingexport.gcp_billing_export_v1_00615D_35664D_BF0DF0`
  WHERE
    _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
  GROUP BY
    project_id, service_description
  HAVING
    cost_last_7d > 0 OR cost_prev_7d > 0
  ORDER BY
    cost_last_7d DESC
  """
  try:
    out = subprocess.check_output(
        ['bq', 'query', '--use_legacy_sql=false', '--format=json', sql],
        stderr=subprocess.DEVNULL,
        timeout=20,
    ).decode('utf-8')
    return json.loads(out)
  except Exception:
    return []


def get_billing_accounts():
  accs = run_cmd(['gcloud', 'billing', 'accounts', 'list', '--format=json'])
  if not accs:
    return {}
  return {
      a['name'].replace('billingAccounts/', ''): (
          a.get('displayName', ''),
          a.get('open', False),
      )
      for a in accs
  }


def get_billing_budgets(billing_acc_id):
  """Queries configured billing budgets and threshold alerts for a billing account."""
  raw = run_cmd([
      'gcloud',
      'billing',
      'budgets',
      'list',
      f'--billing-account={billing_acc_id}',
      '--billing-project=generative-bazaar-001',
      '--format=json',
  ])
  if not isinstance(raw, list):
    return []
  budgets = []
  for b in raw:
    budgets.append({
        'displayName': b.get('displayName'),
        'amount': b.get('amount', {}),
        'filter': b.get('budgetFilter', {}),
        'thresholds': b.get('thresholdRules', []),
    })
  return budgets


def describe_project_billing(pid, billing_accs):
  info = run_cmd([
      'gcloud',
      'beta',
      'billing',
      'projects',
      'describe',
      pid,
      '--format=json',
  ])
  if not info:
    return {'billingAccountId': '', 'billingAccountName': '', 'enabled': False}
  b_id = info.get('billingAccountName', '').replace('billingAccounts/', '')
  b_name, _ = billing_accs.get(b_id, ('Unknown', False))
  return {
      'billingAccountId': b_id,
      'billingAccountName': b_name,
      'enabled': info.get('billingEnabled', False),
  }


def scan_single_project(p, billing_accs, start_30d):
  pid = p['projectId']
  b_info = describe_project_billing(pid, billing_accs)

  res = {
      'projectId': pid,
      'name': p.get('name', ''),
      'projectNumber': p.get('projectNumber', ''),
      'createTime': p.get('createTime', ''),
      'billingEnabled': b_info['enabled'],
      'billingAccountName': b_info['billingAccountName'],
      'compute_vms': [],
      'disks': [],
      'cloud_run': [],
      'app_engine': [],
      'functions': [],
      'buckets_count': 0,
      'static_ips': [],
      'http_requests_30d': 0,
      'has_recent_logs': False,
      'firestore_dbs': [],
      'firebase_apps': [],
      'firebase_hosting_sites': [],
  }

  if not b_info['enabled']:
    return res

  # Check enabled services
  apis_raw = run_cmd([
      'gcloud',
      'services',
      'list',
      f'--project={pid}',
      '--enabled',
      '--format=json',
  ])
  apis_set = (
      {s['config']['name'] for s in apis_raw} if isinstance(apis_raw, list) else set()
  )

  # Compute Engine VMs & Disks
  if 'compute.googleapis.com' in apis_set:
    vms = run_cmd(
        ['gcloud', 'compute', 'instances', 'list', f'--project={pid}', '--format=json']
    )
    if isinstance(vms, list):
      res['compute_vms'] = [
          {
              'name': v['name'],
              'zone': v['zone'].split('/')[-1],
              'status': v['status'],
          }
          for v in vms
      ]

    disks = run_cmd(
        ['gcloud', 'compute', 'disks', 'list', f'--project={pid}', '--format=json']
    )
    if isinstance(disks, list):
      res['disks'] = [
          {
              'name': d['name'],
              'sizeGb': d['sizeGb'],
              'zone': d['zone'].split('/')[-1],
              'inUse': bool(d.get('users')),
          }
          for d in disks
      ]

    addrs = run_cmd(
        ['gcloud', 'compute', 'addresses', 'list', f'--project={pid}', '--format=json']
    )
    if isinstance(addrs, list):
      res['static_ips'] = [
          {
              'name': a['name'],
              'address': a['address'],
              'status': a.get('status'),
          }
          for a in addrs
      ]

  # Cloud Run
  if 'run.googleapis.com' in apis_set:
    svcs = run_cmd(
        ['gcloud', 'run', 'services', 'list', f'--project={pid}', '--format=json']
    )
    if isinstance(svcs, list):
      res['cloud_run'] = [
          {
              'name': s['metadata']['name'],
              'region': s['metadata']
              .get('labels', {})
              .get('cloud.googleapis.com/location', 'unknown'),
          }
          for s in svcs
      ]

  # App Engine
  if 'appengine.googleapis.com' in apis_set:
    apps = run_cmd(
        ['gcloud', 'app', 'services', 'list', f'--project={pid}', '--format=json']
    )
    if isinstance(apps, list):
      res['app_engine'] = [{'id': a['id']} for a in apps]

  # Cloud Functions
  if 'cloudfunctions.googleapis.com' in apis_set:
    funcs = run_cmd(
        ['gcloud', 'functions', 'list', f'--project={pid}', '--format=json']
    )
    if isinstance(funcs, list):
      res['functions'] = [{'name': f['name'].split('/')[-1]} for f in funcs]

  # Storage Buckets
  buckets = run_cmd(
      ['gcloud', 'storage', 'buckets', 'list', f'--project={pid}', '--format=json']
  )
  if isinstance(buckets, list):
    res['buckets_count'] = len(buckets)

  # Cloud Logging 30d HTTP traffic
  logs = run_cmd([
      'gcloud',
      'logging',
      'read',
      f'timestamp >= "{start_30d}" AND httpRequest.requestMethod:*',
      f'--project={pid}',
      '--limit=10',
      '--format=json',
  ])
  if isinstance(logs, list) and logs:
    res['http_requests_30d'] = len(logs)
    res['has_recent_logs'] = True

  # Firestore
  dbs = run_cmd(
      ['gcloud', 'firestore', 'databases', 'list', f'--project={pid}', '--format=json']
  )
  if isinstance(dbs, list):
    res['firestore_dbs'] = [
        {
            'name': d['name'].split('/')[-1],
            'type': d.get('type'),
            'location': d.get('locationId'),
        }
        for d in dbs
    ]

  # Firebase Apps
  fb_apps = run_cmd(['firebase', 'apps:list', f'--project={pid}', '--json'])
  if isinstance(fb_apps, dict) and 'result' in fb_apps:
    res['firebase_apps'] = [
        {
            'appId': a.get('appId'),
            'displayName': a.get('displayName'),
            'platform': a.get('platform'),
        }
        for a in fb_apps['result']
    ]

  # Firebase Hosting
  fb_sites = run_cmd(['firebase', 'hosting:sites:list', f'--project={pid}', '--json'])
  if (
      isinstance(fb_sites, dict)
      and 'result' in fb_sites
      and 'sites' in fb_sites['result']
  ):
    res['firebase_hosting_sites'] = [
        {
            'name': s.get('name', '').split('/')[-1],
            'defaultUrl': s.get('defaultUrl'),
        }
        for s in fb_sites['result']
    ]

  return res


def main():
  parser = argparse.ArgumentParser(description='GCP Portfolio Audit Script')
  parser.add_argument(
      '--output',
      default='gcp_audit_results.json',
      help='Path to output JSON file',
  )
  args = parser.parse_args()

  start_30d = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
      '%Y-%m-%dT%H:%M:%SZ'
  )

  print('[1/5] Fetching GCP projects and billing accounts...')
  projects = run_cmd(['gcloud', 'projects', 'list', '--format=json'])
  if not projects:
    print('Error: Could not retrieve gcloud projects list.', file=sys.stderr)
    sys.exit(1)

  billing_accs = get_billing_accounts()
  print(f'Discovered {len(projects)} total projects.')

  print('[2/5] Inspecting Billing Budgets & Alerts across Billing Accounts...')
  billing_budgets = {}
  for acc_id, (acc_name, is_open) in billing_accs.items():
    if is_open:
      b_list = get_billing_budgets(acc_id)
      if b_list:
        billing_budgets[acc_id] = {'accountName': acc_name, 'budgets': b_list}

  print(
      '[3/5] Querying BigQuery Billing Export for itemized spend & spend'
      ' trends...'
  )
  billing_export_spend = query_bigquery_billing()
  billing_export_trends = query_bigquery_trends()

  print('[4/5] Concurrently scanning resources across projects (READ-ONLY)...')
  results = []
  with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(scan_single_project, p, billing_accs, start_30d)
        for p in projects
    ]
    for future in concurrent.futures.as_completed(futures):
      results.append(future.result())

  output_data = {
      'timestamp': datetime.now(timezone.utc).isoformat(),
      'projects': results,
      'billing_budgets': billing_budgets,
      'billing_export_spend': billing_export_spend,
      'billing_export_trends': billing_export_trends,
  }

  print(f'[5/5] Writing audit data to {args.output}...')
  with open(args.output, 'w') as f:
    json.dump(output_data, f, indent=2)

  enabled_count = sum(1 for r in results if r['billingEnabled'])
  active_traffic = sum(1 for r in results if r['http_requests_30d'] > 0)

  print('\n=== GCP & Firebase Audit Summary ===')
  print(f'Total Projects: {len(results)}')
  print(f'Billing Enabled: {enabled_count}')
  print(f'Configured Billing Budgets Found: {len(billing_budgets)}')
  print(f'Projects with Active 30d HTTP Traffic: {active_traffic}')


if __name__ == '__main__':
  main()
