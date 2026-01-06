variable "name" {
  type        = string
  description = "Service Bus namespace name"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "sku" {
  type        = string
  default     = "Standard"
  description = "SKU tier (Basic, Standard, Premium)"
}

variable "queues" {
  type = list(object({
    name               = string
    max_delivery_count = number
  }))
  default     = []
  description = "List of queues to create"
}

variable "topics" {
  type = list(object({
    name = string
    subscriptions = list(object({
      name               = string
      max_delivery_count = number
      sql_filter         = string
    }))
  }))
  default     = []
  description = "List of topics with subscriptions"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}

resource "azurerm_servicebus_namespace" "sb" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku

  tags = var.tags
}

# Queues
resource "azurerm_servicebus_queue" "queues" {
  for_each = { for q in var.queues : q.name => q }

  name                                 = each.value.name
  namespace_id                         = azurerm_servicebus_namespace.sb.id
  max_delivery_count                   = each.value.max_delivery_count
  dead_lettering_on_message_expiration = true
  enable_partitioning                  = false
}

# Topics
resource "azurerm_servicebus_topic" "topics" {
  for_each = { for t in var.topics : t.name => t }

  name                = each.value.name
  namespace_id        = azurerm_servicebus_namespace.sb.id
  enable_partitioning = false
}

# Subscriptions
resource "azurerm_servicebus_subscription" "subscriptions" {
  for_each = {
    for item in flatten([
      for t in var.topics : [
        for s in t.subscriptions : {
          key        = "${t.name}-${s.name}"
          topic_name = t.name
          sub        = s
        }
      ]
    ]) : item.key => item
  }

  name               = each.value.sub.name
  topic_id           = azurerm_servicebus_topic.topics[each.value.topic_name].id
  max_delivery_count = each.value.sub.max_delivery_count
}

# Subscription rules (SQL filters)
resource "azurerm_servicebus_subscription_rule" "rules" {
  for_each = {
    for item in flatten([
      for t in var.topics : [
        for s in t.subscriptions : {
          key        = "${t.name}-${s.name}"
          topic_name = t.name
          sub_name   = s.name
          sql_filter = s.sql_filter
        } if s.sql_filter != ""
      ]
    ]) : item.key => item
  }

  name            = "${each.value.sub_name}-rule"
  subscription_id = azurerm_servicebus_subscription.subscriptions[each.key].id
  filter_type     = "SqlFilter"
  sql_filter      = each.value.sql_filter
}

output "namespace_id" {
  value       = azurerm_servicebus_namespace.sb.id
  description = "Service Bus namespace ID"
}

output "namespace_name" {
  value       = azurerm_servicebus_namespace.sb.name
  description = "Service Bus namespace name"
}

output "primary_connection_string" {
  value       = azurerm_servicebus_namespace.sb.default_primary_connection_string
  sensitive   = true
  description = "Primary connection string"
}
