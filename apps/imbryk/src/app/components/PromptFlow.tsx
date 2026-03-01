import { useReducer, useState } from 'react';
import type { FlowData, FlowAction } from './types';
import { useQuote } from '../hooks/useQuote';
import { usePromptValidation } from '../hooks/usePromptValidation';
import { OrbInput } from './OrbInput';
import { QuotePreview } from './QuotePreview';
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
      return { state: 'input', prompt: '', quote: null, errorMessage: null };
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
  errorMessage: null,
};

export function PromptFlow() {
  const [flow, dispatch] = useReducer(flowReducer, initialState);
  const [prompt, setPrompt] = useState('');
  const [isReleasing, setIsReleasing] = useState(false);
  const { isValid } = usePromptValidation(prompt);
  const { quote, isLoading, error: quoteError } = useQuote(prompt);

  const handleProceedToPayment = () => {
    if (!quote) return;
    setIsReleasing(true);
    setTimeout(() => {
      dispatch({ type: 'PROCEED_TO_PAYMENT', quote });
      setIsReleasing(false);
    }, 800);
  };

  const handlePaymentSuccess = () => {
    dispatch({ type: 'PAYMENT_SUCCESS' });
  };

  const handleBack = () => {
    dispatch({ type: 'BACK_TO_INPUT' });
  };

  const handleReset = () => {
    dispatch({ type: 'RESET' });
    setPrompt('');
  };

  if (flow.state === 'confirmed' && flow.quote) {
    return <Confirmation quote={flow.quote} onReset={handleReset} />;
  }

  if (flow.state === 'payment' && flow.quote) {
    return (
      <PaymentForm
        quote={flow.quote}
        onSuccess={handlePaymentSuccess}
        onBack={handleBack}
      />
    );
  }

  return (
    <div className="flex flex-col items-center gap-8">
      <OrbInput
        value={prompt}
        onChange={setPrompt}
        onSubmit={handleProceedToPayment}
        isSubmitDisabled={!isValid || !quote || isLoading}
        isReleasing={isReleasing}
      />

      {isLoading && (
        <p className="text-sm text-text-muted font-sans animate-pulse">
          Checking newspaper coverage...
        </p>
      )}

      {quoteError && (
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>{quoteError}</AlertDescription>
        </Alert>
      )}

      {quote && !isLoading && <QuotePreview quote={quote} />}

      {flow.errorMessage && (
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>{flow.errorMessage}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
