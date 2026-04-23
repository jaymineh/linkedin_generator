from __future__ import annotations

import argparse
import subprocess

from common import (
    TERRAFORM_DIR,
    echo,
    ensure_azure_login,
    ensure_command,
    ensure_github_auth,
    fail,
    get_openai_key,
    gh_secret_delete,
    load_config,
    load_local_env,
    run,
    terraform_backend_args,
    terraform_var_args,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Destroy Azure infrastructure for the LinkedIn generator.")
    parser.add_argument("--openai-api-key")
    parser.add_argument("--db-password")
    parser.add_argument("--alert-email")
    parser.add_argument("--include-bootstrap", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_command("az", "Install Azure CLI first.")
    ensure_command("terraform", "Install Terraform first.")
    ensure_azure_login()
    if args.include_bootstrap:
        ensure_command("gh", "Install GitHub CLI first.")
        ensure_github_auth()

    config = load_config()
    if not config:
        fail("Missing .deploy.auto.json. Run `python scripts/bootstrap.py` first.")

    local_env = load_local_env()
    openai_api_key = get_openai_key(local_env, args.openai_api_key)
    db_password = args.db_password or config.get("db_password")
    if not db_password:
        fail("Database password missing. Re-run bootstrap or pass `--db-password`.")

    alert_email = args.alert_email if args.alert_email is not None else config.get("alert_email", "")

    echo("Initializing Terraform backend...")
    run(["terraform", "init", *terraform_backend_args(config)], cwd=TERRAFORM_DIR)

    echo("Destroying Terraform-managed infrastructure...")
    var_args = terraform_var_args(
        openai_api_key=openai_api_key,
        db_password=db_password,
        alert_email=alert_email,
        backend_image_tag="destroy",
        allowed_origins="*",
    )
    run(["terraform", "destroy", "-auto-approve", "-input=false", *var_args], cwd=TERRAFORM_DIR)

    if args.include_bootstrap:
        echo("Removing GitHub Actions secrets...")
        owner = config["repo_owner"]
        repo = config["repo_name"]
        for name in [
            "AZURE_CLIENT_ID",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
            "TF_BACKEND_STORAGE_ACCOUNT",
            "OPENAI_API_KEY",
            "DB_PASSWORD",
            "ALERT_EMAIL",
        ]:
            gh_secret_delete(owner, repo, name)

        echo("Deleting Azure AD app registration and Terraform state resource group...")
        run(["az", "ad", "app", "delete", "--id", config["azure_client_id"]], check=False)
        run(
            [
                "az",
                "group",
                "delete",
                "--name",
                config["tfstate_resource_group"],
                "--yes",
                "--no-wait",
            ],
            check=False,
        )

    echo("")
    echo("Destroy complete.")
    if args.include_bootstrap:
        echo("Bootstrap resources are being removed as well.")
    else:
        echo("Bootstrap resources were kept. Reuse them for the next deploy.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(str(exc))
    except Exception as exc:  # noqa: BLE001
        fail(str(exc))
