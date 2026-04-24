# LinkedIn Generator

This repo uses Python scripts for one-time bootstrap and destroy, while production deploys run from GitHub Actions.

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

## Production deploy

Production deploys happen in GitHub Actions, not on your local machine.

After bootstrap is complete:

1. Commit your changes
2. Push to `main`
3. The `Deploy` workflow builds the backend image on the GitHub runner, pushes it to ACR, applies Terraform, builds the frontend, deploys it to Static Web Apps, tightens CORS, and smoke-tests the live app

If you run `python scripts/deploy.py`, it will only remind you to deploy through GitHub Actions.

## Full destroy

Destroy only the application infrastructure:

```bash
python scripts/destroy.py
```

Destroy the application infrastructure plus the bootstrap resources (GitHub secrets, Azure AD app registration, Terraform state resource group):

```bash
python scripts/destroy.py --include-bootstrap
```
