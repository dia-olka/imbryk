export interface RoutingDetail {
  newspaper_id: string;
  matched_categories: string[];
}

export interface QuoteResponse {
  quote_id: string;
  categories: string[];
  newspapers_reached: number;
  estimated_cost: number;
  newspapers: RoutingDetail[];
}

export interface CreateCheckoutSessionRequest {
  quote_id: string;
  weight_multiplier: number;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
}

export interface PromptAcceptedResponse {
  prompt_id: string;
  status: string;
  categories: string[];
  newspapers_reached: number;
}
