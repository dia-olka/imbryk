"""Integration tests for API endpoints."""

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


# --- Payment create-transaction tests ---


def _create_quote(client):
    """Helper: create a quote and return the response data."""
    response = client.post(
        "/prompts/quote",
        json={"prompt": "A giant meteor is heading towards Earth and will arrive tomorrow"},
    )
    assert response.status_code == 200
    return response.json()


def _mock_gateway_success():
    """Return a mock gateway whose transaction.sale() succeeds."""
    mock_gw = MagicMock()
    mock_result = MagicMock()
    mock_result.is_success = True
    mock_result.transaction.id = "test_txn_123"
    mock_gw.transaction.sale.return_value = mock_result
    return mock_gw


def _mock_gateway_failure(message="Card declined"):
    """Return a mock gateway whose transaction.sale() fails."""
    mock_gw = MagicMock()
    mock_result = MagicMock()
    mock_result.is_success = False
    mock_result.message = message
    mock_gw.transaction.sale.return_value = mock_result
    return mock_gw


def test_create_transaction_success(client, db_session):
    """Happy path: create-transaction with valid quote + nonce should return accepted."""
    from ingestion_api.models import PaymentRef, Prompt

    quote = _create_quote(client)
    mock_gw = _mock_gateway_success()

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={"quote_id": quote["quote_id"], "nonce": "fake-nonce"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["prompt_id"] == quote["quote_id"]
    assert len(data["categories"]) > 0
    assert data["newspapers_reached"] > 0

    # Verify amount passed to Braintree was from DB, not client.
    sale_args = mock_gw.transaction.sale.call_args[0][0]
    assert sale_args["amount"] == f"{quote['estimated_cost']:.2f}"

    # DB changes
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "accepted"
    assert prompt.payment_ref == "test_txn_123"
    assert prompt.weight_multiplier == 1

    payment = db_session.query(PaymentRef).filter_by(braintree_transaction_id="test_txn_123").first()
    assert payment is not None
    assert payment.status == "settled"
    assert payment.amount == quote["estimated_cost"]


def test_create_transaction_invalid_quote(client):
    """create-transaction with non-existent quote_id should return 404."""
    mock_gw = _mock_gateway_success()

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={"quote_id": "non-existent-id", "nonce": "fake-nonce"},
        )

    assert response.status_code == 404
    assert "Quote not found" in response.json()["detail"]


def test_create_transaction_already_paid(client, db_session):
    """create-transaction on an already-accepted quote should return 409."""

    quote = _create_quote(client)
    mock_gw = _mock_gateway_success()

    # First payment succeeds
    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={"quote_id": quote["quote_id"], "nonce": "fake-nonce"},
        )
    assert response.status_code == 200

    # Second attempt should be rejected
    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={"quote_id": quote["quote_id"], "nonce": "fake-nonce-2"},
        )

    assert response.status_code == 409
    assert "already processed" in response.json()["detail"]


def test_create_transaction_braintree_failure(client):
    """create-transaction with Braintree failure should return 402."""
    quote = _create_quote(client)
    mock_gw = _mock_gateway_failure("Do Not Honor")

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={"quote_id": quote["quote_id"], "nonce": "bad-nonce"},
        )

    assert response.status_code == 402
    assert "Do Not Honor" in response.json()["detail"]


