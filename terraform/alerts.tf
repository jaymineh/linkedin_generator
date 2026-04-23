resource "azurerm_monitor_action_group" "email" {
  count               = var.alert_email != "" ? 1 : 0
  name                = "ag-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "linkedin"
  tags                = local.common_tags

  email_receiver {
    name          = "admin"
    email_address = var.alert_email
  }
}

resource "azurerm_monitor_metric_alert" "high_error_rate" {
  count               = var.alert_email != "" ? 1 : 0
  name                = "alert-errors-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights.main.id]
  description         = "Fires when failed request count exceeds 5 in 5 minutes"
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "requests/failed"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 5
  }

  action {
    action_group_id = azurerm_monitor_action_group.email[0].id
  }
}

resource "azurerm_monitor_metric_alert" "high_latency" {
  count               = var.alert_email != "" ? 1 : 0
  name                = "alert-latency-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights.main.id]
  description         = "Fires when server response time exceeds 15 seconds"
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "requests/duration"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 15000
  }

  action {
    action_group_id = azurerm_monitor_action_group.email[0].id
  }
}
