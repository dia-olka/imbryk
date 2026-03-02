# Zero-PII Invariant

Imbryk is designed to store **no personal user data**. Braintree owns all user
identity and payment information. Our systems never receive, log, or persist
names, email addresses, IP addresses, payment card details, or any other
personally identifiable information.

## What each table stores

| Table | Columns stored | PII? |
|---|---|---|
| `prompts` | UUID, prompt text, Braintree transaction ID (ref only), status, timestamp | No |
| `categorised_prompts` | UUID, prompt FK, category label, timestamp | No |
| `payment_refs` | UUID, Braintree transaction ID (ref only), amount, currency, status, timestamp | No |
| `editions` | UUID, date string, status, timestamp | No |
| `edition_articles` | UUID, edition FK, newspaper ID, content JSON, timestamp | No |
| `world_ledger` | UUID, ledger JSON (fictional world state), timestamp | No |

The `payment_refs` table stores only the Braintree **transaction ID** (an opaque
reference like `abc123xyz`) and the settled **amount**. No customer name, billing
address, card number, or email is stored. Braintree retains all of that.

## What is NOT stored

- User names, email addresses, or account identifiers
- IP addresses (used transiently by `slowapi` for rate limiting, never written to DB)
- Payment card details, billing addresses, or bank information
- Browser fingerprints, device identifiers, or session tokens
- HTTP headers beyond what FastAPI uses internally for request routing

## Error monitoring (Sentry)

Both the backend and frontend are configured with `send_default_pii = false` /
`sendDefaultPii: false`. Sentry will not attach cookies, user IP addresses, or
HTTP headers to error events.

- Backend: `apps/ingestion-api/ingestion_api/main.py` — `sentry_sdk.init(..., send_default_pii=False)`
- Frontend: `apps/imbryk/src/main.tsx` — `Sentry.init(..., sendDefaultPii: false)`

## Rate limiting

`slowapi` uses `get_remote_address` to enforce per-IP rate limits on the
`/prompts/quote` endpoint. The IP address is held in memory for the duration of
the request window only and is **never written to the database**.

## Braintree webhook

The `/payments/braintree-webhook` handler extracts only:

- `transaction.id` — the Braintree transaction reference
- `transaction.amount` — the settled payment amount
- `transaction.custom_fields.prompt_text` — the prompt submitted by the user

No customer object, no billing details, and no payment method data from the
webhook payload are read or stored.

## Maintaining this invariant

When adding new database columns, API endpoints, or logging statements:

1. Do not add columns that identify a user (name, email, phone, IP, device ID).
2. Do not log request headers, bodies, or IP addresses at INFO level or above.
3. Do not add third-party analytics, tracking pixels, or fingerprinting scripts
   to the frontend.
4. Keep `send_default_pii = false` in all Sentry (or equivalent) SDK
   initialisation calls.
