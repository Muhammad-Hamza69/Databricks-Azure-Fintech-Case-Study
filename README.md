# Clickstream Lakehouse

Implements the architecture in `Architecture.png`. To run the ingestion-through-training portion
end-to-end with one command instead of five manual steps, see `PIPELINE.md`
(`python run_pipeline.py`).

```
CSV (local)  ->  Python producer  ->  Azure Function  ->  Event Hubs  ->  ADLS Gen2 (Bronze)
                                                                              |
                                                                      Auto Loader (Databricks)
                                                                              v
                                                                   Unity Catalog: clickstream.staging
                                                                              |
                                                                        dbt (dbt-databricks)
                                                                              v
                                                                   Unity Catalog: clickstream.silver
                                                                              |
                                                                        dbt (dbt-databricks)
                                                            +-----------------+-----------------+
                                                            v                                   v
                                                 Unity Catalog: clickstream.gold      clickstream.ml_feature
                                                        |                   |                    |
                                                        v                   v                    v
                                                   Power BI            Fivetran         clickstream.ml_training
                                                                            |                     |
                                                                            v                     v
                                                                       Salesforce      scikit-learn + MLflow
                                                                                                   |
                                                                                                   v
                                                                                        clickstream.ml_models
```

Source data is the RetailRocket clickstream dataset (`events.csv`, `item_properties_part1.csv`,
`category_tree.csv`) at the repo root, replayed as a simulated live stream rather than bulk-loaded.

## Resources (resource group: `rg-clickstream-bronze`, centralus)

| Resource | Name | Purpose |
|---|---|---|
| Storage (ADLS Gen2) | `csbrzyp6pon7l` | `bronze` container = raw Event Hubs Capture landing; `unity-catalog` container = Unity Catalog managed table storage |
| Storage (StorageV2) | `csfuncyp6pon7l` | Function App runtime storage (must be non-HNS) |
| Event Hubs namespace | `clickstream-ehns-yp6pon7lzod3o` | Hubs: `events`, `item-properties`, `category-tree` - Standard tier, Capture enabled (Avro, 5 min/300 MB) |
| Function App | `clickstream-func-yp6pon7lzod3o` | Python HTTP function `POST /api/ingest/{source}` - forwards batches to Event Hubs via managed identity |
| Application Insights | `clickstream-appi-yp6pon7lzod3o` | Function App telemetry |
| Databricks workspace | `clickstream-dbx-yp6pon7lzod3o` | `https://adb-7405616477706025.5.azuredatabricks.net` - Premium, Unity Catalog auto-enabled |
| Access Connector | `clickstream-dbx-ac-yp6pon7lzod3o` | Managed identity Databricks uses to read/write the bronze storage account (no keys/SAS) |

IaC lives in `infra/main.bicep` (bronze/Function/Event Hubs) and `infra/databricks.bicep`
(workspace + Access Connector).

## Unity Catalog layout

Catalog `clickstream`, storage rooted at `abfss://unity-catalog@csbrzyp6pon7l.dfs.core.windows.net/clickstream`:

- **`clickstream.staging`** - `events`, `item_properties`, `category_tree`. Written directly by
  Auto Loader from the bronze Avro capture files: typed columns (bigint/timestamp casts applied
  from the JSON-string payload), no cleaning or dedup. This is the first queryable Delta
  representation of the source data - there's no separate "raw" schema, Auto Loader lands
  straight into staging.
- **`clickstream.silver`** - `silver_events`, `silver_category_tree`,
  `silver_item_properties_history`, `silver_item_properties_current`. Built by dbt on top of
  `staging`: deduplicated, quality-filtered (not-null keys, valid event types, no self-referencing
  categories), conformed types. 9 dbt tests cover not-null/uniqueness/accepted-values.
- **`clickstream.gold`** - business-level marts built by dbt on top of silver:
  - `gold_daily_funnel` - daily view/addtocart/transaction counts and view-to-purchase rate
  - `gold_item_performance` - per-item engagement + conversion rate, joined with current
    category and availability (pivoted from `silver_item_properties_current`)
  - `gold_category_performance` - item performance rolled up to directly-tagged category
    (one level, not full ancestry)
  - `gold_visitor_summary` - per-visitor engagement totals and a purchase-conversion flag
  - `export_visitor_engagement_salesforce` - a thin view over `gold_visitor_summary`, the stable
    contract the Fivetran reverse-ETL sync reads from (see "Gold -> Fivetran -> Salesforce" below)
