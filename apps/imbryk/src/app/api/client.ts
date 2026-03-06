import { API_BASE_URL } from '../constants';
import type { CheckoutSessionResponse, QuoteResponse } from './types';

export async function fetchQuote(
  prompt: string,
  signal?: AbortSignal
): Promise<QuoteResponse> {
  const response = await fetch(`${API_BASE_URL}/prompts/quote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Quote request failed: ${response.status}`);
  }

  return response.json();
}

export async function createCheckoutSession(
  quoteId: string,
  weightMultiplier = 1,
  signal?: AbortSignal
): Promise<CheckoutSessionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/payments/create-checkout-session`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        quote_id: quoteId,
        weight_multiplier: weightMultiplier,
      }),
      signal,
    }
  );

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Checkout failed: ${response.status}`);
  }

  return response.json();
}