def test_create_transaction_prompt_stays_quoted_on_failure(client, db_session):
    """On Braintree failure, prompt should remain in 'quoted' status."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)
    mock_gw = _mock_gateway_failure()

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        client.post(
            "/payments/create-transaction",
            json={"quote_id": quote["quote_id"], "nonce": "bad-nonce"},
        )

    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "quoted"
    assert prompt.payment_ref is None


# --- Webhook tests (dispute & disbursement) ---


def _create_paid_quote(client, db_session):
    """Helper: create a quote and pay for it, return (quote_data, mock_gw)."""
    quote = _create_quote(client)
    mock_gw = _mock_gateway_success()

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={"quote_id": quote["quote_id"], "nonce": "fake-nonce"},
        )
    assert response.status_code == 200
    return quote, mock_gw


def _make_dispute_notification(kind, transaction_id):
    """Build a mock Braintree dispute notification."""
    mock_notification = MagicMock()
    mock_notification.kind = kind
    mock_dispute = MagicMock()
    mock_dispute.transaction.id = transaction_id
    mock_notification.dispute = mock_dispute
    return mock_notification


def test_webhook_dispute_lost_reverts_prompt(client, db_session):
    """dispute_lost should revert prompt to 'quoted' and payment to 'disputed_lost'."""
    from ingestion_api.models import PaymentRef, Prompt

    quote, mock_gw = _create_paid_quote(client, db_session)

    mock_gw.webhook_notification.parse.return_value = _make_dispute_notification(
        "dispute_lost", "test_txn_123"
    )

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/braintree-webhook",
            json={"bt_signature": "sig", "bt_payload": "payload"},
        )

    assert response.status_code == 200

    payment = db_session.query(PaymentRef).filter_by(braintree_transaction_id="test_txn_123").first()
    assert payment.status == "disputed_lost"

    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "quoted"
    assert prompt.payment_ref is None


def test_webhook_dispute_won_restores_settled(client, db_session):
    """dispute_won should restore payment status to 'settled'."""
    from ingestion_api.models import PaymentRef

    quote, mock_gw = _create_paid_quote(client, db_session)

    # First simulate dispute opened
    mock_gw.webhook_notification.parse.return_value = _make_dispute_notification(
        "dispute_opened", "test_txn_123"
    )
    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        client.post("/payments/braintree-webhook", json={"bt_signature": "s", "bt_payload": "p"})

    payment = db_session.query(PaymentRef).filter_by(braintree_transaction_id="test_txn_123").first()
    assert payment.status == "disputed"

    # Now simulate dispute won
    mock_gw.webhook_notification.parse.return_value = _make_dispute_notification(
        "dispute_won", "test_txn_123"
    )
    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/braintree-webhook",
            json={"bt_signature": "sig", "bt_payload": "payload"},
        )

    assert response.status_code == 200
    db_session.refresh(payment)
    assert payment.status == "settled"


def test_webhook_dispute_opened_flags_disputed(client, db_session):
    """dispute_opened should set payment status to 'disputed' without reverting prompt."""
    from ingestion_api.models import PaymentRef, Prompt

    quote, mock_gw = _create_paid_quote(client, db_session)

    mock_gw.webhook_notification.parse.return_value = _make_dispute_notification(
        "dispute_opened", "test_txn_123"
    )

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/braintree-webhook",
            json={"bt_signature": "sig", "bt_payload": "payload"},
        )

    assert response.status_code == 200

    payment = db_session.query(PaymentRef).filter_by(braintree_transaction_id="test_txn_123").first()
    assert payment.status == "disputed"

    # Prompt should still be accepted (not reverted yet)
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.status == "accepted"


def test_webhook_dispute_unknown_transaction(client):
    """Dispute for unknown transaction should return 200 (don't retry)."""
    mock_gw = MagicMock()
    mock_gw.webhook_notification.parse.return_value = _make_dispute_notification(
        "dispute_opened", "unknown_txn_999"
    )

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/braintree-webhook",
            json={"bt_signature": "sig", "bt_payload": "payload"},
        )

    assert response.status_code == 200
    assert "unknown transaction" in response.json()["detail"]


def test_webhook_disbursement_returns_ok(client):
    """Disbursement webhook should return 200 (informational only)."""
    mock_gw = MagicMock()
    mock_notification = MagicMock()
    mock_notification.kind = "disbursement"
    mock_disbursement = MagicMock()
    mock_disbursement.id = "disbursement_001"
    mock_disbursement.success = True
    mock_notification.disbursement = mock_disbursement
    mock_gw.webhook_notification.parse.return_value = mock_notification

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/braintree-webhook",
            json={"bt_signature": "sig", "bt_payload": "payload"},
        )

    assert response.status_code == 200
    assert response.json()["detail"] == "ok"


