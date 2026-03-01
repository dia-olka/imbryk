import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import type { QuoteResponse } from '../api/types';
import { NewspaperCard } from './NewspaperCard';
import { NEWSPAPER_DISPLAY } from './newspaper-display';

interface QuotePreviewProps {
  quote: QuoteResponse;
}

export function QuotePreview({ quote }: QuotePreviewProps) {
  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-center">
            <span className="text-2xl font-bold font-sans">
              ${quote.estimated_cost.toFixed(2)}
            </span>
          </CardTitle>
          <p className="text-center text-sm text-text-muted font-sans">
            {quote.newspapers_reached} newspaper{quote.newspapers_reached !== 1 ? 's' : ''} &times; $1.00
          </p>
        </CardHeader>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2">
        {quote.newspapers.map((routing) => {
          const display = NEWSPAPER_DISPLAY[routing.newspaper_id];
          return (
            <NewspaperCard
              key={routing.newspaper_id}
              routing={routing}
              paperName={display?.paperName ?? routing.newspaper_id}
              tagline={display?.tagline ?? ''}
            />
          );
        })}
      </div>
    </div>
  );
}
