variable "name_prefix" {
  description = "Short prefix used to name every resource, matching infra/main.bicep's default"
  type        = string
  default     = "clickstream"
}

variable "resource_group_name" {
  description = "Resource group to (re)create - matches the one this project has always used"
  type        = string
  default     = "rg-clickstream-bronze"
}

variable "location" {
  description = "Azure region for all resources - matches where everything already lives"
  type        = string
  default     = "centralus"
}

variable "event_hub_throughput_units" {
  description = "Event Hubs Standard tier throughput units (matches infra/main.bicep's default of 1)"
  type        = number
  default     = 1
}

variable "databricks_account_user_email" {
  description = "Used as single_user_name on the Auto Loader job's cluster (matches infra/job_spec.json and databricks/jobs/train_purchase_propensity_submit.json)"
  type        = string
  default     = "muhammadhamzasiddiqui883@gmail.com"
}
