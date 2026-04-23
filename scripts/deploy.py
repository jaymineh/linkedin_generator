from __future__ import annotations

import argparse
import subprocess
from datetime import UTC, datetime

from common import (
    FRONTEND_DIR,
    TERRAFORM_DIR,
    echo,
    ensure_azure_login,
    ensure_command,
    fail,
    get_openai_key,
    http_get,
    load_config,
    load_local_env,
    resource_group_name,
    run,
    terraform_backend_args,
    terraform_output,
    terraform_var_args,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fully automated Azure deploy for the LinkedIn generator.")
    parser.add_argument("--backend-image-tag")
    parser.add_argument("--openai-api-key")
    parser.add_argument("--db-password")
    parser.add_argument("--alert-email")
    parser.add_argument("--allowed-origins")
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--skip-cors-tighten", action="store_true")
    return parser.parse_args()


def git_sha() -> str:
    try:
        return run(["git", "rev-parse", "--short", "HEAD"])
    except Exception:  # noqa: BLE001
        return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def terraform_apply(*, var_args: list[str], targets: list[str] | None = None) -> None:
    command = ["terraform", "apply", "-auto-approve", "-input=false"]
    if targets:
        for target in targets:
            command.append(f"-target={target}")
    command.extend(var_args)
    run(command, cwd=TERRAFORM_DIR)


def main() -> None:
    args = parse_args()
    ensure_command("az", "Install Azure CLI first.")
    ensure_command("terraform", "Install Terraform first.")
    ensure_command("npm", "Install Node.js first.")
    ensure_azure_login()

    config = load_config()
    if not config:
        fail("Missing .deploy.auto.json. Run `python scripts/bootstrap.py` first.")

    local_env = load_local_env()
    openai_api_key = get_openai_key(local_env, args.openai_api_key)
    db_password = args.db_password or config.get("db_password")
    if not db_password:
        fail("Database password missing. Re-run bootstrap or pass `--db-password`.")

    alert_email = args.alert_email if args.alert_email is not None else config.get("alert_email", "")
    initial_allowed_origins = args.allowed_origins or "*"
    backend_image_tag = args.backend_image_tag or git_sha()
    rg_name = config.get("resource_group", resource_group_name())

    echo("Initializing Terraform backend...")
    run(["terraform", "init", *terraform_backend_args(config)], cwd=TERRAFORM_DIR)

    initial_var_args = terraform_var_args(
        openai_api_key=openai_api_key,
        db_password=db_password,
        alert_email=alert_email,
        backend_image_tag=backend_image_tag,
        allowed_origins=initial_allowed_origins,
    )

    echo("Bootstrapping Azure resource group and ACR...")
    terraform_apply(
        var_args=initial_var_args,
        targets=["azurerm_resource_group.main", "azurerm_container_registry.acr"],
    )

    echo("Building backend image in Azure Container Registry...")
    acr_name = run(["az", "acr", "list", "-g", rg_name, "--query", "[0].name", "-o", "tsv"])
    if not acr_name:
        fail(f"No Azure Container Registry found in resource group {rg_name}.")

    run(
        [
            "az",
            "acr",
            "build",
            "--registry",
            acr_name,
            "--image",
            f"backend:{backend_image_tag}",
            "--image",
            "backend:latest",
            "./backend",
        ]
    )

    echo("Applying full Terraform stack...")
    terraform_apply(var_args=initial_var_args)

    backend_url = terraform_output("backend_url")
    frontend_url = terraform_output("frontend_url")

    if not args.allowed_origins and not args.skip_cors_tighten:
        echo("Tightening CORS to the deployed frontend URL...")
        tightened_var_args = terraform_var_args(
            openai_api_key=openai_api_key,
            db_password=db_password,
            alert_email=alert_email,
            backend_image_tag=backend_image_tag,
            allowed_origins=frontend_url,
        )
        terraform_apply(var_args=tightened_var_args)
        backend_url = terraform_output("backend_url")
        frontend_url = terraform_output("frontend_url")

    echo("Smoke testing backend readiness...")
    status = http_get(f"{backend_url}/health/ready")
    if status != 200:
        fail(f"Backend readiness check failed with HTTP {status}")

    if not args.skip_frontend:
        echo("Building frontend...")
        env = {"NEXT_PUBLIC_API_URL": backend_url}
        run(["npm", "ci"], cwd=FRONTEND_DIR, env=env)
        run(["npm", "run", "build"], cwd=FRONTEND_DIR, env=env)

        echo("Uploading frontend to Azure Static Web Apps...")
        swa_name = run(["az", "staticwebapp", "list", "-g", rg_name, "--query", "[0].name", "-o", "tsv"])
        if not swa_name:
            fail(f"No Azure Static Web App found in resource group {rg_name}.")
        token = run(
            [
                "az",
                "staticwebapp",
                "secrets",
                "list",
                "-n",
                swa_name,
                "-g",
                rg_name,
                "--query",
                "properties.apiKey",
                "-o",
                "tsv",
            ]
        )
        if not token:
            fail("Could not retrieve Static Web App deployment token.")

        run(
            [
                "npx",
                "--yes",
                "@azure/static-web-apps-cli",
                "deploy",
                "frontend/out",
                "--deployment-token",
                token,
                "--env",
                "production",
            ]
        )

        frontend_status = http_get(frontend_url)
        if frontend_status != 200:
            fail(f"Frontend smoke test failed with HTTP {frontend_status}")

    echo("")
    echo("Deployment complete.")
    echo(f"Backend URL:  {backend_url}")
    echo(f"Frontend URL: {frontend_url}")
    echo(f"Backend image tag: {backend_image_tag}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(str(exc))
    except Exception as exc:  # noqa: BLE001
        fail(str(exc))
