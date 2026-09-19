"use client";

import React, { useState } from "react";
import { AlertOctagon, CheckCircle2, ChevronDown, ChevronUp, BookOpen, HelpCircle } from "lucide-react";
import { RedFlagItem } from "../types";
import { useTranslation } from "../lib/useTranslation";

interface RedFlagsPanelProps {
  redFlags: RedFlagItem[];
}

export default function RedFlagsPanel({ redFlags }: RedFlagsPanelProps) {
  const { t, lang } = useTranslation();
  const [expandedQuotes, setExpandedQuotes] = useState<Record<string, boolean>>({});

  const toggleQuote = (id: string) => {
    setExpandedQuotes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Partial success state: 0 red flags
  if (!redFlags || redFlags.length === 0) {
    return (
      <div className="bg-canvas rounded-3xl p-8 shadow-sm border border-positive/20 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-primary-pale text-positive-deep mx-auto flex items-center justify-center">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-ink">{t.doc.noRedFlagsTitle}</h3>
        <p className="text-sm text-body max-w-lg mx-auto">
          {t.doc.noRedFlagsDesc}
        </p>
      </div>
    );
  }

  const getSeverityBadge = (severity: string) => {
    const isHi = lang === "hi";
    switch (severity.toLowerCase()) {
      case "high":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-negative/10 text-negative border border-negative/20">
            {isHi ? "उच्च जोखिम" : "High Severity"}
          </span>
        );
      case "medium":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-warning/20 text-warning-deep border border-warning/30">
            {isHi ? "मध्यम जोखिम" : "Medium Severity"}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-accent-cyan/20 text-ink border border-accent-cyan/30">
            {isHi ? "कम जोखिम" : "Low Severity"}
          </span>
        );
    }
  };

  return (
    <div className="bg-canvas rounded-3xl p-6 sm:p-8 shadow-sm border border-ink/10 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-2xl bg-negative/10 flex items-center justify-center text-negative">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-ink tracking-tight">
              {t.doc.redFlagsTitle} ({redFlags.length})
            </h2>
            <p className="text-xs text-body">
              {lang === "hi"
                ? "IRDAI/RBI ओम्बड्समैन विवादों में बार-बार खारिज होने वाले क्लॉज"
                : "Clauses with high dispute frequencies in IRDAI/RBI ombudsman cases"}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {redFlags.map((flag) => {
          const isExpanded = !!expandedQuotes[flag.id];
          return (
            <div
              key={flag.id}
              className="bg-canvas-soft/70 hover:bg-canvas-soft border border-ink/10 rounded-3xl p-5 flex flex-col justify-between transition-all hover:shadow-md"
            >
              <div>
                {/* Header: Severity + Page Citation */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  {getSeverityBadge(flag.severity)}
                  <span className="text-xs font-bold text-body bg-canvas px-2.5 py-1 rounded-xl border border-ink/10 flex items-center gap-1">
                    <BookOpen className="w-3 h-3 text-mute" />
                    {t.chat.pageLabel} {flag.page_number}
                  </span>
                </div>

                {/* Clause Title */}
                <h3 className="font-bold text-sm text-ink mb-2">
                  {flag.clause_label || (lang === "hi" ? "विवादित क्लॉज" : "Disputed Clause")}
                </h3>

                {/* Plain-Language Explanation */}
                <p className="text-xs text-body leading-relaxed mb-4">
                  {flag.plain_explanation}
                </p>
              </div>

              {/* Collapsible Source Text + Ombudsman Why It Matters */}
              <div className="border-t border-ink/10 pt-3 mt-auto space-y-2">
                <button
                  onClick={() => toggleQuote(flag.id)}
                  className="w-full flex items-center justify-between text-[11px] font-bold text-ink hover:text-primary-deep transition-colors"
                >
                  <span>
                    {isExpanded
                      ? (lang === "hi" ? "मूल क्लॉज छिपाएं" : "Hide source clause")
                      : (lang === "hi" ? "मूल क्लॉज देखें" : "View source clause quote")}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                </button>

                {isExpanded && (
                  <div className="bg-canvas p-3 rounded-2xl border border-ink/10 text-[11px] text-body italic font-serif leading-relaxed animate-fade-in">
                    &ldquo;{flag.source_text}&rdquo;
                  </div>
                )}

                <div className="flex items-start gap-1.5 text-[11px] text-mute pt-1">
                  <HelpCircle className="w-3.5 h-3.5 flex-shrink-0 text-warning-deep mt-0.5" />
                  <span>
                    Pattern: <strong>{flag.pattern_id || "Ombudsman Repudiation Signal"}</strong>
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
