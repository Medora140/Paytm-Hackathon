import os
import json
from google import genai
from google.genai import types
from backend.models.schemas import AnalysisResponse, ChatResponse

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def analyze_document(document_text: str, ombudsman_context: str) -> dict:
    """
    Calls Gemini using structured JSON output to extract plain-language summary,
    red flags, and fair scoring metrics.
    """
    prompt = f"""
You are an expert financial and legal document analyzer. 
Review this financial contract (Insurance, Loan, Credit Card, or Mutual Fund).

OMBUDSMAN DISPUTE KNOWLEDGE BASE:
{ombudsman_context}

DOCUMENT TEXT WITH PAGE LABELS:
{document_text}

INSTRUCTIONS:
1. Identify the Document Type (e.g., Health Insurance Policy, Home Loan Agreement).
2. Create a Plain-Language Breakdown of 4-6 concise, user-centric bullet points covering coverage, exclusions, fees, and rules.
3. Identify all critical Red Flags (especially room rent limits, hidden fees, high copays, or arbitration constraints).
4. Provide the exact page number and a direct quote for every red flag.
5. Return the result strictly in valid JSON matching the schema.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "document_type": {"type": "STRING"},
                    "plain_summary": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "red_flags": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {"type": "STRING"},
                                "severity": {"type": "STRING"},
                                "page_number": {"type": "INTEGER"},
                                "excerpt": {"type": "STRING"},
                                "explanation": {"type": "STRING"}
                            },
                            "required": ["title", "severity", "page_number", "excerpt", "explanation"]
                        }
                    }
                },
                "required": ["document_type", "plain_summary", "red_flags"]
            },
            temperature=0.1
        )
    )

    return json.loads(response.text)

def answer_query(document_text: str, question: str) -> dict:
    """
    Answers user queries strictly grounded in the document context with exact page citations.
    """
    prompt = f"""
You are a trusted personal financial document interpreter. 
Answer the user's question using ONLY the provided document text. 
If the document does not mention the answer, state clearly that it is not covered in the document.

DOCUMENT TEXT:
{document_text}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Provide a direct, plain-language answer.
2. Provide citations with the exact page number and relevant quote from the document text.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "answer": {"type": "STRING"},
                    "citations": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "page_number": {"type": "INTEGER"},
                                "quote": {"type": "STRING"}
                            },
                            "required": ["page_number", "quote"]
                        }
                    }
                },
                "required": ["answer", "citations"]
            },
            temperature=0.1
        )
    )

    return json.loads(response.text)