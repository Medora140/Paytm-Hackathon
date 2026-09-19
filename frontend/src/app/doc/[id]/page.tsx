"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
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
} from "@/lib/api";
import { DashboardSkeleton } from "@/components/SkeletonLoader";
import ConfidenceScoreWidget from "@/components/ConfidenceScoreWidget";
import SummaryCard from "@/components/SummaryCard";
import RedFlagsPanel from "@/components/RedFlagsPanel";
import BenchmarkStrip from "@/components/BenchmarkStrip";
import FallbackWarningBanner from "@/components/FallbackWarningBanner";
import DocumentProcessingState from "@/components/DocumentProcessingState";

export default function DocumentDashboardPage({
  params,
}: {
  params: { id: string };
}) {
  const routeParams = useParams();
  const docId = (params?.id || routeParams?.id || "") as string;

  const [loading, setLoading] = useState(true);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [document, setDocument] = useState<DocumentDetailResponse | null>(null);
  const [summary, setSummary] = useState<DocumentSummaryResponse | null>(null);
  const [redFlagsData, setRedFlagsData] = useState<RedFlagsResponse | null>(null);
  const [scoreData, setScoreData] = useState<ConfidenceScoreResponse | null>(null);
  const [currentLang, setCurrentLang] = useState<string>("en");

  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollAttemptsRef = useRef<number>(0);
  const MAX_POLL_ATTEMPTS = 45; // 45 * 2s = 90 seconds timeout

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const loadFullDashboard = useCallback(
    async (lang = currentLang) => {
      if (!docId) return;
      try {
        setLoading(true);
        setError(null);

        const [docRes, sumRes, flagsRes, scoreRes] = await Promise.all([
          getDocument(docId),
          getSummary(docId, lang),
          getRedFlags(docId),
          getConfidenceScore(docId),
        ]);

        setDocument(docRes);
        setSummary(sumRes);
        setRedFlagsData(flagsRes);
        setScoreData(scoreRes);
      } catch (err: any) {
        console.error("Dashboard data load error:", err);
        setError(
          err?.message || "Unable to load document analysis. Please try again."
        );
      } finally {
        setLoading(false);
      }
    },
    [docId, currentLang]
  );

  const checkStatus = useCallback(async () => {
    if (!docId) return;
    try {
      setIsChecking(true);
      const docRes = await getDocument(docId);
      setDocument(docRes);

      if (docRes.status === "analyzed") {
        stopPolling();
        await loadFullDashboard(currentLang);
        return;
      }

      if (docRes.status === "failed") {
        stopPolling();
        setError(
          docRes.pipeline_stage ||
            "Document analysis failed during processing. Please try uploading again."
        );
        setLoading(false);
        return;
      }

      pollAttemptsRef.current += 1;
      if (pollAttemptsRef.current >= MAX_POLL_ATTEMPTS) {
        stopPolling();
        await loadFullDashboard(currentLang);
      }
    } catch (err: any) {
      console.warn("Polling status check error:", err);
    } finally {
      setIsChecking(false);
    }
  }, [docId, currentLang, stopPolling, loadFullDashboard]);

  // Initial load and polling setup
  useEffect(() => {
    if (!docId) return;

    let isSubscribed = true;
    pollAttemptsRef.current = 0;

    const initialize = async () => {
      setLoading(true);
      setError(null);
      stopPolling();

      try {
        const docRes = await getDocument(docId);
        if (!isSubscribed) return;

        setDocument(docRes);

        if (docRes.status === "analyzed") {
          // Document already processed: load complete dashboard data immediately
          await loadFullDashboard(currentLang);
        } else if (docRes.status === "failed") {
          setError(
            docRes.pipeline_stage || "Document processing failed."
          );
          setLoading(false);
        } else {
          // Document still in progress: show intermediate state and begin 2s polling
          setLoading(false);
          pollTimerRef.current = setInterval(() => {
            checkStatus();
          }, 2000);
        }
      } catch (err: any) {
        if (!isSubscribed) return;
        console.error("Initial document fetch error:", err);
        setError(err?.message || "Unable to retrieve document metadata.");
        setLoading(false);
      }
    };

    initialize();

    return () => {
      isSubscribed = false;
      stopPolling();
    };
  }, [docId]);

  // Handle language switch
  useEffect(() => {
    const handleLangChange = (e: any) => {
      const newLang = e.detail || "en";
      setCurrentLang(newLang);
      if (document?.status === "analyzed") {
        getSummary(docId, newLang).then((sumRes) => setSummary(sumRes));
      }
    };

    window.addEventListener("languageChanged", handleLangChange);
    return () => window.removeEventListener("languageChanged", handleLangChange);
  }, [docId, document?.status]);

  // Initial loading skeleton before document metadata is retrieved
  if (loading && !document) {
    return <DashboardSkeleton />;
  }

  // Intermediate state: document is being ingested / analyzed
  if (
    document &&
    document.status !== "analyzed" &&
    document.status !== "failed"
  ) {
    return (
      <DocumentProcessingState
        document={document}
        onRefreshNow={checkStatus}
        isChecking={isChecking}
      />
    );
  }

  // Error state
  if (error || !document || !summary || !redFlagsData || !scoreData) {
    return (
      <div className="bg-canvas rounded-3xl p-10 border border-negative/20 text-center space-y-4 shadow-sm max-w-xl mx-auto my-12 animate-fade-in">
        <div className="w-14 h-14 rounded-full bg-negative/10 text-negative mx-auto flex items-center justify-center">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-black text-ink">Unable to load document analysis</h2>
        <p className="text-xs text-body">
          {error || "An unexpected error occurred while communicating with the analysis pipeline."}
        </p>
        <button
          onClick={() => loadFullDashboard(currentLang)}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl transition-all shadow-sm active:scale-95"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Analysis</span>
        </button>
      </div>
    );
  }

  const isAnyFallback = Boolean(
    document?.is_fallback ||
    summary?.is_fallback ||
    redFlagsData?.is_fallback ||
    scoreData?.is_fallback
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Fallback Banner when live backend data is unavailable */}
      {isAnyFallback && <FallbackWarningBanner />}

      {/* Top Header Card */}
      <div className="bg-canvas rounded-3xl p-6 sm:p-8 shadow-sm border border-ink/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-5">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-mute">
              Policy Analysis
            </span>
            <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-primary-pale text-positive-deep border border-positive/20">
              {document.status}
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
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              Analyzed {new Date(document.uploaded_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <Link
            href={`/doc/${docId}/compare`}
            className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-canvas-soft hover:bg-canvas-soft/70 text-ink text-xs font-bold rounded-2xl border border-ink/10 transition-all shadow-xs"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Compare Market</span>
          </Link>

          {/* Primary CTA into Chat */}
          <Link
            href={`/doc/${docId}/chat`}
            className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-primary hover:bg-primary-active text-ink text-xs font-bold rounded-2xl shadow-sm transition-all active:scale-95"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Ask a question about this document</span>
          </Link>
        </div>
      </div>

      {/* Market Benchmark Strip */}
      <BenchmarkStrip documentId={docId} />

      {/* Core Grid: Confidence Score + Plain-Language Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ConfidenceScoreWidget
          scoreData={scoreData}
          redFlagsCount={redFlagsData.count}
        />
        <div className="lg:col-span-2">
          <SummaryCard summary={summary} />
        </div>
      </div>

      {/* Red Flags Panel */}
      <RedFlagsPanel redFlags={redFlagsData.red_flags} />
    </div>
  );
}
