export interface KPIs {
  total_reviews_analysed: number;
  enriched_reviews: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  avg_sentiment_score: number | null;
  churn_risk_count: number;
  churn_risk_pct: number;
  product_opportunities: number;
}

export interface Theme {
  theme: string;
  count: number;
  pct_of_reviews?: number;
}

export interface SentimentOverall {
  total: number;
  counts: Record<string, number>;
  percentages: Record<string, number>;
  avg_score: number | null;
}

export interface PainPoint {
  pain_point: string;
  weighted_score: number;
  mention_count: number;
  sources: Record<string, number>;
  negativity_rate: number;
}

export interface FeatureRequest {
  feature_request: string;
  count: number;
  sources: Record<string, number>;
  top_themes: string[];
}

export interface Opportunity {
  title: string;
  priority: "high" | "medium" | "low";
  problem_statement: string;
  evidence: string[];
  recommendation: string;
  affected_segments: string[];
  themes: string[];
}

export interface SegmentInfo {
  count: number;
  pct: number;
}

export interface Summary {
  summary: string;
  key_issues: string[];
  recommendations: string[];
  review_count?: number;
}
