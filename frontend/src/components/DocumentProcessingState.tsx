"use client";

import React from "react";
import {
  FileText,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  Cpu,
  Layers,
  ShieldCheck,
  Building,
} from "lucide-react";
import { DocumentDetailResponse, DocumentStatus } from "@/types";

interface DocumentProcessingStateProps {
  document: DocumentDetailResponse;
  onRefreshNow?: () => void;
  isChecking?: boolean;
}

export default function DocumentProcessingState({
  document,
  onRefreshNow,
  isChecking = false,
}: DocumentProcessingStateProps) {
  const status = document.status;
  const stageText =
    document.pipeline_stage || "Analyzing policy clauses and generating scores...";

  // Determine stage progress level (0 to 3)
  const getStageIndex = (docStatus: DocumentStatus, stage: string): number => {
    const s = stage.toLowerCase();
    if (docStatus === "analyzed") return 3;
    if (docStatus === "embedded" || s.includes("red flag") || s.includes("score") || s.includes("fairness") || s.includes("audit")) return 3;
    if (docStatus === "chunked" || s.includes("embedding") || s.includes("vector")) return 2;
    if (docStatus === "extracted" || s.includes("chunk") || s.includes("clause")) return 1;
    if (s.includes("extract") || s.includes("ocr")) return 1;
    return 0;
  };

  const currentStageIndex = getStageIndex(status, stageText);

  const stages = [
    {
      label: "Document Verification",
      desc: "Validated format, size & integrity",
      icon: FileText,
    },
    {
      label: "Clause Extraction & OCR",
      desc: "Extracted clauses across all pages",
      icon: Layers,
    },
    {
      label: "Semantic Indexing",
      desc: "Computing 384-d clause embeddings",
      icon: Cpu,
    },
    {
      label: "Fairness & Red Flag Audit",
      desc: "Scanning for sub-limits & waiting periods",
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in py-6">
      {/* Top Header Card */}
      <div className="bg-canvas rounded-3xl p-6 sm:p-8 shadow-sm border border-ink/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-5">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-mute">
              Document Analysis
            </span>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
              Processing In Progress
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-ink tracking-tight flex items-center gap-2.5">
            <FileText className="w-7 h-7 text-primary-deep flex-shrink-0" />
            <span className="truncate">{document.filename}</span>
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-mute pt-0.5">
            {document.issuer_name && (
              <span className="flex items-center gap-1 font-semibold text-body">
                <Building className="w-3.5 h-3.5" />
                {document.issuer_name}
              </span>
            )}
            <span className="font-mono text-[11px] text-mute">
              ID: {document.id.slice(0, 13)}...
            </span>
          </div>
        </div>

        {onRefreshNow && (
          <button
            onClick={onRefreshNow}
            disabled={isChecking}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-canvas-soft hover:bg-canvas-soft/80 text-ink text-xs font-bold rounded-2xl border border-ink/10 transition-all shadow-xs active:scale-95 disabled:opacity-50"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 text-primary-deep ${
                isChecking ? "animate-spin" : ""
              }`}
            />
            <span>{isChecking ? "Checking..." : "Check Status"}</span>
          </button>
        )}
      </div>

      {/* Main Processing Visual Card */}
      <div className="bg-canvas rounded-3xl p-8 sm:p-12 shadow-sm border border-ink/10 text-center relative overflow-hidden">
        {/* Glowing background gradient effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none -z-0" />

        <div className="relative z-10 max-w-xl mx-auto space-y-8">
          {/* Animated Central Scanner */}
          <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
            {/* Outer pulsating rings */}
            <div className="absolute inset-0 rounded-full border-2 border-primary/30 animate-ping opacity-60" />
            <div className="absolute -inset-2 rounded-full border border-primary/20 animate-pulse" />
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-primary-deep via-primary to-primary-pale flex items-center justify-center shadow-lg shadow-primary/20">
              <Sparkles className="w-10 h-10 text-ink animate-bounce" />
            </div>
          </div>

          <div className="space-y-2.5">
            <h2 className="text-2xl font-black text-ink tracking-tight">
              Decoding Your Document...
            </h2>
            <p className="text-xs sm:text-sm text-body leading-relaxed max-w-md mx-auto">
              Our AI and rule engine are auditing each policy clause, detecting hidden
              room rent limits, PED waiting periods, and calculating an impartial fairness score.
            </p>
          </div>

          {/* Live Stage Status Callout */}
          <div className="inline-flex items-center gap-3 px-5 py-3 rounded-2xl bg-primary-pale/40 border border-primary/30 text-ink text-xs font-semibold shadow-xs">
            <RefreshCw className="w-4 h-4 text-primary-deep animate-spin" />
            <span>{stageText}</span>
          </div>

          {/* 4-Stage Visual Stepper */}
          <div className="pt-4 grid grid-cols-1 sm:grid-cols-4 gap-3 text-left">
            {stages.map((stage, idx) => {
              const isCompleted = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              const Icon = stage.icon;

              return (
                <div
                  key={stage.label}
                  className={`p-3.5 rounded-2xl border transition-all ${
                    isCompleted
                      ? "bg-positive/5 border-positive/20 text-ink"
                      : isCurrent
                      ? "bg-primary-pale/60 border-primary/40 shadow-xs text-ink scale-[1.02]"
                      : "bg-canvas-soft/40 border-ink/5 text-mute opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={`w-7 h-7 rounded-xl flex items-center justify-center ${
                        isCompleted
                          ? "bg-positive text-white"
                          : isCurrent
                          ? "bg-primary text-ink"
                          : "bg-ink/10 text-mute"
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4 text-white" />
                      ) : (
                        <Icon className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <span className="text-[10px] font-mono font-bold text-mute">
                      0{idx + 1}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold tracking-tight text-ink">
                    {stage.label}
                  </h4>
                  <p className="text-[10px] text-body mt-0.5 leading-snug">
                    {stage.desc}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Auto-Reload Notification */}
          <div className="pt-2 text-[11px] text-mute flex items-center justify-center gap-2">
            <span className="w-2 h-2 rounded-full bg-positive animate-pulse" />
            <span>
              This page will automatically update as soon as analysis is complete.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
