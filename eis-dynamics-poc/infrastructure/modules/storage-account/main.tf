variable "name" {
  type        = string
  description = "Storage account name (3-24 chars, lowercase alphanumeric)"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "account_tier" {
  type        = string
  default     = "Standard"
  description = "Storage account tier"
}

variable "account_replication_type" {
  type        = string
  default     = "LRS"
  description = "Replication type (LRS, GRS, RAGRS, ZRS)"
}

variable "containers" {
  type = list(object({
    name                  = string
    container_access_type = string
  }))
  default     = []
  description = "List of blob containers to create"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}

resource "azurerm_storage_account" "sa" {
  name                     = var.name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type = var.account_replication_type

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 7
    }

    container_delete_retention_policy {
      days = 7
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "containers" {
  for_each = { for c in var.containers : c.name => c }

  name                  = each.value.name
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = each.value.container_access_type
}

output "storage_account_id" {
  value       = azurerm_storage_account.sa.id
  description = "Storage account ID"
}

output "storage_account_name" {
  value       = azurerm_storage_account.sa.name
  description = "Storage account name"
}

output "primary_access_key" {
  value       = azurerm_storage_account.sa.primary_access_key
  sensitive   = true
  description = "Primary access key"
}

output "primary_connection_string" {
  value       = azurerm_storage_account.sa.primary_connection_string
  sensitive   = true
  description = "Primary connection string"
}

output "primary_blob_endpoint" {
  value       = azurerm_storage_account.sa.primary_blob_endpoint
  description = "Primary blob endpoint URL"
}
