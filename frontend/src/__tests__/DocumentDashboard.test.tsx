import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import DocumentDashboardPage from "../app/doc/[id]/page";
import * as api from "../lib/api";
import {
  MOCK_CONFIDENCE_SCORE,
  MOCK_DOCUMENT_DETAIL,
  MOCK_RED_FLAGS,
  MOCK_SUMMARY,
} from "../lib/mockData";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }),
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Document Dashboard / Summary Page - States and Features", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton states while data is loading", () => {
    // Return pending promise
    vi.spyOn(api, "getDocument").mockReturnValue(new Promise(() => {}));
    vi.spyOn(api, "getSummary").mockReturnValue(new Promise(() => {}));
    vi.spyOn(api, "getRedFlags").mockReturnValue(new Promise(() => {}));
    vi.spyOn(api, "getConfidenceScore").mockReturnValue(new Promise(() => {}));

    render(<DocumentDashboardPage params={{ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }} />);

    expect(screen.getByTestId("dashboard-skeleton")).toBeInTheDocument();
  });

  it("renders full dashboard with confidence score, plain-language summary, and red flags with page citations", async () => {
    vi.spyOn(api, "getDocument").mockResolvedValue(MOCK_DOCUMENT_DETAIL);
    vi.spyOn(api, "getSummary").mockResolvedValue(MOCK_SUMMARY);
    vi.spyOn(api, "getRedFlags").mockResolvedValue(MOCK_RED_FLAGS);
    vi.spyOn(api, "getConfidenceScore").mockResolvedValue(MOCK_CONFIDENCE_SCORE);

    render(<DocumentDashboardPage params={{ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }} />);

    // Check document header
    await waitFor(() => {
      expect(screen.getByText("Star_Health_Optima_Policy.pdf")).toBeInTheDocument();
    });

    // Check Confidence Score
    expect(screen.getByText("68")).toBeInTheDocument();
    expect(screen.getByText(/Below-average fairness/i)).toBeInTheDocument();

    // Check plain language summary items
    expect(
      screen.getByText(/In-patient hospitalisation expenses up to Sum Insured/i)
    ).toBeInTheDocument();
    // Switch to Exclusions tab to view exclusions
    const exclusionsTab = screen.getByRole("button", { name: /Exclusions/i });
    fireEvent.click(exclusionsTab);
    expect(
      screen.getByText(/Permanent exclusion on cosmetic/i)
    ).toBeInTheDocument();

    // Check red flags & page citations
    expect(screen.getByText(/Clause 4.2 - Room Rent Sub-limits/i)).toBeInTheDocument();
    expect(screen.getByText(/Page 14/i)).toBeInTheDocument();
    expect(screen.getByText(/High Severity/i)).toBeInTheDocument();

    // Check Chat CTA
    expect(
      screen.getByRole("link", { name: /Ask a question about this document/i })
    ).toBeInTheDocument();
  });

  it("handles partial success state when 0 red flags are detected", async () => {
    vi.spyOn(api, "getDocument").mockResolvedValue(MOCK_DOCUMENT_DETAIL);
    vi.spyOn(api, "getSummary").mockResolvedValue(MOCK_SUMMARY);
    vi.spyOn(api, "getRedFlags").mockResolvedValue({
      document_id: "doc_clean",
      count: 0,
      red_flags: [],
    });
    vi.spyOn(api, "getConfidenceScore").mockResolvedValue({
      ...MOCK_CONFIDENCE_SCORE,
      score: 95,
      breakdown: [{ reason: "Standard terms confirmed", points: 95 }],
    });

    render(<DocumentDashboardPage params={{ id: "doc_clean" }} />);

    await waitFor(() => {
      expect(screen.getByText(/No red flags detected/i)).toBeInTheDocument();
    });
    expect(
      screen.getByText(/This policy aligns well with standard regulatory protections/i)
    ).toBeInTheDocument();
  });

  it("renders non-technical error state with retry button on API failure", async () => {
    vi.spyOn(api, "getDocument").mockRejectedValue(new Error("Database connection lost"));
    vi.spyOn(api, "getSummary").mockRejectedValue(new Error("Database connection lost"));
    vi.spyOn(api, "getRedFlags").mockRejectedValue(new Error("Database connection lost"));
    vi.spyOn(api, "getConfidenceScore").mockRejectedValue(new Error("Database connection lost"));

    render(<DocumentDashboardPage params={{ id: "doc_err" }} />);

    await waitFor(() => {
      expect(screen.getByText(/Unable to load document analysis/i)).toBeInTheDocument();
    });

    const retryBtn = screen.getByRole("button", { name: /Retry Analysis/i });
    expect(retryBtn).toBeInTheDocument();
  });
});
