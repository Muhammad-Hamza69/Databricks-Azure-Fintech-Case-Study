# Port of infra/databricks.bicep - Databricks Premium workspace (Unity Catalog auto-enabled) +
# Access Connector so Databricks can read/write the bronze storage account without any storage
# keys or SAS tokens.

resource "azurerm_databricks_access_connector" "this" {
  name                = "${var.name_prefix}-dbx-ac-${local.suffix}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_databricks_workspace" "this" {
  name                        = "${var.name_prefix}-dbx-${local.suffix}"
  resource_group_name         = azurerm_resource_group.this.name
  location                    = azurerm_resource_group.this.location
  sku                         = "premium"
  managed_resource_group_name = "${var.name_prefix}-dbx-managed-${local.suffix}"
}

# ---------- RBAC: Access Connector's managed identity can read/write the bronze storage account ----------
resource "azurerm_role_assignment" "access_connector_storage" {
  scope                = azurerm_storage_account.bronze.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.this.identity[0].principal_id
}
