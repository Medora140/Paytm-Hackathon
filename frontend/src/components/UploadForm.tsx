"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileText,
  AlertCircle,
  RefreshCw,
  CheckCircle2,
  Sparkles,
  Shield,
  Bot,
  Zap,
} from "lucide-react";
import { uploadDocument } from "@/lib/api";
import { useTranslation } from "@/lib/useTranslation";

interface UploadFormProps {
  initialLowConfidence?: boolean;
}

export default function UploadForm({
  initialLowConfidence = false,
}: UploadFormProps) {
  const router = useRouter();
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState(false);
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
      const stageTimer1 = setTimeout(() => setCurrentStageIndex(1), 500);
      const stageTimer2 = setTimeout(() => setCurrentStageIndex(2), 1000);
      const stageTimer3 = setTimeout(() => setCurrentStageIndex(3), 1600);

      // Upload file directly; backend AI automatically identifies the document category
      const response = await uploadDocument(file);

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      setCurrentStageIndex(3);

      setTimeout(() => {
        router.push(`/doc/${response.id}`);
      }, 500);
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
          <span>AI Clause Reasoning & Benchmark Engine</span>
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
            <h2 className="text-xl font-black text-ink">Analyzing Your Document</h2>
            <p className="text-xs text-body">
              Auto-identifying document type, extracting Hindi/English text, chunking clauses, and checking market alternatives
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
        /* Drag & Drop Area with AI Auto-Identification Badge */
        <div className="space-y-6">
          {/* AI Feature Pill */}
          <div className="bg-canvas rounded-2xl p-4 border border-ink/10 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-ink font-semibold">
              <Zap className="w-4 h-4 text-primary-deep" />
              <span>AI Auto-Classification</span>
            </div>
            <div className="flex items-center gap-4 text-mute text-[11px]">
              <span className="flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-positive-deep" /> Insurance, Loans & Contracts
              </span>
              <span className="flex items-center gap-1">
                <FileText className="w-3.5 h-3.5 text-primary-deep" /> Auto-detected clauses
              </span>
            </div>
          </div>

          {/* Drag & Drop Area */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-3xl p-10 sm:p-14 text-center cursor-pointer transition-all bg-canvas shadow-xs ${
              dragActive
                ? "border-primary bg-primary-pale/30 scale-[1.01]"
                : "border-ink/20 hover:border-ink/40"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <div className="flex flex-col items-center justify-center space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-primary-pale flex items-center justify-center text-primary-deep transition-transform group-hover:scale-105">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <div className="text-base font-extrabold text-ink">
                  {t.upload.dragDropText}
                </div>
                <div className="text-xs text-body">
                  {t.upload.dragDropSubtext}
                </div>
              </div>
              <button
                type="button"
                className="mt-2 inline-flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl transition-all shadow-xs"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>{t.upload.uploadButton}</span>
              </button>
            </div>
          </div>

          {/* Privacy & Engine Callout */}
          <div className="text-center text-xs text-mute space-y-1">
            <p>
              ⚡ Supports Hindi (हिंदी) and English PDF policies, scans, and financial contracts.
            </p>
            <p className="text-[11px]">
              Direct guest analysis &bull; DPDP Act 2023 compliant &bull; Instant red-flag detection & market benchmarking
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
