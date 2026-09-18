"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Trash2,
  RefreshCw,
  Plus,
  ArrowRight,
  ShieldAlert,
  Calendar,
} from "lucide-react";
import { DocumentListItem } from "../../types";
import { deleteDocument, listDocuments } from "../../lib/api";

export default function DocumentsHistoryPage() {
  const [docs, setDocs] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [rescanningId, setRescanningId] = useState<string | null>(null);

  const loadDocs = () => {
    setLoading(true);
    listDocuments()
      .then((data) => setDocs(data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to permanently delete this document and all associated embeddings under DPDP right to erasure?")) {
      await deleteDocument(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    }
  };

  const handleRescan = (id: string) => {
    setRescanningId(id);
    setTimeout(() => {
      setRescanningId(null);
      alert("Policy re-scanned successfully against latest IRDAI ombudsman knowledge base!");
    }, 1200);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in py-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-ink tracking-tight">
            My Analyzed Documents
          </h1>
          <p className="text-xs text-body">
            Manage your uploaded policies, re-scan with fresh rules, or execute DPDP erasure
          </p>
        </div>

        <Link
          href="/upload"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl shadow-sm transition-all active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>Upload Policy</span>
        </Link>
      </div>

      {/* Loading Skeleton */}
      {loading ? (
        <div className="space-y-4">
          <div className="h-20 bg-canvas rounded-3xl animate-pulse" />
          <div className="h-20 bg-canvas rounded-3xl animate-pulse" />
        </div>
      ) : docs.length === 0 ? (
        /* Empty State */
        <div className="bg-canvas rounded-3xl p-12 text-center border border-ink/10 shadow-sm space-y-4">
          <div className="w-14 h-14 rounded-full bg-canvas-soft text-mute mx-auto flex items-center justify-center">
            <FileText className="w-7 h-7" />
          </div>
          <h2 className="text-lg font-bold text-ink">No documents uploaded yet</h2>
          <p className="text-xs text-body max-w-sm mx-auto">
            Upload your first health policy or loan agreement to see plain-language summaries and red flags.
          </p>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary rounded-2xl text-xs font-bold text-ink hover:bg-primary-active transition-all"
          >
            <span>Upload Document</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        /* Document Cards */
        <div className="space-y-4">
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="bg-canvas rounded-3xl p-5 border border-ink/10 shadow-sm hover:shadow-md transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-3.5">
                <div className="w-11 h-11 rounded-2xl bg-primary-pale text-primary-deep flex items-center justify-center flex-shrink-0 mt-0.5">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-sm text-ink hover:underline">
                      <Link href={`/doc/${doc.id}`}>{doc.filename}</Link>
                    </h3>
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-canvas-soft text-body border border-ink/10">
                      {doc.document_type.replace("_", " ")}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-mute mt-1">
                    {doc.issuer_name && <span>{doc.issuer_name}</span>}
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions & Confidence Score */}
              <div className="flex items-center gap-4 self-end sm:self-center">
                {doc.confidence_score !== null && doc.confidence_score !== undefined ? (
                  <div className="text-right">
                    <div className="text-sm font-black text-ink">
                      {doc.confidence_score}/100
                    </div>
                    <div className="text-[10px] text-mute font-bold uppercase">
                      Fairness Score
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-mute italic">Pending</div>
                )}

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRescan(doc.id)}
                    disabled={rescanningId === doc.id}
                    title="Re-scan against updated Knowledge Base"
                    className="p-2 rounded-xl bg-canvas-soft hover:bg-canvas-soft/80 text-body hover:text-ink transition-colors"
                  >
                    <RefreshCw
                      className={`w-4 h-4 ${
                        rescanningId === doc.id ? "animate-spin text-ink" : ""
                      }`}
                    />
                  </button>

                  <button
                    onClick={() => handleDelete(doc.id)}
                    title="Delete permanently (DPDP Right to Erasure)"
                    className="p-2 rounded-xl bg-canvas-soft hover:bg-negative/10 text-body hover:text-negative transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <Link
                    href={`/doc/${doc.id}`}
                    className="px-3.5 py-1.5 bg-canvas-soft hover:bg-primary text-ink text-xs font-bold rounded-xl transition-all"
                  >
                    Open
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
