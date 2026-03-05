import { useState, useEffect, useRef, useCallback } from 'react';
import dropin, { type Dropin } from 'braintree-web-drop-in';
import { fetchBraintreeClientToken } from '../api/client';

export interface UseBraintreeResult {
  isReady: boolean;
  isProcessing: boolean;
  error: string | null;
  requestPayment: () => Promise<{ nonce: string } | null>;
}

export function useBraintree(containerId: string): UseBraintreeResult {
  const [isReady, setIsReady] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const instanceRef = useRef<Dropin | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const clientToken = await fetchBraintreeClientToken();
        if (cancelled) return;

        const instance = await dropin.create({
          authorization: clientToken,
          container: `#${containerId}`,
        });

        if (cancelled) {
          instance.teardown();
          return;
        }

        instanceRef.current = instance;
        setIsReady(true);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to initialize payment'
          );
        }
      }
    }

    init();

    return () => {
      cancelled = true;
      instanceRef.current?.teardown();
      instanceRef.current = null;
    };
  }, [containerId]);

  const requestPayment = useCallback(async () => {
    if (!instanceRef.current) return null;

    setIsProcessing(true);
    setError(null);

    try {
      const { nonce } = await instanceRef.current.requestPaymentMethod();
      return { nonce };
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Payment failed'
      );
      return null;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  return { isReady, isProcessing, error, requestPayment };
}
