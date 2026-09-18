"""
Test suite for rule-based red flag detection on synthetic mutual fund clauses and insurance clauses.
"""

from app.ml.knowledge_base import RedFlagKnowledgeBase
from app.ml.red_flag_detector import RuleBasedRedFlagDetector
from app.ml.mock_data import SYNTHETIC_MUTUAL_FUND_CHUNKS, MOCK_HEALTH_INSURANCE_CHUNKS
from app.schemas import SeverityLevel


def test_mutual_fund_red_flags():
    detector = RuleBasedRedFlagDetector()
    flags = detector.detect_red_flags("test_doc_mf", SYNTHETIC_MUTUAL_FUND_CHUNKS)
    
    assert len(flags) >= 2
    clause_types = [f.pattern_id for f in flags]
    assert any("exit_load" in cid for cid in clause_types)
    assert any("expense_ratio" in cid for cid in clause_types)


def test_health_insurance_red_flags():
    detector = RuleBasedRedFlagDetector()
    flags = detector.detect_red_flags("test_doc_health", MOCK_HEALTH_INSURANCE_CHUNKS)
    
    assert len(flags) >= 2
    clause_types = [f.pattern_id for f in flags]
    assert any("room_rent" in cid for cid in clause_types)
    assert any("ped_waiting" in cid for cid in clause_types)
