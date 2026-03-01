import { render, screen } from '@testing-library/react';
import { QuotePreview } from './QuotePreview';
import type { QuoteResponse } from '../api/types';

const mockQuote: QuoteResponse = {
  categories: ['Finance & Markets', 'Trade & Commerce'],
  newspapers_reached: 2,
  estimated_cost: 2.0,
  newspapers: [
    {
      newspaper_id: 'sovereign',
      matched_categories: ['Trade & Commerce'],
    },
    {
      newspaper_id: 'owner',
      matched_categories: ['Finance & Markets', 'Trade & Commerce'],
    },
  ],
};

describe('QuotePreview', () => {
  it('should display the estimated cost', () => {
    render(<QuotePreview quote={mockQuote} />);
    expect(screen.getByText('$2.00')).toBeTruthy();
  });

  it('should display newspaper count', () => {
    render(<QuotePreview quote={mockQuote} />);
    expect(screen.getByText(/2 newspapers/)).toBeTruthy();
  });

  it('should render newspaper names', () => {
    render(<QuotePreview quote={mockQuote} />);
    expect(screen.getByText('The Sovereign')).toBeTruthy();
    expect(screen.getByText('The Owner')).toBeTruthy();
  });

  it('should render matched categories as badges', () => {
    render(<QuotePreview quote={mockQuote} />);
    expect(screen.getAllByText('Trade & Commerce')).toHaveLength(2);
    expect(screen.getByText('Finance & Markets')).toBeTruthy();
  });
});
