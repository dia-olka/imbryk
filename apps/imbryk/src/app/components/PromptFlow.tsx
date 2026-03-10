import { useReducer, useState, useEffect, useCallback } from 'react';
import type { FlowData, FlowAction } from './types';
import { useQuote } from '../hooks/useQuote';
import { usePromptValidation } from '../hooks/usePromptValidation';
import { createCheckoutSession } from '../api/client';
import { OrbInput } from './OrbInput';
import { Confirmation } from './Confirmation';
import { Alert, AlertDescription } from '@/components/ui/alert';

function flowReducer(state: FlowData, action: FlowAction): FlowData {
  switch (action.type) {
    case 'PAYMENT_SUCCESS':
      return { ...state, state: 'confirmed', errorMessage: null };
    case 'RESET':
      return { state: 'input', prompt: '', weightMultiplier: 1, errorMessage: null };
    case 'SET_WEIGHT_MULTIPLIER':
      return { ...state, weightMultiplier: action.multiplier };
    case 'ERROR':
      return { ...state, state: 'error', errorMessage: action.message };
    default:
      return state;
  }
}

const initialState: FlowData = {
  state: 'input',
  prompt: '',
  weightMultiplier: 1,
  errorMessage: null,
};

export function PromptFlow() {
  const [flow, dispatch] = useReducer(flowReducer, initialState);
  const [prompt, setPrompt] = useState('');
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const { isValid } = usePromptValidation(prompt);
  const { quote, isLoading, error: quoteError, submit, reset: resetQuote } = useQuote();

  // Handle Stripe Checkout return — check URL for ?status=success
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('status') === 'success') {
      dispatch({ type: 'PAYMENT_SUCCESS' });
      // Clean up query params from URL
      window.history.replaceState({}, '', window.location.pathname);
    } else if (params.get('status') === 'cancelled') {
      // User cancelled — just clean up the URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const handlePay = useCallback(async () => {
    if (!quote) return;
    setCheckoutError(null);
    setIsCheckingOut(true);

    try {
      const { checkout_url } = await createCheckoutSession(
        quote.quote_id,
        flow.weightMultiplier
      );
      window.location.href = checkout_url;
    } catch (err) {
      setCheckoutError(
        err instanceof Error ? err.message : 'Failed to start checkout'
      );
      setIsCheckingOut(false);
    }
  }, [quote, flow.weightMultiplier]);

  const handleReset = () => {
    resetQuote();
    dispatch({ type: 'RESET' });
    setPrompt('');
    setCheckoutError(null);
  };

  if (flow.state === 'confirmed') {
    return <Confirmation quote={quote ?? null} onReset={handleReset} />;
  }

  return (
    <div className="flex flex-col items-center gap-8">
      <OrbInput
        value={prompt}
        onChange={setPrompt}
        onPay={handlePay}
        onSubmit={() => submit(prompt)}
        isSubmitDisabled={!isValid || isLoading}
        isPayDisabled={!quote || isLoading || isCheckingOut}
        isCheckingOut={isCheckingOut}
        quote={quote}
        weightMultiplier={flow.weightMultiplier}
        onWeightMultiplierChange={(m) =>
          dispatch({ type: 'SET_WEIGHT_MULTIPLIER', multiplier: m })
        }
        isQuoteLoading={isLoading}
      />

      {(quoteError || checkoutError || flow.errorMessage) && (
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>
            {quoteError || checkoutError || flow.errorMessage}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
