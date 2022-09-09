variable "azure_resource_group" {}
variable "azure_resource_group_location" {
    default = "West Europe"
}

variable "azure_eventhub_namespace" {
    default = "streaming-merging-streams"
}

variable "azure_eventhub_stream" {
    default = "locations-stream"
}

