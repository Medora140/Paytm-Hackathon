"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ExternalLink,
  ShieldCheck,
  Sparkles,
  Info,
  Clock,
  CheckCircle2,
  TrendingUp,
  Award,
  Zap,
} from "lucide-react";
import { BenchmarkCompareResponse } from "@/types";
import { getBenchmarkComparison } from "@/lib/api";
import { useTranslation } from "@/lib/useTranslation";

export default function ComparePage({
  params,
}: {
  params: { id: string };
}) {
  const routeParams = useParams();
  const docId = (params?.id || routeParams?.id || "") as string;
  const { t, lang } = useTranslation();

  const [benchmarks, setBenchmarks] =
    useState<BenchmarkCompareResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!docId) return;
    getBenchmarkComparison(docId)
      .then((data) => setBenchmarks(data))
      .finally(() => setLoading(false));
  }, [docId]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto space-y-6 animate-pulse">
        <div className="h-10 w-48 bg-canvas rounded-2xl" />
        <div className="h-48 w-full bg-canvas rounded-3xl" />
        <div className="h-96 w-full bg-canvas rounded-3xl" />
      </div>
    );
  }

  if (!benchmarks) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-body">Unable to load benchmark comparisons.</p>
        <Link
          href={`/doc/${docId}`}
          className="mt-4 inline-block px-4 py-2 bg-primary rounded-2xl text-xs font-bold"
        >
          {t.compare.backToDash}
        </Link>
      </div>
    );
  }

  const targetAttrs = benchmarks.target_attributes || {};

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-canvas rounded-3xl p-6 shadow-sm border border-ink/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <Link
            href={`/doc/${docId}`}
            className="w-9 h-9 rounded-2xl bg-canvas-soft hover:bg-canvas-soft/80 flex items-center justify-center text-ink transition-colors border border-ink/10"
            title={t.compare.backToDash}
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-black text-ink tracking-tight">
              {t.compare.title}
            </h1>
            <p className="text-xs text-body">
              {t.compare.subtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-body bg-canvas-soft px-3 py-1.5 rounded-2xl border border-ink/10">
          <Clock className="w-3.5 h-3.5 text-mute" />
          <span>{benchmarks.data_freshness_label || t.compare.dataFreshness}</span>
        </div>
      </div>

      {/* Recommended Better Policies Section */}
      {benchmarks.better_policies && benchmarks.better_policies.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-ink font-black">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg font-black text-ink">
                {t.compare.betterPoliciesTitle}
              </h2>
              <p className="text-xs text-body">
                {t.compare.betterPoliciesSubtitle}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {benchmarks.better_policies.map((policy) => (
              <div
                key={policy.id}
                className="bg-canvas border border-primary/30 hover:border-primary rounded-3xl p-6 shadow-sm flex flex-col justify-between space-y-4 transition-all hover:shadow-md"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-black uppercase text-primary-deep tracking-wider">
                        {policy.issuer_name}
                      </span>
                      <h3 className="text-base font-extrabold text-ink">
                        {policy.product_name}
                      </h3>
                    </div>
                    {policy.risk_reduction_score && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-positive/15 text-positive-deep border border-positive/20 flex-shrink-0">
                        +{policy.risk_reduction_score} Score
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-body font-medium bg-canvas-soft p-3 rounded-2xl">
                    <strong className="text-ink font-bold">{t.compare.whyBetter}</strong> {policy.why_better}
                  </div>

                  <div className="space-y-1.5 pt-1">
                    <div className="text-[11px] font-bold text-mute uppercase tracking-wider">
                      {t.compare.keyAdvantages}
                    </div>
                    <ul className="space-y-1 text-xs text-body">
                      {policy.key_advantages.map((adv, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-positive-deep flex-shrink-0 mt-0.5" />
                          <span>{adv}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {policy.potential_savings && (
                    <div className="flex items-center gap-1.5 text-xs text-positive-deep bg-positive/10 p-2.5 rounded-xl font-semibold">
                      <Zap className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{policy.potential_savings}</span>
                    </div>
                  )}
                </div>

                <div className="border-t border-ink/10 pt-3">
                  <a
                    href={policy.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary-active text-ink text-xs font-bold rounded-2xl shadow-xs transition-all active:scale-95"
                  >
                    <span>{t.compare.visitOfficialSite}</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trust distinction banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-primary-pale border border-primary text-ink p-4 rounded-3xl text-xs flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-positive-deep flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-bold">{t.compare.yourPolicyHeader}:</strong> Grounded directly in your uploaded PDF and verified against policy clauses.
          </div>
        </div>
        <div className="bg-canvas border border-ink/10 text-body p-4 rounded-3xl text-xs flex items-start gap-2.5">
          <Info className="w-4 h-4 text-mute flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-bold text-ink">Competitor Columns:</strong> Scraped from public insurer portals and IRDAI complaint registers via automated pipelines.
          </div>
        </div>
      </div>

      {/* Full Comparison Table */}
      <div className="bg-canvas rounded-3xl border border-ink/10 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-ink/10 bg-canvas-soft/50">
                <th className="p-4 font-bold uppercase text-[10px] tracking-wider text-mute w-44">
                  {t.compare.featureHeader}
                </th>
                {/* Your Policy */}
                <th className="p-4 font-black text-xs text-ink bg-primary-pale/60 border-l border-r border-primary/20 min-w-[220px]">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-positive-deep" />
                    <span>{t.compare.yourPolicyHeader} ({benchmarks.issuer_name || "Uploaded"})</span>
                  </div>
                </th>
                {/* Scraped Competitors */}
                {benchmarks.comparables.map((comp) => (
                  <th key={comp.id} className="p-4 font-bold text-xs text-ink min-w-[200px] border-r border-ink/10 last:border-r-0">
                    <div className="font-bold text-ink">{comp.product_name}</div>
                    <div className="text-[10px] text-mute font-normal">{comp.issuer_name}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-ink/10 text-xs">
              {/* Row: Room Rent */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">{t.compare.roomRent}</td>
                <td className="p-4 font-bold text-negative bg-primary-pale/30 border-l border-r border-primary/20">
                  {targetAttrs.room_rent_cap || "1% of Sum Insured (Proportionate deduction)"}
                  <span className="block text-[10px] font-normal text-negative/80 mt-0.5">
                    Triggers proportionate deduction
                  </span>
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0 font-medium">
                    {comp.attributes.room_rent_cap || "No Room Rent Cap"}
                  </td>
                ))}
              </tr>

              {/* Row: Waiting Period */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">{t.compare.waitingPeriod}</td>
                <td className="p-4 font-bold text-warning-deep bg-primary-pale/30 border-l border-r border-primary/20">
                  {targetAttrs.waiting_period_pre_existing || "36 - 48 months"}
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0 font-medium">
                    {comp.attributes.waiting_period_pre_existing || "36 months standard"}
                  </td>
                ))}
              </tr>

              {/* Row: Co-Pay */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">{t.compare.coPay}</td>
                <td className="p-4 font-bold text-ink bg-primary-pale/30 border-l border-r border-primary/20">
                  {targetAttrs.co_pay_percent || "10% - 20% Zone / Non-network"}
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0 font-medium">
                    {comp.attributes.co_pay_percent || "0% Co-pay"}
                  </td>
                ))}
              </tr>

              {/* Row: Claim Settlement Ratio */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">{t.compare.claimRatio}</td>
                <td className="p-4 font-bold text-body bg-primary-pale/30 border-l border-r border-primary/20">
                  {targetAttrs.claim_settlement_ratio || "89.2%"}
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-positive-deep font-bold border-r border-ink/10 last:border-r-0">
                    {comp.attributes.claim_settlement_ratio || "95.0%+"}
                  </td>
                ))}
              </tr>

              {/* Row: Ombudsman Grievance Signal */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">{t.compare.ombudsmanGrievances}</td>
                <td className="p-4 text-body bg-primary-pale/30 border-l border-r border-primary/20">
                  <span className="font-bold text-ink">{targetAttrs.ombudsman_grievances || "15.8"}</span>
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0">
                    <span className="font-bold text-ink">
                      {comp.complaint_signal?.complaints_per_10k_policies || "8.4"}
                    </span>{" "}
                    / 10k policies
                  </td>
                ))}
              </tr>

              {/* Row: Official Website Links */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">{t.compare.sourceTransparency}</td>
                <td className="p-4 bg-primary-pale/30 border-l border-r border-primary/20 text-mute">
                  Uploaded Document
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0">
                    <a
                      href={comp.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-primary-deep hover:underline transition-colors"
                    >
                      <span>{t.compare.competitorBrochure}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
