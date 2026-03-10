"""Imbryk Ingestion API — prompts, payments, and editions."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import sentry_sdk
import sentry_sdk.integrations.logging
import stripe
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from ingestion_api.categoriser import CategoriserStrategy, StubCategoriser
from ingestion_api.config import (
    CORS_ALLOWED_ORIGINS,
    QUOTE_CLEANUP_INTERVAL_SECONDS,
    QUOTE_EXPIRY_SECONDS,
    RATE_LIMIT_QUOTE,
    SENTRY_DSN,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    VERTEX_LOCATION,
    VERTEX_PROJECT,
    _log_level_int,
)

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        send_default_pii=False,
        integrations=[
            sentry_sdk.integrations.logging.LoggingIntegration(
                level=_log_level_int,  # Capture logs at configured level or higher
                event_level=logging.ERROR,  # Send only ERROR logs as Sentry events
            ),
        ],
    )
    logging.captureWarnings(True)  # Route warnings.warn() through logging so Sentry sees them

from ingestion_api.database import SessionLocal, get_db
from ingestion_api.models import (
    CategorisedPrompt,
    Edition,
    EditionArticle,
    PaymentRef,
    Prompt,
)
from ingestion_api.pricing import calculate_cost, calculate_cost_cents
from ingestion_api.schemas import (
    CheckoutSessionResponse,
    CreateCheckoutSessionRequest,
    EditionSummary,
    HealthResponse,
    QuoteRequest,
    QuoteResponse,
    RoutingDetail,
)
from ingestion_api.stripe_client import configure_stripe, verify_webhook
from ingestion_api.taxonomy import route_prompt

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Imbryk Ingestion API", version="0.2.0")
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.on_event("startup")
async def startup_event():
    """Log API startup for visibility in Cloud Logging & Sentry."""
    global _cleanup_task
    _cleanup_task = asyncio.create_task(_quote_cleanup_loop())
    configure_stripe()
    if not STRIPE_SECRET_KEY:
        logger.error(
            "STRIPE_SECRET_KEY is not set — checkout session creation will fail. "
            "Set the env var (or Secret Manager secret) before accepting payments."
        )
    if not STRIPE_WEBHOOK_SECRET:
        logger.warning(
            "STRIPE_WEBHOOK_SECRET is not set — incoming Stripe webhooks will fail signature verification."
        )
    if VERTEX_PROJECT:
        from ingestion_api.categoriser import GeminiFlashCategoriser

        set_categoriser(GeminiFlashCategoriser(project=VERTEX_PROJECT, location=VERTEX_LOCATION))
        logger.info("Using GeminiFlashCategoriser (project=%s)", VERTEX_PROJECT)
    else:
        logger.warning(
            "VERTEX_PROJECT not set — using StubCategoriser; all prompts will be classified as 'geopolitics'"
        )
    logger.info(
        "Imbryk Ingestion API started",
        extra={"allowed_origins": CORS_ALLOWED_ORIGINS},
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cancel background tasks on graceful shutdown."""
    if _cleanup_task is not None:
        _cleanup_task.cancel()


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning("Rate limit exceeded for %s", request.client)
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected errors — logs to console & Sentry."""
    logger.exception("Unhandled exception in %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# --- Quote expiry cleanup ---


def purge_expired_quotes(db, cutoff: datetime) -> int:
    """Delete 'quoted' prompts older than *cutoff* and their category rows.

    Returns the number of prompts purged.  Safe to call from tests.
    """
    expired_ids = [
        p.id
        for p in db.query(Prompt).filter(
            Prompt.status == "quoted",
            Prompt.created_at < cutoff,
        ).all()
    ]
    if expired_ids:
        db.query(CategorisedPrompt).filter(
            CategorisedPrompt.prompt_id.in_(expired_ids)
        ).delete(synchronize_session=False)
        db.query(Prompt).filter(Prompt.id.in_(expired_ids)).delete(
            synchronize_session=False
        )
        db.commit()
        logger.info("Purged %d expired quoted prompt(s)", len(expired_ids))
    return len(expired_ids)


async def _quote_cleanup_loop() -> None:
    """Background asyncio task: purge orphaned quotes on a fixed interval."""
    while True:
        await asyncio.sleep(QUOTE_CLEANUP_INTERVAL_SECONDS)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=QUOTE_EXPIRY_SECONDS)
        db = SessionLocal()
        try:
            purge_expired_quotes(db, cutoff)
        except Exception:
            logger.exception("Error during expired quote cleanup")
            db.rollback()
        finally:
            db.close()


_cleanup_task: asyncio.Task | None = None


# --- Dependency: categoriser ---

_categoriser: CategoriserStrategy = StubCategoriser()


def set_categoriser(categoriser: CategoriserStrategy) -> None:
    """Replace the active categoriser (used by tests and app startup)."""
    global _categoriser
    _categoriser = categoriser


def get_categoriser() -> CategoriserStrategy:
    return _categoriser


# --- Endpoints ---


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/prompts/quote", response_model=QuoteResponse)
@limiter.limit(RATE_LIMIT_QUOTE)
async def quote(
    request: Request,
    body: QuoteRequest,
    db: Session = Depends(get_db),
    categoriser: CategoriserStrategy = Depends(get_categoriser),
):
    """Categorise, price, and persist a quote — locks in the amount server-side."""
    categories = categoriser.categorise(body.prompt)
    routing = route_prompt(categories)
    cost = calculate_cost(len(routing))

    # Persist the quote so the amount is locked server-side.
    prompt = Prompt(
        text=body.prompt,
        amount=cost,
        status="quoted",
    )
    db.add(prompt)
    db.flush()

    for cat_id in categories:
        db.add(CategorisedPrompt(prompt_id=prompt.id, category_id=cat_id))

    db.commit()

    return QuoteResponse(
        quote_id=prompt.id,
        categories=categories,
        newspapers_reached=len(routing),
        estimated_cost=cost,
        newspapers=[
            RoutingDetail(
                newspaper_id=r.newspaper_id,
                matched_categories=r.matched_categories,
            )
            for r in routing
        ],
    )


@app.post("/payments/create-checkout-session", response_model=CheckoutSessionResponse)
@limiter.limit(RATE_LIMIT_QUOTE)
async def create_checkout_session(
    request: Request,
    body: CreateCheckoutSessionRequest,
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session from the server-side quote.

    The base amount is read from the stored quote — never from the client — so
    the user cannot pay less than the classified price.  The
    ``weight_multiplier`` (validated by Pydantic to be an integer in [1, 100])
    is applied server-side to produce the final charged amount.

    Returns a ``checkout_url`` that the frontend redirects to.  Payment
    confirmation happens asynchronously via the ``stripe-webhook`` endpoint
    when Stripe sends the ``checkout.session.completed`` event.
    """
    prompt = db.query(Prompt).filter_by(id=body.quote_id).first()
    if prompt is None:
        return JSONResponse(status_code=404, content={"detail": "Quote not found"})

    if prompt.status != "quoted":
        return JSONResponse(
            status_code=409,
            content={"detail": f"Quote already processed (status={prompt.status})"},
        )

    # Base amount comes from the DB — tamper-proof.
    base_amount = prompt.amount
    if base_amount is None or base_amount <= 0:
        return JSONResponse(status_code=400, content={"detail": "Invalid quote amount"})

    # Apply weight multiplier (already validated by Pydantic: int, 1–100).
    multiplier = body.weight_multiplier
    amount_cents = calculate_cost_cents(
        int(round(base_amount)),  # base_amount is newspapers_reached * BASE_PRICE ($1)
        weight_multiplier=1,
    ) * multiplier

    # Mark the multiplier on the prompt now so we don't lose it.
    prompt.weight_multiplier = multiplier
    db.commit()

    # Determine success/cancel URLs from the Referer or use the configured
    # CORS origin as a fallback (first allowed origin is the app).
    origin = CORS_ALLOWED_ORIGINS[0] if CORS_ALLOWED_ORIGINS else "http://localhost:4200"

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": "Imbryk Prompt",
                        },
                    },
                    "quantity": 1,
                },
            ],
            metadata={
                "quote_id": body.quote_id,
                "weight_multiplier": str(multiplier),
            },
            success_url=f"{origin}?session_id={{CHECKOUT_SESSION_ID}}&status=success",
            cancel_url=f"{origin}?status=cancelled",
        )
    except stripe.AuthenticationError:
        logger.error(
            "Stripe authentication failed — STRIPE_SECRET_KEY is missing or invalid"
        )
        return JSONResponse(
            status_code=502,
            content={"detail": "Payment service unavailable — configuration error"},
        )
    except stripe.StripeError as e:
        logger.warning("Stripe checkout session creation failed: %s", e)
        return JSONResponse(status_code=502, content={"detail": "Payment service error"})

    return CheckoutSessionResponse(checkout_url=session.url)


