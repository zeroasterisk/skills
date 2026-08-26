---
type: Reference
title: Run a computation on BigQuery
description: Executor run instructions for the revenue Attested Computation.
tags: [executor, bigquery]
status: stable
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-15T14:30:00Z }
---

# Steps

1. Bind the declared `parameters` from the [revenue
   computation](/computations/revenue.md) into the `# Computation` SQL.
2. Submit the bound SQL as a BigQuery job.
3. Return a receipt with `job_id`, `executed_sql`, and `result` for the attester
   to inspect.
