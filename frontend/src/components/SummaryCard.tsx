"use client";

import React, { useState } from "react";
import { Check, X, Clock, DollarSign, FileText } from "lucide-react";
import { DocumentSummaryResponse } from "../types";
import { useTranslation } from "../lib/useTranslation";

interface SummaryCardProps {
  summary: DocumentSummaryResponse;
}

export default function SummaryCard({ summary }: SummaryCardProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"coverage" | "exclusions" | "fees" | "waiting">("coverage");

  return (
    <div className="bg-canvas rounded-3xl p-6 sm:p-8 shadow-sm border border-ink/10 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-ink tracking-tight">
              {t.doc.summaryTitle}
            </h2>
            <p className="text-xs text-body">
              Instant plain-language extraction ({summary.language.toUpperCase()})
            </p>
          </div>
          <span className="text-[11px] font-bold text-mute bg-canvas-soft px-2.5 py-1 rounded-full border border-ink/10">
            {summary.model_version}
          </span>
        </div>

        {/* Tab Pills */}
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setActiveTab("coverage")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl text-xs font-bold transition-all ${
              activeTab === "coverage"
                ? "bg-primary text-ink shadow-sm"
                : "bg-canvas-soft text-body hover:text-ink"
            }`}
          >
            <Check className="w-3.5 h-3.5" />
            {t.doc.tabCoverage} ({summary.coverage.length})
          </button>
          <button
            onClick={() => setActiveTab("exclusions")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl text-xs font-bold transition-all ${
              activeTab === "exclusions"
                ? "bg-primary text-ink shadow-sm"
                : "bg-canvas-soft text-body hover:text-ink"
            }`}
          >
            <X className="w-3.5 h-3.5" />
            {t.doc.tabExclusions} ({summary.exclusions.length})
          </button>
          <button
            onClick={() => setActiveTab("fees")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl text-xs font-bold transition-all ${
              activeTab === "fees"
                ? "bg-primary text-ink shadow-sm"
                : "bg-canvas-soft text-body hover:text-ink"
            }`}
          >
            <DollarSign className="w-3.5 h-3.5" />
            {t.doc.tabFees} ({summary.key_fees.length})
          </button>
          <button
            onClick={() => setActiveTab("waiting")}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl text-xs font-bold transition-all ${
              activeTab === "waiting"
                ? "bg-primary text-ink shadow-sm"
                : "bg-canvas-soft text-body hover:text-ink"
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            {t.doc.tabWaiting} ({summary.waiting_periods.length})
          </button>
        </div>

        {/* Tab Content List */}
        <div className="space-y-3 min-h-[180px]">
          {activeTab === "coverage" && (
            <ul className="space-y-2.5 animate-fade-in">
              {summary.coverage.length === 0 ? (
                <li className="text-xs text-mute italic p-2">{t.doc.noItemsInTab}</li>
              ) : (
                summary.coverage.map((item, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 text-xs text-ink leading-relaxed p-2.5 rounded-2xl bg-canvas-soft/50 border border-ink/5"
                  >
                    <div className="w-5 h-5 rounded-full bg-primary-pale text-positive-deep flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-3 h-3" />
                    </div>
                    <span>{item}</span>
                  </li>
                ))
              )}
            </ul>
          )}

          {activeTab === "exclusions" && (
            <ul className="space-y-2.5 animate-fade-in">
              {summary.exclusions.length === 0 ? (
                <li className="text-xs text-mute italic p-2">{t.doc.noItemsInTab}</li>
              ) : (
                summary.exclusions.map((item, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 text-xs text-ink leading-relaxed p-2.5 rounded-2xl bg-canvas-soft/50 border border-ink/5"
                  >
                    <div className="w-5 h-5 rounded-full bg-negative/10 text-negative flex items-center justify-center flex-shrink-0 mt-0.5">
                      <X className="w-3 h-3" />
                    </div>
                    <span>{item}</span>
                  </li>
                ))
              )}
            </ul>
          )}

          {activeTab === "fees" && (
            <ul className="space-y-2.5 animate-fade-in">
              {summary.key_fees.length === 0 ? (
                <li className="text-xs text-mute italic p-2">{t.doc.noItemsInTab}</li>
              ) : (
                summary.key_fees.map((item, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 text-xs text-ink leading-relaxed p-2.5 rounded-2xl bg-canvas-soft/50 border border-ink/5"
                  >
                    <div className="w-5 h-5 rounded-full bg-warning/20 text-warning-deep flex items-center justify-center flex-shrink-0 mt-0.5">
                      <DollarSign className="w-3 h-3" />
                    </div>
                    <span>{item}</span>
                  </li>
                ))
              )}
            </ul>
          )}

          {activeTab === "waiting" && (
            <ul className="space-y-2.5 animate-fade-in">
              {summary.waiting_periods.length === 0 ? (
                <li className="text-xs text-mute italic p-2">{t.doc.noItemsInTab}</li>
              ) : (
                summary.waiting_periods.map((item, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 text-xs text-ink leading-relaxed p-2.5 rounded-2xl bg-canvas-soft/50 border border-ink/5"
                  >
                    <div className="w-5 h-5 rounded-full bg-accent-orange/30 text-ink flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Clock className="w-3 h-3" />
                    </div>
                    <span>{item}</span>
                  </li>
                ))
              )}
            </ul>
          )}
        </div>
      </div>

      {/* Notable fine-print footer */}
      {summary.notable_terms && summary.notable_terms.length > 0 && (
        <div className="border-t border-ink/10 pt-4 mt-6 text-xs text-body">
          <div className="font-bold text-ink mb-1.5 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-mute" />
            <span>{t.doc.tabTerms}:</span>
          </div>
          <p className="text-[11px] text-body">
            {summary.notable_terms.join(" • ")}
          </p>
        </div>
      )}
    </div>
  );
}
