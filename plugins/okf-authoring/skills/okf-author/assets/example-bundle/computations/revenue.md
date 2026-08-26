---
type: Attested Computation
title: Revenue for fiscal year
description: Recognized revenue for a fiscal year, per Finance's definition.
tags: [finance, revenue]
status: stable
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-15T14:30:00Z }
verified:
  - { by: process:finance-nightly, at: 2026-08-15T02:00:00Z }
stale_after: 2026-12-31
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: Revenue recognition policy
---

# Computation

    SELECT SUM(total_usd) AS revenue
    FROM sales.orders
    WHERE EXTRACT(YEAR FROM placed_at) = @year

The computation binds only the declared `parameters`, per the recognition
policy.[^rev-policy]

Used by the [revenue metric](/metrics/revenue.md). Derived trust tier (not
stored): **machine-confirmed** — `verified` has only non-`human:` actors.

[^rev-policy]: Revenue recognition policy
