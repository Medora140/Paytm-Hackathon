import React from "react";
import { AlertCircle } from "lucide-react";

export default function DisclaimerBanner() {
  return (
    <aside
      aria-label="Compliance disclaimer"
      className="bg-canvas-soft border-b border-ink/10 text-body text-xs py-2 px-4 flex items-center justify-center gap-2 text-center"
    >
      <AlertCircle className="w-4 h-4 text-warning-deep flex-shrink-0" />
      <span>
        <strong>Regulatory & Compliance Notice:</strong> Not financial or legal
        advice — always confirm with the policy issuer before signing or claiming.
      </span>
    </aside>
  );
}
