import React from "react";
import { AlertTriangle } from "lucide-react";

interface FallbackWarningBannerProps {
  message?: string;
}

export default function FallbackWarningBanner({
  message = "Showing sample data — live analysis unavailable",
}: FallbackWarningBannerProps) {
  return (
    <div
      data-testid="fallback-warning-banner"
      className="bg-amber-500/15 border border-amber-500/30 text-amber-900 dark:text-amber-200 px-4 py-3 rounded-2xl flex items-center justify-center gap-2.5 text-xs font-semibold shadow-xs animate-fade-in my-3"
    >
      <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
}
