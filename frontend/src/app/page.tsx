import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  FileCheck2,
  MessageSquare,
  ArrowRight,
  ShieldCheck,
  Zap,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { MOCK_DOCUMENT_ID } from "../lib/mockData";

export default function LandingPage() {
  return (
    <div className="space-y-16 py-6 animate-fade-in">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-6 pt-6 sm:pt-12">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-canvas border border-ink/10 text-xs font-bold text-ink shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-primary-deep" />
          <span>Grounded in Real IRDAI &amp; RBI Ombudsman Rulings</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black text-ink tracking-tight leading-[1.08]">
          Understand your policy before you sign —{" "}
          <span className="text-primary-deep">or claim.</span>
        </h1>

        <p className="text-base sm:text-lg text-body max-w-2xl mx-auto leading-relaxed">
          Dense financial clauses hide room-rent caps, proportionate deductions, and surprise exclusions. We decode them in 60 seconds into cited, plain-English answers.
        </p>

        {/* CTA Strip */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            href="/upload"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-primary hover:bg-primary-active text-ink font-extrabold text-base rounded-3xl shadow-sm transition-all active:scale-95"
          >
            <span>Upload a document</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          {/* Sample Document Demo Flow Button */}
          <Link
            href={`/doc/${MOCK_DOCUMENT_ID}`}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-4 bg-canvas hover:bg-canvas-soft text-ink font-bold text-sm rounded-3xl border border-ink/15 shadow-xs transition-colors"
          >
            <Zap className="w-4 h-4 text-warning-deep" />
            <span>Try Sample Document (Star Health 1-Click Demo)</span>
          </Link>
        </div>
      </section>

      {/* Trust Strip */}
      <section className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-xs max-w-5xl mx-auto flex flex-wrap items-center justify-around gap-6 text-center text-xs font-bold text-body">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-positive-deep" />
          <span>IRDAI &amp; RBI Ombudsman Case Grounding</span>
        </div>
        <div className="flex items-center gap-2">
          <FileCheck2 className="w-5 h-5 text-primary-deep" />
          <span>Works on Any PDF, Any Insurer</span>
        </div>
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-warning-deep" />
          <span>Live Market Benchmarking Intelligence</span>
        </div>
      </section>

      {/* 3-Card Feature Strip */}
      <section className="max-w-6xl mx-auto space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-2xl sm:text-3xl font-black text-ink tracking-tight">
            How Docs Decoded Protects You
          </h2>
          <p className="text-xs sm:text-sm text-body">
            Empirical reasoning over clauses instead of generic summaries
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="bg-canvas rounded-3xl p-8 border border-ink/10 shadow-sm space-y-4 hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-2xl bg-primary-pale text-positive-deep flex items-center justify-center">
              <FileCheck2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">
              Plain-Language Breakdown
            </h3>
            <p className="text-xs text-body leading-relaxed">
              Instantly converts 40 pages of legal jargon into clear bullets: what&apos;s covered, what&apos;s excluded, key co-pay percentages, and waiting periods.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-canvas rounded-3xl p-8 border border-ink/10 shadow-sm space-y-4 hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-2xl bg-negative/10 text-negative flex items-center justify-center">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">
              Red-Flag Dispute Detector
            </h3>
            <p className="text-xs text-body leading-relaxed">
              Trained on real ombudsman repudiations to identify sub-limits that silently cut hospital payouts by up to 50% at claim time.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-canvas rounded-3xl p-8 border border-ink/10 shadow-sm space-y-4 hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-2xl bg-accent-cyan/20 text-ink flex items-center justify-center">
              <MessageSquare className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-ink">
              Ask Anything with Citations
            </h3>
            <p className="text-xs text-body leading-relaxed">
              Converse with your policy in natural language. Every answer is backed by an expandable citation showing the exact page and clause quote.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
