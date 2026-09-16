#!/usr/bin/env bash
# Unity Catalog's metastore is account/region-level, so the `clickstream` catalog (and its
# storage credential/external locations) can survive a resource-group deletion even though the
# storage it points at is gone. Run before creating fresh UC objects so `terraform apply` is
# idempotent no matter what state Unity Catalog was left in - drops it (CASCADE) if present,
# no-ops if not. This is deliberately destructive to anything left in the catalog - the user
# chose this behavior over failing-and-asking, to keep the redeploy a single command.
set -euo pipefail

# Same fallback PATH pattern as infra/dbx_sql.sh - the databricks CLI in this project isn't
# always on PATH, it lives at this fixed install location.
export PATH="$PATH:/c/Users/hp/databricks-cli"
export DATABRICKS_HOST="$1"
export DATABRICKS_AUTH_TYPE="azure-cli"

if databricks catalogs get clickstream >/dev/null 2>&1; then
  echo "[drop_stale_catalog] Found existing 'clickstream' catalog - dropping it (CASCADE) before recreating."
  databricks catalogs delete clickstream --force
else
  echo "[drop_stale_catalog] No existing 'clickstream' catalog found - nothing to drop."
fi
