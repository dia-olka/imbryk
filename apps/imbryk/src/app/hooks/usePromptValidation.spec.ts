import { renderHook } from '@testing-library/react';
import { usePromptValidation } from './usePromptValidation';

describe('usePromptValidation', () => {
  it('should return not valid for empty string', () => {
    const { result } = renderHook(() => usePromptValidation(''));
    expect(result.current.isValid).toBe(false);
    expect(result.current.charCount).toBe(0);
    expect(result.current.validationMessage).toBe('');
  });

  it('should return not valid for too-short prompt', () => {
    const { result } = renderHook(() => usePromptValidation('Short'));
    expect(result.current.isValid).toBe(false);
    expect(result.current.validationMessage).toContain('At least 10');
  });

  it('should return valid for prompt within range', () => {
    const { result } = renderHook(() =>
      usePromptValidation('This is a valid prompt')
    );
    expect(result.current.isValid).toBe(true);
    expect(result.current.charCount).toBe(22);
  });

  it('should return not valid for prompt exceeding max', () => {
    const longText = 'a'.repeat(2001);
    const { result } = renderHook(() => usePromptValidation(longText));
    expect(result.current.isValid).toBe(false);
    expect(result.current.validationMessage).toContain('Maximum 2000');
  });
});
