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
  ExternalLink,
  Award,
} from "lucide-react";
import { CitationItem } from "@/types";
import { sendChatMessage } from "@/lib/api";
import { useTranslation } from "@/lib/useTranslation";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: CitationItem[];
  suggestedPolicies?: string[];
  isFallback?: boolean;
  timestamp: string;
}

export default function ChatPage({
  params,
}: {
  params: { id: string };
}) {
  const routeParams = useParams();
  const docId = (params?.id || routeParams?.id || "") as string;
  const { t, lang } = useTranslation();

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
      const response = await sendChatMessage(docId, question, lang);

      // Detect fallback pattern
      const isFallback =
        response.content.toLowerCase().includes("not found") ||
        response.content.includes("नहीं मिली") ||
        (response.citations.length === 0 &&
          response.content.toLowerCase().includes("contact the issuer"));

      const assistantMessage: Message = {
        id: response.id || `asst_${Date.now()}`,
        role: "assistant",
        content: response.content,
        citations: response.citations,
        suggestedPolicies: response.suggested_policies_referenced,
        isFallback,
        timestamp: response.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error("Chat error:", err);
      setError(
        lang === "hi"
          ? "उत्तर उत्पन्न करने में समस्या आई। कृपया पुनः प्रयास करें।"
          : "Failed to generate answer. Please try again."
      );
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
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-140px)] min-h-[550px] animate-fade-in">
      {/* Top Header */}
      <div className="bg-canvas rounded-3xl p-5 shadow-sm border border-ink/10 flex items-center justify-between gap-4 mb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href={`/doc/${docId}`}
            className="w-9 h-9 rounded-2xl bg-canvas-soft hover:bg-canvas-soft/80 flex items-center justify-center text-ink transition-colors border border-ink/10"
            title={t.chat.backToDash}
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-black text-ink tracking-tight flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary-deep" />
              <span>{t.chat.pageTitle}</span>
            </h1>
            <p className="text-xs text-body">
              {t.chat.pageSubtitle}
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs font-bold text-positive-deep bg-positive/10 px-3 py-1.5 rounded-2xl border border-positive/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Dual-Context Grounded</span>
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 bg-canvas rounded-3xl border border-ink/10 shadow-sm p-4 sm:p-6 overflow-y-auto space-y-6">
        {messages.length === 0 ? (
          /* Empty / Welcome State */
          <div className="text-center py-10 max-w-lg mx-auto space-y-5 animate-fade-in">
            <div className="w-14 h-14 rounded-3xl bg-primary-pale text-positive-deep mx-auto flex items-center justify-center shadow-xs">
              <Bot className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-lg font-black text-ink">
                {lang === "hi" ? "आपकी पॉलिसी और तुलना के लिए एआई सहायक" : "Grounded Policy & Comparison Assistant"}
              </h2>
              <p className="text-xs text-body mt-1 leading-relaxed">
                {t.chat.notGroundedNote}
              </p>
            </div>

            {/* Suggested Question Chips */}
            <div className="text-left space-y-2.5 pt-2">
              <div className="text-[11px] font-bold text-mute uppercase tracking-wider">
                {t.chat.suggestedHeading}
              </div>
              <div className="grid grid-cols-1 gap-2">
                {t.chat.suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    className="w-full text-left p-3 rounded-2xl bg-canvas-soft hover:bg-primary-pale hover:border-primary/40 border border-ink/10 text-xs font-semibold text-ink transition-all flex items-center justify-between group shadow-xs"
                  >
                    <span>{q}</span>
                    <Send className="w-3.5 h-3.5 text-mute group-hover:text-primary-deep transition-colors flex-shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Messages Timeline */
          <div className="space-y-6">
            {messages.map((msg) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${
                    isUser ? "justify-end" : "justify-start"
                  }`}
                >
                  {!isUser && (
                    <div className="w-8 h-8 rounded-2xl bg-primary-pale text-positive-deep flex items-center justify-center flex-shrink-0 mt-0.5 shadow-xs border border-primary/20">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] sm:max-w-[75%] rounded-3xl p-4 sm:p-5 text-xs leading-relaxed space-y-3 ${
                      isUser
                        ? "bg-primary text-ink font-semibold rounded-tr-sm shadow-xs"
                        : msg.isFallback
                        ? "bg-warning/10 border border-warning/30 text-ink rounded-tl-sm shadow-xs"
                        : "bg-canvas-soft/80 border border-ink/10 text-ink rounded-tl-sm shadow-xs"
                    }`}
                  >
                    {/* Message Body */}
                    <div className="whitespace-pre-wrap leading-relaxed">
                      {msg.content}
                    </div>

                    {/* Suggested Policy Badges Referenced */}
                    {msg.suggestedPolicies && msg.suggestedPolicies.length > 0 && (
                      <div className="border-t border-ink/10 pt-2.5 mt-2 space-y-1.5">
                        <div className="text-[10px] font-bold text-primary-deep uppercase tracking-wider flex items-center gap-1">
                          <Award className="w-3 h-3" />
                          <span>{t.chat.policiesRefHeader}</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.suggestedPolicies.map((pName, pIdx) => (
                            <Link
                              key={pIdx}
                              href={`/doc/${docId}/compare`}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-canvas border border-ink/10 text-[11px] font-bold text-ink hover:bg-primary-pale hover:border-primary/40 transition-colors shadow-xs"
                            >
                              <span>{pName}</span>
                              <ExternalLink className="w-3 h-3 text-mute" />
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Expandable Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="border-t border-ink/10 pt-2.5 mt-2 space-y-2">
                        <div className="text-[10px] font-bold text-mute uppercase tracking-wider">
                          {t.chat.citationsHeader}
                        </div>
                        <div className="space-y-1.5">
                          {msg.citations.map((cite, cIdx) => {
                            const cKey = `${msg.id}_cite_${cIdx}`;
                            const isExpanded = !!expandedCitations[cKey];
                            return (
                              <div
                                key={cKey}
                                className="bg-canvas rounded-2xl p-2.5 border border-ink/10 text-[11px] space-y-1.5"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-bold text-ink flex items-center gap-1">
                                    <BookOpen className="w-3 h-3 text-primary-deep" />
                                    {t.chat.pageLabel} {cite.page_number} &bull; {cite.clause_label || "Policy Clause"}
                                  </span>
                                  <button
                                    onClick={() => toggleCitation(cKey)}
                                    className="text-mute hover:text-ink transition-colors p-0.5"
                                  >
                                    {isExpanded ? (
                                      <ChevronUp className="w-3 h-3" />
                                    ) : (
                                      <ChevronDown className="w-3 h-3" />
                                    )}
                                  </button>
                                </div>

                                {isExpanded && (
                                  <div className="italic font-serif text-body bg-canvas-soft p-2 rounded-xl border border-ink/5 animate-fade-in text-[10px] leading-relaxed">
                                    &ldquo;{cite.quote}&rdquo;
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-2xl bg-canvas border border-ink/10 text-ink flex items-center justify-center flex-shrink-0 mt-0.5 shadow-xs">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Loading / Typing Indicator */}
        {loading && (
          <div className="flex items-center gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-2xl bg-primary-pale text-positive-deep flex items-center justify-center flex-shrink-0 shadow-xs animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-canvas-soft border border-ink/10 p-3.5 rounded-2xl rounded-tl-sm text-xs text-body flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-primary-deep animate-spin" />
              <span>{t.chat.typingIndicator}</span>
            </div>
          </div>
        )}

        {/* Inline Error with Retry */}
        {error && (
          <div className="bg-negative/10 border border-negative/20 text-negative p-3 rounded-2xl text-xs flex items-center justify-between gap-3 animate-fade-in">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={handleRetry}
              className="inline-flex items-center gap-1 font-bold underline hover:no-underline text-xs"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="mt-3 flex items-center gap-2 bg-canvas rounded-3xl p-2 border border-ink/10 shadow-sm focus-within:border-ink/40 transition-colors flex-shrink-0"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={t.chat.inputPlaceholder}
          disabled={loading}
          className="flex-1 bg-transparent px-4 py-2.5 text-xs text-ink placeholder:text-mute focus:outline-hidden disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || loading}
          className="px-4 py-2.5 bg-primary hover:bg-primary-active disabled:opacity-40 disabled:hover:bg-primary text-ink font-bold text-xs rounded-2xl transition-all shadow-xs flex items-center gap-1.5 active:scale-95"
        >
          <span>{t.chat.sendButton}</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
