resource "azurerm_monitor_diagnostic_setting" "container_app_metrics" {
  name                       = "diag-containerapp-${local.prefix}"
  target_resource_id         = azurerm_container_app.backend.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  metric {
    category = "AllMetrics"
  }
}

resource "azurerm_monitor_diagnostic_setting" "static_web_app" {
  name                       = "diag-staticsite-${local.prefix}"
  target_resource_id         = azurerm_static_web_app.frontend.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "StaticSiteHttpLogs"
  }

  enabled_log {
    category = "StaticSiteDiagnosticLogs"
  }

  metric {
    category = "AllMetrics"
  }
}

resource "azurerm_monitor_diagnostic_setting" "postgres" {
  name                       = "diag-postgres-${local.prefix}"
  target_resource_id         = azurerm_postgresql_flexible_server.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "PostgreSQLLogs"
  }

  enabled_log {
    category = "PostgreSQLFlexSessions"
  }

  enabled_log {
    category = "PostgreSQLFlexQueryStoreRuntime"
  }

  enabled_log {
    category = "PostgreSQLFlexQueryStoreWaitStats"
  }

  enabled_log {
    category = "PostgreSQLFlexTableStats"
  }

  enabled_log {
    category = "PostgreSQLFlexDatabaseXacts"
  }

  enabled_log {
    category = "PostgreSQLFlexPGBouncer"
  }

  enabled_log {
    category = "PostgreSQLQueryStoreSqlText"
  }

  metric {
    category = "AllMetrics"
  }
}

locals {
  operations_dashboard = {
    lenses = {
      "0" = {
        order = 0
        parts = {
          "0" = {
            position = {
              x       = 0
              y       = 0
              rowSpan = 4
              colSpan = 4
            }
            metadata = {
              inputs = []
              type   = "Extension/HubsExtension/PartType/MarkdownPart"
              settings = {
                content = {
                  settings = {
                    title    = "LinkedIn Generator Ops"
                    subtitle = "Live overview"
                    content  = <<-EOT
                    ### Endpoints
                    - Public app: [${local.frontend_public_url}](${local.frontend_public_url})
                    - Backend: [https://${azurerm_container_app.backend.ingress[0].fqdn}](https://${azurerm_container_app.backend.ingress[0].fqdn})

                    ### Alerts
                    - `alert-errors-${local.prefix}`
                    - `alert-latency-${local.prefix}`

                    ### Resources
                    - App Insights: `${azurerm_application_insights.main.name}`
                    - Log Analytics: `${azurerm_log_analytics_workspace.main.name}`
                    - Postgres: `${azurerm_postgresql_flexible_server.main.name}`
                    EOT
                  }
                }
              }
            }
          }
          "1" = {
            position = {
              x       = 4
              y       = 0
              rowSpan = 4
              colSpan = 6
            }
            metadata = {
              inputs = [
                {
                  name = "queryInputs"
                  value = {
                    timespan = {
                      duration = "PT24H"
                    }
                    id        = azurerm_application_insights.main.id
                    chartType = 0
                    metrics = [
                      {
                        name       = "requests/count"
                        resourceId = azurerm_application_insights.main.id
                      }
                    ]
                  }
                }
              ]
              type = "Extension/Microsoft_Azure_Monitoring/PartType/MetricsChartPart"
            }
          }
          "2" = {
            position = {
              x       = 10
              y       = 0
              rowSpan = 4
              colSpan = 6
            }
            metadata = {
              inputs = [
                {
                  name = "queryInputs"
                  value = {
                    timespan = {
                      duration = "PT24H"
                    }
                    id        = azurerm_application_insights.main.id
                    chartType = 0
                    metrics = [
                      {
                        name       = "requests/failed"
                        resourceId = azurerm_application_insights.main.id
                      }
                    ]
                  }
                }
              ]
              type = "Extension/Microsoft_Azure_Monitoring/PartType/MetricsChartPart"
            }
          }
          "3" = {
            position = {
              x       = 0
              y       = 4
              rowSpan = 4
              colSpan = 8
            }
            metadata = {
              inputs = [
                {
                  name = "queryInputs"
                  value = {
                    timespan = {
                      duration = "PT24H"
                    }
                    id        = azurerm_application_insights.main.id
                    chartType = 0
                    metrics = [
                      {
                        name       = "requests/duration"
                        resourceId = azurerm_application_insights.main.id
                      }
                    ]
                  }
                }
              ]
              type = "Extension/Microsoft_Azure_Monitoring/PartType/MetricsChartPart"
            }
          }
          "4" = {
            position = {
              x       = 8
              y       = 4
              rowSpan = 4
              colSpan = 4
            }
            metadata = {
              inputs = [
                {
                  name = "queryInputs"
                  value = {
                    timespan = {
                      duration = "PT24H"
                    }
                    id        = azurerm_container_app.backend.id
                    chartType = 0
                    metrics = [
                      {
                        name       = "UsageNanoCores"
                        resourceId = azurerm_container_app.backend.id
                      }
                    ]
                  }
                }
              ]
              type = "Extension/Microsoft_Azure_Monitoring/PartType/MetricsChartPart"
            }
          }
          "5" = {
            position = {
              x       = 12
              y       = 4
              rowSpan = 4
              colSpan = 4
            }
            metadata = {
              inputs = [
                {
                  name = "queryInputs"
                  value = {
                    timespan = {
                      duration = "PT24H"
                    }
                    id        = azurerm_container_app.backend.id
                    chartType = 0
                    metrics = [
                      {
                        name       = "WorkingSetBytes"
                        resourceId = azurerm_container_app.backend.id
                      }
                    ]
                  }
                }
              ]
              type = "Extension/Microsoft_Azure_Monitoring/PartType/MetricsChartPart"
            }
          }
        }
      }
    }
    metadata = {
      model = {
        timeRange = {
          value = {
            relative = {
              duration = 24
              timeUnit = 1
            }
          }
          type = "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
        }
      }
    }
  }
}

resource "azurerm_portal_dashboard" "operations" {
  name                 = "dash-${local.prefix}"
  resource_group_name  = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  tags                 = local.common_tags
  dashboard_properties = jsonencode(local.operations_dashboard)
}
