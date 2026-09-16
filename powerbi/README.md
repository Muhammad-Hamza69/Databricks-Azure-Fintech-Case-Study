# Power BI KPI dashboard

This isn't a generated `.pbix` — Power BI Desktop is a GUI app with no scriptable way to author
report visuals from the outside. What's here is everything needed to build the report in ~15-20
minutes of clicking: the exact connection details, the DAX measures (copy-paste ready), and a
page-by-page layout spec. `measures.dax` has the measure definitions; this file has the
connection steps and layout.

## 1. Connect Power BI Desktop to the gold layer

**Get Data -> Databricks** (built-in connector; if missing, install "Power BI connector for
Azure Databricks" from Options > Preview features, or update Power BI Desktop).

| Field | Value |
|---|---|
| Server hostname | `adb-7405616477706025.5.azuredatabricks.net` |
| HTTP path | `/sql/1.0/warehouses/3ae0ca482ea10df2` (the workspace's Serverless Starter Warehouse — same one dbt uses) |
| Catalog | `clickstream` |
| Data connectivity mode | **Import** (recommended — these gold tables are a few thousand rows each, no reason to pay DirectQuery's latency) |

**Authentication**: either
- **Azure AD** (interactive sign-in with the same account used for the Databricks workspace), or
- **Personal Access Token**: `databricks tokens create --comment "powerbi" --lifetime-seconds 7776000`
  (90 days) using the Databricks CLI already configured for this workspace, then paste the token
  value into Power BI's PAT auth prompt.

## 2. Tables to import (schema `clickstream.gold`)

- `gold_daily_funnel` — one row per day: `event_date`, `views`, `addtocarts`, `transactions`, `unique_visitors`, `view_to_purchase_rate`
- `gold_item_performance` — one row per item: `item_id`, `category_id`, `is_available`, `views`, `addtocarts`, `transactions`, `unique_visitors`, `conversion_rate`, `first_seen`, `last_seen`
- `gold_category_performance` — one row per category: `category_id`, `parent_category_id`, `item_count`, `views`, `addtocarts`, `transactions`, `conversion_rate`
- `gold_visitor_summary` — one row per visitor: `visitor_id`, `total_views`, `total_addtocarts`, `total_transactions`, `distinct_items_viewed`, `first_seen`, `last_seen`, `is_converted`

No relationships need to be manually drawn between these four for the layout below — each page's
visuals pull from a single table. If you later want cross-table slicing (e.g. filter item
performance by category), add a relationship `gold_item_performance[category_id]` ->
`gold_category_performance[category_id]` (many-to-one).

## 3. Measures

Paste everything in `measures.dax` into each respective table via **Table tools > New measure**
(the file groups them by which table they belong on).

## 4. Dashboard layout

**Page 1 — Executive Overview**
- KPI card row (6 cards, left to right): Total Views, Total AddToCarts, Total Transactions,
  Total Unique Visitors, View to Purchase Rate, Visitor Conversion Rate
- Line chart, full width below the cards: `event_date` (axis) vs Views / AddToCarts /
  Transactions (three lines, from `gold_daily_funnel`) — shows the funnel trend over time
- Funnel visual (bottom right): Views -> AddToCarts -> Transactions, summed across
  `gold_daily_funnel`

**Page 2 — Item & Category Performance**
- Bar chart (top left): top 15 categories from `gold_category_performance` by `transactions`
- Table (top right): top 20 items from `gold_item_performance` sorted by `conversion_rate`
  descending, filtered to `views >= 10` (avoid single-view 100%-conversion noise) — columns
  `item_id`, `category_id`, `views`, `transactions`, `conversion_rate`
- Donut chart (bottom left): item count split by `is_available` (from `gold_item_performance`)
- Scatter chart (bottom right): `views` (x) vs `conversion_rate` (y) per item, sized by
  `transactions` — surfaces high-volume, high-converting items

See the layout wireframe artifact for a visual reference before building the pages.

## 5. Refresh

These are Import-mode tables, so they're a snapshot as of whenever you last refreshed. To
schedule refresh, publish to the Power BI service and set up a gateway/refresh schedule
pointed at the same Databricks connection — or just re-run **Refresh** in Desktop after each
`dbt run`.
