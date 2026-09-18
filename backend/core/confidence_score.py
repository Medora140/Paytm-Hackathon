from typing import List, Dict, Tuple

def calculate_score(heuristic_matches: List[Dict[str, any]], llm_red_flags: List[Dict[str, any]]) -> Tuple[int, List[str]]:
    """
    Computes a fairness/clarity confidence score from 0 to 100 based on deductions.
    Combines rule-based matches and LLM severity evaluations.
    """
    base_score = 100
    deductions = 0
    breakdown = []
    seen_clauses = set()

    # Apply deductions from ombudsman heuristic hits
    for match in heuristic_matches:
        c_type = match["clause_type"]
        if c_type not in seen_clauses:
            pts = match["severity_deduction"]
            deductions += pts
            breakdown.append(f"-{pts} pts: High-risk ombudsman clause detected ({c_type})")
            seen_clauses.add(c_type)

    # Apply deductions for additional severe flags reported by the LLM
    for flag in llm_red_flags:
        title = flag.get("title", "Unknown")
        severity = flag.get("severity", "Medium").upper()
        
        if title not in seen_clauses:
            pts = 10 if severity == "HIGH" else 5
            deductions += pts
            breakdown.append(f"-{pts} pts: {severity.capitalize()} severity condition ({title})")
            seen_clauses.add(title)

    final_score = max(20, base_score - deductions)
    if not breakdown:
        breakdown.append("No significant restrictive exclusions or penalties identified.")

    return final_score, breakdown