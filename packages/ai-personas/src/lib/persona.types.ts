import type { CategoryId } from '@org/taxonomy';

/** A real-world article excerpt used as a few-shot style exemplar. */
export interface Exemplar {
  /** Article type: "news_report", "analysis", or "editorial". */
  type: string;
  headline: string;
  lede: string;
  bodyExcerpt: string;
  /** Instruction to the model about what to observe in this exemplar. */
  note: string;
}

export interface NewsroomPersona {
  id: string;
  paperName: string;
  tagline: string;
  ideology: string;
  politicalLeaning: string;
  writingStyle: string;
  biases: string[];
  blindspots: string[];
  regionalBias: string;
  toneAdjustment: string;
  subscribedCategories: CategoryId[];
  modelTier: 'pro' | 'flash';
  /** Full system prompt (preamble + persona-specific suffix). Null for non-newspaper personas. */
  systemPromptTemplate: string;
}

/** A single article within a newspaper edition. */
export interface Article {
  headline: string;
  body: string;
  length: number;
  clusters: number[];
  weight: number;
  word_count: number;
  /** Vivid scene description for Imagen generation, or null if no image. */
  imagePrompt: string | null;
  /** URL of the generated image in R2, or null if not yet generated / failed. */
  image_url: string | null;
}

/** An "In Brief" item — short summary of a lower-weight cluster. */
export interface InBriefItem {
  headline: string;
  summary: string;
  clusters: number[];
}

/** Full output schema for a single newspaper's edition. */
export interface NewspaperEditionOutput {
  newspaper_id: string;
  newspaper_name: string;
  articles: Article[];
  in_brief: InBriefItem[];
  editors_note: string;
  /** Scene description for the edition hero image, or null. */
  frontPageImagePrompt: string | null;
  /** URL of the generated hero image, or null. */
  heroImageUrl: string | null;
  metadata: {
    article_to_cluster_mapping: Record<string, number>;
    weights_used: Record<string, number>;
    generation_timestamp: string;
  };
}
