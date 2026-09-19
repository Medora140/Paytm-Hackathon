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
import { supabase } from "./supabaseClient";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function headers(extra: Record<string, string> = {}) {
  try {
    const { data } = await supabase.auth.getSession();
    const merged: Record<string, string> = { ...extra };
    if (data?.session?.access_token) {
      merged.Authorization = `Bearer ${data.session.access_token}`;
    }
    return merged;
  } catch {
    return extra;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, options);
  } catch (netErr: any) {
    if (
      typeof window !== "undefined" &&
      window.location.protocol === "https:" &&
      baseUrl.startsWith("http://")
    ) {
      throw new Error(
        "Mixed Content Error: Frontend is loaded over HTTPS, but NEXT_PUBLIC_API_BASE_URL is using http://. Please configure NEXT_PUBLIC_API_BASE_URL with your HTTPS backend URL in Render/Vercel."
      );
    }
    throw new Error(
      netErr?.message === "Failed to fetch"
        ? `Network Error: Unable to reach backend API at ${baseUrl}. Check that the backend is awake and CORS ALLOWED_ORIGINS includes your frontend URL.`
        : (netErr?.message || "Network request failed.")
    );
  }
  if (response.ok) return response.json() as Promise<T>;
  const body = await response.json().catch(() => ({}));
  throw new Error(body.detail || `Request failed (${response.status}).`);
}

export async function uploadDocument(
  file: File,
  documentType?: DocumentType
): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  if (documentType) {
    form.append("document_type", documentType);
  }
  return request("/documents", {
    method: "POST",
    headers: await headers(),
    body: form,
  });
}

export async function listDocuments(): Promise<DocumentListItem[]> {
  return request("/documents", { headers: await headers() });
}

export async function getDocument(id: string): Promise<DocumentDetailResponse> {
  return request(`/documents/${id}`, { headers: await headers() });
}

export async function deleteDocument(
  id: string
): Promise<{ status: string; message: string }> {
  return request(`/documents/${id}`, {
    method: "DELETE",
    headers: await headers(),
  });
}

export async function getSummary(
  id: string,
  language = "en"
): Promise<DocumentSummaryResponse> {
  return request(
    `/documents/${id}/summary?language=${encodeURIComponent(language)}`,
    { headers: await headers() }
  );
}

export async function getRedFlags(id: string): Promise<RedFlagsResponse> {
  return request(`/documents/${id}/red-flags`, { headers: await headers() });
}

export async function getConfidenceScore(
  id: string
): Promise<ConfidenceScoreResponse> {
  return request(`/documents/${id}/confidence-score`, {
    headers: await headers(),
  });
}

export async function sendChatMessage(
  id: string,
  question: string,
  language = "en"
): Promise<ChatResponse> {
  return request(`/documents/${id}/chat`, {
    method: "POST",
    headers: await headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ question, language, include_benchmarks: true }),
  });
}

export async function getBenchmarkComparison(
  id: string
): Promise<BenchmarkCompareResponse> {
  return request(`/documents/${id}/compare`, { headers: await headers() });
}

export async function reprocessDocument(
  id: string
): Promise<{ status: string; document_id: string; message: string }> {
  return request(`/documents/${id}/reprocess`, {
    method: "POST",
    headers: await headers(),
  });
}
