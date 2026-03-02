import type { QuoteResponse } from '../api/types';
import { NEWSPAPER_DISPLAY } from './newspaper-display';

interface OrbQuoteSummaryProps {
  quote: QuoteResponse;
  animate: boolean;
}

export function OrbQuoteSummary({ quote, animate }: OrbQuoteSummaryProps) {
  const baseClass = animate ? 'orb-triangle-text' : '';

  return (
    <div className="flex flex-col items-center gap-0.5 text-white text-center">
      <span
        className={`font-bold ${baseClass}`}
        style={{
          fontSize: 'clamp(1rem, 4vw, 1.5rem)',
          animationDelay: animate ? '0.3s' : undefined,
        }}
      >
        ${quote.estimated_cost.toFixed(2)}
      </span>
      <span
        className={`text-white/70 ${baseClass}`}
        style={{
          fontSize: 'clamp(0.55rem, 2vw, 0.75rem)',
          animationDelay: animate ? '0.5s' : undefined,
        }}
      >
        {quote.newspapers_reached} newspaper{quote.newspapers_reached !== 1 ? 's' : ''}
      </span>
      <div className="flex flex-col items-center gap-0">
        {quote.newspapers.map((routing, i) => {
          const display = NEWSPAPER_DISPLAY[routing.newspaper_id];
          return (
            <span
              key={routing.newspaper_id}
              className={`text-white/90 leading-tight ${baseClass}`}
              style={{
                fontSize: 'clamp(0.5rem, 1.8vw, 0.7rem)',
                animationDelay: animate ? `${0.7 + i * 0.15}s` : undefined,
              }}
            >
              {display?.paperName ?? routing.newspaper_id}
            </span>
          );
        })}
      </div>
    </div>
  );
}
