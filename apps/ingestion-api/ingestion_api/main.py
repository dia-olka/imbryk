"""Imbryk Ingestion API — prompts, payments, and editions."""

from fastapi import Depends, FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from ingestion_api.categoriser import CategoriserStrategy, StubCategoriser
from ingestion_api.config import RATE_LIMIT_QUOTE
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
    EditionSummary,
    HealthResponse,
    PromptAcceptedResponse,
    QuoteRequest,
    QuoteResponse,
    RoutingDetail,
    WebhookPayload,
)
from ingestion_api.taxonomy import route_prompt

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Imbryk Ingestion API", version="0.2.0")
app.state.limiter = limiter


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
        BRAINTREE_MERCHANT_ID,
        BRAINTREE_PRIVATE_KEY,
        BRAINTREE_PUBLIC_KEY,
    )

    gateway = braintree.BraintreeGateway(
        braintree.Configuration(
            environment=braintree.Environment.Sandbox,
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

    # Categorise and save
    categories = categoriser.categorise(prompt_text)
    for cat_id in categories:
        db.add(CategorisedPrompt(prompt_id=prompt.id, category_id=cat_id))

    db.commit()

    routing = route_prompt(categories)

    return PromptAcceptedResponse(
        prompt_id=prompt.id,
        status="accepted",
        categories=categories,
        newspapers_reached=len(routing),
    )


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
