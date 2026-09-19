"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Send,
  ArrowLeft,
  Sparkles,
  Bot,
  User,
  BookOpen,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { CitationItem } from "@/types";
import { sendChatMessage } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: CitationItem[];
  isFallback?: boolean;
  timestamp: string;
}

const SUGGESTED_QUESTIONS = [
  "What is my room rent limit and are there deductions?",
  "What is the waiting period for pre-existing diseases?",
  "Are day-care procedures covered under this policy?",
  "What are the mandatory co-pay requirements for non-network hospitals?",
];

export default function ChatPage({
  params,
}: {
  params: { id: string };
}) {
  const routeParams = useParams();
  const docId = (params?.id || routeParams?.id || "") as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const toggleCitation = (citationKey: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [citationKey]: !prev[citationKey],
    }));
  };

  const handleSend = async (questionToSend?: string) => {
    const question = questionToSend || inputText.trim();
    if (!question || loading) return;

    setInputText("");
    setError(null);
    setLastQuestion(question);

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: "user",
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await sendChatMessage(docId, question);

      // Detect fallback pattern
      const isFallback =
        response.content.toLowerCase().includes("not found in this document") ||
        response.citations.length === 0 &&
          response.content.toLowerCase().includes("contact the issuer");

      const assistantMessage: Message = {
        id: response.id || `asst_${Date.now()}`,
        role: "assistant",
        content: response.content,
        citations: response.citations,
        isFallback,
        timestamp: response.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error("Chat error:", err);
      setError("Failed to generate answer. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastQuestion) {
      handleSend(lastQuestion);
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-140px)] animate-fade-in">
      {/* Header bar */}
      <div className="bg-canvas rounded-3xl p-4 sm:p-5 shadow-sm border border-ink/10 flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Link
            href={`/doc/${docId}`}
            className="w-9 h-9 rounded-2xl bg-canvas-soft hover:bg-canvas-soft/80 flex items-center justify-center text-ink transition-colors border border-ink/10"
            title="Back to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-base font-black text-ink tracking-tight flex items-center gap-2">
              <span>Policy Q&amp;A Assistant</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary-pale text-positive-deep border border-positive/20">
                Ground Truth
              </span>
            </h1>
            <p className="text-xs text-mute">
              Every answer is verified against your policy clauses with page citations
            </p>
          </div>
        </div>

        <Link
          href={`/doc/${docId}`}
          className="text-xs font-bold text-body hover:text-ink transition-colors hidden sm:block"
        >
          View Dashboard
        </Link>
      </div>

      {/* Message List Area */}
      <div className="flex-1 overflow-y-auto bg-canvas rounded-3xl p-4 sm:p-6 border border-ink/10 shadow-sm space-y-6">
        {/* Empty State: Suggested Questions */}
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto py-8 space-y-6">
            <div className="w-16 h-16 rounded-full bg-primary-pale text-primary-deep flex items-center justify-center">
              <Sparkles className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h2 className="text-lg font-black text-ink">
                Ask anything about your document
              </h2>
              <p className="text-xs text-body">
                Our RAG engine cross-checks the fine print and cites exact clause pages.
              </p>
            </div>

            <div className="w-full space-y-2 text-left">
              <span className="text-[11px] font-bold uppercase tracking-wider text-mute block px-1">
                Suggested questions derived from red flags:
              </span>
              {SUGGESTED_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="w-full text-left p-3 rounded-2xl bg-canvas-soft hover:bg-canvas-soft/80 border border-ink/5 hover:border-ink/20 text-xs font-semibold text-ink transition-all flex items-center justify-between group"
                >
                  <span className="group-hover:text-primary-deep transition-colors">{q}</span>
                  <span className="text-mute group-hover:text-ink text-xs font-mono">↵</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Rendered Messages */}
        {messages.map((msg, msgIdx) => (
          <div
            key={msg.id || msgIdx}
            className={`flex flex-col ${
              msg.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div className="flex items-start gap-2.5 max-w-[85%]">
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-2xl bg-primary flex items-center justify-center text-ink flex-shrink-0 mt-1 shadow-xs">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className="space-y-2">
                {/* Fallback Amber Notice per spec */}
                {msg.isFallback ? (
                  <div
                    data-testid="fallback-alert"
                    className="p-4 rounded-3xl bg-warning/20 border border-warning text-ink text-xs space-y-1.5 leading-relaxed"
                  >
                    <div className="flex items-center gap-1.5 font-bold text-warning-deep">
                      <AlertTriangle className="w-4 h-4" />
                      <span>Not found in this document — you may need to contact the issuer directly</span>
                    </div>
                    <p className="text-body">{msg.content}</p>
                  </div>
                ) : (
                  <div
                    className={`p-4 rounded-3xl text-xs sm:text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-ink text-canvas rounded-tr-md font-medium"
                        : "bg-canvas-soft text-ink rounded-tl-md border border-ink/5"
                    }`}
                  >
                    {msg.content}
                  </div>
                )}

                {/* Inline Expandable Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {msg.citations.map((cite, citeIdx) => {
                      const citeKey = `${msg.id}_cite_${citeIdx}`;
                      const isExpanded = !!expandedCitations[citeKey];
                      return (
                        <div key={citeIdx} className="space-y-1">
                          <button
                            onClick={() => toggleCitation(citeKey)}
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-canvas border border-ink/15 hover:border-ink/40 text-[11px] font-bold text-ink transition-all shadow-2xs hover:bg-primary-pale"
                          >
                            <BookOpen className="w-3 h-3 text-mute" />
                            <span>
                              Page {cite.page_number}, {cite.clause_label || "Clause"}
                            </span>
                            {isExpanded ? (
                              <ChevronUp className="w-3 h-3 text-mute" />
                            ) : (
                              <ChevronDown className="w-3 h-3 text-mute" />
                            )}
                          </button>

                          {isExpanded && (
                            <div className="p-3 bg-canvas border border-ink/10 rounded-2xl text-xs text-body italic font-serif max-w-md animate-fade-in shadow-xs">
                              &ldquo;{cite.quote}&rdquo;
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-2xl bg-canvas-soft border border-ink/10 flex items-center justify-center text-body flex-shrink-0 mt-1">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading Spinner Indicator */}
        {loading && (
          <div className="flex items-start gap-2.5 max-w-[85%]">
            <div className="w-8 h-8 rounded-2xl bg-primary flex items-center justify-center text-ink flex-shrink-0 mt-1 shadow-xs">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-4 rounded-3xl bg-canvas-soft text-ink rounded-tl-md border border-ink/5 flex items-center gap-2 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-ink animate-ping" />
              <span>Cross-referencing policy clauses...</span>
            </div>
          </div>
        )}

        {/* Error State with Retry Button */}
        {error && (
          <div className="p-4 rounded-3xl bg-negative/10 border border-negative/20 text-xs text-negative flex items-center justify-between gap-3">
            <span>{error}</span>
            <button
              onClick={handleRetry}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-canvas border border-negative/30 rounded-xl font-bold text-ink hover:bg-canvas/80 text-[11px]"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Chips (when messages exist) */}
      {messages.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto py-2 px-1">
          {SUGGESTED_QUESTIONS.slice(0, 2).map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              className="text-[11px] font-semibold text-body bg-canvas hover:bg-canvas-soft px-3 py-1.5 rounded-full border border-ink/10 whitespace-nowrap transition-colors flex-shrink-0"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="mt-2 bg-canvas rounded-3xl p-2 sm:p-2.5 border border-ink/10 shadow-sm flex items-center gap-2"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask about room rent, exclusions, co-pay..."
          className="flex-1 bg-transparent px-4 py-2 text-xs sm:text-sm text-ink placeholder:text-mute focus:outline-none"
        />

        <button
          type="submit"
          data-testid="send-btn"
          disabled={!inputText.trim() || loading}
          className="w-10 h-10 rounded-2xl bg-primary hover:bg-primary-active disabled:bg-canvas-soft disabled:text-mute text-ink flex items-center justify-center transition-all shadow-xs active:scale-95 flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
