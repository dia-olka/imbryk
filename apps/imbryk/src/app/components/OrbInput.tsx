import { useState, useId } from 'react';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { usePromptValidation } from '../hooks/usePromptValidation';
import { PROMPT_MAX } from '../constants';
import './orb.css';

interface OrbInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitDisabled: boolean;
  isReleasing?: boolean;
}

export function OrbInput({
  value,
  onChange,
  onSubmit,
  isSubmitDisabled,
  isReleasing = false,
}: OrbInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const { charCount, isValid, validationMessage } = usePromptValidation(value);
  const textareaId = useId();
  const validationId = useId();
  const charCountId = useId();

  const orbClasses = [
    'orb',
    isFocused && 'orb--focused',
    isReleasing && 'orb--releasing',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="flex flex-col items-center gap-6">
      <Label htmlFor={textareaId} className="sr-only">
        Describe a world-altering event
      </Label>

      <div className={orbClasses} aria-hidden="true">
        <Textarea
          id={textareaId}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="What happens next in the world?"
          maxLength={PROMPT_MAX}
          aria-describedby={`${validationId} ${charCountId}`}
          aria-invalid={charCount > 0 && !isValid}
          className="w-[70%] max-h-[60%] resize-none bg-transparent border-none text-white placeholder:text-white/40 text-center focus-visible:ring-0 focus-visible:ring-offset-0 scrollbar-thin"
        />
      </div>

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

      <Button
        onClick={onSubmit}
        disabled={isSubmitDisabled}
        size="lg"
        className="min-w-[200px]"
      >
        See which newspapers will cover this
      </Button>
    </div>
  );
}
