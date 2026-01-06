# PetInsure360 - Azure Infrastructure
# Terraform configuration for Pet Insurance Data Platform

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Random suffix for globally unique names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

provider "azurerm" {
  features {}
}

# Variables
variable "resource_group_name" {
  default = "rg-petinsure360"
}

variable "location" {
  default = "West US 2"
}

variable "environment" {
  default = "dev"
}

locals {
  prefix = "petinsure360"
  tags = {
    Environment = var.environment
    Project     = "PetInsure360"
    Owner       = "Gopinath"
    Purpose     = "Pet Insurance Data Platform Demo"
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags
}

# =============================================================================
# STORAGE - Azure Data Lake Gen2 (Shared Storage for Databricks + Synapse)
# =============================================================================

resource "azurerm_storage_account" "datalake" {
  name                     = "petins${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true  # Enable hierarchical namespace for ADLS Gen2

  tags = local.tags
}

# Containers for Medallion Architecture
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

# =============================================================================
# AZURE DATABRICKS - ETL & ML Platform
# =============================================================================

resource "azurerm_databricks_workspace" "main" {
  name                = "${local.prefix}-databricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "standard"  # Use "premium" for Unity Catalog, but standard is cheaper

  tags = local.tags
}

# =============================================================================
# AZURE SYNAPSE - Serverless SQL for BI & Ad-hoc Queries
# =============================================================================

resource "azurerm_synapse_workspace" "main" {
  name                                 = "petins-syn-${random_string.suffix.result}"
  resource_group_name                  = azurerm_resource_group.main.name
  location                             = azurerm_resource_group.main.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.synapse.id
  sql_administrator_login              = "sqladmin"
  sql_administrator_login_password     = "PetIns@Azure2024!"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "synapse" {
  name               = "synapse"
  storage_account_id = azurerm_storage_account.datalake.id
}

# Synapse Firewall - Allow Azure services
resource "azurerm_synapse_firewall_rule" "allow_azure" {
  name                 = "AllowAllWindowsAzureIps"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}

# =============================================================================
# AZURE DATA FACTORY - Orchestration (Optional, can use Databricks workflows)
# =============================================================================

resource "azurerm_data_factory" "main" {
  name                = "${local.prefix}-adf-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# =============================================================================
# AZURE KEY VAULT - Secrets Management
# =============================================================================

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                        = "petins-kv-${random_string.suffix.result}"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge"
    ]
  }

  tags = local.tags
}

# Store storage account key in Key Vault
resource "azurerm_key_vault_secret" "storage_key" {
  name         = "storage-account-key"
  value        = azurerm_storage_account.datalake.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "storage_account_key" {
  value     = azurerm_storage_account.datalake.primary_access_key
  sensitive = true
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.main.workspace_url
}

output "synapse_workspace_name" {
  value = azurerm_synapse_workspace.main.name
}

output "synapse_sql_endpoint" {
  value = azurerm_synapse_workspace.main.connectivity_endpoints["sqlOnDemand"]
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "data_factory_name" {
  value = azurerm_data_factory.main.name
}
