#!/usr/bin/env bash
# Single-command disaster-recovery redeploy: rebuilds every Azure + Databricks/Unity Catalog
# resource with Terraform, patches the handful of files that hardcode values which change on
# every fresh deploy (workspace host, SQL warehouse id, Auto Loader job id), then runs the
# existing pipeline to repopulate data and register a fresh model.
#
# Deliberately destructive: the Unity Catalog `clickstream` catalog is dropped (CASCADE) and
# recreated every run (see terraform/scripts/drop_stale_catalog.sh) so this stays idempotent no
# matter what survived a resource-group deletion. Only run this when you actually mean to
# rebuild from scratch - not for routine use, where `python run_pipeline.py` alone is correct.
#
# What this does NOT cover (unchanged from today - see README.md): the Fivetran connector,
# Salesforce field mapping, and Power BI report all require a human OAuth grant in a browser,
# same as during the original build. Redo those manually after this finishes.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "=== [1/4] terraform apply ==="
terraform -chdir=terraform init -input=false
terraform -chdir=terraform apply -auto-approve

DBX_HOST=$(terraform -chdir=terraform output -raw databricks_workspace_url)
DBX_HOST_BARE="${DBX_HOST#https://}"
FUNCTION_KEY=$(terraform -chdir=terraform output -raw function_key)
WAREHOUSE_ID=$(terraform -chdir=terraform output -raw sql_warehouse_id)
JOB_ID=$(terraform -chdir=terraform output -raw autoloader_job_id)

echo "=== [2/4] Patching files that hardcode this deployment's identity ==="
# dbt/profiles.yml, infra/dbx_sql.sh, run_pipeline.py all hardcode the previous workspace's
# host; run_pipeline.py also hardcodes the previous Auto Loader job id; dbt/profiles.yml,
# streamlit_app/app.py, and infra/dbx_sql.sh hardcode the previous SQL warehouse id (in two
# different textual forms - a URL path and a JSON field with escaped quotes, see patch_files.py).
# Every value here is looked up fresh from this run's terraform outputs, not the literal strings
# that happened to be current when this script was written - safe to run on every future
# redeploy too. Done in Python, not sed, because infra/dbx_sql.sh's escaped-quote JSON literal
# is fragile to get right in shell-quoted sed across bash/Windows.
DBX_HOST_BARE="$DBX_HOST_BARE" WAREHOUSE_ID="$WAREHOUSE_ID" JOB_ID="$JOB_ID" python terraform/scripts/patch_files.py

echo "=== [3/4] Writing .env (function key + a fresh Databricks PAT) ==="
export DATABRICKS_HOST="$DBX_HOST"
export DATABRICKS_AUTH_TYPE="azure-cli"
export PATH="$PATH:/c/Users/hp/databricks-cli"
PAT=$(databricks tokens create --comment "deploy.sh" --lifetime-seconds 7776000 -o json | python -c "import json,sys; print(json.load(sys.stdin)['token_value'])")
cat > .env <<EOF
DATABRICKS_TOKEN=${PAT}
INGEST_FUNCTION_KEY=${FUNCTION_KEY}
EOF

echo "=== [4/4] Running the pipeline (ingest -> Auto Loader -> dbt -> train -> Streamlit) ==="
python run_pipeline.py

echo "=== Done. Redeploy complete. ==="
echo "Still manual (unchanged from before - see README.md): Fivetran connector + Salesforce field mapping, Power BI report."
