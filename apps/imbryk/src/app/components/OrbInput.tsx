import { useState, useId, useEffect, useRef, useCallback } from 'react';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { usePromptValidation } from '../hooks/usePromptValidation';
import { PROMPT_MAX } from '../constants';
import type { QuoteResponse } from '../api/types';
import { Orb3D } from './Orb3D';
import { OrbFrontFace } from './OrbFrontFace';
import { OrbBackFace } from './OrbBackFace';
import { NEWSPAPER_DISPLAY } from './newspaper-display';

interface OrbInputProps {
  value: string;
  onChange: (value: string) => void;
  onProceed: () => void;
  isSubmitDisabled: boolean;
  isReleasing?: boolean;
  quote: QuoteResponse | null;
  isQuoteLoading: boolean;
}

export function OrbInput({
  value,
  onChange,
  onProceed,
  isSubmitDisabled,
  isReleasing = false,
  quote,
  isQuoteLoading,
}: OrbInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const { charCount, isValid, validationMessage } = usePromptValidation(value);
  const textareaId = useId();
  const validationId = useId();
  const charCountId = useId();
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
  }, [quote, isQuoteLoading]);

  const handleFlipBack = useCallback(() => {
    setIsFlipped(false);
    // Refocus textarea after flip animation completes
    setTimeout(() => {
      const el = document.getElementById(textareaId) as HTMLTextAreaElement | null;
      el?.focus();
    }, 850);
  }, [textareaId]);

  return (
    <div className="flex flex-col items-center gap-6">
      <Label htmlFor={textareaId} className="sr-only">
        Describe a world-altering event
      </Label>

      <Orb3D
        isFlipped={isFlipped}
        isReleasing={isReleasing}
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
        />
        <OrbBackFace quote={quote} isVisible={isFlipped} />
      </Orb3D>

      <div
        aria-live="polite"
        className="sr-only"
      >
        {isFlipped && quote
          ? `Quote ready: $${quote.estimated_cost.toFixed(2)} for ${quote.newspapers_reached} newspaper${quote.newspapers_reached !== 1 ? 's' : ''}: ${quote.newspapers.map((n) => NEWSPAPER_DISPLAY[n.newspaper_id]?.paperName ?? n.newspaper_id).join(', ')}`
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
        <Button
          onClick={onProceed}
          disabled={isSubmitDisabled}
          size="lg"
          className="min-w-[200px]"
        >
          Proceed to payment — ${quote.estimated_cost.toFixed(2)}
        </Button>
      ) : (
        <Button
          onClick={onProceed}
          disabled={isSubmitDisabled}
          size="lg"
          className="min-w-[200px] invisible"
          aria-hidden="true"
          tabIndex={-1}
        >
          Placeholder
        </Button>
      )}
    </div>
  );
}
