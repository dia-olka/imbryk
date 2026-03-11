"""Pydantic request/response schemas."""

from pydantic import BaseModel, Field

from ingestion_api.config import (
    PROMPT_MAX_LENGTH,
    PROMPT_MIN_LENGTH,
    WEIGHT_MULTIPLIER_MAX,
    WEIGHT_MULTIPLIER_MIN,
)


class HealthResponse(BaseModel):
    status: str


class QuoteRequest(BaseModel):
    prompt: str = Field(
        ..., min_length=PROMPT_MIN_LENGTH, max_length=PROMPT_MAX_LENGTH
    )
    cf_turnstile_token: str | None = Field(
        default=None,
        description="Cloudflare Turnstile token. Required when TURNSTILE_SECRET_KEY is set.",
    )


class RoutingDetail(BaseModel):
    newspaper_id: str
    matched_categories: list[str]


class QuoteResponse(BaseModel):
    quote_id: str
    categories: list[str]
    newspapers_reached: int
    estimated_cost: float
    newspapers: list[RoutingDetail]


class CreateCheckoutSessionRequest(BaseModel):
    """Frontend sends the server-side quote ID.

    ``weight_multiplier`` lets the user boost their prompt's editorial
    priority by paying a multiple of the base price.  Pydantic enforces
    the range [1, 100] and integer type.
    """

    quote_id: str = Field(..., min_length=1)
    weight_multiplier: int = Field(
        default=1,
        ge=WEIGHT_MULTIPLIER_MIN,
        le=WEIGHT_MULTIPLIER_MAX,
        description="Integer multiplier (1–100) applied to the base price to boost editorial weight.",
    )


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class PromptAcceptedResponse(BaseModel):
    prompt_id: str
    status: str
    categories: list[str]
    newspapers_reached: int


class EditionSummary(BaseModel):
    edition_id: str
    date: str
    newspaper_count: int
