import { render, screen, fireEvent } from '@testing-library/react';
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

  // --- Weight multiplier tests ---

  it('should display multiplied total when weightMultiplier > 1', () => {
    render(<QuotePreview quote={mockQuote} weightMultiplier={5} />);
    expect(screen.getByText('$10.00')).toBeTruthy();
  });

  it('should show multiplier input when onWeightMultiplierChange provided', () => {
    const onChange = vi.fn();
    render(
      <QuotePreview
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={onChange}
      />
    );
    expect(screen.getByLabelText('Weight multiplier')).toBeTruthy();
  });

  it('should not show multiplier input when onWeightMultiplierChange is not provided', () => {
    render(<QuotePreview quote={mockQuote} />);
    expect(screen.queryByLabelText('Weight multiplier')).toBeNull();
  });

  it('should call onWeightMultiplierChange with valid integer', () => {
    const onChange = vi.fn();
    render(
      <QuotePreview
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={onChange}
      />
    );
    const input = screen.getByLabelText('Weight multiplier');
    fireEvent.change(input, { target: { value: '10' } });
    expect(onChange).toHaveBeenCalledWith(10);
  });

  it('should show error for value below minimum', () => {
    const onChange = vi.fn();
    render(
      <QuotePreview
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={onChange}
      />
    );
    const input = screen.getByLabelText('Weight multiplier');
    fireEvent.change(input, { target: { value: '0' } });
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('should show error for value above maximum', () => {
    const onChange = vi.fn();
    render(
      <QuotePreview
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={onChange}
      />
    );
    const input = screen.getByLabelText('Weight multiplier');
    fireEvent.change(input, { target: { value: '101' } });
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('should show error for non-integer value', () => {
    const onChange = vi.fn();
    render(
      <QuotePreview
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={onChange}
      />
    );
    const input = screen.getByLabelText('Weight multiplier');
    fireEvent.change(input, { target: { value: '1.5' } });
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('should show cost breakdown next to multiplier input', () => {
    const onChange = vi.fn();
    render(
      <QuotePreview
        quote={mockQuote}
        weightMultiplier={5}
        onWeightMultiplierChange={onChange}
      />
    );
    expect(screen.getByText(/× \$2\.00 = \$10\.00/)).toBeTruthy();
  });
});
