# LinkedIn Generator

This repo can be bootstrapped, deployed, and destroyed with Python scripts so the Azure setup is largely automated.

## Prerequisites

- Azure CLI installed and logged in: `az login`
- GitHub CLI installed and logged in: `gh auth login`
- Python 3.11+
- Node.js 20+
- Terraform 1.6+

The scripts read `OPENAI_API_KEY` from the root `.env` file. They also accept `OPEN_AI_KEY` as a fallback alias.

## One-time bootstrap

This creates the Terraform remote-state storage, Azure AD app registration for GitHub OIDC, role assignment, and GitHub Actions secrets. It also writes local automation settings to `.deploy.auto.json`.

```bash
python scripts/bootstrap.py
```

Optional overrides:

```bash
python scripts/bootstrap.py --tfstate-storage-account myuniquetfstate123 --alert-email you@example.com
```

## Full deploy

This performs the full Azure deploy flow:

1. Terraform init with remote state
2. bootstrap apply for resource group + ACR
3. build backend image in ACR
4. full Terraform apply
5. tighten CORS to the deployed frontend URL
6. build the frontend
7. upload the frontend to Azure Static Web Apps
8. smoke-test backend and frontend

```bash
python scripts/deploy.py
```

Useful options:

```bash
python scripts/deploy.py --backend-image-tag customtag
python scripts/deploy.py --skip-frontend
python scripts/deploy.py --allowed-origins https://example.com
```

## Full destroy

Destroy only the application infrastructure:

```bash
python scripts/destroy.py
```

Destroy the application infrastructure plus the bootstrap resources (GitHub secrets, Azure AD app registration, Terraform state resource group):

```bash
python scripts/destroy.py --include-bootstrap
```
