output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "bronze_storage_account_name" {
  value = azurerm_storage_account.bronze.name
}

output "function_app_name" {
  value = azurerm_linux_function_app.this.name
}

output "function_app_default_hostname" {
  value = "https://${azurerm_linux_function_app.this.default_hostname}"
}

output "databricks_workspace_url" {
  value = "https://${azurerm_databricks_workspace.this.workspace_url}"
}

output "databricks_workspace_id" {
  value = azurerm_databricks_workspace.this.workspace_id
}

output "function_key" {
  description = "Feeds into deploy.sh's .env write - same key run_pipeline.py/generate_fake_events.py use as --function-key / INGEST_FUNCTION_KEY"
  value       = data.azurerm_function_app_host_keys.this.default_function_key
  sensitive   = true
}

output "sql_warehouse_id" {
  description = "Feeds into deploy.sh's patching of dbt/profiles.yml, streamlit_app/app.py, infra/dbx_sql.sh"
  value       = data.databricks_sql_warehouse.starter.id
}

output "autoloader_job_id" {
  description = "Feeds into deploy.sh's patching of run_pipeline.py's AUTOLOADER_JOB_ID constant - every fresh deploy gets a new job id"
  value       = databricks_job.autoloader.id
}
