"""Stripe client helpers — API key initialisation and webhook verification."""

from __future__ import annotations

import stripe

from ingestion_api.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET


def configure_stripe() -> None:
    """Set the Stripe API key globally (call once at app startup)."""
    stripe.api_key = STRIPE_SECRET_KEY


def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and construct a Stripe webhook event.

    Raises ``stripe.error.SignatureVerificationError`` if the signature is
    invalid, which the caller should handle.
    """
    return stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
