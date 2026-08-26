---
type: BigQuery Table
title: Customer Orders
description: One row per completed customer order across all channels.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, orders, revenue]
status: stable
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-08-15T14:30:00Z }
verified:
  - { by: human:ahormati, at: 2026-08-15T16:00:00Z }
sources:
  - id: sales-schema
    resource: https://wiki.acme/sales/orders-schema
    title: Sales orders table schema
    author: team:sales-data
    last_modified: 2026-08-01
---

# Schema

| Column        | Type      | Description                                          |
|---------------|-----------|------------------------------------------------------|
| `order_id`    | STRING    | Globally unique order identifier.                    |
| `customer_id` | STRING    | Foreign key into [customers](/tables/customers.md).  |
| `total_usd`   | NUMERIC   | Order total in US dollars.[^sales-schema]            |
| `placed_at`   | TIMESTAMP | When the customer submitted the order.               |

# Joins

Joined with [customers](/tables/customers.md) on `customer_id`.

[^sales-schema]: Sales orders table schema
