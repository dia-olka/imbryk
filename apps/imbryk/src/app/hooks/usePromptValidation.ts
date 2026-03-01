import { useMemo } from 'react';
import { PROMPT_MIN, PROMPT_MAX } from '../constants';

export interface PromptValidation {
  charCount: number;
  isValid: boolean;
  validationMessage: string;
}

export function usePromptValidation(prompt: string): PromptValidation {
  return useMemo(() => {
    const charCount = prompt.length;

    if (charCount === 0) {
      return { charCount, isValid: false, validationMessage: '' };
    }

    if (charCount < PROMPT_MIN) {
      return {
        charCount,
        isValid: false,
        validationMessage: `At least ${PROMPT_MIN} characters required (${charCount}/${PROMPT_MIN})`,
      };
    }

    if (charCount > PROMPT_MAX) {
      return {
        charCount,
        isValid: false,
        validationMessage: `Maximum ${PROMPT_MAX} characters exceeded (${charCount}/${PROMPT_MAX})`,
      };
    }

    return {
      charCount,
      isValid: true,
      validationMessage: `${charCount}/${PROMPT_MAX} characters`,
    };
  }, [prompt]);
}
