-- ============================================================================
-- BigQuery Billing Export Queries for Google Cloud & Firebase Portfolio Audits
-- Dataset: `<PROJECT_ID>.billingexport.gcp_billing_export_v1_<BILLING_ACCOUNT_ID>`
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. 30-Day Itemized Spend by Project and Service
-- ----------------------------------------------------------------------------
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
  net_cost_usd DESC;

-- ----------------------------------------------------------------------------
-- 2. Week-over-Week Spend Velocity (Last 7 Days vs. Previous 7 Days)
-- ----------------------------------------------------------------------------
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
  cost_last_7d DESC;

-- ----------------------------------------------------------------------------
-- 3. Current Month-to-Date (MTD) Daily Spend Run Rate
-- ----------------------------------------------------------------------------
SELECT
  EXTRACT(DATE FROM _PARTITIONTIME) AS usage_date,
  ROUND(SUM(cost), 2) AS gross_cost,
  ROUND(SUM(cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost
FROM
  `simple-node-001.billingexport.gcp_billing_export_v1_00615D_35664D_BF0DF0`
WHERE
  _PARTITIONTIME >= TIMESTAMP(DATE_TRUNC(CURRENT_DATE(), MONTH))
GROUP BY
  usage_date
ORDER BY
  usage_date ASC;

-- ----------------------------------------------------------------------------
-- 4. Current Month-to-Date (MTD) Itemized Breakdown by Project & SKU
-- ----------------------------------------------------------------------------
SELECT
  IFNULL(project.id, "Shared / Unassigned") AS project_id,
  service.description AS service_description,
  sku.description AS sku_description,
  ROUND(SUM(cost), 2) AS gross_cost_usd,
  ROUND(SUM(cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost_usd
FROM
  `simple-node-001.billingexport.gcp_billing_export_v1_00615D_35664D_BF0DF0`
WHERE
  _PARTITIONTIME >= TIMESTAMP(DATE_TRUNC(CURRENT_DATE(), MONTH))
GROUP BY
  project_id, service_description, sku_description
HAVING
  gross_cost_usd > 0 OR net_cost_usd > 0
ORDER BY
  net_cost_usd DESC
LIMIT 50;
