import React from "react";
import Link from "next/link";
import { TrendingDown, ArrowRight, ExternalLink } from "lucide-react";

interface BenchmarkStripProps {
  documentId: string;
}

export default function BenchmarkStrip({ documentId }: BenchmarkStripProps) {
  return (
    <div className="bg-canvas-soft border border-ink/10 rounded-3xl p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-canvas border border-ink/10 flex items-center justify-center text-warning-deep flex-shrink-0">
          <TrendingDown className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-black uppercase text-ink tracking-wide">
              Market Intelligence Signal
            </span>
            <span className="text-[10px] bg-primary-pale text-positive-deep px-2 py-0.5 rounded-full font-bold">
              Web Scraped
            </span>
          </div>
          <p className="text-xs text-body mt-0.5">
            This policy&apos;s room-rent cap (1% limit) is stricter than <strong>6 of 8</strong> comparable plans in our market index.
          </p>
        </div>
      </div>

      <Link
        href={`/doc/${documentId}/compare`}
        className="inline-flex items-center gap-1.5 px-4 py-2 bg-canvas hover:bg-canvas/80 text-ink text-xs font-bold rounded-2xl border border-ink/10 shadow-xs transition-colors flex-shrink-0"
      >
        <span>Compare with Market</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    </div>
  );
}
