#!/usr/bin/env python3
"""
Build a landscape PDF slide deck for the LinkedIn Generator capstone overview.
Run from repo root: python scripts/build_overview_pdf.py
"""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "docs" / "presentations"
IMAGES = REPO_ROOT / "docs" / "images"

# 16:9 slide in points (~10.67" x 6")
W, H = 960, 540

AUTHOR = "Jemine Mene-Ejegi"
# Raster images are downscaled before JPEG re-encode to keep the PDF small.
SLIDE_IMAGE_MAX_PX = 900
SLIDE_IMAGE_JPEG_QUALITY = 80


def register_fonts() -> tuple[str, str]:
    """Prefer Windows system fonts for a polished look; fall back to Helvetica."""
    candidates = [
        (
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "SegoeUI",
            "SegoeUI-Bold",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "DejaVuSans",
            "DejaVuSans-Bold",
        ),
    ]
    for regular, bold, rname, bname in candidates:
        rp, bp = Path(regular), Path(bold)
        if rp.is_file() and bp.is_file():
            pdfmetrics.registerFont(TTFont(rname, str(rp)))
            pdfmetrics.registerFont(TTFont(bname, str(bp)))
            return rname, bname
    return "Helvetica", "Helvetica-Bold"


BODY, TITLE_FONT = register_fonts()


def header_bar(c: canvas.Canvas) -> None:
    c.setFillColorRGB(0.12, 0.22, 0.42)
    c.rect(0, H - 56, W, 56, fill=1, stroke=0)
    c.setFillColorRGB(0.95, 0.96, 0.99)


def footer(c: canvas.Canvas, n: int, total: int) -> None:
    c.setFillColorRGB(0.55, 0.58, 0.65)
    c.setFont(BODY, 9)
    c.drawRightString(W - 28, 18, f"{n} / {total}")
    c.setFillColorRGB(0.35, 0.38, 0.45)
    c.drawString(28, 30, f"Author: {AUTHOR}")
    c.setFont(BODY, 8)
    c.setFillColorRGB(0.42, 0.45, 0.52)
    c.drawString(28, 14, "LinkedIn Post Generator — Azure · Terraform · GitHub Actions")


def slide_title(c: canvas.Canvas, title: str, subtitle: str | None = None) -> None:
    header_bar(c)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(TITLE_FONT, 26)
    c.drawString(36, H - 40, title[:80])
    if subtitle:
        c.setFont(BODY, 13)
        c.drawString(36, H - 72, subtitle[:120])


def slide_body_title(c: canvas.Canvas, title: str) -> None:
    header_bar(c)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(TITLE_FONT, 22)
    c.drawString(36, H - 38, title[:90])


def bullets(
    c: canvas.Canvas,
    items: list[str],
    left: float = 36,
    top: float | None = None,
    width: float | None = None,
    size: int = 13,
    leading: int = 18,
) -> None:
    if top is None:
        top = H - 100
    if width is None:
        width = W - 2 * left
    c.setFillColorRGB(0.15, 0.17, 0.22)
    c.setFont(BODY, size)
    y = top
    for line in items:
        wrapped = wrap_text(line, int(width / (size * 0.48)))
        for wline in wrapped:
            if y < 48:
                break
            c.drawString(left + 14, y, "•")
            c.drawString(left + 32, y, wline)
            y -= leading
        if y < 48:
            break


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        trial = (" ".join(cur + [w])) if cur else w
        if len(trial) <= max_chars:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _compressed_image_reader(path: Path) -> ImageReader | None:
    """Downscale and re-encode as JPEG to shrink embedded image bytes in the PDF."""
    if not path.is_file():
        return None
    try:
        with Image.open(path) as im:
            im = im.copy()
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA")
            im.thumbnail((SLIDE_IMAGE_MAX_PX, SLIDE_IMAGE_MAX_PX), Image.Resampling.LANCZOS)
            if im.mode == "RGBA":
                background = Image.new("RGB", im.size, (255, 255, 255))
                background.paste(im, mask=im.split()[3])
                rgb = background
            else:
                rgb = im.convert("RGB")
            buf = BytesIO()
            rgb.save(
                buf,
                format="JPEG",
                quality=SLIDE_IMAGE_JPEG_QUALITY,
                optimize=True,
                subsampling=2,
            )
            buf.seek(0)
            return ImageReader(buf)
    except (OSError, ValueError):
        return None


