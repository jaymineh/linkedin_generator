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
              rowSpan = 6
              colSpan = 12
            }
            metadata = {
              inputs = []
              type   = "Extension/HubsExtension/PartType/MarkdownPart"
              settings = {
                content = {
                  settings = {
                    title    = "LinkedIn Generator Ops"
                    subtitle = "Deployment summary"
                    content  = <<-EOT
                    ### Endpoints
                    - Public app: [${local.frontend_public_url}](${local.frontend_public_url})
                    - Backend: [https://${azurerm_container_app.backend.ingress[0].fqdn}](https://${azurerm_container_app.backend.ingress[0].fqdn})

                    ### Observability
                    - Workbook: `LinkedIn Generator Ops Workbook`
                    - App Insights: `${azurerm_application_insights.main.name}`
                    - Log Analytics: `${azurerm_log_analytics_workspace.main.name}`

                    ### Alerts
                    - `alert-errors-${local.prefix}`
                    - `alert-latency-${local.prefix}`

                    ### Resources
                    - Postgres: `${azurerm_postgresql_flexible_server.main.name}`
                    - Container App: `${azurerm_container_app.backend.name}`
                    - Static Web App: `${azurerm_static_web_app.frontend.name}`
                    EOT
                  }
                }
              }
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

  operations_workbook = {
    version = "Notebook/1.0"
    items = [
      {
        type = 1
        content = {
          json = <<-EOT
          ## LinkedIn Generator Ops Workbook

          Use this workbook for the live charts. The portal dashboard stays intentionally simple because the AzureRM `azurerm_portal_dashboard` resource cannot reliably manage chart tiles with the current Azure Portal schema.

          **Public app:** [${local.frontend_public_url}](${local.frontend_public_url})  
          **Backend:** [https://${azurerm_container_app.backend.ingress[0].fqdn}](https://${azurerm_container_app.backend.ingress[0].fqdn})
          EOT
        }
        name = "text-overview"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "API Requests"
          query        = <<-EOT
          AppRequests
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | summarize Requests = count() by bin(TimeGenerated, 1h)
          | order by TimeGenerated asc
          | render timechart
          EOT
        }
        name = "requests-chart"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Failed Requests"
          query        = <<-EOT
          AppRequests
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Success == false
          | summarize FailedRequests = count() by bin(TimeGenerated, 1h)
          | order by TimeGenerated asc
          | render timechart
          EOT
        }
        name = "failed-requests-chart"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Average API Latency ms"
          query        = <<-EOT
          AppRequests
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | summarize AvgDurationMs = avg(DurationMs) by bin(TimeGenerated, 1h)
          | order by TimeGenerated asc
          | render timechart
          EOT
        }
        name = "duration-chart"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Generation Requests by Tone"
          query        = <<-EOT
          AppMetrics
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name == "linkedin_generator.generation.requests"
          | extend Tone = tostring(Properties["tone"])
          | summarize Requests = sum(Sum) by Tone
          | order by Requests desc
          | render barchart
          EOT
        }
        name = "generation-by-tone"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Style Mode Mix"
          query        = <<-EOT
          AppMetrics
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name == "linkedin_generator.generation.requests"
          | extend StyleMode = tostring(Properties["style_mode"])
          | summarize Requests = sum(Sum) by StyleMode
          | render piechart
          EOT
        }
        name = "style-mode-mix"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Source Type Mix"
          query        = <<-EOT
          AppMetrics
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name == "linkedin_generator.generation.requests"
          | extend SourceType = tostring(Properties["source_type"])
          | summarize Requests = sum(Sum) by SourceType
          | render piechart
          EOT
        }
        name = "source-type-mix"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Average Generation Latency ms"
          query        = <<-EOT
          AppMetrics
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name == "linkedin_generator.generation.duration_ms"
          | summarize AvgLatencyMs = round(sum(Sum) / sum(ItemCount), 2) by bin(TimeGenerated, 1h)
          | order by TimeGenerated asc
          | render timechart
          EOT
        }
        name = "generation-latency"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Generation Failures by Tone"
          query        = <<-EOT
          AppMetrics
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name == "linkedin_generator.generation.failures"
          | extend Tone = tostring(Properties["tone"])
          | summarize Failures = sum(Sum) by Tone
          | order by Failures desc
          | render barchart
          EOT
        }
        name = "generation-failures-tone"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "OpenAI Latency ms"
          query        = <<-EOT
          AppMetrics
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name == "linkedin_generator.openai.duration_ms"
          | summarize AvgLatencyMs = round(sum(Sum) / sum(ItemCount), 2) by bin(TimeGenerated, 1h)
          | order by TimeGenerated asc
          | render timechart
          EOT
        }
        name = "openai-latency"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Style Imports by Sample Bucket"
          query        = <<-EOT
          AppMetrics
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name == "linkedin_generator.style_import.requests"
          | extend SampleBucket = tostring(Properties["sample_bucket"])
          | summarize Imports = sum(Sum) by SampleBucket
          | order by SampleBucket asc
          | render barchart
          EOT
        }
        name = "style-import-bucket"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Frontend Generate Outcomes"
          query        = <<-EOT
          AppEvents
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name in ("frontend_generate_submitted", "frontend_generate_succeeded", "frontend_generate_failed")
          | summarize Events = count() by Name
          | render piechart
          EOT
        }
        name = "frontend-generate-events"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Frontend Events by Page"
          query        = <<-EOT
          AppEvents
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Name startswith "frontend_"
          | extend Page = tostring(Properties["surface"])
          | extend Page = iff(isempty(Page), "general", Page)
          | summarize Events = count() by Page
          | order by Events desc
          | render barchart
          EOT
        }
        name = "frontend-events-page"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Recent Failed Requests"
          query        = <<-EOT
          AppRequests
          | where _ResourceId =~ "${lower(azurerm_application_insights.main.id)}"
          | where Success == false
          | project TimeGenerated, Name, ResultCode, DurationMs, Url
          | order by TimeGenerated desc
          | take 20
          EOT
        }
        name = "failed-requests-table"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Backend CPU Cores"
          query        = <<-EOT
          AzureMetrics
          | where ResourceId =~ "${lower(azurerm_container_app.backend.id)}"
          | where MetricName == "UsageNanoCores"
          | summarize AvgCpuCores = avg(Average) / 1000000000 by bin(TimeGenerated, 5m)
          | order by TimeGenerated asc
          | render timechart
          EOT
        }
        name = "cpu-chart"
      },
      {
        type = 3
        content = {
          version      = "KqlItem/1.0"
          queryType    = 0
          resourceType = "microsoft.operationalinsights/workspaces"
          size         = 1
          title        = "Backend Memory MiB"
          query        = <<-EOT
          AzureMetrics
          | where ResourceId =~ "${lower(azurerm_container_app.backend.id)}"
          | where MetricName == "WorkingSetBytes"
          | summarize AvgMemoryMiB = avg(Average) / 1024 / 1024 by bin(TimeGenerated, 5m)
          | order by TimeGenerated asc
          | render timechart
          EOT
        }
        name = "memory-chart"
      }
    ]
    isLocked            = false
    fallbackResourceIds = [lower(azurerm_log_analytics_workspace.main.id)]
  }
}

resource "random_uuid" "operations_workbook" {}

resource "azurerm_portal_dashboard" "operations" {
  name                 = "dash-${local.prefix}"
  resource_group_name  = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  tags                 = local.common_tags
  dashboard_properties = jsonencode(local.operations_dashboard)
}

resource "azurerm_application_insights_workbook" "operations" {
  name                = random_uuid.operations_workbook.result
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  display_name        = "LinkedIn Generator Ops Workbook"
  source_id           = lower(azurerm_log_analytics_workspace.main.id)
  data_json           = jsonencode(local.operations_workbook)
  tags                = local.common_tags
}
