# Uploads the two notebooks the pipeline actually runs on a schedule/on demand, and recreates
# the Auto Loader job exactly as defined in infra/job_spec.json. The training job stays
# deliberately un-managed here - it's run ad-hoc via `databricks jobs submit` against
# databricks/jobs/train_purchase_propensity_submit.json (see README's "What Terraform does NOT
# manage"), matching this project's existing choice to retrain on demand, not on a schedule.

resource "databricks_notebook" "autoloader" {
  depends_on = [databricks_schema.this]
  source     = "${path.module}/../databricks/notebooks/autoloader_bronze_to_staging.py"
  path       = "/Workspace/Shared/clickstream/autoloader_bronze_to_staging"
  language   = "PYTHON"
}

resource "databricks_notebook" "train_purchase_propensity" {
  depends_on = [databricks_schema.this]
  source     = "${path.module}/../databricks/notebooks/train_purchase_propensity.py"
  path       = "/Workspace/Shared/clickstream/train_purchase_propensity"
  language   = "PYTHON"
}

# ---------- Auto Loader job (Bronze -> Staging), scheduled every 30 minutes ----------
resource "databricks_job" "autoloader" {
  name = "clickstream-bronze-to-staging"

  tags = {
    project = "clickstream-lakehouse"
  }

  schedule {
    quartz_cron_expression = "0 0/30 * * * ?"
    timezone_id            = "UTC"
    pause_status           = "UNPAUSED"
  }

  max_concurrent_runs = 1

  task {
    task_key = "autoloader"

    notebook_task {
      notebook_path = databricks_notebook.autoloader.path
    }

    new_cluster {
      spark_version      = "16.4.x-scala2.12"
      node_type_id       = "Standard_D2ads_v6"
      num_workers        = 0
      data_security_mode = "SINGLE_USER"
      single_user_name   = var.databricks_account_user_email

      spark_conf = {
        "spark.master"                     = "local[*]"
        "spark.databricks.cluster.profile" = "singleNode"
      }

      custom_tags = {
        ResourceClass = "SingleNode"
        project       = "clickstream-lakehouse"
      }
    }

    timeout_seconds = 1800
  }
}

# ---------- SQL Warehouse (auto-provisioned per workspace, not created here) ----------
# dbt, the Streamlit app, and infra/dbx_sql.sh all hardcode this warehouse's ID - deploy.sh
# patches those files with the freshly looked-up ID after apply (a new workspace's
# auto-provisioned Starter Warehouse gets a new ID every time).
data "databricks_sql_warehouse" "starter" {
  depends_on = [azurerm_databricks_workspace.this]
  name       = "Serverless Starter Warehouse"
}
