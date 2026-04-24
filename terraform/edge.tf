resource "random_string" "edge_suffix" {
  count   = var.enable_front_door_waf ? 1 : 0
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_cdn_frontdoor_profile" "main" {
  count                    = var.enable_front_door_waf ? 1 : 0
  name                     = "fdp-${local.prefix}"
  resource_group_name      = azurerm_resource_group.main.name
  sku_name                 = var.front_door_sku
  response_timeout_seconds = 120
  tags                     = local.common_tags
}

resource "azurerm_cdn_frontdoor_endpoint" "main" {
  count                    = var.enable_front_door_waf ? 1 : 0
  name                     = "fd-${local.prefix}-${random_string.edge_suffix[0].result}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main[0].id
  tags                     = local.common_tags
}

resource "azurerm_cdn_frontdoor_origin_group" "frontend" {
  count                    = var.enable_front_door_waf ? 1 : 0
  name                     = "og-frontend"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main[0].id
  session_affinity_enabled = false

  load_balancing {
    additional_latency_in_milliseconds = 0
    sample_size                        = 4
    successful_samples_required        = 3
  }

  health_probe {
    interval_in_seconds = 240
    path                = "/"
    protocol            = "Https"
    request_type        = "GET"
  }
}

resource "azurerm_cdn_frontdoor_origin" "frontend" {
  count                          = var.enable_front_door_waf ? 1 : 0
  name                           = "static-site"
  cdn_frontdoor_origin_group_id  = azurerm_cdn_frontdoor_origin_group.frontend[0].id
  enabled                        = true
  certificate_name_check_enabled = true
  host_name                      = azurerm_static_web_app.frontend.default_host_name
  origin_host_header             = azurerm_static_web_app.frontend.default_host_name
  http_port                      = 80
  https_port                     = 443
  priority                       = 1
  weight                         = 1000
}

resource "azurerm_cdn_frontdoor_origin_group" "backend" {
  count                    = var.enable_front_door_waf ? 1 : 0
  name                     = "og-backend"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main[0].id
  session_affinity_enabled = false

  load_balancing {
    additional_latency_in_milliseconds = 0
    sample_size                        = 4
    successful_samples_required        = 3
  }

  health_probe {
    interval_in_seconds = 120
    path                = "/health/ready"
    protocol            = "Https"
    request_type        = "GET"
  }
}

resource "azurerm_cdn_frontdoor_origin" "backend" {
  count                          = var.enable_front_door_waf ? 1 : 0
  name                           = "backend-api"
  cdn_frontdoor_origin_group_id  = azurerm_cdn_frontdoor_origin_group.backend[0].id
  enabled                        = true
  certificate_name_check_enabled = true
  host_name                      = azurerm_container_app.backend.ingress[0].fqdn
  origin_host_header             = azurerm_container_app.backend.ingress[0].fqdn
  http_port                      = 80
  https_port                     = 443
  priority                       = 1
  weight                         = 1000
}

resource "azurerm_cdn_frontdoor_route" "api" {
  count                         = var.enable_front_door_waf ? 1 : 0
  name                          = "api-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.main[0].id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.backend[0].id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.backend[0].id]
  enabled                       = true
  forwarding_protocol           = "HttpsOnly"
  https_redirect_enabled        = true
  link_to_default_domain        = true
  patterns_to_match             = ["/api/*"]
  supported_protocols           = ["Http", "Https"]
}

resource "azurerm_cdn_frontdoor_route" "frontend" {
  count                         = var.enable_front_door_waf ? 1 : 0
  name                          = "frontend-route"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.main[0].id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.frontend[0].id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.frontend[0].id]
  enabled                       = true
  forwarding_protocol           = "HttpsOnly"
  https_redirect_enabled        = true
  link_to_default_domain        = true
  patterns_to_match             = ["/*"]
  supported_protocols           = ["Http", "Https"]
}

resource "azurerm_cdn_frontdoor_firewall_policy" "main" {
  count               = var.enable_front_door_waf ? 1 : 0
  name                = "waf${replace(local.prefix, "-", "")}"
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = azurerm_cdn_frontdoor_profile.main[0].sku_name
  enabled             = true
  mode                = var.waf_mode
  tags                = local.common_tags

  managed_rule {
    type    = "DefaultRuleSet"
    version = "1.0"
    action  = "Block"
  }

  managed_rule {
    type    = "Microsoft_BotManagerRuleSet"
    version = "1.1"
    action  = "Block"
  }
}

resource "azurerm_cdn_frontdoor_security_policy" "main" {
  count                    = var.enable_front_door_waf ? 1 : 0
  name                     = "sp-${local.prefix}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main[0].id

  security_policies {
    firewall {
      cdn_frontdoor_firewall_policy_id = azurerm_cdn_frontdoor_firewall_policy.main[0].id

      association {
        domain {
          cdn_frontdoor_domain_id = azurerm_cdn_frontdoor_endpoint.main[0].id
        }

        patterns_to_match = ["/*"]
      }
    }
  }
}
