"""Imbryk Ingestion API — prompts, payments, and editions."""

import logging

import sentry_sdk
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from ingestion_api.categoriser import CategoriserStrategy, StubCategoriser
from ingestion_api.config import CORS_ALLOWED_ORIGINS, RATE_LIMIT_QUOTE, SENTRY_DSN

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
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


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
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
    categoriser: CategoriserStrategy = Depends(get_categoriser),
):
    """Preview categorisation, routing, and cost — no payment required."""
    categories = categoriser.categorise(body.prompt)
    routing = route_prompt(categories)
    cost = calculate_cost(len(routing))

    return QuoteResponse(
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


@app.post("/payments/braintree-webhook", response_model=PromptAcceptedResponse)
async def braintree_webhook(
    payload: WebhookPayload,
    db: Session = Depends(get_db),
    categoriser: CategoriserStrategy = Depends(get_categoriser),
):
    """Handle Braintree payment webhook — validate, store, categorise."""
    import braintree

    from ingestion_api.config import (
        BRAINTREE_ENVIRONMENT,
        BRAINTREE_MERCHANT_ID,
        BRAINTREE_PRIVATE_KEY,
        BRAINTREE_PUBLIC_KEY,
    )

    _bt_env = (
        braintree.Environment.Production
        if BRAINTREE_ENVIRONMENT == "production"
        else braintree.Environment.Sandbox
    )
    gateway = braintree.BraintreeGateway(
        braintree.Configuration(
            environment=_bt_env,
            merchant_id=BRAINTREE_MERCHANT_ID,
            public_key=BRAINTREE_PUBLIC_KEY,
            private_key=BRAINTREE_PRIVATE_KEY,
        )
    )

    notification = gateway.webhook_notification.parse(
        payload.bt_signature, payload.bt_payload
    )

    transaction = notification.subject.get("transaction", {})
    transaction_id = transaction.get("id", payload.bt_signature[:20])
    amount = float(transaction.get("amount", 0))
    prompt_text = transaction.get("custom_fields", {}).get("prompt_text", "")

    # Idempotency: Braintree may redeliver the same webhook on timeout/retry.
    # Return 200 without re-processing if we've already handled this transaction.
    existing_payment = (
        db.query(PaymentRef)
        .filter_by(braintree_transaction_id=transaction_id)
        .first()
    )
    if existing_payment is not None:
        existing_prompt = (
            db.query(Prompt).filter_by(payment_ref=transaction_id).first()
        )
        if existing_prompt is not None:
            existing_cats = [
                cp.category_id
                for cp in db.query(CategorisedPrompt)
                .filter_by(prompt_id=existing_prompt.id)
                .all()
            ]
            routing = route_prompt(existing_cats)
            return PromptAcceptedResponse(
                prompt_id=existing_prompt.id,
                status=existing_prompt.status,
                categories=existing_cats,
                newspapers_reached=len(routing),
            )

    # Save payment ref
    payment = PaymentRef(
        braintree_transaction_id=transaction_id,
        amount=amount,
        currency="USD",
        status="settled",
    )
    db.add(payment)

    # Save prompt
    prompt = Prompt(
        text=prompt_text,
        payment_ref=transaction_id,
        status="accepted",
    )
    db.add(prompt)
    db.flush()

    # Categorise and save. If the categoriser fails (e.g. Gemini API error),
    # we still commit the payment and prompt so the record is not lost.
    # The prompt is marked 'categorisation_failed' and excluded from the next
    # batch run; manual recovery can re-run categorisation against the saved text.
    categories: list[str] = []
    try:
        categories = categoriser.categorise(prompt_text)
        for cat_id in categories:
            db.add(CategorisedPrompt(prompt_id=prompt.id, category_id=cat_id))
    except Exception:
        logger.exception(
            "Categorisation failed for prompt %s; saving with 'categorisation_failed' status",
            prompt.id,
        )
        prompt.status = "categorisation_failed"

    db.commit()

    routing = route_prompt(categories)

    return PromptAcceptedResponse(
        prompt_id=prompt.id,
        status=prompt.status,
        categories=categories,
        newspapers_reached=len(routing),
    )


@app.get("/payments/client-token", response_model=ClientTokenResponse)
async def get_client_token():
    """Generate a Braintree client token for Drop-in UI initialisation."""
    import braintree

    from ingestion_api.config import (
        BRAINTREE_ENVIRONMENT,
        BRAINTREE_MERCHANT_ID,
        BRAINTREE_PRIVATE_KEY,
        BRAINTREE_PUBLIC_KEY,
    )

    _bt_env = (
        braintree.Environment.Production
        if BRAINTREE_ENVIRONMENT == "production"
        else braintree.Environment.Sandbox
    )
    gateway = braintree.BraintreeGateway(
        braintree.Configuration(
            environment=_bt_env,
            merchant_id=BRAINTREE_MERCHANT_ID,
            public_key=BRAINTREE_PUBLIC_KEY,
            private_key=BRAINTREE_PRIVATE_KEY,
        )
    )
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
