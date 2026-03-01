import { useState, useEffect, useRef } from 'react';
import { fetchQuote } from '../api/client';
import type { QuoteResponse } from '../api/types';
import { DEBOUNCE_MS, PROMPT_MIN } from '../constants';

export interface UseQuoteResult {
  quote: QuoteResponse | null;
  isLoading: boolean;
  error: string | null;
}

export function useQuote(prompt: string): UseQuoteResult {
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (prompt.length < PROMPT_MIN) {
      setQuote(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    const timer = setTimeout(() => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      fetchQuote(prompt, controller.signal)
        .then((data) => {
          if (!controller.signal.aborted) {
            setQuote(data);
            setIsLoading(false);
          }
        })
        .catch((err) => {
          if (!controller.signal.aborted) {
            setError(err instanceof Error ? err.message : 'Failed to fetch quote');
            setIsLoading(false);
          }
        });
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(timer);
      abortRef.current?.abort();
    };
  }, [prompt]);

  return { quote, isLoading, error };
}
