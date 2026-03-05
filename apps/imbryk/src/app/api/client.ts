import { API_BASE_URL } from '../constants';
import type { PromptAcceptedResponse, QuoteResponse } from './types';

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

export async function fetchBraintreeClientToken(
  signal?: AbortSignal
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/payments/client-token`, {
    signal,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch client token: ${response.status}`);
  }

  const data = await response.json();
  return data.client_token;
}

export async function createTransaction(
  quoteId: string,
  nonce: string,
  signal?: AbortSignal
): Promise<PromptAcceptedResponse> {
  const response = await fetch(`${API_BASE_URL}/payments/create-transaction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quote_id: quoteId, nonce }),
    signal,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Payment failed: ${response.status}`);
  }

  return response.json();
}
