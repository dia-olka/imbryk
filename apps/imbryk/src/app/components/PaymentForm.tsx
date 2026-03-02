import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useBraintree } from '../hooks/useBraintree';
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

  const handlePay = async () => {
    const result = await requestPayment();
    if (result) {
      onSuccess();
    }
  };

  return (
    <div className="w-full max-w-md mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-center font-sans">
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
          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-3 sm:flex-row sm:justify-between">
          <Button variant="outline" onClick={onBack} disabled={isProcessing}>
            Back
          </Button>
          <Button
            onClick={handlePay}
            disabled={!isReady || isProcessing}
            size="lg"
          >
            {isProcessing
              ? 'Processing...'
              : `Pay $${quote.estimated_cost.toFixed(2)}`}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
