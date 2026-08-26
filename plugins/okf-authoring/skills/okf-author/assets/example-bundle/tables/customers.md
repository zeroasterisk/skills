---
type: BigQuery Table
title: Customers
description: One row per customer across all channels.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=customers
tags: [sales, customers]
status: stable
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-15T14:30:00Z }
---

# Schema

| Column        | Type   | Description                          |
|---------------|--------|--------------------------------------|
| `customer_id` | STRING | Globally unique customer identifier. |
| `email`       | STRING | Primary contact email.               |

Referenced by [orders](/tables/orders.md) via `customer_id`.
