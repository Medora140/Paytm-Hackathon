"use client";

import React, { useEffect, useState } from "react";
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
  Sparkles,
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

export default function DocumentDashboardPage({
  params,
}: {
  params: { id: string };
}) {
  const routeParams = useParams();
  const docId = (params?.id || routeParams?.id || "") as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [document, setDocument] = useState<DocumentDetailResponse | null>(null);
  const [summary, setSummary] = useState<DocumentSummaryResponse | null>(null);
  const [redFlagsData, setRedFlagsData] = useState<RedFlagsResponse | null>(null);
  const [scoreData, setScoreData] = useState<ConfidenceScoreResponse | null>(null);
  const [currentLang, setCurrentLang] = useState<string>("en");

  const fetchData = async (lang = "en") => {
    if (!docId) return;
    setLoading(true);
    setError(null);
    try {
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
      console.error("Dashboard data fetch error:", err);
      setError(
        err?.message || "Unable to load document analysis. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(currentLang);

    const handleLangChange = (e: any) => {
      const newLang = e.detail || "en";
      setCurrentLang(newLang);
      fetchData(newLang);
    };

    window.addEventListener("languageChanged", handleLangChange);
    return () => window.removeEventListener("languageChanged", handleLangChange);
  }, [docId]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error || !document || !summary || !redFlagsData || !scoreData) {
    return (
      <div className="bg-canvas rounded-3xl p-10 border border-negative/20 text-center space-y-4 shadow-sm max-w-xl mx-auto my-12">
        <div className="w-14 h-14 rounded-full bg-negative/10 text-negative mx-auto flex items-center justify-center">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-black text-ink">Unable to load document analysis</h2>
        <p className="text-xs text-body">
          {error || "An unexpected error occurred while communicating with the analysis pipeline."}
        </p>
        <button
          onClick={() => fetchData(currentLang)}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl transition-all shadow-sm active:scale-95"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Analysis</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
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