@app.post("/payments/stripe-webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook notifications.

    Listens for:
    * ``checkout.session.completed`` — marks prompt as accepted and creates
      a ``PaymentRef``.
    * ``charge.dispute.created`` — flags the payment as disputed.
    * ``charge.dispute.closed`` — depending on ``status``, either restores
      the payment or reverts the prompt.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook(payload, sig_header)
    except Exception:
        logger.warning("Stripe webhook signature verification failed")
        return JSONResponse(status_code=400, content={"detail": "Invalid signature"})

    event_type = event.get("type", "")
    logger.info("Stripe webhook received: type=%s", event_type)

    # --- Checkout completed ---
    if event_type == "checkout.session.completed":
        session_data = event["data"]["object"]
        metadata = session_data.get("metadata", {})
        quote_id = metadata.get("quote_id")
        multiplier = int(metadata.get("weight_multiplier", "1"))
        payment_intent_id = session_data.get("payment_intent", "")
        amount_total = session_data.get("amount_total", 0)  # cents

        if not quote_id:
            logger.warning("checkout.session.completed missing quote_id in metadata")
            return JSONResponse(status_code=200, content={"detail": "ignored"})

        prompt = db.query(Prompt).filter_by(id=quote_id).first()
        if prompt is None:
            logger.warning("checkout.session.completed for unknown quote %s", quote_id)
            return JSONResponse(status_code=200, content={"detail": "unknown quote"})

        # Idempotency: skip if already processed
        if prompt.status != "quoted":
            logger.info("Quote %s already processed (status=%s)", quote_id, prompt.status)
            return JSONResponse(status_code=200, content={"detail": "already processed"})

        amount_dollars = amount_total / 100

        payment = PaymentRef(
            provider_transaction_id=payment_intent_id,
            amount=amount_dollars,
            currency="USD",
            status="settled",
        )
        db.add(payment)

        prompt.payment_ref = payment_intent_id
        prompt.status = "accepted"
        prompt.amount = amount_dollars
        prompt.weight_multiplier = multiplier
        db.commit()

        logger.info(
            "Payment completed for quote %s: pi=%s amount=$%.2f",
            quote_id,
            payment_intent_id,
            amount_dollars,
        )
        return JSONResponse(status_code=200, content={"detail": "ok"})

    # --- Dispute events ---
    if event_type == "charge.dispute.created":
        dispute = event["data"]["object"]
        payment_intent_id = dispute.get("payment_intent", "")

        if not payment_intent_id:
            return JSONResponse(status_code=200, content={"detail": "ignored"})

        payment = (
            db.query(PaymentRef)
            .filter_by(provider_transaction_id=payment_intent_id)
            .first()
        )
        if payment is None:
            logger.warning("Dispute for unknown payment intent %s", payment_intent_id)
            return JSONResponse(status_code=200, content={"detail": "unknown transaction"})

        payment.status = "disputed"
        db.commit()
        logger.info("Dispute opened for payment intent %s", payment_intent_id)
        return JSONResponse(status_code=200, content={"detail": "ok"})

    if event_type == "charge.dispute.closed":
        dispute = event["data"]["object"]
        payment_intent_id = dispute.get("payment_intent", "")
        dispute_status = dispute.get("status", "")

        if not payment_intent_id:
            return JSONResponse(status_code=200, content={"detail": "ignored"})

        payment = (
            db.query(PaymentRef)
            .filter_by(provider_transaction_id=payment_intent_id)
            .first()
        )
        if payment is None:
            logger.warning("Dispute close for unknown payment intent %s", payment_intent_id)
            return JSONResponse(status_code=200, content={"detail": "unknown transaction"})

        if dispute_status == "won":
            payment.status = "settled"
            logger.info("Dispute won for payment intent %s", payment_intent_id)
        else:
            # lost or warning_closed
            payment.status = "disputed_lost"
            prompt = db.query(Prompt).filter_by(payment_ref=payment_intent_id).first()
            if prompt is not None:
                prompt.status = "quoted"
                prompt.payment_ref = None
            logger.info("Dispute lost for payment intent %s — prompt reverted", payment_intent_id)

        db.commit()
        return JSONResponse(status_code=200, content={"detail": "ok"})

    # --- Unknown / unhandled event ---
    logger.info("Stripe webhook ignored: type=%s", event_type)
    return JSONResponse(status_code=200, content={"detail": "ignored"})


@app.get("/editions", response_model=list[EditionSummary])
async def list_editions(db: Session = Depends(get_db)):
    """List available editions. """
    editions = db.query(Edition).order_by(Edition.date.desc()).all()
    results = []
    for edition in editions:
        article_count = (
            db.query(EditionArticle)
            .filter(EditionArticle.edition_id == edition.id)
            .count()
        )
        results.append(
            EditionSummary(
                edition_id=edition.id,
                date=edition.date,
                newspaper_count=article_count,
            )
        )
    return results
