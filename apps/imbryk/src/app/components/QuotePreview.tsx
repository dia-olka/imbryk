import { useState } from 'react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import type { QuoteResponse } from '../api/types';
import { NewspaperCard } from './NewspaperCard';
import { NEWSPAPER_DISPLAY } from './newspaper-display';
import { WEIGHT_MULTIPLIER_MIN, WEIGHT_MULTIPLIER_MAX } from '../constants';

interface QuotePreviewProps {
  quote: QuoteResponse;
  weightMultiplier?: number;
  onWeightMultiplierChange?: (multiplier: number) => void;
}

export function QuotePreview({
  quote,
  weightMultiplier = 1,
  onWeightMultiplierChange,
}: QuotePreviewProps) {
  const [inputError, setInputError] = useState<string | null>(null);
  const totalCost = quote.estimated_cost * weightMultiplier;

  const handleMultiplierChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;

    // Allow empty field while typing
    if (raw === '') {
      setInputError('Multiplier is required');
      return;
    }

    const parsed = Number(raw);

    if (!Number.isInteger(parsed)) {
      setInputError('Must be a whole number');
      return;
    }

    if (parsed < WEIGHT_MULTIPLIER_MIN) {
      setInputError(`Minimum is ${WEIGHT_MULTIPLIER_MIN}`);
      return;
    }

    if (parsed > WEIGHT_MULTIPLIER_MAX) {
      setInputError(`Maximum is ${WEIGHT_MULTIPLIER_MAX}`);
      return;
    }

    setInputError(null);
    onWeightMultiplierChange?.(parsed);
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-center">
            <span className="text-2xl font-bold font-sans">
              ${totalCost.toFixed(2)}
            </span>
          </CardTitle>
          <p className="text-center text-sm text-text-muted font-sans">
            {quote.newspapers_reached} newspaper{quote.newspapers_reached !== 1 ? 's' : ''} &times; $1.00
            {weightMultiplier > 1 && (
              <> &times; {weightMultiplier}&#215;</>
            )}
          </p>

          {onWeightMultiplierChange && (
            <div className="mt-4 space-y-2">
              <label
                htmlFor="weight-multiplier"
                className="block text-sm font-medium font-sans text-center"
              >
                Weight multiplier
              </label>
              <p
                id="weight-multiplier-help"
                className="text-xs text-text-muted text-center font-sans"
              >
                Boost your prompt's editorial priority — higher multiplier means
                more coverage in the newsroom.
              </p>
              <div className="flex items-center justify-center gap-2">
                <input
                  id="weight-multiplier"
                  type="number"
                  inputMode="numeric"
                  min={WEIGHT_MULTIPLIER_MIN}
                  max={WEIGHT_MULTIPLIER_MAX}
                  step={1}
                  value={weightMultiplier}
                  onChange={handleMultiplierChange}
                  aria-describedby="weight-multiplier-help"
                  aria-invalid={inputError ? 'true' : undefined}
                  className={[
                    'w-20 rounded-md border px-3 py-1.5 text-center text-sm font-sans',
                    'focus:outline-none focus:ring-2 focus:ring-primary',
                    inputError ? 'border-destructive' : 'border-input',
                  ].join(' ')}
                />
                <span className="text-sm text-text-muted font-sans">
                  &times; ${quote.estimated_cost.toFixed(2)} = ${totalCost.toFixed(2)}
                </span>
              </div>
              {inputError && (
                <p
                  role="alert"
                  className="text-xs text-destructive text-center font-sans"
                >
                  {inputError}
                </p>
              )}
            </div>
          )}
        </CardHeader>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2">
        {quote.newspapers.map((routing) => {
          const display = NEWSPAPER_DISPLAY[routing.newspaper_id];
          return (
            <NewspaperCard
              key={routing.newspaper_id}
              paperName={display?.paperName ?? routing.newspaper_id}
              tagline={display?.tagline ?? ''}
              display={display}
            />
          );
        })}
      </div>
    </div>
  );
}
