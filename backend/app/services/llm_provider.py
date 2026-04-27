from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from app.config import settings

ProviderName = str

OPENAI_PROVIDER = "openai"
GOOGLE_PROVIDER = "google"
ZAI_PROVIDER = "zai"

PROVIDER_PRIORITY: list[ProviderName] = [OPENAI_PROVIDER, GOOGLE_PROVIDER, ZAI_PROVIDER]

OPENAI_MODELS = ["gpt-5.4", "gpt-5.4-mini"]
GOOGLE_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
ZAI_MODELS = ["glm-4.7", "glm-4.7-flash"]


@dataclass(frozen=True)
class ProviderConfig:
    name: ProviderName
    api_key: str
    base_url: str | None
    default_model: str
    models: list[str]

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


def _provider_configs() -> dict[ProviderName, ProviderConfig]:
    return {
        OPENAI_PROVIDER: ProviderConfig(
            name=OPENAI_PROVIDER,
            api_key=settings.OPENAI_API_KEY,
            base_url=getattr(settings, "OPENAI_BASE_URL", "") or None,
            default_model=getattr(settings, "OPENAI_MODEL", "gpt-5.4"),
            models=OPENAI_MODELS,
        ),
        GOOGLE_PROVIDER: ProviderConfig(
            name=GOOGLE_PROVIDER,
            api_key=getattr(settings, "GOOGLE_API_KEY", ""),
            base_url=getattr(settings, "GOOGLE_BASE_URL", "") or None,
            default_model=getattr(settings, "GOOGLE_MODEL", "gemini-2.5-flash"),
            models=GOOGLE_MODELS,
        ),
        ZAI_PROVIDER: ProviderConfig(
            name=ZAI_PROVIDER,
            api_key=getattr(settings, "ZAI_API_KEY", ""),
            base_url=getattr(settings, "ZAI_BASE_URL", "") or None,
            default_model=getattr(settings, "ZAI_MODEL", "glm-4.7-flash"),
            models=ZAI_MODELS,
        ),
    }


def get_available_provider_options() -> list[dict]:
    options: list[dict] = []
    for provider in PROVIDER_PRIORITY:
        cfg = _provider_configs()[provider]
        if not cfg.enabled:
            continue
        options.append(
            {
                "provider": cfg.name,
                "default_model": cfg.default_model,
                "models": cfg.models,
            }
        )
    return options


def resolve_provider_and_model(
    requested_provider: ProviderName | None = None,
    requested_model: str | None = None,
) -> tuple[ProviderName, str]:
    configs = _provider_configs()

    if requested_provider:
        cfg = configs.get(requested_provider)
        if cfg is None:
            raise ValueError(f"Unsupported provider: {requested_provider}")
        if not cfg.enabled:
            raise ValueError(f"Provider '{requested_provider}' is not configured on the server.")
        resolved_model = requested_model or cfg.default_model
        if resolved_model not in cfg.models:
            raise ValueError(
                f"Model '{resolved_model}' is not supported for provider '{requested_provider}'."
            )
        return cfg.name, resolved_model

    if requested_model:
        matching_providers: list[ProviderName] = []
        for provider in PROVIDER_PRIORITY:
            cfg = configs[provider]
            if cfg.enabled and requested_model in cfg.models:
                matching_providers.append(provider)
        if len(matching_providers) == 1:
            provider = matching_providers[0]
            return provider, requested_model
        if len(matching_providers) > 1:
            raise ValueError(
                f"Model '{requested_model}' is available on multiple providers. Specify llm_provider."
            )
        raise ValueError(
            f"Model '{requested_model}' is not available for any configured provider on this server."
        )

    for provider in PROVIDER_PRIORITY:
        cfg = configs[provider]
        if cfg.enabled:
            return cfg.name, cfg.default_model

    raise ValueError("No LLM provider is configured. Add at least one API key in the environment.")


def make_client(provider: ProviderName) -> OpenAI:
    cfg = _provider_configs().get(provider)
    if cfg is None:
        raise ValueError(f"Unsupported provider: {provider}")
    if not cfg.enabled:
        raise ValueError(f"Provider '{provider}' is not configured on the server.")

    kwargs: dict = {"api_key": cfg.api_key, "timeout": 30.0}
    if cfg.base_url:
        kwargs["base_url"] = cfg.base_url
    return OpenAI(**kwargs)

