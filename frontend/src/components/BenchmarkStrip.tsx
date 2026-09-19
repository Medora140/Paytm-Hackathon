"use client";

import React from "react";
import Link from "next/link";
import { TrendingUp, ArrowRight } from "lucide-react";
import { useTranslation } from "../lib/useTranslation";

interface BenchmarkStripProps {
  documentId: string;
}

export default function BenchmarkStrip({ documentId }: BenchmarkStripProps) {
  const { t, lang } = useTranslation();
  const isHi = lang === "hi";

  return (
    <div className="bg-canvas-soft border border-ink/10 rounded-3xl p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-canvas border border-ink/10 flex items-center justify-center text-primary-deep flex-shrink-0">
          <TrendingUp className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-black uppercase text-ink tracking-wide">
              {isHi ? "बाजार तुलना और बेहतर विकल्प" : "Market Intelligence Signal"}
            </span>
            <span className="text-[10px] bg-primary-pale text-positive-deep px-2 py-0.5 rounded-full font-bold">
              Web Scraped &amp; n8n
            </span>
          </div>
          <p className="text-xs text-body mt-0.5">
            {isHi
              ? "आपकी पॉलिसी के क्लॉज की तुलना ऑनलाइन अग्रणी पॉलिसियों (केयर, एचडीएफसी एर्गो, निवा बूपा) से की गई है।"
              : "Compare your policy terms directly against top-rated alternative policies scraped online."}
          </p>
        </div>
      </div>

      <Link
        href={`/doc/${documentId}/compare`}
        className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary-active text-ink text-xs font-bold rounded-2xl shadow-xs transition-colors flex-shrink-0"
      >
        <span>{t.doc.compareCta}</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    </div>
  );
}
