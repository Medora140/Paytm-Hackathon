import React, { useState } from "react";
import { Shield, ChevronDown, ChevronUp, AlertTriangle, CheckCircle2 } from "lucide-react";
import { ConfidenceScoreResponse } from "../types";

interface ConfidenceScoreWidgetProps {
  scoreData: ConfidenceScoreResponse;
  redFlagsCount: number;
}

export default function ConfidenceScoreWidget({
  scoreData,
  redFlagsCount,
}: ConfidenceScoreWidgetProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const score = scoreData.score;

  // Determine score color and status
  let scoreBg = "bg-warning/20 border-warning text-warning-content";
  let scoreBadge = "bg-warning/30 text-warning-content";
  let interpretation = `Below-average fairness — ${redFlagsCount} red flags found`;

  if (score >= 80) {
    scoreBg = "bg-positive/10 border-positive text-positive-deep";
    scoreBadge = "bg-primary-pale text-positive-deep";
    interpretation = "High fairness & transparency — standard terms confirmed";
  } else if (score < 50) {
    scoreBg = "bg-negative/10 border-negative text-negative";
    scoreBadge = "bg-negative/20 text-negative-darkest";
    interpretation = `Critical risk — ${redFlagsCount} severe dispute-prone clauses identified`;
  }

  return (
    <div className="bg-canvas rounded-3xl p-6 sm:p-8 shadow-sm border border-ink/10 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-ink font-bold text-base">
            <Shield className="w-5 h-5 text-primary-deep" />
            <span>Fairness & Transparency Score</span>
          </div>
          <span className={`text-[11px] font-extrabold uppercase px-2.5 py-1 rounded-full ${scoreBadge}`}>
            IRDAI Grounded
          </span>
        </div>

        {/* Large Score Gauge */}
        <div className="flex flex-col items-center justify-center my-4 py-3">
          <div
            className={`w-32 h-32 rounded-full border-4 flex flex-col items-center justify-center shadow-inner ${scoreBg}`}
          >
            <span className="text-5xl font-black tracking-tight text-ink">
              {score}
            </span>
            <span className="text-xs font-bold text-mute uppercase tracking-widest mt-0.5">
              out of 100
            </span>
          </div>

          <p className="text-sm font-semibold text-ink text-center mt-4 max-w-xs">
            {interpretation}
          </p>
        </div>
      </div>

      {/* Itemized deduction breakdown toggle */}
      <div className="border-t border-ink/10 pt-4 mt-2">
        <button
          onClick={() => setShowBreakdown(!showBreakdown)}
          className="w-full flex items-center justify-between text-xs font-bold text-body hover:text-ink transition-colors p-2 rounded-xl hover:bg-canvas-soft"
        >
          <span>Why this score? (Itemized breakdown)</span>
          {showBreakdown ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {showBreakdown && (
          <div className="mt-3 space-y-2 text-xs bg-canvas-soft/80 p-3.5 rounded-2xl border border-ink/5 animate-fade-in">
            <div className="text-[10px] font-bold text-mute uppercase tracking-wider mb-2">
              Deduction Breakdown ({scoreData.kb_version})
            </div>
            {scoreData.breakdown.map((item, idx) => (
              <div
                key={idx}
                className="flex items-start justify-between gap-3 py-1 border-b border-ink/5 last:border-0"
              >
                <div className="flex items-start gap-1.5 text-body">
                  {item.points < 0 ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-negative flex-shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-positive flex-shrink-0 mt-0.5" />
                  )}
                  <span>{item.reason}</span>
                </div>
                <span
                  className={`font-mono font-bold flex-shrink-0 ${
                    item.points < 0 ? "text-negative" : "text-positive"
                  }`}
                >
                  {item.points > 0 ? `+${item.points}` : item.points}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
