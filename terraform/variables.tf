variable "location" {
  default = "East US"
}

variable "postgres_location" {
  description = "Azure region for PostgreSQL Flexible Server"
  default     = "Central US"
}

variable "project" {
  default = "linkedin-gen"
}

variable "environment" {
  default = "prod"
}

variable "openai_api_key" {
  sensitive = true
}

variable "db_password" {
  sensitive = true
}

variable "allowed_origins" {
  description = "Comma-separated list of allowed CORS origins"
  default     = "*"
}

variable "alert_email" {
  description = "Email address for monitoring alert notifications"
  default     = ""
}

variable "front_door_sku" {
  description = "Azure Front Door SKU used for the app edge and WAF"
  default     = "Standard_AzureFrontDoor"
}

variable "waf_mode" {
  description = "Front Door WAF mode"
  default     = "Prevention"
}

variable "backend_image_tag" {
  description = "Docker image tag to deploy for the backend container"
  default     = "latest"
}
