import { renderHook, act, waitFor } from '@testing-library/react';
import { fetchQuote } from '../api/client';
import { useQuote } from './useQuote';

vi.mock('../api/client', () => ({
  fetchQuote: vi.fn(),
}));

vi.mock('../constants', () => ({
  PROMPT_MIN: 10,
  PROMPT_MAX: 2000,
  API_BASE_URL: 'http://localhost:8000',
  TURNSTILE_SITE_KEY: '',
}));

const mockFetchQuote = vi.mocked(fetchQuote);

const VALID_PROMPT = 'This is a valid prompt text';
const SHORT_PROMPT = 'abc';

const MOCK_RESPONSE = {
  categories: ['Finance & Markets'],
  newspapers_reached: 1,
  estimated_cost: 1.0,
  newspapers: [
    { newspaper_id: 'owner', matched_categories: ['Finance & Markets'] },
  ],
};

describe('useQuote', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should start with null quote, not loading', () => {
    const { result } = renderHook(() => useQuote());
    expect(result.current.quote).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should not fetch when prompt is shorter than PROMPT_MIN', () => {
    const { result } = renderHook(() => useQuote());
    act(() => {
      result.current.submit(SHORT_PROMPT);
    });
    expect(mockFetchQuote).not.toHaveBeenCalled();
    expect(result.current.isLoading).toBe(false);
  });

  it('should set isLoading immediately when submit is called with a valid prompt', () => {
    mockFetchQuote.mockResolvedValue(MOCK_RESPONSE);
    const { result } = renderHook(() => useQuote());
    act(() => {
      result.current.submit(VALID_PROMPT);
    });
    expect(result.current.isLoading).toBe(true);
  });

  it('should resolve quote after successful fetch', async () => {
    mockFetchQuote.mockResolvedValue(MOCK_RESPONSE);
    const { result } = renderHook(() => useQuote());
    act(() => {
      result.current.submit(VALID_PROMPT);
    });
    await waitFor(() => {
      expect(result.current.quote).toEqual(MOCK_RESPONSE);
      expect(result.current.isLoading).toBe(false);
    });
    expect(mockFetchQuote).toHaveBeenCalledTimes(1);
  });

  it('should handle API errors', async () => {
    mockFetchQuote.mockRejectedValue(new Error('Server error'));
    const { result } = renderHook(() => useQuote());
    act(() => {
      result.current.submit(VALID_PROMPT);
    });
    await waitFor(() => {
      expect(result.current.error).toBe('Server error');
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('should abort previous in-flight request when submit is called again', async () => {
    mockFetchQuote.mockResolvedValue(MOCK_RESPONSE);
    const { result } = renderHook(() => useQuote());
    act(() => {
      result.current.submit(VALID_PROMPT);
    });
    act(() => {
      result.current.submit('Another valid prompt text');
    });
    await waitFor(() => {
      expect(result.current.quote).toEqual(MOCK_RESPONSE);
    });
    // fetchQuote called twice (second call replaces first)
    expect(mockFetchQuote).toHaveBeenCalledTimes(2);
  });

  it('should forward turnstile token to fetchQuote', async () => {
    mockFetchQuote.mockResolvedValue(MOCK_RESPONSE);
    const { result } = renderHook(() => useQuote());
    act(() => {
      result.current.submit(VALID_PROMPT, 'turnstile_token_abc');
    });
    await waitFor(() => {
      expect(result.current.quote).toEqual(MOCK_RESPONSE);
    });
    expect(mockFetchQuote).toHaveBeenCalledWith(
      VALID_PROMPT,
      'turnstile_token_abc',
      expect.any(AbortSignal)
    );
  });

  it('should clear quote and stop loading on reset', async () => {
    mockFetchQuote.mockResolvedValue(MOCK_RESPONSE);
    const { result } = renderHook(() => useQuote());
    act(() => {
      result.current.submit(VALID_PROMPT);
    });
    await waitFor(() => expect(result.current.quote).toEqual(MOCK_RESPONSE));
    act(() => {
      result.current.reset();
    });
    expect(result.current.quote).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
