import { render, screen, fireEvent } from '@testing-library/react';
import { OrbInput } from './OrbInput';

describe('OrbInput', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    onSubmit: vi.fn(),
    isSubmitDisabled: true,
  };

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

  it('should disable submit button when isSubmitDisabled is true', () => {
    render(<OrbInput {...defaultProps} isSubmitDisabled={true} />);
    const button = screen.getByRole('button', {
      name: /see which newspapers/i,
    });
    expect(button).toBeDisabled();
  });

  it('should call onSubmit when button clicked', () => {
    const onSubmit = vi.fn();
    render(
      <OrbInput {...defaultProps} onSubmit={onSubmit} isSubmitDisabled={false} />
    );
    const button = screen.getByRole('button', {
      name: /see which newspapers/i,
    });
    fireEvent.click(button);
    expect(onSubmit).toHaveBeenCalled();
  });
});
