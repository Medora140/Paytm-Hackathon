import logging
import uuid
from datetime import datetime
from typing import Any, List, Optional
from app.schemas import ConfidenceScoreResponse, ScoreBreakdownItem, SeverityLevel

logger = logging.getLogger("app.ml.confidence_score")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# §3 weights: high = 15, medium = 8, low = 3
SEVERITY_WEIGHTS = {
    SeverityLevel.HIGH: 15,
    SeverityLevel.MEDIUM: 8,
    SeverityLevel.LOW: 3
}

CURRENT_KB_VERSION = "kb_v2026.09_sebi_irda_ombudsman"


def calculate_confidence_score(
    document_id: str,
    red_flags: List[Any],
    benchmark_penalty: int = 0,
    transparency_bonus: int = 0,
    kb_version: str = CURRENT_KB_VERSION
) -> ConfidenceScoreResponse:
    """
    Implements the transparent confidence score formula from §3:
        score = 100
              - (Σ severity_weight for each red flag: high=15, medium=8, low=3)
              - (benchmark_penalty: points off if key terms are worse than scraped comparables)
              + (transparency_bonus: small bonus if doc has fewer ambiguous/hard-to-parse clauses)
        clamp(score, 0, 100)
    
    Returns ConfidenceScoreResponse with full itemized breakdown.
    """
    breakdown: List[ScoreBreakdownItem] = []
    
    # 1. Base Score
    base_points = 100
    breakdown.append(ScoreBreakdownItem(reason="Base transparency score", points=base_points))
    
    total_deductions = 0

    # 2. Red Flag Deductions
    for flag in red_flags:
        severity = flag.severity
        if severity not in SEVERITY_WEIGHTS:
            logger.warning(
                "[FALLBACK WARNING] [confidence_score] Unrecognized severity '%s' on flag '%s' for doc '%s'. Defaulting weight to 8.",
                severity,
                getattr(flag, "id", "unknown"),
                document_id
            )
        weight = SEVERITY_WEIGHTS.get(severity, 8)
        total_deductions += weight
        
        clause_desc = getattr(flag, "clause_label", None) or getattr(flag, "plain_explanation", "Identified risk clause")
        if len(clause_desc) > 60:
            clause_desc = clause_desc[:57] + "..."
            
        severity_label = severity.value.capitalize() if hasattr(severity, "value") else str(severity).capitalize()
        breakdown.append(
            ScoreBreakdownItem(
                reason=f"{severity_label}-severity penalty: {clause_desc}",
                points=-weight
            )
        )

    # 3. Benchmark Penalty (if terms deviate from comparables)
    if benchmark_penalty > 0:
        total_deductions += benchmark_penalty
        breakdown.append(
            ScoreBreakdownItem(
                reason="Benchmark penalty: Document terms stricter or costlier than median market comparables",
                points=-benchmark_penalty
            )
        )

    # 4. Transparency Bonus (if document has clear disclosures / grievance officers)
    if transparency_bonus > 0:
        breakdown.append(
            ScoreBreakdownItem(
                reason="Transparency bonus: Clear disclosure of grievance redressal, cooling-off/free-look terms",
                points=transparency_bonus
            )
        )

    # 5. Compute and Clamp Score
    raw_score = base_points - total_deductions + transparency_bonus
    clamped_score = max(0, min(100, raw_score))

    return ConfidenceScoreResponse(
        id=f"cs_{uuid.uuid4().hex[:12]}",
        document_id=document_id,
        score=clamped_score,
        breakdown=breakdown,
        kb_version=kb_version,
        computed_at=datetime.utcnow()
    )
