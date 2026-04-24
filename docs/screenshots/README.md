# Portal screenshots (optional)

This folder holds **visual documentation** for the README.

## What is here today

- `mock-portal-app-insights.png` — **illustrative mock** of an Application Insights style overview (not your live subscription).
- `mock-portal-workbook.png` — **illustrative mock** of an Azure Monitor workbook layout (not your live subscription).

You can **replace** these files with real captures from your Azure tenant using the same filenames, or add new files and update the links in the root `README.md`.

## Recommended real screenshots to capture

Save PNG or JPG files here and link them from the main README if you want authentic portal shots.

| # | What to capture | Suggested filename |
|---|-----------------|-------------------|
| 1 | Resource group `rg-linkedin-gen-prod` — all resources visible | `01-resource-group-overview.png` |
| 2 | Container App — overview + ingress URL | `02-container-app-overview.png` |
| 3 | Static Web App — overview + default hostname | `03-static-web-app-overview.png` |
| 4 | PostgreSQL Flexible Server — overview | `04-postgresql-overview.png` |
| 5 | Application Insights — default dashboard or Overview | `05-application-insights-dashboard.png` |
| 6 | Log Analytics — workspace blade | `06-log-analytics-workspace.png` |
| 7 | Workbook **LinkedIn Generator Ops Workbook** open in edit or view mode | `07-ops-workbook.png` |
| 8 | Portal shared dashboard `dash-linkedin-gen-prod` | `08-ops-dashboard.png` |
| 9 | GitHub Actions — successful `Pipeline` run showing stages | `09-github-actions-pipeline.png` |
| 10 | Metric alert rules (if `ALERT_EMAIL` is set) | `10-metric-alerts.png` |

## How to capture quickly

1. In Azure Portal, open the resource group from Terraform outputs (`terraform output -raw` from `terraform/` or the GitHub Actions log).
2. Use **Windows Snipping Tool** or **Snip & Sketch** (Win+Shift+S).
3. Save into this folder with a descriptive name.
4. Reference in Markdown: `![caption](./docs/screenshots/your-file.png)` from the repository root.

**Privacy:** redact subscription IDs, emails, and connection strings if you share the repo publicly.
