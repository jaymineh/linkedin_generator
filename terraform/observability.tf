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

resource "azurerm_portal_dashboard" "operations" {
  name                = "dash-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags

  dashboard_properties = <<DASH
{
  "lenses": {
    "0": {
      "order": 0,
      "parts": {
        "0": {
          "position": {
            "x": 0,
            "y": 0,
            "rowSpan": 8,
            "colSpan": 16
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "settings": {
                  "title": "LinkedIn Generator Operations",
                  "subtitle": "Runbook and observability shortcuts",
                  "content": "## Live endpoints\\n- Public app URL: ${local.frontend_public_url}\\n- Backend direct URL: https://${azurerm_container_app.backend.ingress[0].fqdn}\\n- Static Web App direct URL: https://${azurerm_static_web_app.frontend.default_host_name}\\n\\n## Azure resources\\n- Application Insights: ${azurerm_application_insights.main.name}\\n- Log Analytics Workspace: ${azurerm_log_analytics_workspace.main.name}\\n- Container App: ${azurerm_container_app.backend.name}\\n- PostgreSQL Flexible Server: ${azurerm_postgresql_flexible_server.main.name}\\n- Front Door endpoint: ${var.enable_front_door_waf ? azurerm_cdn_frontdoor_endpoint.main[0].host_name : "Disabled on current subscription"}\\n\\n## Useful KQL queries\\n### Requests by result code\\n```kusto\\nAppRequests\\n| summarize requests=count() by ResultCode\\n| order by ResultCode asc\\n```\\n\\n### Slow requests over time\\n```kusto\\nAppRequests\\n| summarize avg(DurationMs) by bin(TimeGenerated, 5m)\\n```\\n\\n### Exceptions\\n```kusto\\nAppExceptions\\n| project TimeGenerated, ProblemId, Type, InnermostMessage\\n| order by TimeGenerated desc\\n```\\n\\n### Static Web App diagnostics\\n```kusto\\nAzureDiagnostics\\n| where ResourceProvider == \\\"MICROSOFT.WEB\\\"\\n| order by TimeGenerated desc\\n```\\n\\n### PostgreSQL logs\\n```kusto\\nAzureDiagnostics\\n| where ResourceProvider == \\\"MICROSOFT.DBFORPOSTGRESQL\\\"\\n| order by TimeGenerated desc\\n```"
                }
              }
            }
          }
        }
      }
    }
  },
  "metadata": {
    "model": {
      "timeRange": {
        "value": {
          "relative": {
            "duration": 24,
            "timeUnit": 1
          }
        },
        "type": "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
      }
    }
  }
}
DASH
}
