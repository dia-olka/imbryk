import { useEffect, useRef, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useBraintree } from '../hooks/useBraintree';
import { createTransaction } from '../api/client';
import { QuotePreview } from './QuotePreview';
import type { QuoteResponse } from '../api/types';

const DROPIN_CONTAINER_ID = 'braintree-dropin';

interface PaymentFormProps {
  quote: QuoteResponse;
  onSuccess: () => void;
  onBack: () => void;
}

export function PaymentForm({ quote, onSuccess, onBack }: PaymentFormProps) {
  const { isReady, isProcessing, error, requestPayment } = useBraintree(DROPIN_CONTAINER_ID);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);

  // Move focus to the heading when the payment form mounts (state transition: input → payment)
  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  const handlePay = async () => {
    setCheckoutError(null);
    const result = await requestPayment();
    if (!result) return;

    setIsSubmitting(true);
    try {
      await createTransaction(quote.quote_id, result.nonce);
      onSuccess();
    } catch (err) {
      setCheckoutError(
        err instanceof Error ? err.message : 'Payment processing failed'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const isBusy = isProcessing || isSubmitting;

  return (
    <div className="w-full max-w-md mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle
            ref={headingRef}
            tabIndex={-1}
            className="text-center font-sans focus-visible:outline-none"
          >
            Complete Payment
          </CardTitle>
          <p className="text-center text-2xl font-bold font-sans">
            ${quote.estimated_cost.toFixed(2)}
          </p>
          <p className="text-center text-sm text-text-muted font-sans">
            {quote.newspapers_reached} newspaper{quote.newspapers_reached !== 1 ? 's' : ''} will cover your event
          </p>
        </CardHeader>
        <CardContent>
          <details className="mb-4">
            <summary className="cursor-pointer text-sm text-text-muted font-sans hover:text-foreground transition-colors">
              View newspaper details
            </summary>
            <div className="mt-3">
              <QuotePreview quote={quote} />
            </div>
          </details>
          <div id={DROPIN_CONTAINER_ID} />
          {(error || checkoutError) && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{checkoutError ?? error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-3 sm:flex-row sm:justify-between">
          <Button variant="outline" onClick={onBack} disabled={isBusy}>
            Back
          </Button>
          <Button
            onClick={handlePay}
            disabled={!isReady || isBusy}
            size="lg"
          >
            {isBusy
              ? 'Processing...'
              : `Pay $${quote.estimated_cost.toFixed(2)}`}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