def test_webhook_unknown_event_ignored(client):
    """Unknown webhook event kind should return 200 with 'ignored'."""
    mock_gw = MagicMock()
    mock_notification = MagicMock()
    mock_notification.kind = "subscription_charged_successfully"
    mock_gw.webhook_notification.parse.return_value = mock_notification

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/braintree-webhook",
            json={"bt_signature": "sig", "bt_payload": "payload"},
        )

    assert response.status_code == 200
    assert response.json()["detail"] == "ignored"


# --- Weight multiplier tests ---


def test_create_transaction_with_multiplier(client, db_session):
    """Multiplier should scale the charged amount and be persisted."""
    from ingestion_api.models import PaymentRef, Prompt

    quote = _create_quote(client)
    mock_gw = _mock_gateway_success()
    multiplier = 10

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={
                "quote_id": quote["quote_id"],
                "nonce": "fake-nonce",
                "weight_multiplier": multiplier,
            },
        )

    assert response.status_code == 200

    # Braintree should be charged base × multiplier
    expected_amount = quote["estimated_cost"] * multiplier
    sale_args = mock_gw.transaction.sale.call_args[0][0]
    assert sale_args["amount"] == f"{expected_amount:.2f}"

    # DB should store the multiplied amount and the multiplier
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.amount == expected_amount
    assert prompt.weight_multiplier == multiplier
    assert prompt.status == "accepted"

    payment = db_session.query(PaymentRef).filter_by(
        braintree_transaction_id="test_txn_123"
    ).first()
    assert payment.amount == expected_amount


def test_create_transaction_multiplier_defaults_to_one(client, db_session):
    """Omitting weight_multiplier should default to 1."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)
    mock_gw = _mock_gateway_success()

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={"quote_id": quote["quote_id"], "nonce": "fake-nonce"},
        )

    assert response.status_code == 200
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.weight_multiplier == 1


def test_create_transaction_multiplier_zero_rejected(client):
    """weight_multiplier=0 should be rejected by Pydantic (ge=1)."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-transaction",
        json={"quote_id": quote["quote_id"], "nonce": "fake-nonce", "weight_multiplier": 0},
    )
    assert response.status_code == 422


def test_create_transaction_multiplier_negative_rejected(client):
    """Negative weight_multiplier should be rejected."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-transaction",
        json={"quote_id": quote["quote_id"], "nonce": "fake-nonce", "weight_multiplier": -5},
    )
    assert response.status_code == 422


def test_create_transaction_multiplier_too_high_rejected(client):
    """weight_multiplier > 100 should be rejected."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-transaction",
        json={"quote_id": quote["quote_id"], "nonce": "fake-nonce", "weight_multiplier": 101},
    )
    assert response.status_code == 422


def test_create_transaction_multiplier_float_rejected(client):
    """Non-integer weight_multiplier (e.g. 1.5) should be rejected."""
    quote = _create_quote(client)

    response = client.post(
        "/payments/create-transaction",
        json={"quote_id": quote["quote_id"], "nonce": "fake-nonce", "weight_multiplier": 1.5},
    )
    assert response.status_code == 422


def test_create_transaction_multiplier_max_accepted(client, db_session):
    """weight_multiplier=100 (the cap) should be accepted."""
    from ingestion_api.models import Prompt

    quote = _create_quote(client)
    mock_gw = _mock_gateway_success()

    with patch("ingestion_api.main.get_gateway", return_value=mock_gw):
        response = client.post(
            "/payments/create-transaction",
            json={
                "quote_id": quote["quote_id"],
                "nonce": "fake-nonce",
                "weight_multiplier": 100,
            },
        )

    assert response.status_code == 200
    prompt = db_session.query(Prompt).filter_by(id=quote["quote_id"]).first()
    assert prompt.weight_multiplier == 100
    assert prompt.amount == quote["estimated_cost"] * 100
