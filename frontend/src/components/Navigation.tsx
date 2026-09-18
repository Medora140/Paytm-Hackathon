"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FileText, ChevronDown, Globe, ShieldAlert, ArrowUpRight } from "lucide-react";
import { MOCK_DOCUMENTS_LIST } from "../lib/mockData";

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [docDropdownOpen, setDocDropdownOpen] = useState(false);
  const [currentLang, setCurrentLang] = useState<"en" | "hi">("en");

  // Extract active doc ID from URL if present
  const docIdMatch = pathname?.match(/\/doc\/([^/]+)/);
  const activeDocId = docIdMatch ? docIdMatch[1] : null;

  useEffect(() => {
    const saved = localStorage.getItem("app_language");
    if (saved === "hi" || saved === "en") {
      setCurrentLang(saved);
    }
  }, []);

  const handleLanguageChange = (lang: "en" | "hi") => {
    setCurrentLang(lang);
    localStorage.setItem("app_language", lang);
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: lang }));
  };

  return (
    <header className="sticky top-0 z-50 bg-canvas/95 backdrop-blur border-b border-ink/10 px-4 lg:px-8 py-3.5 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-2xl bg-primary flex items-center justify-center font-black text-ink text-lg tracking-tight group-hover:bg-primary-active transition-colors shadow-sm">
              W
            </div>
            <span className="font-extrabold text-xl tracking-tight text-ink">
              Docs<span className="text-primary font-black">Decoded</span>
            </span>
          </Link>

          {/* Primary Nav Links */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-semibold text-ink">
            <Link
              href="/upload"
              className={`px-3.5 py-2 rounded-2xl transition-colors ${
                pathname === "/upload"
                  ? "bg-canvas-soft text-ink"
                  : "hover:bg-canvas-soft/60 text-body hover:text-ink"
              }`}
            >
              Upload
            </Link>
            <Link
              href="/documents"
              className={`px-3.5 py-2 rounded-2xl transition-colors ${
                pathname === "/documents"
                  ? "bg-canvas-soft text-ink"
                  : "hover:bg-canvas-soft/60 text-body hover:text-ink"
              }`}
            >
              My Documents
            </Link>
          </nav>
        </div>

        {/* Right tools: Document Switcher + Language Toggle + CTA */}
        <div className="flex items-center gap-3">
          {/* Document Switcher Dropdown */}
          <div className="relative">
            <button
              onClick={() => setDocDropdownOpen(!docDropdownOpen)}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-2xl border border-ink/20 hover:border-ink/50 bg-canvas transition-all text-ink shadow-sm"
              title="Switch Active Document"
            >
              <FileText className="w-3.5 h-3.5 text-body" />
              <span className="max-w-[130px] md:max-w-[180px] truncate">
                {activeDocId
                  ? MOCK_DOCUMENTS_LIST.find((d) => d.id === activeDocId)?.filename || "Active Policy"
                  : "Select Policy"}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-mute" />
            </button>

            {docDropdownOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-canvas rounded-2xl shadow-xl border border-ink/10 p-2 z-50">
                <div className="text-[11px] font-bold text-mute uppercase px-3 py-1 tracking-wider">
                  Switch Document
                </div>
                {MOCK_DOCUMENTS_LIST.map((doc) => (
                  <button
                    key={doc.id}
                    onClick={() => {
                      setDocDropdownOpen(false);
                      router.push(`/doc/${doc.id}`);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between transition-colors ${
                      doc.id === activeDocId
                        ? "bg-primary-pale font-bold text-ink"
                        : "hover:bg-canvas-soft text-body hover:text-ink"
                    }`}
                  >
                    <div className="truncate mr-2">
                      <div className="font-semibold truncate">{doc.filename}</div>
                      <div className="text-[10px] text-mute">{doc.issuer_name}</div>
                    </div>
                    {doc.confidence_score && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-canvas border border-ink/10 font-bold">
                        {doc.confidence_score}
                      </span>
                    )}
                  </button>
                ))}
                <div className="border-t border-ink/10 mt-1 pt-1">
                  <Link
                    href="/upload"
                    onClick={() => setDocDropdownOpen(false)}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs font-bold text-ink hover:bg-canvas-soft flex items-center justify-between"
                  >
                    <span>+ Upload New Policy</span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-mute" />
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Language Switcher */}
          <div className="flex items-center bg-canvas-soft p-1 rounded-2xl border border-ink/10 text-xs font-bold">
            <button
              onClick={() => handleLanguageChange("en")}
              className={`px-2 py-1 rounded-xl transition-colors ${
                currentLang === "en"
                  ? "bg-canvas text-ink shadow-xs"
                  : "text-mute hover:text-ink"
              }`}
            >
              EN
            </button>
            <button
              onClick={() => handleLanguageChange("hi")}
              className={`px-2 py-1 rounded-xl transition-colors ${
                currentLang === "hi"
                  ? "bg-canvas text-ink shadow-xs"
                  : "text-mute hover:text-ink"
              }`}
            >
              हिंदी
            </button>
          </div>

          {/* Upload CTA pill */}
          <Link
            href="/upload"
            className="hidden sm:inline-flex items-center justify-center px-4 py-2 bg-primary hover:bg-primary-active text-ink font-bold text-xs rounded-2xl transition-all shadow-sm active:scale-95"
          >
            Upload Policy
          </Link>
        </div>
      </div>
    </header>
  );
}
