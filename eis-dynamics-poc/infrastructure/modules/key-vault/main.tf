variable "name" {
  type        = string
  description = "Key Vault name (must be globally unique)"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "tenant_id" {
  type        = string
  description = "Azure AD tenant ID"
}

variable "sku_name" {
  type        = string
  default     = "standard"
  description = "Key Vault SKU (standard or premium)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
  name                       = var.name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = var.sku_name
  soft_delete_retention_days = 7
  purge_protection_enabled   = false # Set to true for production

  enable_rbac_authorization = true

  network_acls {
    default_action = "Allow" # Restrict in production
    bypass         = "AzureServices"
  }

  tags = var.tags
}

# Grant deploying identity Key Vault Administrator role
resource "azurerm_role_assignment" "kv_admin" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

output "key_vault_id" {
  value       = azurerm_key_vault.kv.id
  description = "Key Vault resource ID"
}

output "key_vault_uri" {
  value       = azurerm_key_vault.kv.vault_uri
  description = "Key Vault URI"
}

output "key_vault_name" {
  value       = azurerm_key_vault.kv.name
  description = "Key Vault name"
}
