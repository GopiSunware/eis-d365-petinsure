terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
  }

  # Uncomment after creating storage account for state
  # backend "azurerm" {
  #   resource_group_name  = "rg-terraform-state"
  #   storage_account_name = "steisd365tfstate"
  #   container_name       = "tfstate"
  #   key                  = "dev.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
}

locals {
  environment = "dev"
  location    = "eastus"
  project     = "eis-d365-poc"

  common_tags = {
    environment = local.environment
    project     = local.project
    managed_by  = "terraform"
  }
}

data "azurerm_client_config" "current" {}

# =============================================================================
# Resource Groups
# =============================================================================
module "resource_groups" {
  source = "../../modules/resource-group"

  resource_groups = {
    shared = {
      name     = "rg-${local.project}-shared-${local.environment}"
      location = local.location
      tags     = local.common_tags
    }
    compute = {
      name     = "rg-${local.project}-compute-${local.environment}"
      location = local.location
      tags     = local.common_tags
    }
    data = {
      name     = "rg-${local.project}-data-${local.environment}"
      location = local.location
      tags     = local.common_tags
    }
    integration = {
      name     = "rg-${local.project}-integration-${local.environment}"
      location = local.location
      tags     = local.common_tags
    }
    ai = {
      name     = "rg-${local.project}-ai-${local.environment}"
      location = local.location
      tags     = local.common_tags
    }
  }
}

# =============================================================================
# Key Vault
# =============================================================================
module "key_vault" {
  source = "../../modules/key-vault"

  name                = "kv-eisd365-${local.environment}"
  resource_group_name = module.resource_groups.resource_group_names["shared"]
  location            = local.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  tags                = local.common_tags

  depends_on = [module.resource_groups]
}

# =============================================================================
# Storage Account
# =============================================================================
module "storage_account" {
  source = "../../modules/storage-account"

  name                = "steisd365${local.environment}"
  resource_group_name = module.resource_groups.resource_group_names["data"]
  location            = local.location

  containers = [
    { name = "policy-documents", container_access_type = "private" },
    { name = "claim-documents", container_access_type = "private" },
    { name = "function-deployments", container_access_type = "private" }
  ]

  tags = local.common_tags

  depends_on = [module.resource_groups]
}

# =============================================================================
# Cosmos DB
# =============================================================================
module "cosmos_db" {
  source = "../../modules/cosmos-db"

  account_name        = "cosmos-eisd365-${local.environment}"
  resource_group_name = module.resource_groups.resource_group_names["data"]
  location            = local.location

  databases = [
    {
      name = "insurance-data"
      containers = [
        { name = "policies", partition_key_path = "/policyNumber" },
        { name = "claims", partition_key_path = "/claimNumber" },
        { name = "customers", partition_key_path = "/customerId" },
        { name = "sync-state", partition_key_path = "/entityType" }
      ]
    }
  ]

  tags = local.common_tags

  depends_on = [module.resource_groups]
}

# =============================================================================
# Service Bus
# =============================================================================
module "service_bus" {
  source = "../../modules/service-bus"

  name                = "sb-eisd365-${local.environment}"
  resource_group_name = module.resource_groups.resource_group_names["integration"]
  location            = local.location

  queues = [
    { name = "policy-sync-queue", max_delivery_count = 10 },
    { name = "claim-sync-queue", max_delivery_count = 10 }
  ]

  topics = [
    {
      name = "policy-events"
      subscriptions = [
        { name = "dataverse-sync", max_delivery_count = 10, sql_filter = "" },
        { name = "analytics", max_delivery_count = 5, sql_filter = "" }
      ]
    },
    {
      name = "claim-events"
      subscriptions = [
        { name = "dataverse-sync", max_delivery_count = 10, sql_filter = "" },
        { name = "ai-processor", max_delivery_count = 5, sql_filter = "EventType = 'ClaimCreated'" }
      ]
    }
  ]

  tags = local.common_tags

  depends_on = [module.resource_groups]
}

# =============================================================================
# Azure OpenAI
# =============================================================================
module "openai_service" {
  source = "../../modules/openai-service"

  name                = "oai-eisd365-${local.environment}"
  resource_group_name = module.resource_groups.resource_group_names["ai"]
  location            = local.location

  deployments = [
    {
      name          = "gpt-4o"
      model_name    = "gpt-4o"
      model_version = "2024-08-06"
      capacity      = 10
    },
    {
      name          = "text-embedding-ada-002"
      model_name    = "text-embedding-ada-002"
      model_version = "2"
      capacity      = 10
    }
  ]

  tags = local.common_tags

  depends_on = [module.resource_groups]
}

# =============================================================================
# Store Secrets in Key Vault
# =============================================================================
resource "azurerm_key_vault_secret" "cosmos_connection" {
  name         = "cosmos-db-connection-string"
  value        = module.cosmos_db.connection_string
  key_vault_id = module.key_vault.key_vault_id

  depends_on = [module.key_vault, module.cosmos_db]
}

resource "azurerm_key_vault_secret" "service_bus_connection" {
  name         = "service-bus-connection-string"
  value        = module.service_bus.primary_connection_string
  key_vault_id = module.key_vault.key_vault_id

  depends_on = [module.key_vault, module.service_bus]
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "openai-api-key"
  value        = module.openai_service.openai_key
  key_vault_id = module.key_vault.key_vault_id

  depends_on = [module.key_vault, module.openai_service]
}

resource "azurerm_key_vault_secret" "storage_connection" {
  name         = "storage-connection-string"
  value        = module.storage_account.primary_connection_string
  key_vault_id = module.key_vault.key_vault_id

  depends_on = [module.key_vault, module.storage_account]
}

# =============================================================================
# Outputs
# =============================================================================
output "resource_group_names" {
  value       = module.resource_groups.resource_group_names
  description = "Resource group names"
}

output "key_vault_uri" {
  value       = module.key_vault.key_vault_uri
  description = "Key Vault URI"
}

output "storage_account_name" {
  value       = module.storage_account.storage_account_name
  description = "Storage account name"
}

output "cosmos_db_endpoint" {
  value       = module.cosmos_db.account_endpoint
  description = "Cosmos DB endpoint"
}

output "service_bus_namespace" {
  value       = module.service_bus.namespace_name
  description = "Service Bus namespace"
}

output "openai_endpoint" {
  value       = module.openai_service.openai_endpoint
  description = "Azure OpenAI endpoint"
}
