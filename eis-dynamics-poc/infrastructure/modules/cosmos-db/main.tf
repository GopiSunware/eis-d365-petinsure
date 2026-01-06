variable "account_name" {
  type        = string
  description = "Cosmos DB account name"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "databases" {
  type = list(object({
    name = string
    containers = list(object({
      name               = string
      partition_key_path = string
    }))
  }))
  default     = []
  description = "List of databases and containers to create"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}

resource "azurerm_cosmosdb_account" "db" {
  name                = var.account_name
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  # Serverless for cost optimization in POC
  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "databases" {
  for_each = { for db in var.databases : db.name => db }

  name                = each.value.name
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.db.name
}

resource "azurerm_cosmosdb_sql_container" "containers" {
  for_each = {
    for item in flatten([
      for db in var.databases : [
        for c in db.containers : {
          key               = "${db.name}-${c.name}"
          db_name           = db.name
          name              = c.name
          partition_key_path = c.partition_key_path
        }
      ]
    ]) : item.key => item
  }

  name                  = each.value.name
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.db.name
  database_name         = azurerm_cosmosdb_sql_database.databases[each.value.db_name].name
  partition_key_path    = each.value.partition_key_path
  partition_key_version = 2

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}

output "account_id" {
  value       = azurerm_cosmosdb_account.db.id
  description = "Cosmos DB account ID"
}

output "account_endpoint" {
  value       = azurerm_cosmosdb_account.db.endpoint
  description = "Cosmos DB endpoint"
}

output "primary_key" {
  value       = azurerm_cosmosdb_account.db.primary_key
  sensitive   = true
  description = "Primary key"
}

output "connection_string" {
  value       = azurerm_cosmosdb_account.db.primary_sql_connection_string
  sensitive   = true
  description = "SQL connection string"
}
