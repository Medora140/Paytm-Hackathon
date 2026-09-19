export type DocumentType = "health_insurance" | "loan" | "mutual_fund";

export type DocumentStatus =
  | "uploaded"
  | "extracted"
  | "chunked"
  | "embedded"
  | "analyzed"
  | "failed";

export type SeverityLevel = "high" | "medium" | "low";

export type PlanTier = "free" | "paid";

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  document_type: DocumentType;
  status: DocumentStatus;
  storage_path: string;
  uploaded_at: string;
}

export interface DocumentListItem {
  id: string;
  user_id: string;
  filename: string;
  document_type: DocumentType;
  status: DocumentStatus;
  issuer_name?: string | null;
  uploaded_at: string;
  confidence_score?: number | null;
}

export interface DocumentDetailResponse {
  id: string;
  user_id: string;
  filename: string;
  document_type: DocumentType;
  storage_path: string;
  status: DocumentStatus;
  pipeline_stage: string;
  issuer_name?: string | null;
  uploaded_at: string;
  deleted_at?: string | null;
}

export interface DocumentSummaryResponse {
  id: string;
  document_id: string;
  language: string;
  coverage: string[];
  exclusions: string[];
  key_fees: string[];
  waiting_periods: string[];
  notable_terms: string[];
  model_version: string;
  generated_at: string;
}

export interface RedFlagItem {
  id: string;
  document_id: string;
  pattern_id?: string | null;
  chunk_id?: string | null;
  page_number: number;
  clause_label?: string | null;
  source_text: string;
  severity: SeverityLevel;
  plain_explanation: string;
  confirmed_by_llm: boolean;
  created_at: string;
}

export interface RedFlagsResponse {
  document_id: string;
  count: number;
  red_flags: RedFlagItem[];
}

export interface ScoreBreakdownItem {
  reason: string;
  points: number;
}

export interface ConfidenceScoreResponse {
  id: string;
  document_id: string;
  score: number;
  breakdown: ScoreBreakdownItem[];
  kb_version: string;
  computed_at: string;
}

export interface CitationItem {
  chunk_id: string;
  page_number: number;
  clause_label?: string | null;
  quote: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: CitationItem[];
  isFallback?: boolean;
  timestamp: string;
}

export interface ChatResponse {
  id: string;
  document_id: string;
  role: string;
  content: string;
  cited_chunk_ids: string[];
  citations: CitationItem[];
  suggested_policies_referenced?: string[];
  created_at: string;
}

export interface BetterPolicySuggestion {
  id: string;
  product_name: string;
  issuer_name: string;
  website_url: string;
  why_better: string;
  key_advantages: string[];
  potential_savings?: string | null;
  risk_reduction_score?: number | null;
}

export interface BenchmarkProductItem {
  id: string;
  product_category: string;
  issuer_name: string;
  product_name: string;
  source_url: string;
  attributes: Record<string, any>;
  complaint_signal: Record<string, any>;
  last_scraped_at: string;
}

export interface BenchmarkCompareResponse {
  document_id: string;
  product_category: string;
  issuer_name?: string | null;
  target_attributes: Record<string, any>;
  comparables: BenchmarkProductItem[];
  better_policies?: BetterPolicySuggestion[];
  last_scraped_at?: string | null;
  data_freshness_label: string;
}

export interface SessionResponse {
  user_id: string;
  email: string;
  plan_tier: PlanTier;
  preferred_language: string;
  is_active: boolean;
  session_token?: string | null;
}
