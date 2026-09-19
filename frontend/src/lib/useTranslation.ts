"use client";

import { useState, useEffect, useCallback } from "react";
import { Language, translations, TranslationDict } from "./translations";

export function useTranslation() {
  const [lang, setLangState] = useState<Language>("en");

  useEffect(() => {
    const saved = localStorage.getItem("app_language") as Language | null;
    if (saved === "hi" || saved === "en") {
      setLangState(saved);
    }

    const handleLangChange = (e: any) => {
      const newLang = e.detail as Language;
      if (newLang === "hi" || newLang === "en") {
        setLangState(newLang);
      }
    };

    window.addEventListener("languageChanged", handleLangChange);
    return () => window.removeEventListener("languageChanged", handleLangChange);
  }, []);

  const setLang = useCallback((newLang: Language) => {
    setLangState(newLang);
    localStorage.setItem("app_language", newLang);
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: newLang }));
  }, []);

  const t: TranslationDict = translations[lang] || translations.en;

  return { t, lang, setLang };
}
