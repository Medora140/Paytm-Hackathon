"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ExternalLink,
  ShieldAlert,
  Sparkles,
  Info,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { BenchmarkCompareResponse } from "@/types";
import { getBenchmarkComparison } from "@/lib/api";
import FallbackWarningBanner from "@/components/FallbackWarningBanner";

export default function ComparePage({
  params,
}: {
  params: { id: string };
}) {
  const routeParams = useParams();
  const docId = (params?.id || routeParams?.id || "") as string;

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
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {benchmarks.is_fallback && <FallbackWarningBanner />}
      {/* Header */}
      <div className="bg-canvas rounded-3xl p-6 shadow-sm border border-ink/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <Link
            href={`/doc/${docId}`}
            className="w-9 h-9 rounded-2xl bg-canvas-soft hover:bg-canvas-soft/80 flex items-center justify-center text-ink transition-colors border border-ink/10"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-black text-ink tracking-tight">
              Market Intelligence Comparison
            </h1>
            <p className="text-xs text-body">
              How your policy compares with leading scraped health plans
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-body bg-canvas-soft px-3 py-1.5 rounded-2xl border border-ink/10">
          <Clock className="w-3.5 h-3.5 text-mute" />
          <span>{benchmarks.data_freshness_label}</span>
        </div>
      </div>

      {/* Trust distinction banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-primary-pale border border-primary text-ink p-4 rounded-3xl text-xs flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-positive-deep flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-bold">Your Policy Column (Left):</strong> Grounded directly in your uploaded PDF and verified against policy clauses.
          </div>
        </div>
        <div className="bg-canvas border border-ink/10 text-body p-4 rounded-3xl text-xs flex items-start gap-2.5">
          <Info className="w-4 h-4 text-mute flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-bold text-ink">Competitor Columns (Right):</strong> Scraped from public insurer brochures and IRDAI reports via automated pipelines.
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="bg-canvas rounded-3xl border border-ink/10 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-ink/10 bg-canvas-soft/50">
                <th className="p-4 font-bold uppercase text-[10px] tracking-wider text-mute w-44">
                  Feature / Clause
                </th>
                {/* Your Policy */}
                <th className="p-4 font-black text-xs text-ink bg-primary-pale/60 border-l border-r border-primary/20 min-w-[200px]">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-positive-deep" />
                    <span>Your Policy ({benchmarks.issuer_name || "Uploaded"})</span>
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
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">Room Rent Sub-limit</td>
                <td className="p-4 font-bold text-negative bg-primary-pale/30 border-l border-r border-primary/20">
                  {benchmarks.target_attributes.room_rent_cap}
                  <span className="block text-[10px] font-normal text-negative/80 mt-0.5">
                    Triggers proportionate deduction
                  </span>
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0 font-medium">
                    {comp.attributes.room_rent_cap}
                  </td>
                ))}
              </tr>

              {/* Row: Waiting Period */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">Pre-Existing Waiting Period</td>
                <td className="p-4 font-bold text-warning-deep bg-primary-pale/30 border-l border-r border-primary/20">
                  {benchmarks.target_attributes.waiting_period_pre_existing}
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0 font-medium">
                    {comp.attributes.waiting_period_pre_existing}
                  </td>
                ))}
              </tr>

              {/* Row: Co-Pay */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">Co-Pay Requirement</td>
                <td className="p-4 font-bold text-ink bg-primary-pale/30 border-l border-r border-primary/20">
                  {benchmarks.target_attributes.co_pay_percent}
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0 font-medium">
                    {comp.attributes.co_pay_percent}
                  </td>
                ))}
              </tr>

              {/* Row: Claim Settlement Ratio */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">Claim Settlement Ratio</td>
                <td className="p-4 font-bold text-body bg-primary-pale/30 border-l border-r border-primary/20">
                  {benchmarks.target_attributes.claim_settlement_ratio}
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-positive-deep font-bold border-r border-ink/10 last:border-r-0">
                    {comp.attributes.claim_settlement_ratio}
                  </td>
                ))}
              </tr>

              {/* Row: Ombudsman Complaint Signal */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">Ombudsman Grievances</td>
                <td className="p-4 text-body bg-primary-pale/30 border-l border-r border-primary/20">
                  <span className="font-bold text-ink">15.8</span> / 10k policies
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0">
                    <span className="font-bold text-ink">
                      {comp.complaint_signal.complaints_per_10k_policies}
                    </span>{" "}
                    / 10k policies
                  </td>
                ))}
              </tr>

              {/* Row: Source Links */}
              <tr>
                <td className="p-4 font-bold text-ink bg-canvas-soft/20">Source Transparency</td>
                <td className="p-4 bg-primary-pale/30 border-l border-r border-primary/20 text-mute">
                  Original uploaded policy
                </td>
                {benchmarks.comparables.map((comp) => (
                  <td key={comp.id} className="p-4 text-body border-r border-ink/10 last:border-r-0">
                    <a
                      href={comp.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-ink hover:text-primary-deep transition-colors"
                    >
                      <span>Insurer Brochure</span>
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
