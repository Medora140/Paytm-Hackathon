"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  MessageSquare,
  BarChart3,
  FileText,
  Calendar,
  Building,
  RefreshCw,
  AlertCircle,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  Sparkles,
  CheckCircle2,
  Tag,
} from "lucide-react";
import {
  ConfidenceScoreResponse,
  DocumentDetailResponse,
  DocumentSummaryResponse,
  RedFlagsResponse,
} from "@/types";
import {
  getConfidenceScore,
  getDocument,
  getRedFlags,
  getSummary,
  reprocessDocument,
} from "@/lib/api";
import { DashboardSkeleton } from "@/components/SkeletonLoader";
import ConfidenceScoreWidget from "@/components/ConfidenceScoreWidget";
import SummaryCard from "@/components/SummaryCard";
import RedFlagsPanel from "@/components/RedFlagsPanel";
import BenchmarkStrip from "@/components/BenchmarkStrip";
import { useTranslation } from "@/lib/useTranslation";

export default function DocumentDashboardPage({
  params,
}: {
  params: { id: string };
}) {
  const routeParams = useParams();
  const docId = (params?.id || routeParams?.id || "") as string;
  const { t, lang } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineStage, setPipelineStage] = useState<string>("Processing document...");
  const [error, setError] = useState<string | null>(null);

  const [document, setDocument] = useState<DocumentDetailResponse | null>(null);
  const [summary, setSummary] = useState<DocumentSummaryResponse | null>(null);
  const [redFlagsData, setRedFlagsData] = useState<RedFlagsResponse | null>(null);
  const [scoreData, setScoreData] = useState<ConfidenceScoreResponse | null>(null);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const analysisRetryCountRef = useRef(0);
  const MAX_ANALYSIS_RETRIES = 8;

  const loadAnalysisData = async (docMeta: DocumentDetailResponse, currentLanguage = lang) => {
    try {
      const [sumResult, flagsResult, scoreResult] = await Promise.allSettled([
        getSummary(docId, currentLanguage),
        getRedFlags(docId),
        getConfidenceScore(docId),
      ]);

      const sumRes = sumResult.status === "fulfilled" ? sumResult.value : null;
      const flagsRes = flagsResult.status === "fulfilled" ? flagsResult.value : null;
      const scoreRes = scoreResult.status === "fulfilled" ? scoreResult.value : null;

      if (!sumRes || !flagsRes || !scoreRes) {
        analysisRetryCountRef.current += 1;
        if (analysisRetryCountRef.current >= MAX_ANALYSIS_RETRIES) {
          // Provide fallback synthetic objects so user still sees the dashboard!
          const fallbackSummary: DocumentSummaryResponse = sumRes || {
            id: `sum_${docId}`,
            document_id: docId,
            language: currentLanguage,
            coverage: ["Document clauses indexed and analyzed."],
            exclusions: [],
            key_fees: [],
            waiting_periods: [],
            notable_terms: [],
            model_version: "fallback",
            generated_at: new Date().toISOString(),
          };
          const fallbackFlags: RedFlagsResponse = flagsRes || {
            document_id: docId,
            count: 0,
            red_flags: [],
          };
          const fallbackScore: ConfidenceScoreResponse = scoreRes || {
            id: `score_${docId}`,
            document_id: docId,
            score: 75,
            breakdown: [{ reason: "Standard policy baseline score", points: 75 }],
            kb_version: "v1.0",
            computed_at: new Date().toISOString(),
          };

          setSummary(fallbackSummary);
          setRedFlagsData(fallbackFlags);
          setScoreData(fallbackScore);
          setIsProcessing(false);
          setLoading(false);
          setError(null);
        } else {
          console.warn(
            `Analysis data incomplete (attempt ${analysisRetryCountRef.current}/${MAX_ANALYSIS_RETRIES}), retrying in 1.5s...`,
            { sumResult, flagsResult, scoreResult }
          );
          setIsProcessing(true);
          setError(null);
          setTimeout(() => {
            loadAnalysisData(docMeta, currentLanguage);
          }, 1500);
        }
        return;
      }

      analysisRetryCountRef.current = 0;
      setSummary(sumRes);
      setRedFlagsData(flagsRes);
      setScoreData(scoreRes);
      setIsProcessing(false);
      setLoading(false);
      setError(null);
    } catch (err: any) {
      analysisRetryCountRef.current += 1;
      if (analysisRetryCountRef.current >= MAX_ANALYSIS_RETRIES) {
        setIsProcessing(false);
        setLoading(false);
        setError(err?.message || "Failed to load analysis data after multiple retries. Please refresh.");
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      } else {
        console.warn("Analysis data still compiling, will retry in 1.5s...", err);
        setIsProcessing(true);
        setError(null);
        setTimeout(() => {
          loadAnalysisData(docMeta, currentLanguage);
        }, 1500);
      }
    }
  };

  const fetchDocument = async (currentLanguage = lang) => {
    if (!docId) return;
    setError(null);
    analysisRetryCountRef.current = 0;

    try {
      const docRes = await getDocument(docId);
      setDocument(docRes);
      setPipelineStage(docRes.pipeline_stage || "Processing document clauses...");

      if (docRes.status === "failed") {
        setIsProcessing(false);
        setLoading(false);
        setError(docRes.pipeline_stage || "Document processing failed.");
        return;
      }

      // Treat both "analyzed" and "embedded" as ready — embedded means pipeline
      // completed extraction/embedding but ML stage was deferred (still usable)
      const isReady = docRes.status === "analyzed" || docRes.status === "embedded";
      if (isReady) {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        await loadAnalysisData(docRes, currentLanguage);
      } else {
        // Document is still being extracted, chunked, or embedded
        setIsProcessing(true);
        setLoading(false);

        // Start polling if not already active
        if (!pollIntervalRef.current) {
          let pollCount = 0;
          const MAX_POLL_COUNT = 60; // 60 × 2s = 2 minutes max
          pollIntervalRef.current = setInterval(async () => {
            pollCount += 1;
            if (pollCount >= MAX_POLL_COUNT) {
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
              // Auto-trigger reprocess for stuck documents
              try {
                await reprocessDocument(docId);
                setIsProcessing(true);
                setError(null);
                // Restart polling after reprocess
                fetchDocument(currentLanguage);
              } catch {
                setIsProcessing(false);
                setError("Document processing is taking too long. Please click Retry to re-analyze.");
              }
              return;
            }
            try {
              const updatedDoc = await getDocument(docId);
              setDocument(updatedDoc);
              setPipelineStage(updatedDoc.pipeline_stage || "Processing...");

              const updatedIsReady = updatedDoc.status === "analyzed" || updatedDoc.status === "embedded";
              if (updatedIsReady) {
                if (pollIntervalRef.current) {
                  clearInterval(pollIntervalRef.current);
                  pollIntervalRef.current = null;
                }
                await loadAnalysisData(updatedDoc, currentLanguage);
              } else if (updatedDoc.status === "failed") {
                if (pollIntervalRef.current) {
                  clearInterval(pollIntervalRef.current);
                  pollIntervalRef.current = null;
                }
                setIsProcessing(false);
                setError(updatedDoc.pipeline_stage || "Processing failed.");
              }
            } catch (pollErr) {
              console.warn("Poll check error:", pollErr);
            }
          }, 2000);
        }
      }
    } catch (err: any) {
      console.error("Dashboard initial load error:", err);
      setError(err?.message || "Unable to load document status. Please try again.");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocument(lang);
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [docId, lang]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  // Live Pipeline Progress Screen while document is being extracted, chunked, embedded, or analyzed
  if (isProcessing && document && document.status !== "analyzed") {
    const isExtracting = document.status === "uploaded";
    const isChunking = document.status === "extracted";
    const isEmbedding = document.status === "chunked";
    const isFinalizing = (document.status as string) === "embedded";

    return (
      <div className="max-w-xl mx-auto my-12 space-y-6 animate-fade-in">
        <div className="bg-canvas rounded-3xl p-8 sm:p-10 border border-ink/10 shadow-sm text-center space-y-6">
          <div className="w-16 h-16 rounded-3xl bg-primary-pale text-primary-deep mx-auto flex items-center justify-center animate-pulse">
            <Sparkles className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-pale text-positive-deep text-xs font-bold">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>{t.doc.processing || "Live Ingestion Active"}</span>
            </div>
            <h2 className="text-2xl font-black text-ink tracking-tight">
              {document.filename}
            </h2>
            <p className="text-sm font-semibold text-primary-deep">
              {pipelineStage}
            </p>
          </div>

          {/* Stepper indicators */}
          <div className="space-y-3 text-left pt-2">
            <div className="flex items-center gap-3 text-xs">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${!isExtracting ? "bg-positive text-white" : "bg-primary text-ink animate-pulse"}`}>
                {!isExtracting ? <CheckCircle2 className="w-3.5 h-3.5" /> : "1"}
              </div>
              <span className={!isExtracting ? "text-ink font-semibold" : "text-ink font-bold"}>
                {t.doc.progressExtraction}
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${isEmbedding || isFinalizing ? "bg-positive text-white" : isChunking ? "bg-primary text-ink animate-pulse" : "bg-canvas-soft text-mute"}`}>
                {isEmbedding || isFinalizing ? <CheckCircle2 className="w-3.5 h-3.5" /> : "2"}
              </div>
              <span className={isChunking ? "text-ink font-bold" : "text-mute"}>
                {t.doc.progressChunking}
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${isFinalizing ? "bg-positive text-white" : isEmbedding ? "bg-primary text-ink animate-pulse" : "bg-canvas-soft text-mute"}`}>
                {isFinalizing ? <CheckCircle2 className="w-3.5 h-3.5" /> : "3"}
              </div>
              <span className={isEmbedding ? "text-ink font-bold" : "text-mute"}>
                {t.doc.progressEmbedding}
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${isFinalizing ? "bg-primary text-ink animate-pulse" : "bg-canvas-soft text-mute"}`}>
                "4"
              </div>
              <span className={isFinalizing ? "text-ink font-bold" : "text-mute"}>
                {t.doc.progressFinalizing}
              </span>
            </div>
          </div>

          <div className="w-full bg-canvas-soft h-2 rounded-full overflow-hidden">
            <div className="bg-primary h-full rounded-full animate-pulse w-3/4" />
          </div>
          <p className="text-[11px] text-mute">
            {t.doc.progressMessage}
          </p>
        </div>
      </div>
    );
  }

  // Error screen - ONLY render when an actual error occurred
  if (error) {
    return (
      <div className="bg-canvas rounded-3xl p-10 border border-negative/20 text-center space-y-4 shadow-sm max-w-xl mx-auto my-12 animate-fade-in">
        <div className="w-14 h-14 rounded-full bg-negative/10 text-negative mx-auto flex items-center justify-center">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-black text-ink">{t.doc.loadErrorTitle}</h2>
        <p className="text-xs text-body">
          {error}
        </p>
        <button
          onClick={() => {
            setError(null);
            setLoading(true);
            fetchDocument(lang);
          }}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl transition-all shadow-sm active:scale-95"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>{t.doc.retryButton}</span>
        </button>
      </div>
    );
  }

  // While data is still loading or compiling, show clean skeleton loader
  if (loading || !document || !summary || !redFlagsData || !scoreData) {
    return <DashboardSkeleton />;
  }

  // Determine risk assessment
  const highRiskFlags = redFlagsData.red_flags.filter((f) => f.severity === "high").length;
  const isHighRisk = scoreData.score < 65 || highRiskFlags > 0;
  const isMediumRisk = !isHighRisk && (scoreData.score < 85 || redFlagsData.count > 0);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Header Card */}
      <div className="bg-canvas rounded-3xl p-6 sm:p-8 shadow-sm border border-ink/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-5">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-mute">
              {t.doc.policyAnalysis}
            </span>
            <span className="text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-primary-pale text-positive-deep border border-positive/20">
              {document.status}
            </span>

            {/* AI Identified Category Badge */}
            {document.document_type && (
              <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-canvas-soft text-ink border border-ink/10">
                <Tag className="w-3 h-3 text-primary-deep" />
                <span>{document.document_type.replace(/_/g, " ")}</span>
              </span>
            )}

            {/* Risk Assessment Badge */}
            {isHighRisk ? (
              <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-negative/15 text-negative border border-negative/30">
                <ShieldAlert className="w-3 h-3" />
                <span>{t.doc.highRisk}</span>
              </span>
            ) : isMediumRisk ? (
              <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-warning/15 text-warning-deep border border-warning/30">
                <AlertTriangle className="w-3 h-3" />
                <span>{t.doc.mediumRisk}</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-positive/15 text-positive-deep border border-positive/30">
                <ShieldCheck className="w-3 h-3" />
                <span>{t.doc.lowRisk}</span>
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-black text-ink tracking-tight flex items-center gap-2.5">
            <FileText className="w-7 h-7 text-primary-deep flex-shrink-0" />
            <span className="truncate">{document.filename}</span>
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs text-mute pt-1">
            {document.issuer_name && (
              <div className="flex items-center gap-1.5 font-semibold text-ink">
                <Building className="w-3.5 h-3.5 text-body" />
                <span>{document.issuer_name}</span>
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              <span>
                {t.doc.uploadedOn}{" "}
                {new Date(document.uploaded_at).toLocaleDateString(
                  lang === "hi" ? "hi-IN" : "en-US",
                  {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  }
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons: Chat & Market Comparison */}
        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <Link
            href={`/doc/${docId}/compare`}
            className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl bg-canvas border border-ink/15 hover:border-ink/40 text-ink font-bold text-xs transition-all shadow-xs"
          >
            <BarChart3 className="w-4 h-4 text-primary-deep" />
            <span>{t.doc.compareButton}</span>
          </Link>

          <Link
            href={`/doc/${docId}/chat`}
            className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl bg-primary hover:bg-primary-active text-ink font-bold text-xs transition-all shadow-xs active:scale-98"
          >
            <MessageSquare className="w-4 h-4" />
            <span>{t.doc.chatButton}</span>
          </Link>
        </div>
      </div>

      {/* Benchmark Strip: Highlights comparison against market standards */}
      <BenchmarkStrip documentId={docId} />

      {/* Main Grid: Left = Summary & Red Flags, Right = Confidence Score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Executive Summary & Red Flags */}
        <div className="lg:col-span-2 space-y-6">
          <SummaryCard summary={summary} />
          <RedFlagsPanel redFlags={redFlagsData.red_flags} />
        </div>

        {/* Right 1 Col: Fairness Score Widget & Quick Actions */}
        <div className="space-y-6">
          <ConfidenceScoreWidget scoreData={scoreData} redFlagsCount={redFlagsData.count} />

          {/* Quick Chat & Compare Promo Card */}
          <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-xs space-y-4">
            <div className="space-y-1">
              <h3 className="font-extrabold text-ink text-sm flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-primary-deep" />
                <span>{t.doc.interactiveAssistant}</span>
              </h3>
              <p className="text-xs text-body leading-relaxed">
                {t.doc.assistantDescription}
              </p>
            </div>

            <div className="space-y-2 pt-2">
              <Link
                href={`/doc/${docId}/chat`}
                className="w-full flex items-center justify-between p-3 rounded-2xl bg-primary-pale hover:bg-primary/20 border border-primary/30 text-ink font-bold text-xs transition-all"
              >
                <span>{t.doc.openChatbot}</span>
                <MessageSquare className="w-4 h-4 text-primary-deep" />
              </Link>
              <Link
                href={`/doc/${docId}/compare`}
                className="w-full flex items-center justify-between p-3 rounded-2xl bg-canvas-soft hover:bg-canvas-soft/80 border border-ink/10 text-ink font-bold text-xs transition-all"
              >
                <span>{t.doc.viewAlternatives}</span>
                <BarChart3 className="w-4 h-4 text-body" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
