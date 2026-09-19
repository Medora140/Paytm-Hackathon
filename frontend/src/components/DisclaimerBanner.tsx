"use client";

import React from "react";
import { AlertCircle } from "lucide-react";
import { useTranslation } from "@/lib/useTranslation";

export default function DisclaimerBanner() {
  const { t } = useTranslation();

  return (
    <aside
      aria-label="Compliance disclaimer"
      className="bg-canvas-soft border-b border-ink/10 text-body text-xs py-2 px-4 flex items-center justify-center gap-2 text-center"
    >
      <AlertCircle className="w-4 h-4 text-warning-deep flex-shrink-0" />
      <span>
        <strong>{t.nav.disclaimerHighlight}:</strong> {t.nav.disclaimer}
      </span>
    </aside>
  );
}
