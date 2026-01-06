variable "name" {
  type        = string
  description = "Azure OpenAI service name"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  default     = "eastus"
  description = "Azure region (OpenAI availability varies)"
}

variable "sku_name" {
  type        = string
  default     = "S0"
  description = "SKU name"
}

variable "deployments" {
  type = list(object({
    name          = string
    model_name    = string
    model_version = string
    capacity      = number
  }))
  default = [
    {
      name          = "gpt-4o"
      model_name    = "gpt-4o"
      model_version = "2024-08-06"
      capacity      = 10
    }
  ]
  description = "Model deployments"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}

resource "azurerm_cognitive_account" "openai" {
  name                  = var.name
  location              = var.location
  resource_group_name   = var.resource_group_name
  kind                  = "OpenAI"
  sku_name              = var.sku_name
  custom_subdomain_name = var.name

  identity {
    type = "SystemAssigned"
  }

  network_acls {
    default_action = "Allow"
  }

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "deployments" {
  for_each = { for d in var.deployments : d.name => d }

  name                 = each.value.name
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = each.value.model_name
    version = each.value.model_version
  }

  scale {
    type     = "Standard"
    capacity = each.value.capacity
  }
}

output "openai_endpoint" {
  value       = azurerm_cognitive_account.openai.endpoint
  description = "Azure OpenAI endpoint"
}

output "openai_id" {
  value       = azurerm_cognitive_account.openai.id
  description = "Azure OpenAI resource ID"
}

output "openai_key" {
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
  description = "Primary access key"
}
