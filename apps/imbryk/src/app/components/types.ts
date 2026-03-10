export type FlowState = 'input' | 'confirmed' | 'error';

export type FlowAction =
  | { type: 'PAYMENT_SUCCESS' }
  | { type: 'RESET' }
  | { type: 'SET_WEIGHT_MULTIPLIER'; multiplier: number }
  | { type: 'ERROR'; message: string };

export interface FlowData {
  state: FlowState;
  prompt: string;
  weightMultiplier: number;
  errorMessage: string | null;
}
