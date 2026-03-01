import { renderHook, waitFor } from '@testing-library/react';
import { fetchQuote } from '../api/client';
import { useQuote } from './useQuote';

vi.mock('../api/client', () => ({
  fetchQuote: vi.fn(),
}));

// Override DEBOUNCE_MS to 50ms for tests
vi.mock('../constants', () => ({
  PROMPT_MIN: 10,
  PROMPT_MAX: 2000,
  DEBOUNCE_MS: 50,
  API_BASE_URL: 'http://localhost:8000',
}));

const mockFetchQuote = vi.mocked(fetchQuote);

describe('useQuote', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return null quote for short prompts', () => {
    const { result } = renderHook(() => useQuote('abc'));
    expect(result.current.quote).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('should set isLoading when prompt is long enough', () => {
    const { result } = renderHook(() =>
      useQuote('This is a valid prompt text')
    );
    expect(result.current.isLoading).toBe(true);
  });

  it('should fetch quote after debounce', async () => {
    const mockResponse = {
      categories: ['Finance & Markets'],
      newspapers_reached: 1,
      estimated_cost: 1.0,
      newspapers: [
        { newspaper_id: 'owner', matched_categories: ['Finance & Markets'] },
      ],
    };
    mockFetchQuote.mockResolvedValue(mockResponse);

    const { result } = renderHook(() =>
      useQuote('This is a valid prompt text')
    );

    await waitFor(() => {
      expect(result.current.quote).toEqual(mockResponse);
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockFetchQuote).toHaveBeenCalledTimes(1);
  });

  it('should handle API errors', async () => {
    mockFetchQuote.mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() =>
      useQuote('This is a valid prompt text')
    );

    await waitFor(() => {
      expect(result.current.error).toBe('Server error');
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('should cancel previous request on prompt change', async () => {
    const mockResponse = {
      categories: ['Finance & Markets'],
      newspapers_reached: 1,
      estimated_cost: 1.0,
      newspapers: [
        { newspaper_id: 'owner', matched_categories: ['Finance & Markets'] },
      ],
    };
    mockFetchQuote.mockResolvedValue(mockResponse);

    const { result, rerender } = renderHook(
      ({ prompt }) => useQuote(prompt),
      { initialProps: { prompt: 'First valid prompt text' } }
    );

    // Change prompt immediately to trigger cancellation
    rerender({ prompt: 'Second valid prompt text' });

    await waitFor(() => {
      expect(result.current.quote).toEqual(mockResponse);
    });
  });
});
