from __future__ import annotations

import argparse
import json

from common import (
    CONFIG_PATH,
    DEFAULT_LOCATION,
    DEFAULT_STATE_CONTAINER,
    DEFAULT_STATE_KEY,
    DEFAULT_STATE_RG,
    echo,
    ensure_azure_login,
    ensure_command,
    ensure_github_auth,
    fail,
    generate_db_password,
    get_git_remote_repo,
    get_openai_key,
    gh_secret_set,
    load_config,
    load_local_env,
    make_storage_account_name,
    resource_group_name,
    run,
    run_json,
    save_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap Azure + GitHub OIDC + remote state for the LinkedIn generator."
    )
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--tfstate-resource-group", default=DEFAULT_STATE_RG)
    parser.add_argument("--tfstate-storage-account")
    parser.add_argument("--tfstate-container", default=DEFAULT_STATE_CONTAINER)
    parser.add_argument("--tfstate-key", default=DEFAULT_STATE_KEY)
    parser.add_argument("--openai-api-key")
    parser.add_argument("--db-password")
    parser.add_argument("--alert-email", default="")
    parser.add_argument("--app-display-name", default="linkedin-generator-github-actions")
    parser.add_argument("--skip-github-secrets", action="store_true")
    return parser.parse_args()


def ensure_remote_state(
    *,
    resource_group: str,
    storage_account: str,
    container: str,
    location: str,
) -> None:
    echo("Ensuring Terraform remote state resources exist...")
    run(["az", "group", "create", "--name", resource_group, "--location", location, "-o", "none"])

    show_account = run(
        [
            "az",
            "storage",
            "account",
            "show",
            "--name",
            storage_account,
            "--resource-group",
            resource_group,
            "-o",
            "json",
        ],
        check=False,
    )
    if not show_account:
        run(
            [
                "az",
                "storage",
                "account",
                "create",
                "--name",
                storage_account,
                "--resource-group",
                resource_group,
                "--location",
                location,
                "--sku",
                "Standard_LRS",
                "-o",
                "none",
            ]
        )

    exists = run_json(
        [
            "az",
            "storage",
            "container",
            "exists",
            "--name",
            container,
            "--account-name",
            storage_account,
            "--auth-mode",
            "login",
            "-o",
            "json",
        ]
    )
    if not exists or not exists.get("exists"):
        run(
            [
                "az",
                "storage",
                "container",
                "create",
                "--name",
                container,
                "--account-name",
                storage_account,
                "--auth-mode",
                "login",
                "-o",
                "none",
            ]
        )


def ensure_app_registration(
    *,
    app_display_name: str,
    owner: str,
    repo: str,
    subscription_id: str,
) -> tuple[str, str]:
    echo("Ensuring Azure AD app registration and federated credentials exist...")
    apps = run_json(["az", "ad", "app", "list", "--display-name", app_display_name, "-o", "json"]) or []
    if apps:
        app_id = apps[0]["appId"]
    else:
        app_id = run(
            [
                "az",
                "ad",
                "app",
                "create",
                "--display-name",
                app_display_name,
                "--query",
                "appId",
                "-o",
                "tsv",
            ]
        )

    sp_show = run(["az", "ad", "sp", "show", "--id", app_id, "--query", "id", "-o", "tsv"], check=False)
    service_principal_object_id = sp_show or run(
        ["az", "ad", "sp", "create", "--id", app_id, "--query", "id", "-o", "tsv"]
    )

    creds = run_json(["az", "ad", "app", "federated-credential", "list", "--id", app_id, "-o", "json"]) or []
    existing_names = {item["name"] for item in creds}

    desired_credentials = [
        {
            "name": "github-main",
            "issuer": "https://token.actions.githubusercontent.com",
            "subject": f"repo:{owner}/{repo}:ref:refs/heads/main",
            "audiences": ["api://AzureADTokenExchange"],
        },
        {
            "name": "github-prs",
            "issuer": "https://token.actions.githubusercontent.com",
            "subject": f"repo:{owner}/{repo}:pull_request",
            "audiences": ["api://AzureADTokenExchange"],
        },
    ]

    for credential in desired_credentials:
        if credential["name"] not in existing_names:
            run(
                [
                    "az",
                    "ad",
                    "app",
                    "federated-credential",
                    "create",
                    "--id",
                    app_id,
                    "--parameters",
                    json.dumps(credential),
                ]
            )

    scope = f"/subscriptions/{subscription_id}"
    assignments = run_json(
        [
            "az",
            "role",
            "assignment",
            "list",
            "--assignee-object-id",
            service_principal_object_id,
            "--scope",
            scope,
            "-o",
            "json",
        ]
    ) or []
    if not any(item.get("roleDefinitionName") == "Contributor" for item in assignments):
        run(
            [
                "az",
                "role",
                "assignment",
                "create",
                "--assignee-object-id",
                service_principal_object_id,
                "--assignee-principal-type",
                "ServicePrincipal",
                "--role",
                "Contributor",
                "--scope",
                scope,
                "-o",
                "none",
            ]
        )

    return app_id, service_principal_object_id


