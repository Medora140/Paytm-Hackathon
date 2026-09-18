import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ChatPage from "../app/doc/[id]/chat/page";
import * as api from "../lib/api";
import { MOCK_CHAT_ANSWERS } from "../lib/mockData";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }),
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Conversational Q&A / Chat Page - States and Interactions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty state with pre-populated suggested question chips", () => {
    render(<ChatPage params={{ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }} />);

    expect(screen.getByText(/Ask anything about your document/i)).toBeInTheDocument();
    expect(
      screen.getByText(/What is my room rent limit and are there deductions\?/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/What is the waiting period for pre-existing diseases\?/i)
    ).toBeInTheDocument();
  });

  it("allows user to ask a question, displays cited response, and expands citation chip", async () => {
    vi.spyOn(api, "sendChatMessage").mockResolvedValueOnce(
      MOCK_CHAT_ANSWERS.room_rent
    );

    render(<ChatPage params={{ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }} />);

    const input = screen.getByPlaceholderText(/Ask about room rent, exclusions, co-pay.../i);
    const sendBtn = screen.getByTestId("send-btn");

    fireEvent.change(input, {
      target: { value: "What is my room rent limit?" },
    });
    fireEvent.click(sendBtn);

    // Check user message is rendered
    expect(screen.getByText("What is my room rent limit?")).toBeInTheDocument();

    // Check assistant response
    await waitFor(() => {
      expect(
        screen.getByText(/Yes, your policy has a strict room rent cap/i)
      ).toBeInTheDocument();
    });

    // Check citation chip is present
    const citationChip = screen.getByText(/Page 14, Clause 4.2/i);
    expect(citationChip).toBeInTheDocument();

    // Expand citation chip on click
    fireEvent.click(citationChip);

    // Check source quote appears
    await waitFor(() => {
      expect(
        screen.getByText(/The company's liability for room charges is restricted/i)
      ).toBeInTheDocument();
    });
  });

  it("displays distinct amber fallback state when question topic is not found in document", async () => {
    vi.spyOn(api, "sendChatMessage").mockResolvedValueOnce({
      id: "msg_fallback",
      document_id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
      role: "assistant",
      content:
        "Not found in this document — you may need to contact the issuer directly. The uploaded policy text does not specify cryptocurrency coverage.",
      cited_chunk_ids: [],
      citations: [],
      created_at: new Date().toISOString(),
    });

    render(<ChatPage params={{ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }} />);

    const input = screen.getByPlaceholderText(/Ask about room rent, exclusions, co-pay.../i);
    const sendBtn = screen.getByTestId("send-btn");

    fireEvent.change(input, {
      target: { value: "Does this cover Bitcoin theft?" },
    });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByTestId("fallback-alert")).toBeInTheDocument();
    });

    expect(
      screen.getAllByText(/Not found in this document/i).length
    ).toBeGreaterThan(0);
  });

  it("handles chat error with actionable retry mechanism", async () => {
    vi.spyOn(api, "sendChatMessage").mockRejectedValueOnce(
      new Error("LLM service timeout")
    );

    render(<ChatPage params={{ id: "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d" }} />);

    const input = screen.getByPlaceholderText(/Ask about room rent, exclusions, co-pay.../i);
    const sendBtn = screen.getByTestId("send-btn");

    fireEvent.change(input, {
      target: { value: "Explain the exclusions" },
    });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to generate answer\. Please try again\./i)
      ).toBeInTheDocument();
    });

    const retryBtn = screen.getByRole("button", { name: /Retry/i });
    expect(retryBtn).toBeInTheDocument();
  });
});