def draw_image_fit(
    c: canvas.Canvas,
    path: Path,
    x: float,
    y: float,
    max_w: float,
    max_h: float,
) -> bool:
    reader = _compressed_image_reader(path)
    if reader is None:
        return False
    try:
        iw, ih = reader.getSize()
        scale = min(max_w / iw, max_h / ih)
        w, h = iw * scale, ih * scale
        c.drawImage(reader, x, y, width=w, height=h, mask="auto")
        return True
    except Exception:
        return False


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "LinkedIn_Generator_Capstone_Overview.pdf"

    def s1(c: canvas.Canvas) -> None:
        c.setFillColorRGB(0.08, 0.12, 0.22)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColorRGB(0.92, 0.94, 1)
        c.setFont(TITLE_FONT, 34)
        c.drawString(48, H // 2 + 40, "LinkedIn Post Generator")
        c.setFont(BODY, 18)
        c.drawString(48, H // 2 - 8, "End-to-end capstone: app, Azure infra, CI/CD, observability")
        c.setFillColorRGB(0.65, 0.72, 0.9)
        c.setFont(BODY, 13)
        c.drawString(48, H // 2 - 52, "Next.js · FastAPI · PostgreSQL · OpenAI · Terraform · GitHub Actions")
        c.setFont(BODY, 12)
        c.setFillColorRGB(0.55, 0.62, 0.82)
        c.drawString(48, H // 2 - 88, f"Author: {AUTHOR}")

    def s2(c: canvas.Canvas) -> None:
        slide_body_title(c, "What this system is")
        bullets(
            c,
            [
                "Full-stack product that drafts LinkedIn posts from user input, optional article URLs, and tone/audience settings.",
                "Optional writing-style learning: user supplies sample posts; backend builds a compact profile via OpenAI.",
                "History of generations stored in PostgreSQL; users can review and delete past items.",
                "Production deployment on Azure with infrastructure-as-code (Terraform) and one GitHub Actions pipeline.",
            ],
        )

    def s3(c: canvas.Canvas) -> None:
        slide_body_title(c, "User-facing capabilities")
        bullets(
            c,
            [
                "Generate: topic, audience, tone, optional URL (SSR-safe scrape), style mode when a profile exists.",
                "Style import: paste ≥3 prior posts (--- separator); profile drives faithful / improve / off modes.",
                "History: paginated list and delete; API mirrors these operations for the static frontend.",
                "Optional Clerk sign-in in the UI when NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is set at build time.",
            ],
        )

    def s4(c: canvas.Canvas) -> None:
        slide_body_title(c, "High-level architecture")
        img_y = 72
        img_h = H - 100 - img_y
        ok = draw_image_fit(c, IMAGES / "architecture-overview.png", 40, img_y, W - 80, img_h)
        if not ok:
            bullets(
                c,
                [
                    "Browser → Azure Static Web Apps (Next.js static export).",
                    "Browser → Azure Container Apps (FastAPI) for /api/*.",
                    "Backend → PostgreSQL Flexible Server + OpenAI API.",
                    "Optional: Azure Front Door + WAF in front of both (Terraform flag).",
                ],
                top=H - 95,
            )

    def s5(c: canvas.Canvas) -> None:
        slide_body_title(c, "Technology stack")
        bullets(
            c,
            [
                "Frontend: Next.js (static export), Application Insights JS for browser telemetry, optional Clerk.",
                "Backend: FastAPI, SQLAlchemy, OpenAI SDK, httpx; OpenTelemetry via azure-monitor-opentelemetry when configured.",
                "Data: Azure Database for PostgreSQL Flexible Server (primary store for posts + style profile).",
                "Images: Azure Container Registry; runtime: Azure Container Apps with HTTP scaling rules.",
            ],
        )

    def s6(c: canvas.Canvas) -> None:
        slide_body_title(c, "Azure resources (Terraform)")
        bullets(
            c,
            [
                "Resource group + tags (project, environment, managed_by = terraform).",
                "ACR, Container Apps Environment + single backend app (secrets: DATABASE_URL, OPENAI_API_KEY).",
                "PostgreSQL Flexible Server + database linkedin_gen.",
                "Static Web App (Free tier) for exported frontend; Log Analytics + workspace-based Application Insights.",
                "Diagnostic settings: Container App, Static Web App, Postgres → Log Analytics.",
                "Portal dashboard (summary) + Application Insights workbook (KQL charts); metric alerts if ALERT_EMAIL set.",
            ],
            size=12,
            leading=16,
        )

    def s7(c: canvas.Canvas) -> None:
        slide_body_title(c, "CI/CD pipeline")
        img_y = 78
        img_h = H - 108 - img_y
        ok = draw_image_fit(c, IMAGES / "cicd-pipeline.png", 36, img_y, W - 72, img_h)
        if not ok:
            bullets(
                c,
                [
                    "Jobs: codescan → test (Postgres service + pytest) → build → plan → deploy (main only).",
                    "Auth: OIDC / Workload Identity Federation — no long-lived Azure passwords in YAML.",
                    "Deploy: ACR push, terraform apply, smoke tests, frontend build with real NEXT_PUBLIC_*, SWA upload, CORS tightened to frontend URL.",
                ],
                top=H - 95,
            )

    def s7b(c: canvas.Canvas) -> None:
        slide_body_title(c, "Bootstrap & automation")
        bullets(
            c,
            [
                "scripts/bootstrap.py: remote Terraform state (storage account + container), Azure AD app + federated credential for GitHub OIDC.",
                "Grants subscription/RG roles needed for CI; writes .deploy.auto.json and sets GitHub repo secrets (Azure IDs, OpenAI, DB password, TF backend, optional ALERT_EMAIL).",
                "scripts/destroy.py: terraform destroy; --include-bootstrap removes GitHub secrets and state RG (requires gh auth).",
            ],
            size=12,
            leading=16,
        )

    def s8(c: canvas.Canvas) -> None:
        slide_body_title(c, "Security & configuration")
        bullets(
            c,
            [
                "CORS: permissive during apply; pipeline final step sets ALLOWED_ORIGINS to deployed Static Web App URL.",
                "TrustedHostMiddleware on API; scraper blocks private IPs / SSRF patterns.",
                "Security headers via staticwebapp.config.json on the exported site.",
                "Secrets: OpenAI + DB password in Container App secrets and GitHub Actions secrets; bootstrap script wires OIDC + remote state.",
            ],
        )

    def s9(c: canvas.Canvas) -> None:
        slide_body_title(c, "Observability — data flow")
        img_y = 78
        img_h = H - 108 - img_y
        ok = draw_image_fit(c, IMAGES / "observability-data-flow.png", 36, img_y, W - 72, img_h)
        if not ok:
            bullets(
                c,
                [
                    "Backend: APPLICATIONINSIGHTS_CONNECTION_STRING → configure_azure_monitor; spans + custom metrics.",
                    "Frontend: NEXT_PUBLIC_APPLICATIONINSIGHTS_CONNECTION_STRING → page views + custom events (AppEvents).",
                    "Platform: diagnostics send Azure metrics/logs into Log Analytics for cross-resource queries.",
                ],
                top=H - 95,
            )

    def s10(c: canvas.Canvas) -> None:
        slide_body_title(c, "Telemetry detail (concise)")
        bullets(
            c,
            [
                "Custom metrics (examples): linkedin_generator.generation.*, .style_import.*, .openai.*, .scrape.* — dimensions: tone, style_mode, source_type.",
                "Frontend events: e.g. frontend_generate_submitted / succeeded / failed for funnel views in Log Analytics.",
                "Ops workbook: KQL on AppRequests, AppMetrics, AppEvents, AzureMetrics (API volume, latency, failures, CPU/memory).",
                "Portal dashboard: lightweight Markdown summary linking workbook, App Insights, alerts, and resource names.",
            ],
            size=11,
            leading=15,
        )

    def s11(c: canvas.Canvas) -> None:
        slide_body_title(c, "API surface (backend)")
        bullets(
            c,
            [
                "POST /api/generate — generate and persist a post.",
                "GET /api/history — paginated history; DELETE /api/history/{id}.",
                "POST /api/style/import — build profile; GET /api/style/profile — fetch profile.",
                "GET /health/live, /health/ready — liveness and DB readiness (used by probes and CI smoke tests).",
            ],
        )

    def s12(c: canvas.Canvas) -> None:
        slide_body_title(c, "Local development & quality")
        bullets(
            c,
            [
                "docker compose for Postgres + API; frontend: npm run dev against NEXT_PUBLIC_API_URL.",
                "Backend tests: pytest with PYTHONPATH=backend; CI uses Postgres 16 service container.",
                "Terraform: fmt -check, validate, remote state; destroy.py for teardown (optional --include-bootstrap).",
            ],
        )

    def s13(c: canvas.Canvas) -> None:
        slide_body_title(c, "Key takeaways")
        bullets(
            c,
            [
                "Single pipeline delivers app + infra: build, push, apply, configure static site, validate health.",
                "Observable by design: workspace-based App Insights, custom OTel metrics, browser events, workbook + optional alerts.",
                "Production-minded defaults: secrets isolation, CORS tightening, trusted hosts, SSRF-hardened scraping.",
                "Repository: README documents outputs, bootstrap, troubleshooting, and diagram assets used in this deck.",
            ],
        )

    def s14(c: canvas.Canvas) -> None:
        c.setFillColorRGB(0.08, 0.12, 0.22)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColorRGB(0.92, 0.94, 1)
        c.setFont(TITLE_FONT, 28)
        c.drawString(48, H // 2 + 20, "Thank you")
        c.setFont(BODY, 15)
        c.drawString(48, H // 2 - 28, "Questions? See README.md in the repo for deep links, Terraform outputs, and ops runbooks.")
        c.setFont(BODY, 12)
        c.setFillColorRGB(0.55, 0.62, 0.82)
        c.drawString(48, H // 2 - 62, f"— {AUTHOR}")

    deck = [s1, s2, s3, s4, s5, s6, s7, s7b, s8, s9, s10, s11, s12, s13, s14]
    c = canvas.Canvas(str(out_path), pagesize=(W, H), pageCompression=1)
    c.setTitle("LinkedIn Post Generator — Capstone Overview")
    c.setAuthor(AUTHOR)
    total = len(deck)
    for i, draw in enumerate(deck, start=1):
        draw(c)
        footer(c, i, total)
        c.showPage()
    c.save()
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
