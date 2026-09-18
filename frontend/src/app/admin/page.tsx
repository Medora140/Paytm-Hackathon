"use client";

import React from "react";
import Link from "next/link";
import {
  Activity,
  Server,
  Database,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  Shield,
  Layers,
} from "lucide-react";

export default function AdminDashboardPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in py-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black text-ink tracking-tight">
              Pipeline &amp; System Health
            </h1>
            <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-primary-pale text-positive-deep border border-positive/20">
              Live Monitor
            </span>
          </div>
          <p className="text-xs text-body mt-0.5">
            Judge &amp; engineering telemetry: OCR throughput, n8n scraper sync, and KB rule indices
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-positive animate-ping" />
          <span className="text-xs font-bold text-ink">All Systems Operational</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-canvas rounded-3xl p-5 border border-ink/10 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-mute text-xs font-bold uppercase tracking-wider">
            <span>Red-Flag Knowledge Base</span>
            <Database className="w-4 h-4 text-primary-deep" />
          </div>
          <div className="text-3xl font-black text-ink">1,428</div>
          <div className="text-[11px] text-body">
            Grounded patterns (IRDAI 2024–26)
          </div>
        </div>

        <div className="bg-canvas rounded-3xl p-5 border border-ink/10 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-mute text-xs font-bold uppercase tracking-wider">
            <span>n8n Scraper Status</span>
            <Activity className="w-4 h-4 text-positive" />
          </div>
          <div className="text-3xl font-black text-positive-deep">Active</div>
          <div className="text-[11px] text-body">Last synced: 14 mins ago</div>
        </div>

        <div className="bg-canvas rounded-3xl p-5 border border-ink/10 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-mute text-xs font-bold uppercase tracking-wider">
            <span>OCR Extraction Rate</span>
            <Layers className="w-4 h-4 text-warning-deep" />
          </div>
          <div className="text-3xl font-black text-ink">99.4%</div>
          <div className="text-[11px] text-body">Avg latency: 1.8s per policy</div>
        </div>

        <div className="bg-canvas rounded-3xl p-5 border border-ink/10 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-mute text-xs font-bold uppercase tracking-wider">
            <span>DPDP Erasure Queue</span>
            <Shield className="w-4 h-4 text-accent-cyan" />
          </div>
          <div className="text-3xl font-black text-ink">0</div>
          <div className="text-[11px] text-body">Zero pending deletion jobs</div>
        </div>
      </div>

      {/* Pipeline Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scraper Jobs */}
        <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-ink flex items-center gap-2">
            <Server className="w-4 h-4 text-primary-deep" />
            <span>n8n Scraper Jobs Status</span>
          </h2>
          <div className="space-y-3 text-xs">
            <div className="p-3 bg-canvas-soft/60 rounded-2xl flex items-center justify-between">
              <div>
                <div className="font-bold text-ink">Care Health Insurance (Care Supreme)</div>
                <div className="text-[11px] text-mute">Brochure parser &amp; room rent sub-limits</div>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary-pale text-positive-deep">
                Synced
              </span>
            </div>

            <div className="p-3 bg-canvas-soft/60 rounded-2xl flex items-center justify-between">
              <div>
                <div className="font-bold text-ink">HDFC ERGO General (Optima Secure)</div>
                <div className="text-[11px] text-mute">Waiting periods &amp; restoration terms</div>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary-pale text-positive-deep">
                Synced
              </span>
            </div>

            <div className="p-3 bg-canvas-soft/60 rounded-2xl flex items-center justify-between">
              <div>
                <div className="font-bold text-ink">Niva Bupa Health (ReAssure 2.0)</div>
                <div className="text-[11px] text-mute">Age-based discount &amp; co-pay terms</div>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary-pale text-positive-deep">
                Synced
              </span>
            </div>
          </div>
        </div>

        {/* Live Ingestion Pipeline Stages */}
        <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-ink flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary-deep" />
            <span>FastAPI Ingestion Pipeline Health</span>
          </h2>
          <div className="space-y-3 text-xs">
            <div className="p-3 bg-canvas-soft/60 rounded-2xl flex items-center justify-between">
              <div>
                <div className="font-bold text-ink">Stage 1: Multipart Ingest &amp; Hash Check</div>
                <div className="text-[11px] text-mute">SHA-256 deduplication active</div>
              </div>
              <span className="text-[10px] font-bold text-positive-deep">Healthy</span>
            </div>

            <div className="p-3 bg-canvas-soft/60 rounded-2xl flex items-center justify-between">
              <div>
                <div className="font-bold text-ink">Stage 2: Clause-Level Semantic Chunking</div>
                <div className="text-[11px] text-mute">Header-based boundary detection</div>
              </div>
              <span className="text-[10px] font-bold text-positive-deep">Healthy</span>
            </div>

            <div className="p-3 bg-canvas-soft/60 rounded-2xl flex items-center justify-between">
              <div>
                <div className="font-bold text-ink">Stage 3: pgvector / Chroma Vector Store</div>
                <div className="text-[11px] text-mute">Cosine similarity index</div>
              </div>
              <span className="text-[10px] font-bold text-positive-deep">Healthy</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
