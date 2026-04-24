from __future__ import annotations

from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("linkedin_generator.telemetry")
meter = metrics.get_meter("linkedin_generator.telemetry")

generation_requests = meter.create_counter(
    "linkedin_generator.generation.requests",
    unit="1",
    description="Number of generation requests received by the API.",
)
generation_failures = meter.create_counter(
    "linkedin_generator.generation.failures",
    unit="1",
    description="Number of generation requests that failed.",
)
generation_duration = meter.create_histogram(
    "linkedin_generator.generation.duration_ms",
    unit="ms",
    description="Time spent serving generation requests.",
)
posts_generated = meter.create_counter(
    "linkedin_generator.generation.posts_generated",
    unit="1",
    description="Number of LinkedIn posts generated.",
)
generated_word_count = meter.create_histogram(
    "linkedin_generator.generation.output_words",
    unit="words",
    description="Word count of generated LinkedIn posts.",
)
generated_hashtag_count = meter.create_histogram(
    "linkedin_generator.generation.hashtag_count",
    unit="1",
    description="Hashtag count in generated LinkedIn posts.",
)

style_import_requests = meter.create_counter(
    "linkedin_generator.style_import.requests",
    unit="1",
    description="Number of style import requests received by the API.",
)
style_import_failures = meter.create_counter(
    "linkedin_generator.style_import.failures",
    unit="1",
    description="Number of style import requests that failed.",
)
style_import_duration = meter.create_histogram(
    "linkedin_generator.style_import.duration_ms",
    unit="ms",
    description="Time spent building a writing style profile.",
)
style_samples_imported = meter.create_counter(
    "linkedin_generator.style_import.samples_imported",
    unit="1",
    description="Number of historical posts imported into a style profile.",
)

openai_requests = meter.create_counter(
    "linkedin_generator.openai.requests",
    unit="1",
    description="Number of OpenAI requests made by the backend.",
)
openai_failures = meter.create_counter(
    "linkedin_generator.openai.failures",
    unit="1",
    description="Number of failed OpenAI requests.",
)
openai_duration = meter.create_histogram(
    "linkedin_generator.openai.duration_ms",
    unit="ms",
    description="Latency of OpenAI requests.",
)
openai_prompt_tokens = meter.create_histogram(
    "linkedin_generator.openai.prompt_tokens",
    unit="1",
    description="Prompt tokens consumed by OpenAI requests.",
)
openai_completion_tokens = meter.create_histogram(
    "linkedin_generator.openai.completion_tokens",
    unit="1",
    description="Completion tokens returned by OpenAI requests.",
)

scrape_requests = meter.create_counter(
    "linkedin_generator.scrape.requests",
    unit="1",
    description="Number of article scrape attempts.",
)
scrape_failures = meter.create_counter(
    "linkedin_generator.scrape.failures",
    unit="1",
    description="Number of article scrape attempts that failed or were rejected.",
)
scrape_duration = meter.create_histogram(
    "linkedin_generator.scrape.duration_ms",
    unit="ms",
    description="Latency of article scraping attempts.",
)


def _normalize_value(value: Any) -> str | int | float | bool:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return value
    return str(value)


def _normalize_attributes(attributes: dict[str, Any]) -> dict[str, str | int | float | bool]:
    normalized: dict[str, str | int | float | bool] = {}
    for key, value in attributes.items():
        if value is None:
            continue
        normalized[key] = _normalize_value(value)
    return normalized


def _annotate_current_span(attributes: dict[str, Any], *, event_name: str | None = None) -> None:
    span = trace.get_current_span()
    if not span or not span.is_recording():
        return

    normalized = _normalize_attributes(attributes)
    for key, value in normalized.items():
        span.set_attribute(f"app.{key}", value)

    if event_name:
        span.add_event(event_name, normalized)


def _mark_span_success() -> None:
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_status(Status(StatusCode.OK))


def _mark_span_error(error_type: str) -> None:
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_status(Status(StatusCode.ERROR, error_type))
        span.set_attribute("app.error_type", error_type)


def sample_bucket(sample_count: int) -> str:
    if sample_count <= 5:
        return "3-5"
    if sample_count <= 10:
        return "6-10"
    return "11+"


def record_generation_started(
    *,
    audience: str,
    tone: str,
    style_mode: str,
    source_type: str,
    style_profile_available: bool,
) -> None:
    attributes = _normalize_attributes(
        {
            "audience": audience,
            "tone": tone,
            "style_mode": style_mode,
            "source_type": source_type,
            "style_profile_available": style_profile_available,
        }
    )
    generation_requests.add(1, attributes)
    _annotate_current_span(attributes, event_name="generation.started")


