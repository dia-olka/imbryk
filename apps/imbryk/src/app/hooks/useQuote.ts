import { useState, useRef, useCallback, useEffect } from 'react';
import { fetchQuote } from '../api/client';
import type { QuoteResponse } from '../api/types';
import { PROMPT_MIN } from '../constants';

export interface UseQuoteResult {
  quote: QuoteResponse | null;
  isLoading: boolean;
  error: string | null;
  submit: (prompt: string) => void;
  reset: () => void;
}

export function useQuote(): UseQuoteResult {
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Abort any in-flight request on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const submit = useCallback((prompt: string) => {
    if (prompt.length < PROMPT_MIN) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);
    setQuote(null);

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
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setQuote(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return { quote, isLoading, error, submit, reset };
}
