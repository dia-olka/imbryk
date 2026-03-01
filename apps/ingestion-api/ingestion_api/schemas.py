"""Pydantic request/response schemas."""

from pydantic import BaseModel, Field

from ingestion_api.config import PROMPT_MAX_LENGTH, PROMPT_MIN_LENGTH


class HealthResponse(BaseModel):
    status: str


class QuoteRequest(BaseModel):
    prompt: str = Field(
        ..., min_length=PROMPT_MIN_LENGTH, max_length=PROMPT_MAX_LENGTH
    )


class RoutingDetail(BaseModel):
    newspaper_id: str
    matched_categories: list[str]


class QuoteResponse(BaseModel):
    categories: list[str]
    newspapers_reached: int
    estimated_cost: float
    newspapers: list[RoutingDetail]


class WebhookPayload(BaseModel):
    bt_signature: str
    bt_payload: str


class PromptAcceptedResponse(BaseModel):
    prompt_id: str
    status: str
    categories: list[str]
    newspapers_reached: int


class EditionSummary(BaseModel):
    edition_id: str
    date: str
    newspaper_count: int
