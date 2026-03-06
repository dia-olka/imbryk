import { useEffect, useRef, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { createCheckoutSession } from '../api/client';
import { QuotePreview } from './QuotePreview';
import type { QuoteResponse } from '../api/types';

interface PaymentFormProps {
  quote: QuoteResponse;
  weightMultiplier: number;
  onBack: () => void;
}

export function PaymentForm({ quote, weightMultiplier, onBack }: PaymentFormProps) {
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const totalCost = quote.estimated_cost * weightMultiplier;

  // Move focus to the heading when the payment form mounts (state transition: input → payment)
  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  const handleCheckout = async () => {
    setCheckoutError(null);
    setIsRedirecting(true);

    try {
      const { checkout_url } = await createCheckoutSession(
        quote.quote_id,
        weightMultiplier
      );
      window.location.href = checkout_url;
    } catch (err) {
      setCheckoutError(
        err instanceof Error ? err.message : 'Failed to start checkout'
      );
      setIsRedirecting(false);
    }
  };

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
            ${totalCost.toFixed(2)}
          </p>
          <p className="text-center text-sm text-text-muted font-sans">
            {quote.newspapers_reached} newspaper{quote.newspapers_reached !== 1 ? 's' : ''} will cover your event
            {weightMultiplier > 1 && (
              <span className="block text-xs mt-0.5">
                {weightMultiplier}&times; weight boost applied
              </span>
            )}
          </p>
        </CardHeader>
        <CardContent>
          <details className="mb-4">
            <summary className="cursor-pointer text-sm text-text-muted font-sans hover:text-foreground transition-colors">
              View newspaper details
            </summary>
            <div className="mt-3">
              <QuotePreview quote={quote} weightMultiplier={weightMultiplier} />
            </div>
          </details>
          <p className="text-sm text-text-muted font-sans text-center">
            You&rsquo;ll be redirected to Stripe to complete your payment securely.
          </p>
          {checkoutError && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{checkoutError}</AlertDescription>
            </Alert>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-3 sm:flex-row sm:justify-between">
          <Button variant="outline" onClick={onBack} disabled={isRedirecting}>
            Back
          </Button>
          <Button
            onClick={handleCheckout}
            disabled={isRedirecting}
            size="lg"
          >
            {isRedirecting
              ? 'Redirecting to Stripe…'
              : `Pay $${totalCost.toFixed(2)}`}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
