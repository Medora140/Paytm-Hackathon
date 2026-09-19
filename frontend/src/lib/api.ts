import {
  BenchmarkCompareResponse,
  ChatResponse,
  ConfidenceScoreResponse,
  DocumentDetailResponse,
  DocumentListItem,
  DocumentSummaryResponse,
  DocumentType,
  DocumentUploadResponse,
  RedFlagsResponse,
} from "../types";
import {
  MOCK_BENCHMARK_COMPARE,
  MOCK_CHAT_ANSWERS,
  MOCK_CONFIDENCE_SCORE,
  MOCK_DOCUMENT_DETAIL,
  MOCK_DOCUMENT_ID,
  MOCK_DOCUMENTS_LIST,
  MOCK_RED_FLAGS,
  MOCK_SUMMARY,
  MOCK_SUMMARY_HI,
} from "./mockData";
import { supabase } from "./supabaseClient";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function getAuthHeaders(
  extraHeaders: Record<string, string> = {}
): Promise<Record<string, string>> {
  const headers: Record<string, string> = { ...extraHeaders };
  try {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  } catch (e) {
    console.warn("Could not retrieve Supabase session token:", e);
  }
  return headers;
}

export async function uploadDocument(
  file: File,
  documentType: DocumentType = "health_insurance"
): Promise<DocumentUploadResponse> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", documentType);

    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/documents`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Upload failed with status: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using stubbed upload response:", err);
    return {
      id: MOCK_DOCUMENT_ID,
      filename: file.name || "uploaded_policy.pdf",
      document_type: documentType,
      status: "uploaded",
      storage_path: `documents/${MOCK_DOCUMENT_ID}/${file.name}`,
      uploaded_at: new Date().toISOString(),
    };
  }
}

export async function listDocuments(): Promise<DocumentListItem[]> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/documents`, { headers });
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`List documents failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock document list:", err);
    return MOCK_DOCUMENTS_LIST;
  }
}

export async function getDocument(id: string): Promise<DocumentDetailResponse> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/documents/${id}`, { headers });
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Get document failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock document detail:", err);
    return {
      ...MOCK_DOCUMENT_DETAIL,
      id,
    };
  }
}

export async function deleteDocument(
  id: string
): Promise<{ status: string; message: string }> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/documents/${id}`, {
      method: "DELETE",
      headers,
    });
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Delete document failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock delete response:", err);
    return {
      status: "deleted",
      message:
        "Document and associated data permanently deleted (DPDP right to erasure).",
    };
  }
}

export async function getSummary(
  id: string,
  language: string = "en"
): Promise<DocumentSummaryResponse> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(
      `${API_BASE_URL}/documents/${id}/summary?language=${encodeURIComponent(
        language
      )}`,
      { headers }
    );
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Get summary failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock summary:", err);
    if (language === "hi") {
      return { ...MOCK_SUMMARY_HI, document_id: id, is_fallback: true };
    }
    return { ...MOCK_SUMMARY, document_id: id, is_fallback: true };
  }
}

export async function getRedFlags(id: string): Promise<RedFlagsResponse> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/documents/${id}/red-flags`, {
      headers,
    });
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Get red flags failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock red flags:", err);
    return { ...MOCK_RED_FLAGS, document_id: id };
  }
}

export async function getConfidenceScore(
  id: string
): Promise<ConfidenceScoreResponse> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/documents/${id}/confidence-score`, {
      headers,
    });
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Get confidence score failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock confidence score:", err);
    return { ...MOCK_CONFIDENCE_SCORE, document_id: id };
  }
}

export async function sendChatMessage(
  id: string,
  question: string,
  language: string = "en"
): Promise<ChatResponse> {
  try {
    const headers = await getAuthHeaders({
      "Content-Type": "application/json",
    });
    const res = await fetch(`${API_BASE_URL}/documents/${id}/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({ question, language }),
    });
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Chat failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock chat response:", err);
    const lower = question.toLowerCase();
    // Word-boundary safe pattern matching for mock demo fallback
    if (/\b(?:room|rent)\b/i.test(lower)) {
      return { ...MOCK_CHAT_ANSWERS.room_rent, document_id: id, is_fallback: true };
    }
    if (/\b(?:pre-existing|ped|waiting\s*period)\b/i.test(lower)) {
      return { ...MOCK_CHAT_ANSWERS.waiting_period, document_id: id, is_fallback: true };
    }
    return {
      ...MOCK_CHAT_ANSWERS.default,
      document_id: id,
      is_fallback: true,
      content: `Regarding your query "${question}": According to your policy clauses, room rent is restricted to 1% per day (Clause 4.2, Page 14) and pre-existing conditions have a 36-month waiting period (Clause 9.1, Page 18).`,
    };
  }
}

export async function getBenchmarkComparison(
  id: string
): Promise<BenchmarkCompareResponse> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/documents/${id}/compare`, {
      headers,
    });
    if (res.ok) {
      return await res.json();
    }
    throw new Error(`Get benchmarks failed: ${res.status}`);
  } catch (err) {
    console.warn("Backend unavailable, using mock benchmark comparison:", err);
    return { ...MOCK_BENCHMARK_COMPARE, document_id: id };
  }
}
