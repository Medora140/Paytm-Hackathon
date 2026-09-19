import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DocumentDashboardPage from "../app/doc/[id]/page";
import * as api from "../lib/api";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "mock-doc-123" }),
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Fallback Visibility Banner (Agent 4)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders FallbackWarningBanner when api returns fallback data (forced backend failure)", async () => {
    // Force backend failure -> fallback data with is_fallback: true
    vi.spyOn(api, "getDocument").mockResolvedValue({
      id: "mock-doc-123",
      user_id: "demo-user",
      filename: "Test Policy.pdf",
      document_type: "health_insurance",
      storage_path: "docs/test.pdf",
      status: "uploaded",
      pipeline_stage: "Ready",
      uploaded_at: new Date().toISOString(),
      is_fallback: true,
    });

    vi.spyOn(api, "getSummary").mockResolvedValue({
      id: "sum-fallback",
      document_id: "mock-doc-123",
      language: "en",
      coverage: ["Sample coverage"],
      exclusions: ["Sample exclusion"],
      key_fees: ["Sample fees"],
      waiting_periods: ["Sample waiting"],
      notable_terms: ["Sample terms"],
      model_version: "mock",
      is_fallback: true,
      generated_at: new Date().toISOString(),
    });

    vi.spyOn(api, "getRedFlags").mockResolvedValue({
      document_id: "mock-doc-123",
      count: 0,
      red_flags: [],
      is_fallback: true,
    });

    vi.spyOn(api, "getConfidenceScore").mockResolvedValue({
      id: "score-fallback",
      document_id: "mock-doc-123",
      score: 75,
      breakdown: [],
      kb_version: "mock_kb",
      is_fallback: true,
      computed_at: new Date().toISOString(),
    });

    render(<DocumentDashboardPage params={{ id: "mock-doc-123" }} />);

    await waitFor(() => {
      expect(screen.getByTestId("fallback-warning-banner")).toBeInTheDocument();
      expect(screen.getByText("Showing sample data — live analysis unavailable")).toBeInTheDocument();
    });
  });

  it("does NOT render FallbackWarningBanner when real live data is returned", async () => {
    vi.spyOn(api, "getDocument").mockResolvedValue({
      id: "mock-doc-123",
      user_id: "demo-user",
      filename: "Live Policy.pdf",
      document_type: "health_insurance",
      storage_path: "docs/live.pdf",
      status: "analyzed",
      pipeline_stage: "Complete",
      uploaded_at: new Date().toISOString(),
      is_fallback: false,
    });

    vi.spyOn(api, "getSummary").mockResolvedValue({
      id: "sum-live",
      document_id: "mock-doc-123",
      language: "en",
      coverage: ["Live coverage"],
      exclusions: ["Live exclusion"],
      key_fees: ["Live fees"],
      waiting_periods: ["Live waiting"],
      notable_terms: ["Live terms"],
      model_version: "gemini-2.5-flash",
      is_fallback: false,
      generated_at: new Date().toISOString(),
    });

    vi.spyOn(api, "getRedFlags").mockResolvedValue({
      document_id: "mock-doc-123",
      count: 0,
      red_flags: [],
      is_fallback: false,
    });

    vi.spyOn(api, "getConfidenceScore").mockResolvedValue({
      id: "score-live",
      document_id: "mock-doc-123",
      score: 85,
      breakdown: [],
      kb_version: "live_kb",
      is_fallback: false,
      computed_at: new Date().toISOString(),
    });

    render(<DocumentDashboardPage params={{ id: "mock-doc-123" }} />);

    await waitFor(() => {
      expect(screen.queryByTestId("fallback-warning-banner")).not.toBeInTheDocument();
    });
  });
});
