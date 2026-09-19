from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =====================================================================
# Enums matching Database Schema & Architecture Specifications
# =====================================================================

class DocumentType(str, Enum):
    HEALTH_INSURANCE = "health_insurance"
    TERM_LIFE_INSURANCE = "term_life_insurance"
    LOAN = "loan"
    LOAN_AGREEMENT = "loan_agreement"
    MUTUAL_FUND = "mutual_fund"
    CREDIT_CARD = "credit_card"
    EMPLOYMENT_CONTRACT = "employment_contract"
    RENTAL_AGREEMENT = "rental_agreement"
    GENERAL_CONTRACT = "general_contract"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    ANALYZED = "analyzed"
    FAILED = "failed"


class SeverityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PlanTier(str, Enum):
    FREE = "free"
    PAID = "paid"


class ScrapeJobStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED_ROBOTS = "skipped_robots"


# =====================================================================
# Auth Service Schemas (/auth/session)
# =====================================================================

class SessionRequest(BaseModel):
    access_token: str = Field(..., description="Supabase JWT access token")
    refresh_token: Optional[str] = Field(None, description="Optional refresh token")


class SessionResponse(BaseModel):
    user_id: str
    email: str
    plan_tier: PlanTier = PlanTier.FREE
    preferred_language: str = "en"
    is_active: bool = True
    session_token: Optional[str] = None


class AuthSignUpRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")


class AuthLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class AuthResponse(BaseModel):
    user_id: str
    email: str
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    plan_tier: PlanTier = PlanTier.FREE


# =====================================================================
# Ingestion Service Schemas (/documents)
# =====================================================================

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    storage_path: str
    uploaded_at: datetime


class DocumentListItem(BaseModel):
    id: str
    user_id: str
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    issuer_name: Optional[str] = None
    uploaded_at: datetime
    confidence_score: Optional[int] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentListItem]
    total_count: int


class DocumentDetailResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    document_type: DocumentType
    storage_path: str
    status: DocumentStatus
    pipeline_stage: str
    issuer_name: Optional[str] = None
    uploaded_at: datetime
    deleted_at: Optional[datetime] = None


class DocumentDeleteResponse(BaseModel):
    status: str = "deleted"
    document_id: str
    message: str = "Document and associated data permanently deleted (DPDP right to erasure)."


# =====================================================================
# ML Analysis Service Schemas (/documents/{id}/...)
# =====================================================================

class DocumentSummaryResponse(BaseModel):
    id: str
    document_id: str
    language: str = "en"
    coverage: List[str] = Field(default_factory=list, description="Key covered treatments or benefits")
    exclusions: List[str] = Field(default_factory=list, description="Explicitly excluded procedures and scenarios")
    key_fees: List[str] = Field(default_factory=list, description="Co-pays, room rent limits, or deduction terms")
    waiting_periods: List[str] = Field(default_factory=list, description="Specific waiting intervals before coverage applies")
    notable_terms: List[str] = Field(default_factory=list, description="Other critical fine-print terms")
    model_version: str
    generated_at: datetime


class RedFlagItem(BaseModel):
    id: str
    document_id: str
    pattern_id: Optional[str] = None
    chunk_id: Optional[str] = None
    page_number: int
    clause_label: Optional[str] = None
    source_text: str
    severity: SeverityLevel
    plain_explanation: str
    confirmed_by_llm: bool = True
    created_at: datetime


class RedFlagsResponse(BaseModel):
    document_id: str
    count: int
    red_flags: List[RedFlagItem]


class ScoreBreakdownItem(BaseModel):
    reason: str
    points: int


class ConfidenceScoreResponse(BaseModel):
    id: str
    document_id: str
    score: int = Field(..., ge=0, le=100, description="Transparency and fairness confidence score (0-100)")
    breakdown: List[ScoreBreakdownItem]
    kb_version: str
    computed_at: datetime


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question asked by user regarding document")
    language: Optional[str] = Field("en", description="Preferred output language (en or hi)")
    include_benchmarks: Optional[bool] = Field(True, description="Include competitive intelligence and suggested better policies in context")


class CitationItem(BaseModel):
    chunk_id: str
    page_number: int
    clause_label: Optional[str] = None
    quote: str


class ChatResponse(BaseModel):
    id: str
    document_id: str
    role: str = "assistant"
    content: str
    cited_chunk_ids: List[str] = Field(default_factory=list)
    citations: List[CitationItem] = Field(default_factory=list)
    suggested_policies_referenced: List[str] = Field(default_factory=list)
    created_at: datetime


# =====================================================================
# Benchmark / Scraping Service Schemas (/documents/{id}/compare)
# =====================================================================

class BetterPolicySuggestion(BaseModel):
    id: str
    product_name: str
    issuer_name: str
    website_url: str
    why_better: str
    key_advantages: List[str] = Field(default_factory=list)
    potential_savings: Optional[str] = None
    risk_reduction_score: Optional[int] = None


class BenchmarkProductItem(BaseModel):
    id: str
    product_category: str
    issuer_name: str
    product_name: str
    source_url: str
    attributes: Dict[str, Any]
    complaint_signal: Dict[str, Any]
    last_scraped_at: datetime


class BenchmarkCompareResponse(BaseModel):
    document_id: str
    product_category: str
    issuer_name: Optional[str] = None
    target_attributes: Dict[str, Any] = Field(default_factory=dict)
    comparables: List[BenchmarkProductItem] = Field(default_factory=list)
    better_policies: List[BetterPolicySuggestion] = Field(default_factory=list)
    last_scraped_at: Optional[datetime] = None
    data_freshness_label: str = "Scraped within the last 7 days"


# =====================================================================
# Webhooks / Notification Service Schemas (/webhooks/n8n/...)
# =====================================================================

class ScrapeCompleteWebhook(BaseModel):
    job_id: str
    source_url: str
    status: ScrapeJobStatus
    items_scraped: int
    finished_at: datetime
    error_message: Optional[str] = None


class KBUpdatedWebhook(BaseModel):
    kb_version: str
    patterns_added: int
    timestamp: datetime


class WebhookAckResponse(BaseModel):
    success: bool = True
    message: str
    details: Optional[Dict[str, Any]] = None