def main() -> None:
    args = parse_args()
    ensure_command("az", "Install Azure CLI first.")
    if not args.skip_github_secrets:
        ensure_command("gh", "Install GitHub CLI first.")
        ensure_github_auth()

    account = ensure_azure_login()
    owner, repo = get_git_remote_repo()
    existing_config = load_config()
    local_env = load_local_env()

    tfstate_storage_account = (
        args.tfstate_storage_account
        or existing_config.get("tfstate_storage_account")
        or make_storage_account_name(repo, account["subscription_id"])
    )
    openai_api_key = get_openai_key(local_env, args.openai_api_key)
    db_password = args.db_password or existing_config.get("db_password") or generate_db_password()

    ensure_remote_state(
        resource_group=args.tfstate_resource_group,
        storage_account=tfstate_storage_account,
        container=args.tfstate_container,
        location=args.location,
    )

    app_id, sp_object_id = ensure_app_registration(
        app_display_name=args.app_display_name,
        owner=owner,
        repo=repo,
        subscription_id=account["subscription_id"],
    )

    if not args.skip_github_secrets:
        echo("Setting GitHub Actions secrets...")
        gh_secret_set(owner, repo, "AZURE_CLIENT_ID", app_id)
        gh_secret_set(owner, repo, "AZURE_TENANT_ID", account["tenant_id"])
        gh_secret_set(owner, repo, "AZURE_SUBSCRIPTION_ID", account["subscription_id"])
        gh_secret_set(owner, repo, "TF_BACKEND_STORAGE_ACCOUNT", tfstate_storage_account)
        gh_secret_set(owner, repo, "OPENAI_API_KEY", openai_api_key)
        gh_secret_set(owner, repo, "DB_PASSWORD", db_password)
        gh_secret_set(owner, repo, "ALERT_EMAIL", args.alert_email)

    config = {
        "repo_owner": owner,
        "repo_name": repo,
        "location": args.location,
        "tfstate_resource_group": args.tfstate_resource_group,
        "tfstate_storage_account": tfstate_storage_account,
        "tfstate_container": args.tfstate_container,
        "tfstate_key": args.tfstate_key,
        "azure_client_id": app_id,
        "azure_tenant_id": account["tenant_id"],
        "azure_subscription_id": account["subscription_id"],
        "service_principal_object_id": sp_object_id,
        "db_password": db_password,
        "alert_email": args.alert_email,
        "resource_group": resource_group_name(),
        "app_display_name": args.app_display_name,
    }
    save_config(config)

    echo("")
    echo("Bootstrap complete.")
    echo(f"Saved automation config to {CONFIG_PATH}")
    echo(f"GitHub repo detected: {owner}/{repo}")
    echo(f"Terraform state storage account: {tfstate_storage_account}")
    if args.skip_github_secrets:
        echo("GitHub secrets were skipped.")
    echo("")
    echo("Next: run `python scripts/deploy.py`")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        fail(str(exc))
