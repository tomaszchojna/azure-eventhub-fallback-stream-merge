terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.0.0"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_resource_group" "streaming" {
  name     = var.azure_resource_group
}

resource "azurerm_eventhub_namespace" "streaming" {
  name                = var.azure_eventhub_namespace
  location            = data.azurerm_resource_group.streaming.location
  resource_group_name = data.azurerm_resource_group.streaming.name
  sku                 = "Standard"
  capacity            = 1
}

resource "azurerm_eventhub_namespace_authorization_rule" "streaming" {
  name                = "FrontendApp"
  namespace_name      = azurerm_eventhub_namespace.streaming.name
  resource_group_name = data.azurerm_resource_group.streaming.name

  listen = true
  send   = true
  manage = false
}

resource "azurerm_eventhub" "stream" {
  name                = var.azure_eventhub_stream
  namespace_name      = azurerm_eventhub_namespace.streaming.name
  resource_group_name = data.azurerm_resource_group.streaming.name
  partition_count     = 1
  message_retention   = 1
}

resource "azurerm_eventhub_consumer_group" "frontend_demo_low" {
  name                = "frontend_demo"
  namespace_name      = azurerm_eventhub_namespace.streaming.name
  eventhub_name       = azurerm_eventhub.stream.name
  resource_group_name = data.azurerm_resource_group.streaming.name
}

resource "azurerm_storage_account" "eventhub_checkpoint" {
  name                     = "experimenteventhubmerges"
  resource_group_name      = data.azurerm_resource_group.streaming.name
  location                 = data.azurerm_resource_group.streaming.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "eventhub_checkpoint" {
  name                  = "checkpoints"
  storage_account_name  = azurerm_storage_account.eventhub_checkpoint.name
  container_access_type = "private"
}

output "azure_eventhub_connection_string" {
    value = azurerm_eventhub_namespace_authorization_rule.streaming.primary_connection_string
}

output "azure_storage_container_connection_string" {
    value = azurerm_storage_account.eventhub_checkpoint.primary_connection_string
}