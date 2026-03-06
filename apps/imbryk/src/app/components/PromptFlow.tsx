import { useReducer, useState, useEffect } from 'react';
import type { FlowData, FlowAction } from './types';
import { useQuote } from '../hooks/useQuote';
import { usePromptValidation } from '../hooks/usePromptValidation';
import { OrbInput } from './OrbInput';
import { PaymentForm } from './PaymentForm';
import { Confirmation } from './Confirmation';
import { Alert, AlertDescription } from '@/components/ui/alert';

function flowReducer(state: FlowData, action: FlowAction): FlowData {
  switch (action.type) {
    case 'PROCEED_TO_PAYMENT':
      return { ...state, state: 'payment', quote: action.quote, errorMessage: null };
    case 'PAYMENT_SUCCESS':
      return { ...state, state: 'confirmed', errorMessage: null };
    case 'BACK_TO_INPUT':
      return { ...state, state: 'input', errorMessage: null };
    case 'RESET':
      return { state: 'input', prompt: '', quote: null, weightMultiplier: 1, errorMessage: null };
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
  quote: null,
  weightMultiplier: 1,
  errorMessage: null,
};

export function PromptFlow() {
  const [flow, dispatch] = useReducer(flowReducer, initialState);
  const [prompt, setPrompt] = useState('');
  const [isReleasing, setIsReleasing] = useState(false);
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

  const handleProceedToPayment = () => {
    if (!quote) return;
    setIsReleasing(true);
    setTimeout(() => {
      dispatch({ type: 'PROCEED_TO_PAYMENT', quote });
      setIsReleasing(false);
    }, 800);
  };

  const handleBack = () => {
    resetQuote();
    dispatch({ type: 'BACK_TO_INPUT' });
  };

  const handleReset = () => {
    resetQuote();
    dispatch({ type: 'RESET' });
    setPrompt('');
  };

  if (flow.state === 'confirmed' && flow.quote) {
    return <Confirmation quote={flow.quote} onReset={handleReset} />;
  }

  // Also show confirmation when returning from Stripe (quote may be null)
  if (flow.state === 'confirmed') {
    return <Confirmation quote={null} onReset={handleReset} />;
  }

  if (flow.state === 'payment' && flow.quote) {
    return (
      <PaymentForm
        quote={flow.quote}
        weightMultiplier={flow.weightMultiplier}
        onBack={handleBack}
      />
    );
  }

  return (
    <div className="flex flex-col items-center gap-8">
      <OrbInput
        value={prompt}
        onChange={setPrompt}
        onProceed={handleProceedToPayment}
        onSubmit={() => submit(prompt)}
        isSubmitDisabled={!isValid || isLoading}
        isProceedDisabled={!quote || isLoading}
        isReleasing={isReleasing}
        quote={quote}
        weightMultiplier={flow.weightMultiplier}
        onWeightMultiplierChange={(m) =>
          dispatch({ type: 'SET_WEIGHT_MULTIPLIER', multiplier: m })
        }
        isQuoteLoading={isLoading}
      />

      {quoteError && (
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>{quoteError}</AlertDescription>
        </Alert>
      )}

      {flow.errorMessage && (
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>{flow.errorMessage}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
