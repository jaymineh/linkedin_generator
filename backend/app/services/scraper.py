import httpx
import structlog

logger = structlog.get_logger()


async def scrape_url(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            return response.text[:8000]
    except Exception as exc:
        logger.warning("scrape_failed", url=url, error=str(exc))
        return None
