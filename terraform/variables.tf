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

variable "google_api_key" {
  description = "Optional Google Gemini API key (OpenAI-compatible endpoint)."
  sensitive   = true
  default     = ""
}

variable "zai_api_key" {
  description = "Optional ZAI API key."
  sensitive   = true
  default     = ""
}

variable "openai_model" {
  description = "Default OpenAI model used by the backend."
  default     = "gpt-5.4"
}

variable "openai_base_url" {
  description = "Optional OpenAI-compatible base URL override."
  default     = ""
}

variable "google_model" {
  description = "Default Google model used by the backend."
  default     = "gemini-2.5-flash"
}

variable "google_base_url" {
  description = "Google OpenAI-compatible base URL."
  default     = "https://generativelanguage.googleapis.com/v1beta/openai/"
}

variable "zai_model" {
  description = "Default ZAI model used by the backend."
  default     = "glm-4.5-air"
}

variable "zai_base_url" {
  description = "ZAI OpenAI-compatible base URL."
  default     = "https://api.z.ai/api/paas/v4/"
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

variable "enable_front_door_waf" {
  description = "Enable Azure Front Door and WAF in front of the app"
  default     = false
}

variable "waf_mode" {
  description = "Front Door WAF mode"
  default     = "Prevention"
}

variable "backend_image_tag" {
  description = "Docker image tag to deploy for the backend container"
  default     = "latest"
}
