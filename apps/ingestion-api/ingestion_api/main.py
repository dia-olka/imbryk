"""Imbryk Ingestion API — prompts, payments, and editions."""

import logging

import sentry_sdk
import sentry_sdk.integrations.logging
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
    RATE_LIMIT_QUOTE,
    SENTRY_DSN,
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
from ingestion_api.braintree_client import get_gateway
from ingestion_api.database import get_db
from ingestion_api.models import (
    CategorisedPrompt,
    Edition,
    EditionArticle,
    PaymentRef,
    Prompt,
)
from ingestion_api.pricing import calculate_cost
from ingestion_api.schemas import (
    ClientTokenResponse,
    CreateTransactionRequest,
    EditionSummary,
    HealthResponse,
    PromptAcceptedResponse,
    QuoteRequest,
    QuoteResponse,
    RoutingDetail,
    WebhookPayload,
)
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


@app.post("/payments/create-transaction", response_model=PromptAcceptedResponse)
@limiter.limit(RATE_LIMIT_QUOTE)
async def create_transaction(
    request: Request,
    body: CreateTransactionRequest,
    db: Session = Depends(get_db),
):
    """Create a Braintree transaction from the server-side quote.

    The base amount is read from the stored quote — never from the client — so
    the user cannot pay less than the classified price.  The
    ``weight_multiplier`` (validated by Pydantic to be an integer in [1, 100])
    is applied server-side to produce the final charged amount.
    On success the prompt status moves from ``quoted`` → ``accepted`` and a
    ``PaymentRef`` record is created with status ``submitted_for_settlement``.
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
    amount = base_amount * multiplier

    gateway = get_gateway()
    result = gateway.transaction.sale({
        "amount": f"{amount:.2f}",
        "payment_method_nonce": body.nonce,
        "options": {"submit_for_settlement": True},
    })

    if not result.is_success:
        error_msg = result.message if result.message else "Payment failed"
        logger.warning("Braintree transaction failed: %s", error_msg)
        return JSONResponse(status_code=402, content={"detail": error_msg})

    transaction_id = result.transaction.id

    # Record payment reference
    payment = PaymentRef(
        braintree_transaction_id=transaction_id,
        amount=amount,
        currency="USD",
        status="settled",
    )
    db.add(payment)

    # Mark prompt as accepted and persist final (multiplied) amount + multiplier
    prompt.payment_ref = transaction_id
    prompt.status = "accepted"
    prompt.amount = amount
    prompt.weight_multiplier = multiplier

    db.commit()

    # Re-derive routing for response
    categories = [
        cp.category_id
        for cp in db.query(CategorisedPrompt).filter_by(prompt_id=prompt.id).all()
    ]
    routing = route_prompt(categories)

    return PromptAcceptedResponse(
        prompt_id=prompt.id,
        status=prompt.status,
        categories=categories,
        newspapers_reached=len(routing),
    )


@app.post("/payments/braintree-webhook")
async def braintree_webhook(
    payload: WebhookPayload,
    db: Session = Depends(get_db),
):
    """Handle Braintree webhook notifications — disputes and disbursements.

    Transaction settlement does not trigger a Braintree webhook;
    ``transaction.sale(submit_for_settlement=True)`` is authoritative.
    This endpoint handles:

    * **Dispute** events — if a customer disputes a charge, the prompt is
      reverted to ``quoted`` so it won't be consumed.  If we win the dispute
      it is re-accepted.
    * **Disbursement** events — informational logging only (funds reached
      the merchant bank account).
    """
    gateway = get_gateway()
    notification = gateway.webhook_notification.parse(
        payload.bt_signature, payload.bt_payload
    )

    kind = getattr(notification, "kind", None) or ""
    logger.info("Braintree webhook received: kind=%s", kind)

    # --- Dispute events ---
    if kind.startswith("dispute_"):
        dispute = getattr(notification, "dispute", None)
        if dispute is None:
            logger.warning("Dispute webhook missing dispute object")
            return JSONResponse(status_code=200, content={"detail": "ignored"})

        transaction_id = ""
        if hasattr(dispute, "transaction") and dispute.transaction:
            transaction_id = getattr(dispute.transaction, "id", "")
        if not transaction_id:
            logger.warning("Dispute webhook missing transaction id")
            return JSONResponse(status_code=200, content={"detail": "ignored"})

        payment = (
            db.query(PaymentRef)
            .filter_by(braintree_transaction_id=transaction_id)
            .first()
        )
        if payment is None:
            logger.warning("Dispute webhook for unknown transaction %s", transaction_id)
            return JSONResponse(status_code=200, content={"detail": "unknown transaction"})

        # Lost / Accepted / Auto-Accepted / Expired → revert prompt
        if kind in ("dispute_lost", "dispute_accepted", "dispute_auto_accepted", "dispute_expired"):
            payment.status = "disputed_lost"
            prompt = db.query(Prompt).filter_by(payment_ref=transaction_id).first()
            if prompt is not None:
                prompt.status = "quoted"
                prompt.payment_ref = None
            logger.info("Dispute lost for transaction %s — prompt reverted", transaction_id)

        # Won → restore payment status
        elif kind == "dispute_won":
            payment.status = "settled"
            logger.info("Dispute won for transaction %s", transaction_id)

        # Opened / Disputed / Under Review → flag but don't revert yet
        else:
            payment.status = "disputed"
            logger.info("Dispute %s for transaction %s", kind, transaction_id)

        db.commit()
        return JSONResponse(status_code=200, content={"detail": "ok"})

    # --- Disbursement events ---
    if kind in ("disbursement", "disbursement_exception"):
        disbursement = getattr(notification, "disbursement", None)
        if disbursement:
            logger.info(
                "Disbursement webhook: id=%s, success=%s",
                getattr(disbursement, "id", "?"),
                getattr(disbursement, "success", "?"),
            )
        return JSONResponse(status_code=200, content={"detail": "ok"})

    # --- Unknown / unhandled event ---
    logger.info("Braintree webhook ignored: kind=%s", kind)
    return JSONResponse(status_code=200, content={"detail": "ignored"})


@app.get("/payments/client-token", response_model=ClientTokenResponse)
@limiter.limit(RATE_LIMIT_QUOTE)
async def get_client_token(request: Request):
    """Generate a Braintree client token for Drop-in UI initialisation."""
    gateway = get_gateway()
    client_token = gateway.client_token.generate({})
    return ClientTokenResponse(client_token=client_token)


@app.get("/editions", response_model=list[EditionSummary])
async def list_editions(db: Session = Depends(get_db)):
    """List available editions."""
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
