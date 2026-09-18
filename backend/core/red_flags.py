import os
import re
import pandas as pd
from typing import List, Dict, Optional

# Resolve the path to backend/data/ombudsman_dataset.csv regardless of
# where the process is launched from (project root, backend/, etc.)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # -> backend/
DEFAULT_CSV_PATH = os.path.join(BASE_DIR, "data", "ombudsman_dataset.csv")


class RedFlagDetector:
    def __init__(self, csv_path: Optional[str] = None):
        csv_path = csv_path or DEFAULT_CSV_PATH

        if os.path.exists(csv_path):
            self.dataset = pd.read_csv(csv_path)
        else:
            print(f"[RedFlagDetector] WARNING: dataset not found at {csv_path}. "
                  f"Falling back to an empty knowledge base.")
            self.dataset = pd.DataFrame(columns=[
                "category", "clause_type", "keyword_patterns", "severity_deduction", "dispute_reason"
            ])

    def get_knowledge_base_context(self) -> str:
        """Serializes ombudsman dispute data into context for the LLM prompt."""
        if self.dataset.empty:
            return "No ombudsman patterns loaded."

        context_rows = []
        for _, row in self.dataset.iterrows():
            context_rows.append(
                f"- [{row['category']}] {row['clause_type']}: Dispute Reason: '{row['dispute_reason']}' (Keywords: {row['keyword_patterns']})"
            )
        return "\n".join(context_rows)

    def scan_heuristics(self, pages_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Quick deterministic regex check against known high-risk clauses."""
        matches = []
        for page in pages_data:
            text = page["text"].lower()
            for _, row in self.dataset.iterrows():
                patterns = str(row["keyword_patterns"]).split("|")
                for pat in patterns:
                    pat_clean = pat.strip().lower()
                    if pat_clean and re.search(r"\b" + re.escape(pat_clean) + r"\b", text):
                        matches.append({
                            "clause_type": row["clause_type"],
                            "page_number": page["page_number"],
                            "severity_deduction": int(row["severity_deduction"]),
                            "dispute_reason": row["dispute_reason"]
                        })
                        break
        return matches