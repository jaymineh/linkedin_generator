output "backend_url" {
  value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "frontend_url" {
  value = local.frontend_public_url
}

output "api_base_url" {
  value = local.api_public_url
}

output "static_web_app_direct_url" {
  value = "https://${azurerm_static_web_app.frontend.default_host_name}"
}

output "operations_dashboard_name" {
  value = azurerm_portal_dashboard.operations.name
}

output "operations_workbook_name" {
  value = azurerm_application_insights_workbook.operations.display_name
}

output "operations_workbook_id" {
  value = azurerm_application_insights_workbook.operations.id
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "acr_username" {
  value     = azurerm_container_registry.acr.admin_username
  sensitive = true
}

output "acr_password" {
  value     = azurerm_container_registry.acr.admin_password
  sensitive = true
}

output "app_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}

output "static_web_app_api_key" {
  value     = azurerm_static_web_app.frontend.api_key
  sensitive = true
}
