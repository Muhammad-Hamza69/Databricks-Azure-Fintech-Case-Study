# Port of infra/main.bicep - ADLS Gen2 bronze storage, Function App runtime storage, Event Hubs
# namespace/hubs with Capture, the ingest Function App (code included, via zip_deploy_file), and
# the RBAC role assignments that let the Function App and Event Hubs Capture write data without
# any secrets in code. Resource types/names/config mirror the Bicep 1:1 - see that file for the
# original intent/comments on each choice.

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
}

# infra/main.bicep used uniqueString(resourceGroup().id) for a longer suffix (full names) and
# its first 8 chars for storage account names specifically. Here one 8-char suffix is used
# everywhere - functionally equivalent (still unique per deployment, still fits storage
# accounts' 24-char/lowercase-alphanumeric-only limit).
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

locals {
  suffix                = random_string.suffix.result
  bronze_storage_name   = "csbrz${local.suffix}"
  func_storage_name     = "csfunc${local.suffix}"
  event_hub_ns_name     = "${var.name_prefix}-ehns-${local.suffix}"
  function_app_name     = "${var.name_prefix}-func-${local.suffix}"
  app_service_plan_name = "${var.name_prefix}-plan-${local.suffix}"
  app_insights_name     = "${var.name_prefix}-appi-${local.suffix}"
  bronze_container_name = "bronze"

  event_hubs = {
    events = {
      capture_prefix = "events/{Year}/{Month}/{Day}/{Hour}/"
    }
    "item-properties" = {
      capture_prefix = "item-properties/{Year}/{Month}/{Day}/{Hour}/"
    }
    "category-tree" = {
      capture_prefix = "category-tree/{Year}/{Month}/{Day}/{Hour}/"
    }
  }
}

# ---------- ADLS Gen2 storage (Bronze landing zone) ----------
resource "azurerm_storage_account" "bronze" {
  name                            = local.bronze_storage_name
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
}

resource "azurerm_storage_container" "bronze" {
  name                  = local.bronze_container_name
  storage_account_name  = azurerm_storage_account.bronze.name
  container_access_type = "private"
}

# Unity Catalog managed table storage for the clickstream catalog (the storage credential in
# unity_catalog.tf covers the whole storage account, so this container just needs to exist).
resource "azurerm_storage_container" "unity_catalog" {
  name                  = "unity-catalog"
  storage_account_name  = azurerm_storage_account.bronze.name
  container_access_type = "private"
}

# ---------- Function App runtime storage (must be non-HNS: Consumption plan needs Azure Files content share) ----------
resource "azurerm_storage_account" "func" {
  name                            = local.func_storage_name
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
}

# ---------- Event Hubs namespace (Standard tier required for Capture) ----------
resource "azurerm_eventhub_namespace" "this" {
  name                 = local.event_hub_ns_name
  resource_group_name  = azurerm_resource_group.this.name
  location             = azurerm_resource_group.this.location
  sku                  = "Standard"
  capacity             = var.event_hub_throughput_units
  auto_inflate_enabled = false
  minimum_tls_version  = "1.2"

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_eventhub" "this" {
  for_each            = local.event_hubs
  name                = each.key
  resource_group_name = azurerm_resource_group.this.name
  namespace_name      = azurerm_eventhub_namespace.this.name
  partition_count     = 2
  message_retention   = 3

  capture_description {
    enabled             = true
    encoding            = "Avro"
    interval_in_seconds = 300
    size_limit_in_bytes = 314572800
    skip_empty_archives = true

    destination {
      name                = "EventHubArchive.AzureBlockBlob"
      archive_name_format = "${each.value.capture_prefix}{Namespace}-{EventHub}-{PartitionId}-{Year}{Month}{Day}{Hour}{Minute}{Second}"
      blob_container_name = local.bronze_container_name
      storage_account_id  = azurerm_storage_account.bronze.id
    }
  }
}

# ---------- Application Insights ----------
resource "azurerm_application_insights" "this" {
  name                = local.app_insights_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  application_type    = "web"
}

# ---------- Consumption plan + Python Function App ----------
resource "azurerm_service_plan" "this" {
  name                = local.app_service_plan_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

# Zips ingestion_function/ at apply time so the Function's actual code deploys inside this same
# `terraform apply` - in the original Bicep-based build this was a separate manual
# `func azure functionapp publish` step, never captured as code.
data "archive_file" "function_code" {
  type        = "zip"
  source_dir  = "${path.module}/../ingestion_function"
  output_path = "${path.module}/.build/ingestion_function.zip"
  excludes    = ["local.settings.json", "__pycache__", ".venv"]
}

resource "azurerm_linux_function_app" "this" {
  name                = local.function_app_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location

  service_plan_id            = azurerm_service_plan.this.id
  storage_account_name       = azurerm_storage_account.func.name
  storage_account_access_key = azurerm_storage_account.func.primary_access_key
  https_only                 = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME              = "python"
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.this.connection_string
    EVENTHUB_FQDN                         = "${azurerm_eventhub_namespace.this.name}.servicebus.windows.net"
    EVENTHUB_EVENTS_NAME                  = "events"
    EVENTHUB_ITEM_PROPERTIES_NAME         = "item-properties"
    EVENTHUB_CATEGORY_TREE_NAME           = "category-tree"
    WEBSITE_RUN_FROM_PACKAGE              = "1"
  }

  zip_deploy_file = data.archive_file.function_code.output_path
}

# The auto-generated "default" host key - same value `az functionapp keys list` shows, and the
# same key run_pipeline.py/generate_fake_events.py use as --function-key.
data "azurerm_function_app_host_keys" "this" {
  name                = azurerm_linux_function_app.this.name
  resource_group_name = azurerm_resource_group.this.name
}

# ---------- RBAC: Function App managed identity can send to Event Hubs (no connection strings) ----------
resource "azurerm_role_assignment" "function_send" {
  scope                = azurerm_eventhub_namespace.this.id
  role_definition_name = "Azure Event Hubs Data Sender"
  principal_id         = azurerm_linux_function_app.this.identity[0].principal_id
}

# ---------- RBAC: Event Hubs Capture's managed system identity can write to the bronze storage account ----------
resource "azurerm_role_assignment" "capture_storage" {
  scope                = azurerm_storage_account.bronze.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_eventhub_namespace.this.identity[0].principal_id
}