- **`clickstream.ml_feature`** - `ml_feature_visitor_item`: a `(visitor_id, item_id)`-grain
  feature table (view/addtocart counts, recency, item category/availability) for a
  purchase-propensity model. Registered with a Unity Catalog **primary key constraint**
  `(visitor_id, item_id)` via a dbt post-hook, so it's a genuine Databricks Feature Engineering
  table, not just a Delta table. Deliberately excludes transaction counts as a feature to avoid
  label leakage.
- **`clickstream.ml_training`** - `ml_training_purchase_propensity`: labeled training set built
  from `ml_feature_visitor_item` - one row per (visitor, item) that had a view or add-to-cart,
  `label_purchased` (0/1) derived from whether it converted to a transaction. No trained model is
  built here; the architecture diagram stops at "ML Training Dataset," so that's where this does
  too.
- **`clickstream.ml_models`** - `purchase_propensity`: the registered Unity Catalog model
  trained on `ml_training_purchase_propensity` (see "ML model" below).
- Storage access is via a Unity Catalog storage credential (`clickstream_bronze_credential`,
  backed by the Access Connector's managed identity) and two external locations
  (`clickstream_bronze` for reads off the bronze container, `clickstream_managed` for the
  catalog's managed table storage) - no account keys or SAS tokens anywhere in the pipeline.

## Running the ingestion (Bronze)

```
cd producer
pip install -r requirements.txt
python stream_clickstream.py --source events --ingest-url https://clickstream-func-yp6pon7lzod3o.azurewebsites.net \
    --function-key <function key> --max-rows 5000 --rate 200   # quick demo sample
python stream_clickstream.py --source item-properties ...
python stream_clickstream.py --source category-tree ...
```

The pipeline has actually been run end-to-end against the **full** `events.csv` (2,756,101
rows, all 22,457 real transactions - omit `--max-rows` for this) and a 500,000-row
`item-properties` sample, not just the demo sample above - see "ML Training Dataset ->
propensity model" below. Event Hubs was temporarily scaled to 4 throughput units for that bulk
backfill (`az eventhubs namespace update --capacity 4`) and scaled back to 1 afterward
(`--capacity 1`) to avoid ongoing extra cost - do the same for any future full-scale re-ingestion,
since 1 TU caps out around 1,000 events/sec.

Get the function key with:
```
az functionapp keys list --name clickstream-func-yp6pon7lzod3o --resource-group rg-clickstream-bronze
```

Event Hubs Capture lands Avro files under `bronze/<source>/YYYY/MM/DD/HH/` within ~5 minutes.

## Bronze -> staging (Auto Loader)

Notebook: `databricks/notebooks/autoloader_bronze_to_staging.py`
(`/Workspace/Shared/clickstream/autoloader_bronze_to_staging` in the workspace).

Runs on a schedule via Databricks Job **`clickstream-bronze-to-staging`** (job id
`614669053635065`), every 30 minutes, on an ephemeral single-node job cluster
(`Standard_D2ads_v6`, terminates after each run). Each run uses `trigger(availableNow=True)` so
it drains whatever new capture files exist since the last checkpoint and stops - safe to run on a
schedule without an always-on cluster.

To run it manually instead of waiting for the schedule:
```
databricks jobs run-now 614669053635065
```

## Staging -> silver (dbt)

```
cd dbt
pip install -r requirements.txt
export DATABRICKS_TOKEN=<personal access token>   # databricks tokens create --lifetime-seconds 86400
dbt run --profiles-dir .
dbt test --profiles-dir .
```

`profiles.yml` points at the workspace's built-in Serverless Starter Warehouse
(`3ae0ca482ea10df2`) rather than the dev cluster, so `dbt run` doesn't depend on any
interactive cluster being up.

## Gold -> Power BI

Not an automated step - Power BI Desktop is a GUI app with no scriptable way to author report
visuals. `powerbi/README.md` has the connection details (Databricks connector, Import mode,
same Serverless Starter Warehouse as dbt) and a two-page layout spec; `powerbi/measures.dax`
has copy-paste DAX measures for every KPI (view/addtocart/transaction totals, view-to-purchase
rate, visitor conversion rate, item/category conversion). Every column referenced was
cross-checked against the live `clickstream.gold.*` schemas. A layout wireframe was published
as an artifact during the build for visual reference.

## Gold -> Fivetran -> Salesforce (reverse ETL)

**Built and verified.** Fivetran Activations syncs `clickstream.gold.export_visitor_engagement_salesforce`
(a dbt view, decoupled from `gold_visitor_summary` so the sync has a stable contract) into
Salesforce's standard **Account** object - one visitor = one Account record (e.g. "Visitor
629333"), upserted on a `Visitor_Id__c` external-ID field. Runs on a daily schedule (09:00 UTC).

Initial sync: **3,862/3,862 records successful, 0 rejected, 0 invalid**, in 4 minutes -
spot-checked against the source and every field matched exactly.

Full as-built details in `salesforce/README.md`, including two things that changed from the
original plan once real constraints showed up: the target had to become the standard Account
object with 8 custom fields instead of a dedicated `Visitor_Engagement__c` custom object,
because the org's Salesforce Starter edition had already used up its custom-object quota on the
platform's own `Knowledge_kav` object; and the Salesforce OAuth grant itself had to be done by a
human in a browser (same as the Power BI OAuth step) - not something I could complete from this
session, since there's no browser tool available here.

## ML Training Dataset -> propensity model

Notebook: `databricks/notebooks/train_purchase_propensity.py`
(`/Workspace/Shared/clickstream/train_purchase_propensity` in the workspace). Run once via
`databricks jobs submit` on an ephemeral ML-runtime job cluster (`16.4.x-cpu-ml-scala2.12`,
`Standard_D2ads_v6`, single-node) - not on a recurring schedule like the Auto Loader job, since
retraining on demand makes more sense than every 30 minutes for this dataset size.

Trains 10 candidates across 6 algorithm families - Logistic Regression (4 regularization
strengths), Random Forest (2 depths), Extra Trees, XGBoost, LightGBM, and Naive Bayes - on
`clickstream.ml_training.ml_training_purchase_propensity`, logs every one to MLflow (experiment
`/Shared/clickstream/purchase_propensity`), and only registers a candidate to Unity Catalog as
`clickstream.ml_models.purchase_propensity` if it passes two checks beyond PR-AUC: a
non-degenerate probability spread, and an explicit stress test (a hand-built "clearly
disengaged" vs. "clearly engaged" example must score in the correct direction with a real gap
between them) - PR-AUC alone doesn't catch a model whose actual probability output is
saturated or inverted, which earlier versions were.

`item_category_id` is deliberately **not** a model feature - it's a nominal ID with no real
ordering, and feeding it in as a raw number caused early versions to learn nonsense from it
given too little data to properly encode it. It's excluded, not the model - `ml_feature`/
`ml_training` still carry it for reporting.

**Currently registered: version 7 - calibrated LightGBM.** LightGBM won the 10-candidate
comparison (PR-AUC 0.392, narrowly beating XGBoost 0.389 and Random Forest 0.389 in a genuine
three-way near-tie), but its raw `predict_proba` output - like every version before it - was
not an honest probability: an independent check showed rows scored 90-100% only converted
~31% of the time in reality. v7 wraps the winner in `CalibratedClassifierCV` (isotonic
regression, 5-fold), which fixed this for real: predicted vs. actual now match closely across
every score band (e.g. 34.9% predicted -> 35.5% actual), and the model's maximum output across
the entire real candidate pool is now 84% - it can no longer claim 99% for anything, because
that was never true. PR-AUC after calibration: 0.395 (calibration didn't cost any ranking
quality). See `streamlit_app/README.md` for the full comparison table, the calibration check,
and the version-by-version history of what broke and why at each stage - it's a real account
of iterating on a model, not just a final number.

Loading a LightGBM/XGBoost-based model outside Databricks (e.g. the Streamlit app running
locally) needs the matching `lightgbm`/`xgboost` packages installed locally too, pinned to the
same versions as the Databricks ML runtime - already handled in `streamlit_app/requirements.txt`.

To retrain:
```
databricks jobs submit --json @databricks/jobs/train_purchase_propensity_submit.json
```

## Model -> Streamlit app

`streamlit_app/app.py` - a UI on top of the registered model. Queries
`clickstream.ml_feature.ml_feature_visitor_item` for real (visitor, item) pairs that were
viewed/added-to-cart but never bought (pre-filtered in SQL to the top 20,000 by
add-to-cart/view activity - the full pool is 2.1M+ rows at current data scale), scores every
one with the model, and shows a ranked table: Name, View Count, Add-to-Cart Count, Days Since
Last Interaction, Previously Purchased Item Count, Item Name (item ID - no real product names
in this dataset), Score, Percentile, and Meaning (a plain-language bucket derived from
percentile rank). Always loads the latest registered model version automatically.

```
cd streamlit_app
pip install -r requirements.txt
export DATABRICKS_HOST=adb-7405616477706025.5.azuredatabricks.net
export DATABRICKS_TOKEN=<personal access token>
streamlit run app.py
```

See `streamlit_app/README.md` for the full model version history (v1 through v5) - it's a real
account of catching and fixing a saturated-probability bug, an inverted-direction bug from a
mishandled categorical feature, and finally the data-volume problem underlying both, not just a
single training run.

## Cost notes / teardown

Billed while running: Event Hubs Standard (~$22/mo + throughput), Databricks compute (only while
the job cluster or serverless warehouse is active), Function App Consumption (near-free at this
volume), Storage (near-free at this volume). Databricks workspace and Unity Catalog metastore
themselves are free.

To tear everything down:
```
az group delete --name rg-clickstream-bronze --yes
```
This does not delete the Databricks-managed resource group (`clickstream-dbx-managed-...`) or the
Unity Catalog metastore automatically - the workspace deletion (implied by the resource group
delete) cleans up the managed RG, but the metastore is account-level and outlives any one
workspace; delete the catalog/schemas from the Databricks account console if you want it gone too.

## Disaster recovery: redeploy everything with Terraform

If the resource group (`rg-clickstream-bronze`) is ever deleted, `./deploy.sh` rebuilds the
whole architecture with one command: Azure resources + the Function App code
(`terraform/main.tf`, a port of `infra/main.bicep`), the Databricks workspace + Access Connector
(`terraform/databricks_workspace.tf`, a port of `infra/databricks.bicep`), and the Unity Catalog
layer that was originally set up by hand and never captured as code - storage credential,
external locations, the `clickstream` catalog + its 6 schemas, the two production notebooks, and
the Auto Loader job (`terraform/unity_catalog.tf`, `terraform/databricks_jobs.tf`). It then
patches the handful of files that hardcode this deployment's identity (workspace host, SQL
warehouse id, Auto Loader job id - `terraform/scripts/patch_files.py`) and runs
`python run_pipeline.py` to repopulate every table and register a fresh model.

```
./deploy.sh
```

**Deliberately destructive**: Unity Catalog's metastore is account/region-level, so the
`clickstream` catalog can survive a resource-group deletion even though the storage it points at
doesn't - `deploy.sh` always drops it (CASCADE) and recreates it fresh
(`terraform/scripts/drop_stale_catalog.sh`), so the single command stays idempotent regardless
of what state Unity Catalog was left in. Only run this when you actually mean to rebuild from
scratch, not for routine use (`python run_pipeline.py` alone is correct day to day).

**Not covered** - same as the original build, unchanged: the training job stays ad-hoc
(`databricks jobs submit`, not a scheduled Terraform-managed job, matching the existing "retrain
on demand" design) - and the Fivetran connector, Salesforce field mapping, and Power BI report
all need a human to complete an OAuth grant in a browser, so no tool can one-command those; redo
them manually after `deploy.sh` finishes, same as during the original build.

## What's built vs. spec'd

Everything in `Architecture.png` is complete. Bronze through `clickstream.gold` /
`clickstream.ml_feature` / `clickstream.ml_training` / `clickstream.ml_models`, and the
Fivetran -> Salesforce reverse ETL (Fivetran replacing the diagram's original Census), are all
**built and verified live** - actual data sitting in actual tables and Salesforce records, not
just configuration. See `salesforce/README.md` for the as-built reverse-ETL details.

The one piece that's connection kit + spec rather than a finished artifact is the **Power BI
dashboard**: Power BI Desktop is a GUI report authoring tool with no headless "build the
visuals for me" API, so `powerbi/README.md` and `powerbi/measures.dax` give the exact connection
details, DAX measures, and layout to build it in ~15-20 minutes rather than a delivered `.pbix`.
