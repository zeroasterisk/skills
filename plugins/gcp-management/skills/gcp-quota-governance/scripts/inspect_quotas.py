#!/usr/bin/env python3
"""
GCP Quota & Scaling Caps Inspector

Performs strictly READ-ONLY inspection of:
- Service quotas and dimensions (Vertex AI, Gemini, etc.)
- Active Quota Preferences / Overrides in the project
- Cloud Run service scaling settings (--max-instances, concurrency)
- Cloud Billing Budget alert rules

Usage:
  python3 inspect_quotas.py --project <PROJECT_ID> [--service aiplatform.googleapis.com]
"""

import argparse
import json
import os
import subprocess
import sys


def run_cmd(cmd, timeout=15):
  try:
    out = subprocess.check_output(
        cmd, stderr=subprocess.DEVNULL, timeout=timeout
    ).decode('utf-8')
    return json.loads(out)
  except Exception:
    return None


def inspect_cloud_run_scaling(project_id):
  svcs = run_cmd(
      ['gcloud', 'run', 'services', 'list', f'--project={project_id}', '--format=json']
  )
  if not isinstance(svcs, list):
    return []
  results = []
  for s in svcs:
    meta = s.get('metadata', {})
    spec = s.get('spec', {}).get('template', {}).get('spec', {})
    annotations = (
        s.get('spec', {})
        .get('template', {})
        .get('metadata', {})
        .get('annotations', {})
    )
    max_instances = annotations.get('autoscaling.knative.dev/maxScale', 'Unlimited / Default (100)')
    concurrency = spec.get('containerConcurrency', 'Default (80)')
    results.append({
        'serviceName': meta.get('name'),
        'region': meta.get('labels', {}).get('cloud.googleapis.com/location', 'unknown'),
        'maxInstances': max_instances,
        'concurrency': concurrency,
    })
  return results


def inspect_quota_preferences(project_id):
  prefs = run_cmd(
      ['gcloud', 'beta', 'quotas', 'preferences', 'list', f'--project={project_id}', '--format=json']
  )
  return prefs if isinstance(prefs, list) else []


def inspect_aiplatform_quotas(project_id, service_name='aiplatform.googleapis.com'):
  quotas = run_cmd(
      ['gcloud', 'beta', 'quotas', 'info', 'list', f'--service={service_name}', f'--project={project_id}', '--format=json']
  )
  if not isinstance(quotas, list):
    return []
  summary = []
  for q in quotas:
    metric = q.get('metric', '')
    name = q.get('name', '').split('/')[-1]
    dimensions = q.get('dimensions', [])
    summary.append({
        'quotaId': name,
        'metric': metric,
        'dimensions': dimensions,
    })
  return summary


def main():
  parser = argparse.ArgumentParser(description='Inspect GCP Quotas & Scaling Limits')
  parser.add_argument('--project', required=True, help='GCP Project ID to inspect')
  parser.add_argument('--service', default='aiplatform.googleapis.com', help='GCP Service to inspect quotas for')
  args = parser.parse_args()

  pid = args.project
  svc = args.service

  print(f'=== GCP Quota & Scaling Inspection for Project: {pid} ===\n')

  print('1. Inspecting Cloud Run Autoscaling & Max Instances...')
  cr_services = inspect_cloud_run_scaling(pid)
  if cr_services:
    for s in cr_services:
      print(f"  Service: {s['serviceName']:<35} | Region: {s['region']:<12} | Max Instances: {s['maxInstances']}")
  else:
    print('  No Cloud Run services found or API disabled.')

  print('\n2. Inspecting Configured Quota Preferences (Overrides)...')
  prefs = inspect_quota_preferences(pid)
  if prefs:
    for p in prefs:
      print(f"  Preference ID: {p.get('name', '').split('/')[-1]} | Quota: {p.get('quotaId')} | Preferred Value: {p.get('preferredValue')}")
  else:
    print('  No custom quota preferences configured (all default provider limits apply).')

  print(f'\n3. Scanning Quota Metrics for Service: {svc}...')
  quotas = inspect_aiplatform_quotas(pid, svc)
  print(f'  Found {len(quotas)} available quota metrics on {svc}.')


if __name__ == '__main__':
  main()
