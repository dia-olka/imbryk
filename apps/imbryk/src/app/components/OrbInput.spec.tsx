import { render, screen, fireEvent, act } from '@testing-library/react';
import { OrbInput } from './OrbInput';
import type { QuoteResponse } from '../api/types';

const mockQuote: QuoteResponse = {
  quote_id: 'quote123',
  categories: ['politics'],
  newspapers_reached: 2,
  estimated_cost: 2.0,
  newspapers: [
    { newspaper_id: 'sovereign', matched_categories: ['politics'] },
    { newspaper_id: 'owner', matched_categories: ['politics'] },
  ],
};

describe('OrbInput', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    onPay: vi.fn(),
    onSubmit: vi.fn(),
    isSubmitDisabled: true,
    isPayDisabled: true,
    quote: null as QuoteResponse | null,
    isQuoteLoading: false,
    weightMultiplier: 1,
  };

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render textarea with placeholder', () => {
    render(<OrbInput {...defaultProps} />);
    expect(
      screen.getByPlaceholderText('What would you like coverage on?')
    ).toBeTruthy();
  });

  it('should call onChange when typing', () => {
    const onChange = vi.fn();
    render(<OrbInput {...defaultProps} onChange={onChange} />);
    const textarea = screen.getByPlaceholderText(
      'What would you like coverage on?'
    );
    fireEvent.change(textarea, { target: { value: 'Test event' } });
    expect(onChange).toHaveBeenCalledWith('Test event');
  });

  it('should show character count when text is entered', () => {
    render(<OrbInput {...defaultProps} value="Hello world test" />);
    expect(screen.getByText('16/2000 characters')).toBeTruthy();
  });

  it('should show validation error when below minimum', () => {
    render(<OrbInput {...defaultProps} value="Short" />);
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('should have accessible label', () => {
    render(<OrbInput {...defaultProps} />);
    const textarea = screen.getByLabelText('Request coverage of a topic');
    expect(textarea).toBeTruthy();
  });

  it('should flip to back face when quote arrives', () => {
    const { container } = render(
      <OrbInput {...defaultProps} quote={mockQuote} />
    );
    act(() => {
      vi.advanceTimersByTime(300);
    });
    const body = container.querySelector('.orb-body');
    expect(body?.classList.contains('orb-body--flipped')).toBe(true);
  });

  it('should show pay button when flipped', () => {
    render(<OrbInput {...defaultProps} quote={mockQuote} isSubmitDisabled={false} />);
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByRole('button', { name: /pay \$/i })).toBeTruthy();
  });

  it('should flip back on click when flipped', () => {
    const { container } = render(
      <OrbInput {...defaultProps} quote={mockQuote} />
    );
    act(() => {
      vi.advanceTimersByTime(300);
    });
    const body = container.querySelector('.orb-body')!;
    fireEvent.click(body);
    expect(body.classList.contains('orb-body--flipped')).toBe(false);
  });

  it('should set textarea tabIndex to -1 when flipped', () => {
    render(<OrbInput {...defaultProps} quote={mockQuote} />);
    act(() => {
      vi.advanceTimersByTime(300);
    });
    const textarea = screen.getByPlaceholderText('What would you like coverage on?');
    expect(textarea.getAttribute('tabindex')).toBe('-1');
  });

  it('should not flip when quote is null', () => {
    const { container } = render(
      <OrbInput {...defaultProps} quote={null} />
    );
    act(() => {
      vi.advanceTimersByTime(500);
    });
    const body = container.querySelector('.orb-body');
    expect(body?.classList.contains('orb-body--flipped')).toBe(false);
  });

  it('should show divining state when loading', () => {
    const { container } = render(
      <OrbInput {...defaultProps} isQuoteLoading={true} />
    );
    const front = container.querySelector('.orb-face--front');
    expect(front?.classList.contains('orb--divining')).toBe(true);
  });

  it('should show redirecting text when checking out', () => {
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        isCheckingOut={true}
        isPayDisabled={true}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    expect(screen.getByText('Redirecting to Stripe…')).toBeTruthy();
  });

  it('should show secure payment hint when flipped', () => {
    render(<OrbInput {...defaultProps} quote={mockQuote} />);
    act(() => { vi.advanceTimersByTime(300); });
    expect(screen.getByText('Secure payment via Stripe')).toBeTruthy();
  });

  // --- Editorial boost stepper ---

  it('should show stepper when flipped and onWeightMultiplierChange provided', () => {
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={vi.fn()}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    expect(screen.getByRole('group', { name: /editorial boost/i })).toBeTruthy();
  });

  it('should not show stepper when onWeightMultiplierChange is not provided', () => {
    render(<OrbInput {...defaultProps} quote={mockQuote} weightMultiplier={1} />);
    act(() => { vi.advanceTimersByTime(300); });
    expect(screen.queryByRole('group', { name: /editorial boost/i })).toBeNull();
  });

  it('should call onWeightMultiplierChange with incremented value on + click', () => {
    const onChange = vi.fn();
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={onChange}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    fireEvent.click(screen.getByRole('button', { name: /increase boost multiplier/i }));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it('should call onWeightMultiplierChange with decremented value on − click', () => {
    const onChange = vi.fn();
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        weightMultiplier={5}
        onWeightMultiplierChange={onChange}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    fireEvent.click(screen.getByRole('button', { name: /decrease boost multiplier/i }));
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it('should disable − button at minimum multiplier', () => {
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={vi.fn()}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    expect(
      screen.getByRole('button', { name: /decrease boost multiplier/i })
    ).toBeDisabled();
  });

  it('should disable + button at maximum multiplier', () => {
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        weightMultiplier={100}
        onWeightMultiplierChange={vi.fn()}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    expect(
      screen.getByRole('button', { name: /increase boost multiplier/i })
    ).toBeDisabled();
  });

  it('should show cost breakdown when multiplier > 1', () => {
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        weightMultiplier={5}
        onWeightMultiplierChange={vi.fn()}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    expect(screen.getByText(/5× — \$2\.00 × 5 = \$10\.00/)).toBeTruthy();
  });

  it('should not show cost breakdown when multiplier is 1', () => {
    render(
      <OrbInput
        {...defaultProps}
        quote={mockQuote}
        weightMultiplier={1}
        onWeightMultiplierChange={vi.fn()}
      />
    );
    act(() => { vi.advanceTimersByTime(300); });
    expect(screen.queryByText(/×.*=.*\$/)).toBeNull();
  });
});
