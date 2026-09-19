"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  FileCheck2,
  MessageSquare,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Globe,
} from "lucide-react";
import { useTranslation } from "@/lib/useTranslation";

export default function LandingPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-16 py-6 animate-fade-in">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-6 pt-6 sm:pt-12">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-canvas border border-ink/10 text-xs font-bold text-ink shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-primary-deep" />
          <span>{t.home.heroBadge}</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black text-ink tracking-tight leading-[1.08]">
          {t.home.heroTitlePrefix}{" "}
          <span className="text-primary-deep">{t.home.heroTitleHighlight}</span>{" "}
          {t.home.heroTitleSuffix}
        </h1>

        <p className="text-base sm:text-lg text-body max-w-2xl mx-auto leading-relaxed">
          {t.home.heroSubtitle}
        </p>

        {/* CTA Strip */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            href="/upload"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-primary hover:bg-primary-active text-ink font-extrabold text-base rounded-3xl shadow-sm transition-all active:scale-95"
          >
            <span>{t.home.ctaUpload}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Trust Strip */}
      <section className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-xs max-w-5xl mx-auto flex flex-wrap items-center justify-around gap-6 text-center text-xs font-bold text-body">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-positive-deep" />
          <span>IRDAI &amp; RBI Ombudsman Grounding</span>
        </div>
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-primary-deep" />
          <span>English &amp; हिंदी Multilingual OCR</span>
        </div>
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-warning-deep" />
          <span>Live Market Benchmarking Intelligence</span>
        </div>
      </section>

      {/* 4-Card Feature Strip */}
      <section className="max-w-6xl mx-auto space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-2xl sm:text-3xl font-black text-ink tracking-tight">
            {t.home.trustTitle}
          </h2>
          <p className="text-xs sm:text-sm text-body">
            Empirical reasoning over clauses instead of generic summaries
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1 */}
          <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-3 hover:shadow-md transition-all">
            <div className="w-11 h-11 rounded-2xl bg-negative/10 text-negative flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-ink">
              {t.home.feat1Title}
            </h3>
            <p className="text-xs text-body leading-relaxed">
              {t.home.feat1Desc}
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-3 hover:shadow-md transition-all">
            <div className="w-11 h-11 rounded-2xl bg-primary-pale text-positive-deep flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-ink">
              {t.home.feat2Title}
            </h3>
            <p className="text-xs text-body leading-relaxed">
              {t.home.feat2Desc}
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-3 hover:shadow-md transition-all">
            <div className="w-11 h-11 rounded-2xl bg-accent-cyan/20 text-ink flex items-center justify-center">
              <MessageSquare className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-ink">
              {t.home.feat3Title}
            </h3>
            <p className="text-xs text-body leading-relaxed">
              {t.home.feat3Desc}
            </p>
          </div>

          {/* Card 4 */}
          <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-3 hover:shadow-md transition-all">
            <div className="w-11 h-11 rounded-2xl bg-primary/20 text-ink flex items-center justify-center">
              <Globe className="w-5 h-5 text-primary-deep" />
            </div>
            <h3 className="text-base font-bold text-ink">
              {t.home.feat4Title}
            </h3>
            <p className="text-xs text-body leading-relaxed">
              {t.home.feat4Desc}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
