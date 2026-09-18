from typing import List, Optional
from pydantic import BaseModel, Field

class RedFlagItem(BaseModel):
    title: str = Field(..., description="Short title of the flagged clause")
    severity: str = Field(..., description="High, Medium, or Low")
    page_number: int = Field(..., description="Page number where the clause appears")
    excerpt: str = Field(..., description="Exact quoted text from the document")
    explanation: str = Field(..., description="Why this clause causes claim rejections or fees")

class AnalysisResponse(BaseModel):
    document_id: str
    document_type: str
    plain_summary: List[str] = Field(..., description="Bullet points breaking down key terms")
    confidence_score: int = Field(..., ge=0, le=100, description="Fairness score out of 100")
    score_breakdown: List[str]
    red_flags: List[RedFlagItem]
    pages_processed: int

class ChatRequest(BaseModel):
    document_id: str
    question: str

class CitationItem(BaseModel):
    page_number: int
    quote: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationItem]