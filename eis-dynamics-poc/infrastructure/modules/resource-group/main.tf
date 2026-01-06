terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
  }
}

variable "resource_groups" {
  type = map(object({
    name     = string
    location = string
    tags     = map(string)
  }))
  description = "Map of resource groups to create"
}

resource "azurerm_resource_group" "rg" {
  for_each = var.resource_groups

  name     = each.value.name
  location = each.value.location
  tags = merge(each.value.tags, {
    project    = "eis-d365-poc"
    managed_by = "terraform"
  })
}

output "resource_group_ids" {
  value       = { for k, v in azurerm_resource_group.rg : k => v.id }
  description = "Map of resource group IDs"
}

output "resource_group_names" {
  value       = { for k, v in azurerm_resource_group.rg : k => v.name }
  description = "Map of resource group names"
}

output "resource_group_locations" {
  value       = { for k, v in azurerm_resource_group.rg : k => v.location }
  description = "Map of resource group locations"
}
