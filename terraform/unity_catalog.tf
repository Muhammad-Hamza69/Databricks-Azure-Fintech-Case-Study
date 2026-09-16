# Unity Catalog objects that were set up manually via the databricks CLI/UI during the original
# build, never captured as code: storage credential, external locations, the `clickstream`
# catalog, and its 6 schemas. See README.md's "Unity Catalog layout" section for what each is
# for - this file only recreates the shell, `run_pipeline.py` (via dbt/Auto Loader/training)
# repopulates the actual tables afterward.

# Azure auto-attaches a brand-new Premium workspace to the region's existing metastore, but that
# assignment isn't guaranteed to be visible to the API the instant the workspace resource
# reports as created - this buffer avoids a race where the metastore/catalog data sources below
# run before the assignment has actually landed.
resource "time_sleep" "wait_for_metastore_assignment" {
  depends_on      = [azurerm_databricks_workspace.this]
  create_duration = "60s"
}

# No `id`/`name` given - returns the metastore already assigned to the workspace the provider is
# authenticated against (the region's auto-provisioned metastore, e.g. metastore_azure_centralus
# - confirmed live for this project's existing workspace, same behavior expected for a fresh one
# in the same region/account).
data "databricks_metastore" "current" {
  depends_on = [time_sleep.wait_for_metastore_assignment]
}

# ---------- Idempotency: drop a stale catalog left over from a previous deployment ----------
# See terraform/scripts/drop_stale_catalog.sh - the catalog is metastore-level (account/region),
# so it (and its old storage credential/external locations, pointing at now-destroyed storage if
# only the resource group was deleted) can outlive a resource-group deletion. Destructive by
# design - the user chose auto-drop-and-recreate over failing and asking, so this stays one
# command end to end.
resource "null_resource" "drop_stale_catalog" {
  depends_on = [data.databricks_metastore.current]

  triggers = {
    workspace_url = azurerm_databricks_workspace.this.workspace_url
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "bash '${path.module}/scripts/drop_stale_catalog.sh' 'https://${azurerm_databricks_workspace.this.workspace_url}'"
  }
}

# ---------- Storage credential (Access Connector-backed, no keys/SAS) ----------
resource "databricks_storage_credential" "bronze" {
  depends_on = [null_resource.drop_stale_catalog]
  name       = "clickstream_bronze_credential"
  comment    = "Access to the clickstream bronze ADLS Gen2 storage account"

  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.this.id
  }
}

# ---------- External locations ----------
resource "databricks_external_location" "bronze" {
  name            = "clickstream_bronze"
  url             = "abfss://bronze@${azurerm_storage_account.bronze.name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.bronze.id
  comment         = "Raw Event Hub Capture landing zone (bronze)"
}

resource "databricks_external_location" "managed" {
  name            = "clickstream_managed"
  url             = "abfss://unity-catalog@${azurerm_storage_account.bronze.name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.bronze.id
  comment         = "Unity Catalog managed table storage for the clickstream lakehouse"
}

# ---------- Catalog + schemas ----------
resource "databricks_catalog" "clickstream" {
  name           = "clickstream"
  comment        = "Clickstream medallion lakehouse"
  storage_root   = "abfss://unity-catalog@${azurerm_storage_account.bronze.name}.dfs.core.windows.net/clickstream"
  isolation_mode = "OPEN"

  depends_on = [
    databricks_external_location.bronze,
    databricks_external_location.managed,
  ]
}

resource "databricks_schema" "this" {
  for_each     = toset(["staging", "silver", "gold", "ml_feature", "ml_training", "ml_models"])
  catalog_name = databricks_catalog.clickstream.name
  name         = each.value
}
