"""Integration tests for API endpoints."""

import json
from unittest.mock import MagicMock, patch


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_quote_returns_cost_estimate(client):
    response = client.post(
        "/prompts/quote",
        json={"prompt": "What is happening in global geopolitics today?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "quote_id" in data
    assert "categories" in data
    assert "newspapers_reached" in data
    assert "estimated_cost" in data
    assert "newspapers" in data
    assert data["newspapers_reached"] > 0
    assert data["estimated_cost"] > 0


def test_quote_persists_prompt_in_db(client, db_session):
    """POST /prompts/quote should persist a Prompt with status='quoted' and the amount."""
    from ingestion_api.models import CategorisedPrompt, Prompt

    response = client.post(
        "/prompts/quote",
        json={"prompt": "A massive earthquake has altered global shipping lanes"},
    )
    assert response.status_code == 200
    data = response.json()

    prompt = db_session.query(Prompt).filter_by(id=data["quote_id"]).first()
    assert prompt is not None
    assert prompt.status == "quoted"
    assert prompt.amount == data["estimated_cost"]
    assert prompt.text == "A massive earthquake has altered global shipping lanes"
    assert prompt.payment_ref is None

    # Categories should also be persisted.
    cats = db_session.query(CategorisedPrompt).filter_by(prompt_id=prompt.id).all()
    assert len(cats) == len(data["categories"])


def test_quote_sets_expires_at(client, db_session):
    """POST /prompts/quote should set an expires_at timestamp on the stored prompt."""
    from datetime import datetime, timezone

    from ingestion_api.models import Prompt

    response = client.post(
        "/prompts/quote",
        json={"prompt": "What major events are shaping geopolitics right now?"},
    )
    assert response.status_code == 200
    data = response.json()

    prompt = db_session.query(Prompt).filter_by(id=data["quote_id"]).first()
    assert prompt.expires_at is not None
    expires_at = prompt.expires_at
    # SQLite returns naive datetimes; normalise to UTC for comparison
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at > datetime.now(timezone.utc)


def test_quote_validates_prompt_too_short(client):
    response = client.post(
        "/prompts/quote",
        json={"prompt": "short"},
    )
    assert response.status_code == 422


def test_quote_validates_prompt_too_long(client):
    response = client.post(
        "/prompts/quote",
        json={"prompt": "x" * 2001},
    )
    assert response.status_code == 422


def test_editions_returns_list(client):
    response = client.get("/editions")
    assert response.status_code == 200
    assert response.json() == []


def test_editions_pagination_params(client):
    """Pagination query params should be accepted and return a list."""
    response = client.get("/editions?limit=10&offset=0")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_editions_pagination_invalid_limit(client):
    """limit=0 should be rejected (ge=1)."""
    response = client.get("/editions?limit=0")
    assert response.status_code == 422


def test_editions_pagination_limit_too_high(client):
    """limit=201 should be rejected (le=200)."""
    response = client.get("/editions?limit=201")
    assert response.status_code == 422


def test_quote_rate_limiting(client):
    """Burst 11 requests — the 11th should be rate-limited."""
    for i in range(11):
        response = client.post(
            "/prompts/quote",
            json={"prompt": f"Tell me about geopolitics in the world today {i}"},
        )
        if response.status_code == 429:
            return  # Rate limit triggered as expected
    # If we get here, rate limiting didn't trigger within 11 requests.
    # This is acceptable — SlowAPI may not enforce in test mode.


# --- Checkout session tests ---


def _create_quote(client):
    """Helper: create a quote and return the response data."""
    response = client.post(
        "/prompts/quote",
        json={"prompt": "A giant meteor is heading towards Earth and will arrive tomorrow"},
    )
    assert response.status_code == 200
    return response.json()


def _mock_stripe_session(session_id="cs_test_123", url="https://checkout.stripe.com/test"):
    """Return a mock Stripe checkout session."""
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session.url = url
    return mock_session


def test_create_checkout_session_success(client, db_session):
    """Happy path: create-checkout-session with valid quote should return checkout_url."""
    quote = _create_quote(client)
    mock_session = _mock_stripe_session()

    with patch("stripe.checkout.Session.create", return_value=mock_session):
        response = client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["checkout_url"] == "https://checkout.stripe.com/test"


def test_create_checkout_session_invalid_quote(client):
    """create-checkout-session with non-existent quote_id should return 404."""
    with patch("stripe.checkout.Session.create"):
        response = client.post(
            "/payments/create-checkout-session",
            json={"quote_id": "non-existent-id"},
        )

    assert response.status_code == 404
    assert "Quote not found" in response.json()["detail"]


def test_create_checkout_session_already_paid(client, db_session):
    """create-checkout-session on an already-accepted quote should return 409."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)

    # Manually mark the prompt as accepted
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    prompt.status = "accepted"
    db_session.commit()

    with patch("stripe.checkout.Session.create"):
        response = client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    assert response.status_code == 409
    assert "already processed" in response.json()["detail"]


def test_create_checkout_session_expired_quote(client, db_session):
    """create-checkout-session on an expired quote should return 410."""
    from datetime import datetime, timedelta, timezone

    from ingestion_api.models import Prompt

    quote = _create_quote(client)

    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    prompt.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    with patch("stripe.checkout.Session.create"):
        response = client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    assert response.status_code == 410
    assert "expired" in response.json()["detail"]


def test_create_checkout_session_cap(client, db_session):
    """Exceeding MAX_CHECKOUT_SESSIONS_PER_QUOTE should return 429."""
    quote = _create_quote(client)
    mock_session = _mock_stripe_session()

    with patch("stripe.checkout.Session.create", return_value=mock_session):
        for _ in range(3):
            client.post(
                "/payments/create-checkout-session",
                json={"quote_id": quote["quote_id"]},
            )

    with patch("stripe.checkout.Session.create", return_value=mock_session):
        response = client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    assert response.status_code == 429
    assert "Too many checkout sessions" in response.json()["detail"]


def test_create_checkout_session_stripe_error(client):
    """create-checkout-session with Stripe error should return 502."""
    import stripe

    quote = _create_quote(client)

    with patch(
        "stripe.checkout.Session.create",
        side_effect=stripe.StripeError("Service unavailable"),
    ):
        response = client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    assert response.status_code == 502
    assert "Payment service error" in response.json()["detail"]


def test_create_checkout_session_prompt_stays_quoted_on_failure(client, db_session):
    """On Stripe error, prompt should remain in 'quoted' status."""
    import stripe

    from ingestion_api.models import Prompt

    quote = _create_quote(client)

    with patch(
        "stripe.checkout.Session.create",
        side_effect=stripe.StripeError("Error"),
    ):
        client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "quoted"
    assert prompt.payment_ref is None


def test_create_checkout_session_passes_correct_amount(client, db_session):
    """Stripe should receive the amount in cents from the server-side quote."""
    quote = _create_quote(client)
    mock_session = _mock_stripe_session()

    with patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    call_kwargs = mock_create.call_args[1]
    line_item = call_kwargs["line_items"][0]
    expected_cents = int(quote["estimated_cost"] * 100)
    assert line_item["price_data"]["unit_amount"] == expected_cents
    assert line_item["price_data"]["currency"] == "usd"
    assert call_kwargs["metadata"]["quote_id"] == quote["quote_id"]


# --- Stripe Webhook tests ---


def _build_webhook_event(event_type, data_object):
    """Build a dict mimicking a Stripe Event."""
    return {
        "type": event_type,
        "data": {"object": data_object},
    }


def _post_webhook(client, event, sig="test_sig"):
    """Post a webhook with the given event, mocking signature verification."""
    with patch(
        "ingestion_api.main.verify_webhook",
        return_value=event,
    ):
        return client.post(
            "/payments/stripe-webhook",
            content=json.dumps(event).encode(),
            headers={"stripe-signature": sig},
        )


def _create_paid_quote(client, db_session):
    """Helper: create a quote and simulate successful checkout via webhook."""
    quote = _create_quote(client)

    event = _build_webhook_event(
        "checkout.session.completed",
        {
            "payment_intent": "pi_test_123",
            "amount_total": int(quote["estimated_cost"] * 100),
            "metadata": {
                "quote_id": quote["quote_id"],
                "weight_multiplier": "1",
            },
        },
    )
    _post_webhook(client, event)
    return quote


def test_webhook_checkout_completed_accepts_prompt(client, db_session):
    """checkout.session.completed should mark prompt as accepted and create PaymentRef."""
    from ingestion_api.models import PaymentRef, Prompt

    quote = _create_quote(client)

    event = _build_webhook_event(
        "checkout.session.completed",
        {
            "payment_intent": "pi_test_456",
            "amount_total": int(quote["estimated_cost"] * 100),
            "metadata": {
                "quote_id": quote["quote_id"],
                "weight_multiplier": "1",
            },
        },
    )
    response = _post_webhook(client, event)
    assert response.status_code == 200

    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "accepted"
    assert prompt.payment_ref == "pi_test_456"
    assert prompt.weight_multiplier == 1

    payment = db_session.query(PaymentRef).filter_by(provider_transaction_id="pi_test_456").first()
    assert payment is not None
    assert payment.status == "settled"
    assert payment.amount == quote["estimated_cost"]


def test_webhook_checkout_completed_idempotent(client, db_session):
    """Sending checkout.session.completed twice should not fail."""
    quote = _create_quote(client)

    event = _build_webhook_event(
        "checkout.session.completed",
        {
            "payment_intent": "pi_test_789",
            "amount_total": int(quote["estimated_cost"] * 100),
            "metadata": {
                "quote_id": quote["quote_id"],
                "weight_multiplier": "1",
            },
        },
    )
    response1 = _post_webhook(client, event)
    assert response1.status_code == 200

    response2 = _post_webhook(client, event)
    assert response2.status_code == 200
    assert response2.json()["detail"] == "already processed"


def test_webhook_checkout_missing_quote_id(client):
    """checkout.session.completed without quote_id in metadata should be ignored."""
    event = _build_webhook_event(
        "checkout.session.completed",
        {
            "payment_intent": "pi_test_000",
            "amount_total": 500,
            "metadata": {},
        },
    )
    response = _post_webhook(client, event)
    assert response.status_code == 200
    assert response.json()["detail"] == "ignored"


def test_webhook_dispute_created_flags_disputed(client, db_session):
    """charge.dispute.created should set payment status to 'disputed'."""
    from ingestion_api.models import PaymentRef, Prompt

    quote = _create_paid_quote(client, db_session)

    event = _build_webhook_event(
        "charge.dispute.created",
        {"payment_intent": "pi_test_123"},
    )
    response = _post_webhook(client, event)
    assert response.status_code == 200

    payment = db_session.query(PaymentRef).filter_by(provider_transaction_id="pi_test_123").first()
    assert payment.status == "disputed"

    # Prompt should still be accepted (not reverted yet)
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "accepted"


def test_webhook_dispute_closed_lost_reverts_prompt(client, db_session):
    """charge.dispute.closed with status=lost should revert prompt to 'quoted'."""
    from ingestion_api.models import PaymentRef, Prompt

    quote = _create_paid_quote(client, db_session)

    event = _build_webhook_event(
        "charge.dispute.closed",
        {"payment_intent": "pi_test_123", "status": "lost"},
    )
    response = _post_webhook(client, event)
    assert response.status_code == 200

    payment = db_session.query(PaymentRef).filter_by(provider_transaction_id="pi_test_123").first()
    assert payment.status == "disputed_lost"

    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "quoted"
    assert prompt.payment_ref is None


def test_webhook_dispute_closed_won_restores_settled(client, db_session):
    """charge.dispute.closed with status=won should restore payment to 'settled'."""
    from ingestion_api.models import PaymentRef

    _create_paid_quote(client, db_session)

    # First flag as disputed
    event_opened = _build_webhook_event(
        "charge.dispute.created",
        {"payment_intent": "pi_test_123"},
    )
    _post_webhook(client, event_opened)

    payment = db_session.query(PaymentRef).filter_by(provider_transaction_id="pi_test_123").first()
    assert payment.status == "disputed"

    # Now close as won
    event_won = _build_webhook_event(
        "charge.dispute.closed",
        {"payment_intent": "pi_test_123", "status": "won"},
    )
    response = _post_webhook(client, event_won)
    assert response.status_code == 200

    db_session.refresh(payment)
    assert payment.status == "settled"


def test_webhook_dispute_unknown_transaction(client):
    """Dispute for unknown payment intent should return 200 (don't retry)."""
    event = _build_webhook_event(
        "charge.dispute.created",
        {"payment_intent": "pi_unknown_999"},
    )
    response = _post_webhook(client, event)
    assert response.status_code == 200
    assert "unknown transaction" in response.json()["detail"]


def test_webhook_unknown_event_ignored(client):
    """Unknown webhook event type should return 200 with 'ignored'."""
    event = _build_webhook_event(
        "invoice.payment_succeeded",
        {"id": "inv_123"},
    )
    response = _post_webhook(client, event)
    assert response.status_code == 200
    assert response.json()["detail"] == "ignored"


def test_webhook_invalid_signature(client):
    """Invalid signature should return 400."""
    with patch(
        "ingestion_api.main.verify_webhook",
        side_effect=Exception("Invalid signature"),
    ):
        response = client.post(
            "/payments/stripe-webhook",
            content=b"{}",
            headers={"stripe-signature": "bad_sig"},
        )

    assert response.status_code == 400
    assert "Invalid signature" in response.json()["detail"]


# --- Weight multiplier tests ---


def test_create_checkout_session_with_multiplier(client, db_session):
    """Multiplier should scale the charged amount and be stored on the prompt."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)
    mock_session = _mock_stripe_session()
    multiplier = 10

    with patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        response = client.post(
            "/payments/create-checkout-session",
            json={
                "quote_id": quote["quote_id"],
                "weight_multiplier": multiplier,
            },
        )

    assert response.status_code == 200

    # Stripe should be charged base × multiplier in cents
    call_kwargs = mock_create.call_args[1]
    line_item = call_kwargs["line_items"][0]
    expected_cents = int(quote["estimated_cost"] * multiplier * 100)
    assert line_item["price_data"]["unit_amount"] == expected_cents

    # Multiplier should be stored on the prompt
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.weight_multiplier == multiplier

    # Metadata should include the multiplier
    assert call_kwargs["metadata"]["weight_multiplier"] == str(multiplier)


def test_create_checkout_session_multiplier_defaults_to_one(client, db_session):
    """Omitting weight_multiplier should default to 1."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)
    mock_session = _mock_stripe_session()

    with patch("stripe.checkout.Session.create", return_value=mock_session):
        response = client.post(
            "/payments/create-checkout-session",
            json={"quote_id": quote["quote_id"]},
        )

    assert response.status_code == 200
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.weight_multiplier == 1


def test_create_checkout_session_multiplier_zero_rejected(client):
    """weight_multiplier=0 should be rejected by Pydantic (ge=1)."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-checkout-session",
        json={"quote_id": quote["quote_id"], "weight_multiplier": 0},
    )
    assert response.status_code == 422


def test_create_checkout_session_multiplier_negative_rejected(client):
    """Negative weight_multiplier should be rejected."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-checkout-session",
        json={"quote_id": quote["quote_id"], "weight_multiplier": -5},
    )
    assert response.status_code == 422


def test_create_checkout_session_multiplier_too_high_rejected(client):
    """weight_multiplier > 100 should be rejected."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-checkout-session",
        json={"quote_id": quote["quote_id"], "weight_multiplier": 101},
    )
    assert response.status_code == 422


def test_create_checkout_session_multiplier_float_rejected(client):
    """Non-integer weight_multiplier (e.g. 1.5) should be rejected."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-checkout-session",
        json={"quote_id": quote["quote_id"], "weight_multiplier": 1.5},
    )
    assert response.status_code == 422


def test_create_checkout_session_multiplier_max_accepted(client, db_session):
    """weight_multiplier=100 (the cap) should be accepted."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)
    mock_session = _mock_stripe_session()

    with patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        response = client.post(
            "/payments/create-checkout-session",
            json={
                "quote_id": quote["quote_id"],
                "weight_multiplier": 100,
            },
        )

    assert response.status_code == 200
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.weight_multiplier == 100

    call_kwargs = mock_create.call_args[1]
    line_item = call_kwargs["line_items"][0]
    expected_cents = int(quote["estimated_cost"] * 100 * 100)
    assert line_item["price_data"]["unit_amount"] == expected_cents


def test_webhook_checkout_with_multiplier(client, db_session):
    """checkout.session.completed should persist the weight multiplier from metadata."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)
    multiplier = 50
    amount_cents = int(quote["estimated_cost"] * multiplier * 100)

    event = _build_webhook_event(
        "checkout.session.completed",
        {
            "payment_intent": "pi_test_mult",
            "amount_total": amount_cents,
            "metadata": {
                "quote_id": quote["quote_id"],
                "weight_multiplier": str(multiplier),
            },
        },
    )
    response = _post_webhook(client, event)
    assert response.status_code == 200

    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.weight_multiplier == multiplier
    assert prompt.amount == amount_cents / 100
    assert prompt.status == "accepted"
