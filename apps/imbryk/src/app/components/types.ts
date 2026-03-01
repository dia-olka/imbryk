import type { QuoteResponse } from '../api/types';

export type FlowState = 'input' | 'payment' | 'confirmed' | 'error';

export type FlowAction =
  | { type: 'PROCEED_TO_PAYMENT'; quote: QuoteResponse }
  | { type: 'PAYMENT_SUCCESS' }
  | { type: 'BACK_TO_INPUT' }
  | { type: 'RESET' }
  | { type: 'ERROR'; message: string };

export interface FlowData {
  state: FlowState;
  prompt: string;
  quote: QuoteResponse | null;
  errorMessage: string | null;
}
