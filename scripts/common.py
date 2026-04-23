from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_DIR = ROOT / "terraform"
FRONTEND_DIR = ROOT / "frontend"
CONFIG_PATH = ROOT / ".deploy.auto.json"
DEFAULT_STATE_RG = "rg-tfstate"
DEFAULT_STATE_CONTAINER = "tfstate"
DEFAULT_STATE_KEY = "linkedin-gen.tfstate"
DEFAULT_LOCATION = "eastus"
DEFAULT_PROJECT = "linkedin-gen"
DEFAULT_ENVIRONMENT = "prod"


class CommandError(RuntimeError):
    pass


def echo(message: str) -> None:
    print(message, flush=True)


def fail(message: str) -> None:
    raise SystemExit(message)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = True,
) -> str:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    process = subprocess.run(
        command,
        cwd=str(cwd or ROOT),
        env=merged_env,
        text=True,
        capture_output=capture_output,
    )

    if check and process.returncode != 0:
        details = process.stderr.strip() or process.stdout.strip() or "Unknown command failure"
        raise CommandError(f"{' '.join(command)}\n{details}")

    return process.stdout.strip()


def run_json(command: list[str], *, cwd: Path | None = None) -> Any:
    output = run(command, cwd=cwd)
    if not output:
        return None
    return json.loads(output)


def ensure_command(command: str, hint: str) -> None:
    try:
        run([command, "--version"], check=True)
    except Exception as exc:  # noqa: BLE001
        fail(f"`{command}` is required. {hint}\n{exc}")


def ensure_azure_login() -> dict[str, str]:
    account = run_json(["az", "account", "show", "-o", "json"])
    if not account:
        fail("Azure CLI is not logged in. Run `az login` first.")
    return {
        "subscription_id": account["id"],
        "tenant_id": account["tenantId"],
    }


def ensure_github_auth() -> None:
    try:
        run(["gh", "auth", "status"], check=True)
    except Exception as exc:  # noqa: BLE001
        fail(
            "GitHub CLI is required and must be authenticated to set repo secrets.\n"
            "Run `gh auth login` first.\n"
            f"{exc}"
        )


def load_local_env() -> dict[str, str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")


def get_openai_key(local_env: dict[str, str], explicit: str | None = None) -> str:
    key = explicit or local_env.get("OPENAI_API_KEY") or local_env.get("OPEN_AI_KEY")
    if not key:
        fail(
            "OpenAI API key not found. Add `OPENAI_API_KEY=...` to `.env` "
            "(or pass `--openai-api-key`)."
        )
    return key


def generate_db_password(length: int = 32) -> str:
    return secrets.token_urlsafe(length)[:length]


def get_git_remote_repo() -> tuple[str, str]:
    remote = run(["git", "remote", "get-url", "origin"])

    if remote.startswith("git@github.com:"):
        path = remote.split(":", 1)[1]
    else:
        parsed = urlparse(remote)
        path = parsed.path.lstrip("/")

    if path.endswith(".git"):
        path = path[:-4]

    try:
        owner, repo = path.split("/", 1)
    except ValueError as exc:
        fail(f"Could not parse GitHub remote: {remote}\n{exc}")

    return owner, repo


def make_storage_account_name(repo: str, subscription_id: str) -> str:
    base = re.sub(r"[^a-z0-9]", "", repo.lower())
    suffix = re.sub(r"[^a-z0-9]", "", subscription_id.lower())[-6:]
    name = f"tf{base}{suffix}"
    return name[:24]


def gh_secret_set(owner: str, repo: str, name: str, value: str) -> None:
    run(["gh", "secret", "set", name, "--repo", f"{owner}/{repo}", "--body", value])


def gh_secret_delete(owner: str, repo: str, name: str) -> None:
    run(["gh", "secret", "delete", name, "--repo", f"{owner}/{repo}"], check=False)


def terraform_backend_args(config: dict[str, Any]) -> list[str]:
    return [
        f"-backend-config=resource_group_name={config['tfstate_resource_group']}",
        f"-backend-config=storage_account_name={config['tfstate_storage_account']}",
        f"-backend-config=container_name={config['tfstate_container']}",
        f"-backend-config=key={config['tfstate_key']}",
    ]


def terraform_var_args(
    *,
    openai_api_key: str,
    db_password: str,
    alert_email: str,
    backend_image_tag: str,
    allowed_origins: str,
) -> list[str]:
    return [
        f"-var=openai_api_key={openai_api_key}",
        f"-var=db_password={db_password}",
        f"-var=alert_email={alert_email}",
        f"-var=backend_image_tag={backend_image_tag}",
        f"-var=allowed_origins={allowed_origins}",
    ]


def terraform_output(name: str) -> str:
    return run(["terraform", "output", "-raw", name], cwd=TERRAFORM_DIR)


def http_get(url: str) -> int:
    import urllib.request

    with urllib.request.urlopen(url) as response:  # noqa: S310
        return response.status


def resource_group_name(
    project: str = DEFAULT_PROJECT,
    environment: str = DEFAULT_ENVIRONMENT,
) -> str:
    return f"rg-{project}-{environment}"


def print_next_step(step: str) -> None:
    echo("")
    echo(f"Next step: {step}")


def python_executable() -> str:
    return sys.executable
