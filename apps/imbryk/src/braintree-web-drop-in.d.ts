declare module 'braintree-web-drop-in' {
  export interface Dropin {
    requestPaymentMethod(): Promise<{ nonce: string; type: string }>;
    teardown(): Promise<void>;
  }

  export interface CreateOptions {
    authorization: string;
    container: string | HTMLElement;
  }

  export function create(options: CreateOptions): Promise<Dropin>;
  export default { create };
}
