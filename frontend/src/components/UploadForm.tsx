"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Lock,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { DocumentType } from "@/types";
import { uploadDocument } from "@/lib/api";
import { useTranslation } from "@/lib/useTranslation";

export default function UploadForm({
  initialLowConfidence = false,
}: {
  initialLowConfidence?: boolean;
}) {
  const router = useRouter();
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState(false);
  const [selectedDocType, setSelectedDocType] =
    useState<DocumentType>("health_insurance");
  const [isUploading, setIsUploading] = useState(false);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lowConfidence] = useState(initialLowConfidence);

  const stages = [
    { key: "uploading", label: t.upload.stageUploading },
    { key: "extracting", label: t.upload.stageExtracting },
    { key: "chunking", label: t.upload.stageChunking },
    { key: "analyzing", label: t.upload.stageAnalyzing },
  ];

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
      const stageTimer1 = setTimeout(() => setCurrentStageIndex(1), 600);
      const stageTimer2 = setTimeout(() => setCurrentStageIndex(2), 1200);
      const stageTimer3 = setTimeout(() => setCurrentStageIndex(3), 1800);

      const response = await uploadDocument(file, selectedDocType);

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      setCurrentStageIndex(3);

      setTimeout(() => {
        router.push(`/doc/${response.id}`);
      }, 600);
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
          {t.upload.pageTitle}
        </h1>
        <p className="text-sm text-body max-w-lg mx-auto">
          {t.upload.pageSubtitle}
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
              Running multilingual OCR, IRDAI dispute pattern matching, and benchmark comparison
            </p>
          </div>

          {/* Stepper Progress */}
          <div className="grid grid-cols-4 gap-2 pt-4">
            {stages.map((stage, idx) => {
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
                    className={`text-[10px] sm:text-[11px] font-semibold ${
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
                width: `${((currentStageIndex + 1) / stages.length) * 100}%`,
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
              {t.upload.selectDocType}
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
                <div className="text-sm font-bold text-ink">{t.upload.typeHealth}</div>
                <div className="text-[11px] text-body mt-0.5">
                  Supported (IRDAI)
                </div>
              </button>

              <button
                type="button"
                onClick={() => setSelectedDocType("loan")}
                className={`p-4 rounded-2xl border text-left transition-all ${
                  selectedDocType === "loan"
                    ? "border-primary bg-primary-pale font-bold text-ink shadow-xs"
                    : "border-ink/10 hover:border-ink/30 bg-canvas text-body"
                }`}
              >
                <div className="text-sm font-bold text-ink">{t.upload.typeLoan}</div>
                <div className="text-[11px] text-body mt-0.5">
                  Supported (RBI)
                </div>
              </button>

              <button
                type="button"
                onClick={() => setSelectedDocType("mutual_fund")}
                className={`p-4 rounded-2xl border text-left transition-all ${
                  selectedDocType === "mutual_fund"
                    ? "border-primary bg-primary-pale font-bold text-ink shadow-xs"
                    : "border-ink/10 hover:border-ink/30 bg-canvas text-body"
                }`}
              >
                <div className="text-sm font-bold text-ink">{t.upload.typeMf}</div>
                <div className="text-[11px] text-body mt-0.5">
                  Supported (SEBI)
                </div>
              </button>
            </div>
          </div>

          {/* Drag & Drop Area */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`bg-canvas border-2 border-dashed rounded-3xl p-10 sm:p-14 text-center cursor-pointer transition-all ${
              dragActive
                ? "border-primary bg-primary-pale scale-[1.01]"
                : "border-ink/20 hover:border-ink/40 hover:bg-canvas-soft/40 shadow-xs"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <div className="max-w-sm mx-auto space-y-4">
              <div className="w-14 h-14 rounded-3xl bg-primary-pale text-positive-deep mx-auto flex items-center justify-center shadow-xs">
                <UploadCloud className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-base font-bold text-ink">
                  {t.upload.dragDropText}
                </h3>
                <p className="text-xs text-body mt-1">
                  {t.upload.dragDropSubtext}
                </p>
              </div>
              <div className="inline-block px-4 py-2 bg-canvas-soft border border-ink/10 rounded-2xl text-xs font-bold text-ink hover:bg-canvas-soft/80 transition-colors shadow-xs">
                Browse PDF File
              </div>
            </div>
          </div>

          {/* Privacy & Compliance Footer */}
          <div className="bg-canvas rounded-3xl p-5 border border-ink/10 shadow-xs flex items-center gap-3.5 text-xs text-body">
            <ShieldCheck className="w-6 h-6 text-positive-deep flex-shrink-0" />
            <div className="leading-relaxed">
              {t.upload.privacyNote}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
