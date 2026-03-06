import { render, screen } from '@testing-library/react';
import { OrbQuoteSummary } from './OrbQuoteSummary';
import type { QuoteResponse } from '../api/types';

const mockQuote: QuoteResponse = {
  categories: ['politics', 'economics'],
  newspapers_reached: 3,
  estimated_cost: 3.0,
  newspapers: [
    { newspaper_id: 'sovereign', matched_categories: ['politics'] },
    { newspaper_id: 'owner', matched_categories: ['economics'] },
    { newspaper_id: 'hedonist', matched_categories: ['politics'] },
  ],
};

describe('OrbQuoteSummary', () => {
  it('should render price correctly', () => {
    render(<OrbQuoteSummary quote={mockQuote} animate={false} />);
    expect(screen.getByText('$3.00')).toBeTruthy();
  });

  it('should render newspaper count', () => {
    render(<OrbQuoteSummary quote={mockQuote} animate={false} />);
    expect(screen.getByText('3 newspapers')).toBeTruthy();
  });

  it('should render newspaper display names', () => {
    render(<OrbQuoteSummary quote={mockQuote} animate={false} />);
    expect(screen.getByText('The Sovereign')).toBeTruthy();
    expect(screen.getByText('The Owner')).toBeTruthy();
    expect(screen.getByText('The Hedonist')).toBeTruthy();
  });

  it('should use singular "newspaper" for count of 1', () => {
    const singleQuote: QuoteResponse = {
      ...mockQuote,
      newspapers_reached: 1,
      estimated_cost: 1.0,
      newspapers: [{ newspaper_id: 'sovereign', matched_categories: ['politics'] }],
    };
    render(<OrbQuoteSummary quote={singleQuote} animate={false} />);
    expect(screen.getByText('1 newspaper')).toBeTruthy();
  });

  it('should apply animation classes when animate is true', () => {
    const { container } = render(
      <OrbQuoteSummary quote={mockQuote} animate={true} />
    );
    const animatedElements = container.querySelectorAll('.orb-triangle-text');
    expect(animatedElements.length).toBeGreaterThan(0);
  });

  it('should not apply animation classes when animate is false', () => {
    const { container } = render(
      <OrbQuoteSummary quote={mockQuote} animate={false} />
    );
    const animatedElements = container.querySelectorAll('.orb-triangle-text');
    expect(animatedElements.length).toBe(0);
  });

  // --- Weight multiplier tests ---

  it('should display multiplied price when weightMultiplier provided', () => {
    render(<OrbQuoteSummary quote={mockQuote} animate={false} weightMultiplier={10} />);
    expect(screen.getByText('$30.00')).toBeTruthy();
  });

  it('should show boost label when weightMultiplier > 1', () => {
    render(<OrbQuoteSummary quote={mockQuote} animate={false} weightMultiplier={5} />);
    expect(screen.getByText(/5× boost/)).toBeTruthy();
  });

  it('should not show boost label when weightMultiplier is 1', () => {
    render(<OrbQuoteSummary quote={mockQuote} animate={false} weightMultiplier={1} />);
    expect(screen.queryByText(/boost/)).toBeNull();
  });

  it('should default to multiplier 1 when prop is omitted', () => {
    render(<OrbQuoteSummary quote={mockQuote} animate={false} />);
    expect(screen.getByText('$3.00')).toBeTruthy();
    expect(screen.queryByText(/boost/)).toBeNull();
  });
});
