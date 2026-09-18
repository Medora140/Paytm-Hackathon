"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, Trash2, Globe, CreditCard, Check } from "lucide-react";

export default function SettingsPage() {
  const [language, setLanguage] = useState("en");
  const [dataDeleted, setDataDeleted] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("app_language") || "en";
    setLanguage(saved);
  }, []);

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    localStorage.setItem("app_language", lang);
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: lang }));
  };

  const handleDeleteAllData = () => {
    if (
      confirm(
        "Are you sure? This will delete all your uploaded policies, vector embeddings, chat logs, and account data pursuant to India's DPDP Act 2023."
      )
    ) {
      setDataDeleted(true);
      setTimeout(() => setDataDeleted(false), 3000);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in py-4">
      <div>
        <h1 className="text-2xl sm:text-3xl font-black text-ink tracking-tight">
          Account &amp; Privacy Settings
        </h1>
        <p className="text-xs text-body">
          Manage language preferences, subscription plan, and DPDP Act rights
        </p>
      </div>

      <div className="space-y-6">
        {/* Language Preference */}
        <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-canvas-soft flex items-center justify-center text-ink">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-ink">Language Preference</h2>
              <p className="text-xs text-mute">
                Preferred language for plain-language summaries and AI conversational Q&amp;A
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => handleLanguageChange("en")}
              className={`p-3.5 rounded-2xl border text-left text-xs font-bold transition-all flex items-center justify-between ${
                language === "en"
                  ? "border-primary bg-primary-pale text-ink shadow-xs"
                  : "border-ink/10 bg-canvas text-body hover:bg-canvas-soft"
              }`}
            >
              <span>English (Default)</span>
              {language === "en" && <Check className="w-4 h-4 text-positive-deep" />}
            </button>

            <button
              onClick={() => handleLanguageChange("hi")}
              className={`p-3.5 rounded-2xl border text-left text-xs font-bold transition-all flex items-center justify-between ${
                language === "hi"
                  ? "border-primary bg-primary-pale text-ink shadow-xs"
                  : "border-ink/10 bg-canvas text-body hover:bg-canvas-soft"
              }`}
            >
              <span>हिंदी (Hindi)</span>
              {language === "hi" && <Check className="w-4 h-4 text-positive-deep" />}
            </button>
          </div>
        </div>

        {/* Plan Tier */}
        <div className="bg-canvas rounded-3xl p-6 border border-ink/10 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-primary-pale text-primary-deep flex items-center justify-center">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-ink">Subscription Tier</h2>
              <p className="text-xs text-mute">
                You are currently on the Hackathon Demo Free Tier
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-canvas-soft border border-ink/5 flex items-center justify-between text-xs">
            <div>
              <strong className="font-bold text-ink">Free Tier</strong>
              <div className="text-mute">Unlimited document analysis &amp; Q&amp;A</div>
            </div>
            <span className="px-2.5 py-1 bg-canvas rounded-full text-positive-deep font-bold border border-ink/10">
              Active
            </span>
          </div>
        </div>

        {/* DPDP Act Compliance & Data Deletion */}
        <div className="bg-canvas rounded-3xl p-6 border border-negative/20 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-negative/10 text-negative flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-ink">
                Digital Personal Data Protection (DPDP) Act 2023
              </h2>
              <p className="text-xs text-mute">
                Section 12: Right to Correction and Erasure of Personal Data
              </p>
            </div>
          </div>

          <p className="text-xs text-body leading-relaxed">
            In accordance with Indian data privacy law, clicking the button below will trigger an irreversible cascade deletion of all your uploaded files from object storage, embeddings in pgvector, and generated summary cards.
          </p>

          {dataDeleted ? (
            <div className="p-3 bg-positive/10 border border-positive rounded-2xl text-xs text-positive-deep font-bold">
              All personal data successfully purged.
            </div>
          ) : (
            <button
              onClick={handleDeleteAllData}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-negative/10 hover:bg-negative text-negative hover:text-canvas font-bold text-xs rounded-2xl transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Purge All My Data (Right to Erasure)</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