def record_generation_completed(
    *,
    audience: str,
    tone: str,
    style_mode: str,
    source_type: str,
    style_profile_available: bool,
    scrape_succeeded: bool,
    post_count: int,
    word_count: int,
    hashtag_count: int,
    duration_ms: float,
) -> None:
    attributes = _normalize_attributes(
        {
            "audience": audience,
            "tone": tone,
            "style_mode": style_mode,
            "source_type": source_type,
            "style_profile_available": style_profile_available,
            "scrape_succeeded": scrape_succeeded,
            "result": "success",
        }
    )
    generation_duration.record(duration_ms, attributes)
    posts_generated.add(post_count, attributes)
    generated_word_count.record(word_count, attributes)
    generated_hashtag_count.record(hashtag_count, attributes)
    _annotate_current_span(
        {
            **attributes,
            "post_count": post_count,
            "word_count": word_count,
            "hashtag_count": hashtag_count,
            "duration_ms": round(duration_ms, 2),
        },
        event_name="generation.completed",
    )
    _mark_span_success()


def record_generation_failed(
    *,
    audience: str,
    tone: str,
    style_mode: str,
    source_type: str,
    style_profile_available: bool,
    scrape_succeeded: bool,
    error_type: str,
    duration_ms: float,
) -> None:
    attributes = _normalize_attributes(
        {
            "audience": audience,
            "tone": tone,
            "style_mode": style_mode,
            "source_type": source_type,
            "style_profile_available": style_profile_available,
            "scrape_succeeded": scrape_succeeded,
            "error_type": error_type,
            "result": "failure",
        }
    )
    generation_failures.add(1, attributes)
    generation_duration.record(duration_ms, attributes)
    _annotate_current_span({**attributes, "duration_ms": round(duration_ms, 2)}, event_name="generation.failed")
    _mark_span_error(error_type)


def record_style_import_started(*, sample_count: int) -> None:
    attributes = _normalize_attributes(
        {
            "sample_count": sample_count,
            "sample_bucket": sample_bucket(sample_count),
        }
    )
    style_import_requests.add(1, attributes)
    _annotate_current_span(attributes, event_name="style_import.started")


def record_style_import_completed(*, sample_count: int, duration_ms: float) -> None:
    attributes = _normalize_attributes(
        {
            "sample_count": sample_count,
            "sample_bucket": sample_bucket(sample_count),
            "result": "success",
        }
    )
    style_import_duration.record(duration_ms, attributes)
    style_samples_imported.add(sample_count, attributes)
    _annotate_current_span(
        {**attributes, "duration_ms": round(duration_ms, 2)},
        event_name="style_import.completed",
    )
    _mark_span_success()


def record_style_import_failed(*, sample_count: int, error_type: str, duration_ms: float) -> None:
    attributes = _normalize_attributes(
        {
            "sample_count": sample_count,
            "sample_bucket": sample_bucket(sample_count),
            "error_type": error_type,
            "result": "failure",
        }
    )
    style_import_failures.add(1, attributes)
    style_import_duration.record(duration_ms, attributes)
    _annotate_current_span(
        {**attributes, "duration_ms": round(duration_ms, 2)},
        event_name="style_import.failed",
    )
    _mark_span_error(error_type)


def record_openai_completed(
    *,
    operation: str,
    audience: str,
    tone: str,
    style_mode: str,
    success: bool,
    duration_ms: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    error_type: str | None = None,
) -> None:
    attributes = _normalize_attributes(
        {
            "operation": operation,
            "audience": audience,
            "tone": tone,
            "style_mode": style_mode,
            "success": success,
            "error_type": error_type,
        }
    )
    openai_requests.add(1, attributes)
    openai_duration.record(duration_ms, attributes)
    if prompt_tokens:
        openai_prompt_tokens.record(prompt_tokens, attributes)
    if completion_tokens:
        openai_completion_tokens.record(completion_tokens, attributes)
    if not success:
        openai_failures.add(1, attributes)

    _annotate_current_span(
        {
            **attributes,
            "duration_ms": round(duration_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
        event_name=f"openai.{operation}",
    )

    if success:
        _mark_span_success()
    elif error_type:
        _mark_span_error(error_type)


def record_scrape_completed(*, attempted: bool, success: bool, outcome: str, duration_ms: float) -> None:
    attributes = _normalize_attributes(
        {
            "attempted": attempted,
            "success": success,
            "outcome": outcome,
        }
    )
    scrape_requests.add(1, attributes)
    scrape_duration.record(duration_ms, attributes)
    if not success:
        scrape_failures.add(1, attributes)

    _annotate_current_span(
        {**attributes, "duration_ms": round(duration_ms, 2)},
        event_name="scrape.completed",
    )
    if success:
        _mark_span_success()
    else:
        _mark_span_error(outcome)
