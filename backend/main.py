"""
Likitha's portfolio backend.

Serves the static frontend and exposes a small API — currently just a
contact-form endpoint, kept deliberately minimal. Add routes as needed
(e.g. GET /api/projects if projects move from hardcoded HTML to data-driven).
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import get_settings
from .email_service import send_contact_notification
from .models import ContactFormRequest, ContactFormResponse, HealthResponse
from .storage import init_db, save_submission

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("likitha_portfolio")

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Startup complete. environment=%s email_enabled=%s", settings.ENVIRONMENT, settings.email_enabled)
    yield
    logger.info("Shutting down.")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", environment=settings.ENVIRONMENT)


@app.post("/api/contact", response_model=ContactFormResponse)
@limiter.limit(settings.CONTACT_RATE_LIMIT)
async def submit_contact_form(request: Request, form: ContactFormRequest):
    # Honeypot: bots fill every field, real users never see or fill this one.
    if form.website:
        logger.info("Honeypot triggered — treating as spam, returning fake success.")
        return ContactFormResponse(success=True, message="Message sent.")

    email_sent = await send_contact_notification(form.name, form.email, form.message)

    try:
        save_submission(form.name, form.email, form.message, email_sent)
    except Exception:
        logger.exception("Failed to persist submission to database.")

    if email_sent:
        return ContactFormResponse(success=True, message="Thanks! Your message has been sent.")

    # Email failed, but the submission was still recorded — don't tell the
    # user something worse happened than actually did.
    return ContactFormResponse(
        success=True,
        message="Thanks! Your message has been received.",
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


# Serve the static frontend. Mounted last so it doesn't shadow /api routes.
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
