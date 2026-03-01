export interface RoutingDetail {
  newspaper_id: string;
  matched_categories: string[];
}

export interface QuoteResponse {
  categories: string[];
  newspapers_reached: number;
  estimated_cost: number;
  newspapers: RoutingDetail[];
}

export interface PromptAcceptedResponse {
  prompt_id: string;
  status: string;
  categories: string[];
  newspapers_reached: number;
}
