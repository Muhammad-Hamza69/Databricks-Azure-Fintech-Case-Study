terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.11"
    }
  }
}

# Uses the same auth this whole project already relies on everywhere else (the `databricks`
# CLI, dbt's profiles.yml, run_pipeline.py) - `az login` via Azure CLI, no client secrets in
# this repo. `subscription_id` is intentionally left unset so azurerm picks up whatever
# subscription `az account show` currently has active.
provider "azurerm" {
  features {}
}

# The databricks provider needs a workspace host to talk to, but the workspace is created by
# this same `terraform apply` (see databricks_workspace.tf). `azure_workspace_resource_id`
# lets the provider resolve the host lazily from the azurerm_databricks_workspace resource's
# computed ID, instead of requiring a hardcoded host up front - this is the pattern Databricks'
# own docs use for "create workspace + configure Unity Catalog in one apply".
provider "databricks" {
  host                        = azurerm_databricks_workspace.this.workspace_url
  azure_workspace_resource_id = azurerm_databricks_workspace.this.id
  auth_type                   = "azure-cli"
}
