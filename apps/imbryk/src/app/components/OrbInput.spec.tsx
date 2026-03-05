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
    onProceed: vi.fn(),
    onSubmit: vi.fn(),
    isSubmitDisabled: true,
    isProceedDisabled: true,
    quote: null as QuoteResponse | null,
    isQuoteLoading: false,
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
      screen.getByPlaceholderText('What happens next in the world?')
    ).toBeTruthy();
  });

  it('should call onChange when typing', () => {
    const onChange = vi.fn();
    render(<OrbInput {...defaultProps} onChange={onChange} />);
    const textarea = screen.getByPlaceholderText(
      'What happens next in the world?'
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
    const textarea = screen.getByLabelText('Describe a world-altering event');
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

  it('should show proceed button when flipped', () => {
    render(<OrbInput {...defaultProps} quote={mockQuote} isSubmitDisabled={false} />);
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByRole('button', { name: /proceed to payment/i })).toBeTruthy();
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
    const textarea = screen.getByPlaceholderText('What happens next in the world?');
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
});
