---
type: Metric
title: Revenue
description: Recognized revenue for a fiscal year, per Finance's definition.
tags: [finance, revenue]
status: stable
stale_after: 2026-12-31
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-15T14:30:00Z }
verified:
  - { by: human:ahormati, at: 2026-08-15T16:00:00Z }
---

# Definition

Recognized revenue sums `total_usd` over completed [orders](/tables/orders.md)
booked to the fiscal year, computed by [the revenue
computation](/computations/revenue.md).

Derived trust tier (not stored): **human-reviewed** — `verified` includes a
`human:` actor. Fresh until `stale_after` (2026-12-31).
