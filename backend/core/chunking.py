import re
from typing import List, Dict

def segment_into_clauses(pages_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Breaks down page text into logical clause segments using numbered headers or section breaks.
    Preserves page numbers for verification.
    """
    clauses = []
    clause_pattern = re.compile(r"(?:\n|^)(?:(?:Section|Clause|\d+\.)\s+[A-Z0-9\.\s\-]{3,60}|[A-Z\s]{4,40}:)", re.MULTILINE)

    for page in pages_data:
        text = page["text"]
        matches = list(clause_pattern.finditer(text))
        
        if not matches:
            clauses.append({
                "page_number": page["page_number"],
                "header": "General Content",
                "content": text
            })
            continue

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            clause_text = text[start:end].strip()
            header = match.group().strip()

            clauses.append({
                "page_number": page["page_number"],
                "header": header,
                "content": clause_text
            })

    return clauses