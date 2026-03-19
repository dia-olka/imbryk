import { useState, useId, useEffect, useRef, useCallback } from 'react';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { usePromptValidation } from '../hooks/usePromptValidation';
import { PROMPT_MAX, WEIGHT_MULTIPLIER_MIN, WEIGHT_MULTIPLIER_MAX } from '../constants';
import type { QuoteResponse } from '../api/types';
import { Orb3D } from './Orb3D';
import { OrbFrontFace } from './OrbFrontFace';
import { OrbBackFace } from './OrbBackFace';
import { NEWSPAPER_DISPLAY } from './newspaper-display';

interface OrbInputProps {
  value: string;
  onChange: (value: string) => void;
  onPay: () => void;
  onSubmit: () => void;
  isSubmitDisabled: boolean;
  isPayDisabled: boolean;
  isCheckingOut?: boolean;
  quote: QuoteResponse | null;
  isQuoteLoading: boolean;
  weightMultiplier: number;
  onWeightMultiplierChange?: (multiplier: number) => void;
}

export function OrbInput({
  value,
  onChange,
  onPay,
  onSubmit,
  isSubmitDisabled,
  isPayDisabled,
  isCheckingOut = false,
  quote,
  isQuoteLoading,
  weightMultiplier,
  onWeightMultiplierChange,
}: OrbInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const { charCount, isValid, validationMessage } = usePromptValidation(value);
  const textareaId = useId();
  const validationId = useId();
  const charCountId = useId();
  const multiplierId = useId();
  const multiplierLabelId = useId();
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const prevQuoteRef = useRef<QuoteResponse | null>(null);

  // Auto-flip to back when quote arrives
  useEffect(() => {
    if (quote && quote !== prevQuoteRef.current && !isQuoteLoading) {
      const timer = setTimeout(() => setIsFlipped(true), 300);
      prevQuoteRef.current = quote;
      return () => clearTimeout(timer);
    }
    if (!quote) {
      setIsFlipped(false);
      prevQuoteRef.current = null;
    }

    return undefined;
  }, [quote, isQuoteLoading]);

  const handleFlipBack = useCallback(() => {
    setIsFlipped(false);
    // Refocus textarea after flip animation completes
    setTimeout(() => {
      const el = document.getElementById(textareaId) as HTMLTextAreaElement | null;
      el?.focus();
    }, 850);
  }, [textareaId]);

  const handleStepDown = () => {
    onWeightMultiplierChange?.(Math.max(WEIGHT_MULTIPLIER_MIN, weightMultiplier - 1));
  };

  const handleStepUp = () => {
    onWeightMultiplierChange?.(Math.min(WEIGHT_MULTIPLIER_MAX, weightMultiplier + 1));
  };

  const handleMultiplierInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!onWeightMultiplierChange) return;
    const parsed = parseInt(e.target.value, 10);
    if (!isNaN(parsed) && parsed >= WEIGHT_MULTIPLIER_MIN && parsed <= WEIGHT_MULTIPLIER_MAX) {
      onWeightMultiplierChange(parsed);
    }
  };

  const showMultiplier = isFlipped && quote && onWeightMultiplierChange;
  const totalCost = quote ? quote.estimated_cost * weightMultiplier : 0;

  return (
    <div className="flex flex-col items-center gap-6">
      <Label htmlFor={textareaId} className="sr-only">
        Request coverage of a topic
      </Label>

      <Orb3D
        isFlipped={isFlipped}
        isReleasing={isCheckingOut}
        onFlipBack={handleFlipBack}
      >
        <OrbFrontFace
          isFocused={isFocused}
          isDivining={isQuoteLoading}
          isHidden={isFlipped}
          textareaId={textareaId}
          validationId={validationId}
          charCountId={charCountId}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onSubmit={onSubmit}
          isSubmitDisabled={isSubmitDisabled}
        />
        <OrbBackFace quote={quote} isVisible={isFlipped} weightMultiplier={weightMultiplier} />
      </Orb3D>

      <div aria-live="polite" className="sr-only">
        {isFlipped && quote
          ? `Quote ready: $${totalCost.toFixed(2)} for ${quote.newspapers_reached} newspaper${quote.newspapers_reached !== 1 ? 's' : ''}: ${quote.newspapers.map((n) => NEWSPAPER_DISPLAY[n.newspaper_id]?.paperName ?? n.newspaper_id).join(', ')}`
          : ''}
      </div>

      {!isFlipped && (
        <div className="flex flex-col items-center gap-2 font-sans">
          <p
            id={charCountId}
            aria-live="polite"
            className="text-sm text-text-muted"
          >
            {charCount > 0
              ? `${charCount}/${PROMPT_MAX} characters`
              : '\u00A0'}
          </p>
          {validationMessage && charCount > 0 && !isValid && (
            <p id={validationId} role="alert" className="text-sm text-error">
              {validationMessage}
            </p>
          )}
        </div>
      )}

      {isFlipped && quote ? (
        <>
          {onWeightMultiplierChange && (
            <div
              role="group"
              aria-labelledby={multiplierLabelId}
              className="flex flex-col items-center gap-1.5"
            >
              <p
                id={multiplierLabelId}
                className="text-xs text-text-muted font-sans uppercase tracking-wide"
              >
                Editorial boost
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleStepDown}
                  disabled={weightMultiplier <= WEIGHT_MULTIPLIER_MIN || isCheckingOut}
                  aria-label="Decrease boost multiplier"
                  className="w-8 h-8 rounded-full border border-input flex items-center justify-center
                             text-lg font-light font-sans leading-none
                             hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary
                             disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  −
                </button>
                <label htmlFor={multiplierId} className="sr-only">
                  Boost multiplier (1–100)
                </label>
                <input
                  id={multiplierId}
                  type="number"
                  inputMode="numeric"
                  min={WEIGHT_MULTIPLIER_MIN}
                  max={WEIGHT_MULTIPLIER_MAX}
                  step={1}
                  value={weightMultiplier}
                  onChange={handleMultiplierInputChange}
                  onFocus={(e) => e.target.select()}
                  disabled={isCheckingOut}
                  className="w-14 h-8 rounded-md border border-input text-center text-sm font-sans
                             focus:outline-none focus:ring-2 focus:ring-primary
                             disabled:opacity-50
                             [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                />
                <button
                  type="button"
                  onClick={handleStepUp}
                  disabled={weightMultiplier >= WEIGHT_MULTIPLIER_MAX || isCheckingOut}
                  aria-label="Increase boost multiplier"
                  className="w-8 h-8 rounded-full border border-input flex items-center justify-center
                             text-lg font-light font-sans leading-none
                             hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary
                             disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  +
                </button>
              </div>
              {weightMultiplier > 1 && (
                <p className="text-xs text-text-muted font-sans" aria-live="polite">
                  {weightMultiplier}× — ${quote.estimated_cost.toFixed(2)} × {weightMultiplier} = ${totalCost.toFixed(2)}
                </p>
              )}
            </div>
          )}
          <Button
            onClick={onPay}
            disabled={isPayDisabled}
            size="lg"
            className="min-w-[200px]"
            aria-busy={isCheckingOut}
          >
            {isCheckingOut
              ? 'Redirecting to Stripe…'
              : `Pay $${totalCost.toFixed(2)}`}
          </Button>
          <p className="text-xs text-text-muted font-sans">
            Secure payment via Stripe
          </p>
        </>
      ) : (
        <Button
          onClick={onSubmit}
          disabled={isSubmitDisabled}
          size="lg"
          className="min-w-[200px]"
          aria-busy={isQuoteLoading}
        >
          {isQuoteLoading ? 'Consulting the orb…' : 'Whisper →'}
        </Button>
      )}
    </div>
  );
}
