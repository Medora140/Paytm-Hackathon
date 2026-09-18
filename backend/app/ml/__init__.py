"""
ML / AI Engine Package for Money Docs Decoded
Owns document summarization, rule-based red-flag detection with Knowledge Base,
transparent confidence scoring, and grounded RAG conversational Q&A.
"""

from app.ml.knowledge_base import RedFlagKnowledgeBase, STARTER_KNOWLEDGE_BASE
from app.ml.red_flag_detector import RuleBasedRedFlagDetector
from app.ml.confidence_score import calculate_confidence_score, SEVERITY_WEIGHTS
from app.ml.summary_generator import generate_plain_language_summary
from app.ml.rag_chat import GroundedRAGChat
from app.ml.service import MLService, ml_service

__all__ = [
    "RedFlagKnowledgeBase",
    "STARTER_KNOWLEDGE_BASE",
    "RuleBasedRedFlagDetector",
    "calculate_confidence_score",
    "SEVERITY_WEIGHTS",
    "generate_plain_language_summary",
    "GroundedRAGChat",
    "MLService",
    "ml_service",
]
