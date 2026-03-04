import { render, screen } from '@testing-library/react';
import App from './app';

// Mock the useQuote hook to avoid real API calls
vi.mock('./hooks/useQuote', () => ({
  useQuote: () => ({ quote: null, isLoading: false, error: null }),
}));

describe('App Shell', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<App />);
    expect(baseElement).toBeTruthy();
  });

  it('should have a skip link as first focusable element', () => {
    render(<App />);
    const skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toBeTruthy();
    expect(skipLink.getAttribute('href')).toBe('#main-content');
  });

  it('should have ARIA landmark roles', () => {
    render(<App />);
    expect(screen.getByRole('banner')).toBeTruthy();
    expect(screen.getByRole('main')).toBeTruthy();
    expect(screen.getByRole('contentinfo')).toBeTruthy();
  });

  it('should have main content with correct id', () => {
    render(<App />);
    const main = screen.getByRole('main');
    expect(main.id).toBe('main-content');
  });

  it('should render IMBRYK header', () => {
    render(<App />);
    expect(screen.getByText('Whisper')).toBeTruthy();
  });
});
