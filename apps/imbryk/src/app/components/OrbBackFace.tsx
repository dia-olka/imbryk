import type { QuoteResponse } from '../api/types';
import { OrbQuoteSummary } from './OrbQuoteSummary';

interface OrbBackFaceProps {
  quote: QuoteResponse | null;
  isVisible: boolean;
  weightMultiplier?: number;
}

export function OrbBackFace({ quote, isVisible, weightMultiplier = 1 }: OrbBackFaceProps) {
  return (
    <div className="orb-face orb-face--back" aria-hidden={!isVisible}>
      <div className="orb-viewing-window">
        {quote && (
          <div
            className="orb-triangle"
            key={`${quote.estimated_cost}-${quote.newspapers_reached}`}
          >
            <OrbQuoteSummary quote={quote} animate={isVisible} weightMultiplier={weightMultiplier} />
          </div>
        )}
      </div>
      <span className="orb-flip-hint" aria-hidden="true">Tap to edit</span>
    </div>
  );
}
