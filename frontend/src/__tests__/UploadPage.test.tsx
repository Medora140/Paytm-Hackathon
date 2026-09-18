import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import UploadPage from "../app/upload/page";
import * as api from "../lib/api";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe("Upload Page - States and Flows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the initial empty state with file dropzone, document type selector, and privacy note", () => {
    render(<UploadPage />);

    // Check heading & dropzone
    expect(screen.getByText(/Upload your financial policy/i)).toBeInTheDocument();
    expect(screen.getByText(/Drag & drop your policy PDF/i)).toBeInTheDocument();

    // Check document type selector
    expect(screen.getByText(/Health Insurance/i)).toBeInTheDocument();
    expect(screen.getByText(/Loan Agreement/i)).toBeInTheDocument();
    expect(screen.getByText(/Mutual Fund/i)).toBeInTheDocument();

    // Check DigiLocker coming soon button
    expect(screen.getByText(/Import from DigiLocker/i)).toBeInTheDocument();

    // Check privacy guarantee
    expect(screen.getByText(/Privacy & DPDP Act Guarantee/i)).toBeInTheDocument();
  });

  it("progresses through multi-stage pipeline stages on upload: Uploading -> Extracting text -> Analyzing clauses -> Ready", async () => {
    vi.spyOn(api, "uploadDocument").mockResolvedValueOnce({
      id: "doc_test_123",
      filename: "test_policy.pdf",
      document_type: "health_insurance",
      status: "analyzed",
      storage_path: "documents/doc_test_123/test_policy.pdf",
      uploaded_at: new Date().toISOString(),
    });

    render(<UploadPage />);

    const file = new File(["dummy policy text"], "test_policy.pdf", {
      type: "application/pdf",
    });
    const fileInput = screen.getByTestId("file-input");

    fireEvent.change(fileInput, { target: { files: [file] } });

    // Multi-stage pipeline should be visible
    await waitFor(() => {
      expect(screen.getByText(/Uploading file/i)).toBeInTheDocument();
    });

    // Verify stage text indicators exist
    expect(screen.getByText(/Extracting text/i)).toBeInTheDocument();
    expect(screen.getByText(/Analyzing clauses/i)).toBeInTheDocument();
    expect(screen.getByText(/Ready/i)).toBeInTheDocument();
  });

  it("renders error state when upload fails with actionable retry button", async () => {
    vi.spyOn(api, "uploadDocument").mockRejectedValueOnce(
      new Error("Network connection timed out")
    );

    render(<UploadPage />);

    const file = new File(["dummy policy text"], "failed_policy.pdf", {
      type: "application/pdf",
    });
    const fileInput = screen.getByTestId("file-input");

    fireEvent.change(fileInput, { target: { files: [file] } });

    // Wait for error banner
    await waitFor(() => {
      expect(screen.getByText(/Upload Failed/i)).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Network connection timed out/i)
    ).toBeInTheDocument();

    // Retry button is available
    const retryBtn = screen.getByRole("button", { name: /Try Again/i });
    expect(retryBtn).toBeInTheDocument();

    fireEvent.click(retryBtn);

    // After retry, returns to initial dropzone state
    expect(screen.getByText(/Drag & drop your policy PDF/i)).toBeInTheDocument();
  });

  it("handles low-confidence OCR / scanned document warning", async () => {
    render(<UploadPage searchParams={{ lowConfidence: "true" }} />);

    expect(
      screen.getByText(/Low-confidence text extraction detected/i)
    ).toBeInTheDocument();
  });
});
