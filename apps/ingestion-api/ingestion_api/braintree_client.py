"""Braintree gateway singleton — lazily initialised, reused across requests."""

from __future__ import annotations

import braintree

from ingestion_api.config import (
    BRAINTREE_ENVIRONMENT,
    BRAINTREE_MERCHANT_ID,
    BRAINTREE_PRIVATE_KEY,
    BRAINTREE_PUBLIC_KEY,
)

_gateway: braintree.BraintreeGateway | None = None


def get_gateway() -> braintree.BraintreeGateway:
    """Return a shared BraintreeGateway instance (created on first call)."""
    global _gateway
    if _gateway is None:
        _bt_env = (
            braintree.Environment.Production
            if BRAINTREE_ENVIRONMENT == "production"
            else braintree.Environment.Sandbox
        )
        _gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                environment=_bt_env,
                merchant_id=BRAINTREE_MERCHANT_ID,
                public_key=BRAINTREE_PUBLIC_KEY,
                private_key=BRAINTREE_PRIVATE_KEY,
            )
        )
    return _gateway


def reset_gateway() -> None:
    """Reset the singleton — used by tests to inject mocks."""
    global _gateway
    _gateway = None


def set_gateway(gw: braintree.BraintreeGateway) -> None:
    """Inject a gateway instance — used by tests."""
    global _gateway
    _gateway = gw
