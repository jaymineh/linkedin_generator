import ipaddress
import time
from urllib.parse import urlparse

import httpx
import structlog

from app import telemetry

logger = structlog.get_logger()


def _is_public_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return False

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return True

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


async def scrape_url(url: str) -> str | None:
    started = time.perf_counter()
    with telemetry.tracer.start_as_current_span("scrape_reference_article"):
        if not _is_public_http_url(url):
            logger.warning("scrape_rejected_non_public_url", url=url)
            telemetry.record_scrape_completed(
                attempted=True,
                success=False,
                outcome="rejected_non_public_url",
                duration_ms=(time.perf_counter() - started) * 1000,
            )
            return None

        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                telemetry.record_scrape_completed(
                    attempted=True,
                    success=True,
                    outcome="success",
                    duration_ms=(time.perf_counter() - started) * 1000,
                )
                return response.text[:8000]
        except Exception as exc:
            logger.warning("scrape_failed", url=url, error=str(exc))
            telemetry.record_scrape_completed(
                attempted=True,
                success=False,
                outcome=type(exc).__name__,
                duration_ms=(time.perf_counter() - started) * 1000,
            )
            return None
