"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Lock,
  ArrowRight,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { DocumentType } from "@/types";
import { uploadDocument } from "@/lib/api";

const STAGES = [
  { key: "uploading", label: "Uploading file" },
  { key: "extracting", label: "Extracting text" },
  { key: "analyzing", label: "Analyzing clauses" },
  { key: "ready", label: "Ready" },
];

export default function UploadForm({
  initialLowConfidence = false,
}: {
  initialLowConfidence?: boolean;
}) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState(false);
  const [selectedDocType, setSelectedDocType] =
    useState<DocumentType>("health_insurance");
  const [isUploading, setIsUploading] = useState(false);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lowConfidence] = useState(initialLowConfidence);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    setErrorMessage(null);
    setIsUploading(true);
    setCurrentStageIndex(0);

    try {
      const stageTimer1 = setTimeout(() => setCurrentStageIndex(1), 700);
      const stageTimer2 = setTimeout(() => setCurrentStageIndex(2), 1500);

      const response = await uploadDocument(file, selectedDocType);

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setCurrentStageIndex(3);

      setTimeout(() => {
        router.push(`/doc/${response.id}`);
      }, 800);
    } catch (err: any) {
      setIsUploading(false);
      setErrorMessage(
        err?.message ||
          "We couldn't process your document. Please verify the PDF format and try again."
      );
    }
  };

  const handleRetry = () => {
    setErrorMessage(null);
    setIsUploading(false);
    setCurrentStageIndex(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in py-4">
      {/* Page Title */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-pale text-positive-deep text-xs font-bold mb-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Clause Reasoning Engine</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-ink tracking-tight">
          Upload your financial policy
        </h1>
        <p className="text-sm text-body max-w-lg mx-auto">
          Get a plain-language explanation, IRDAI dispute red flags, and fairness benchmark score in seconds.
        </p>
      </div>

      {/* Low confidence OCR alert */}
      {lowConfidence && (
        <div className="bg-warning/15 border border-warning text-ink p-4 rounded-3xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-warning-deep flex-shrink-0 mt-0.5" />
          <div className="text-xs">
            <strong className="font-bold">
              Low-confidence text extraction detected:
            </strong>{" "}
            This document appears to be a scanned photocopy or handwritten policy schedule. Some clauses may have reduced citation fidelity.
          </div>
        </div>
      )}

      {/* Error State Banner with Retry */}
      {errorMessage ? (
        <div className="bg-canvas rounded-3xl p-8 border border-negative/20 text-center space-y-4 shadow-sm">
          <div className="w-12 h-12 rounded-full bg-negative/10 text-negative mx-auto flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-ink">Upload Failed</h2>
          <p className="text-xs text-body max-w-md mx-auto">
            {errorMessage}
          </p>
          <button
            onClick={handleRetry}
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl transition-all shadow-sm active:scale-95"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      ) : isUploading ? (
        /* Multi-stage loading progress bar */
        <div className="bg-canvas rounded-3xl p-8 border border-ink/10 shadow-sm space-y-6">
          <div className="text-center space-y-1">
            <h2 className="text-xl font-black text-ink">Analyzing Your Policy</h2>
            <p className="text-xs text-body">
              Running OCR, IRDAI ombudsman pattern matching, and benchmark comparison
            </p>
          </div>

          {/* Stepper Progress */}
          <div className="grid grid-cols-4 gap-2 pt-4">
            {STAGES.map((stage, idx) => {
              const isDone = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              return (
                <div key={stage.key} className="flex flex-col items-center text-center space-y-2">
                  <div
                    className={`w-9 h-9 rounded-2xl flex items-center justify-center text-xs font-bold transition-all ${
                      isDone
                        ? "bg-primary text-ink"
                        : isCurrent
                        ? "bg-ink text-primary animate-pulse"
                        : "bg-canvas-soft text-mute border border-ink/10"
                    }`}
                  >
                    {isDone ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                  </div>
                  <span
                    className={`text-[11px] font-semibold ${
                      isCurrent ? "text-ink font-bold" : "text-mute"
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Animated Bar */}
          <div className="w-full bg-canvas-soft h-2.5 rounded-full overflow-hidden">
            <div
              className="bg-primary h-full transition-all duration-500 rounded-full"
              style={{
                width: `${((currentStageIndex + 1) / STAGES.length) * 100}%`,
              }}
            />
          </div>
        </div>
      ) : (
        /* Empty / Ready State Dropzone Form */
        <div className="space-y-6">
          {/* Document Type Selector */}
          <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-3">
            <label className="text-xs font-bold uppercase text-mute tracking-wider block">
              Step 1: Select Document Category
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setSelectedDocType("health_insurance")}
                className={`p-4 rounded-2xl border text-left transition-all ${
                  selectedDocType === "health_insurance"
                    ? "border-primary bg-primary-pale font-bold text-ink shadow-xs"
                    : "border-ink/10 hover:border-ink/30 bg-canvas text-body"
                }`}
              >
                <div className="text-sm font-bold text-ink">Health Insurance</div>
                <div className="text-[11px] text-body mt-0.5">
                  Supported in v1 (IRDAI)
                </div>
              </button>

              <button
                type="button"
                disabled
                className="p-4 rounded-2xl border border-ink/5 bg-canvas-soft/60 text-mute text-left cursor-not-allowed opacity-80"
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold text-body">Loan Agreement</div>
                  <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 bg-canvas rounded-md border border-ink/10">
                    Roadmap
                  </span>
                </div>
                <div className="text-[11px] text-mute mt-0.5">
                  RBI lending benchmarks
                </div>
              </button>

              <button
                type="button"
                disabled
                className="p-4 rounded-2xl border border-ink/5 bg-canvas-soft/60 text-mute text-left cursor-not-allowed opacity-80"
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold text-body">Mutual Fund</div>
                  <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 bg-canvas rounded-md border border-ink/10">
                    Roadmap
                  </span>
                </div>
                <div className="text-[11px] text-mute mt-0.5">
                  SEBI expense ratio audits
                </div>
              </button>
            </div>
          </div>

          {/* Drag & Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`bg-canvas rounded-3xl p-10 border-2 border-dashed transition-all cursor-pointer text-center space-y-4 shadow-sm group ${
              dragActive
                ? "border-primary bg-primary-pale/40"
                : "border-ink/20 hover:border-ink/40"
            }`}
          >
            <input
              ref={fileInputRef}
              data-testid="file-input"
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={handleFileInputChange}
            />

            <div className="w-16 h-16 rounded-full bg-canvas-soft group-hover:bg-primary-pale group-hover:text-ink text-body mx-auto flex items-center justify-center transition-colors">
              <UploadCloud className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <h2 className="text-base font-bold text-ink">
                Drag &amp; drop your policy PDF here
              </h2>
              <p className="text-xs text-mute">
                or click to browse from your computer (PDF up to 25 MB)
              </p>
            </div>

            <div className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl shadow-sm transition-all group-hover:scale-105">
              <span>Choose Policy PDF</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* DigiLocker Button (Coming Soon per spec) */}
          <div className="flex items-center justify-center">
            <button
              type="button"
              disabled
              className="flex items-center gap-2 px-4 py-2 rounded-2xl border border-ink/10 bg-canvas text-mute text-xs font-semibold cursor-not-allowed opacity-75"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Import from DigiLocker (Direct verified fetch — Coming Soon)</span>
            </button>
          </div>

          {/* Privacy & DPDP Notice */}
          <div className="bg-canvas-soft rounded-3xl p-5 border border-ink/10 text-xs text-body flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-positive-deep flex-shrink-0 mt-0.5" />
            <div>
              <strong className="font-bold text-ink">
                Privacy &amp; DPDP Act Guarantee:
              </strong>{" "}
              Your policy document is processed in an encrypted ephemeral sandbox. It is never sold, indexed publicly, or shared with your insurer. You can exercise your full right to erasure anytime with one click in settings.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
