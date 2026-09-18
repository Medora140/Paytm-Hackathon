import React from "react";

export function SkeletonBox({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-ink/10 rounded-2xl ${className}`}
      aria-hidden="true"
    />
  );
}

export function DashboardSkeleton() {
  return (
    <div
      data-testid="dashboard-skeleton"
      className="space-y-6 max-w-7xl mx-auto animate-fade-in"
    >
      {/* Header bar skeleton */}
      <div className="bg-canvas rounded-3xl p-6 shadow-sm border border-ink/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-2">
          <SkeletonBox className="h-8 w-72" />
          <SkeletonBox className="h-4 w-48" />
        </div>
        <div className="flex gap-3">
          <SkeletonBox className="h-10 w-28 rounded-2xl" />
          <SkeletonBox className="h-10 w-36 rounded-2xl" />
        </div>
      </div>

      {/* Grid: Score Card + Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Card Skeleton */}
        <div className="bg-canvas rounded-3xl p-8 border border-ink/5 space-y-4 flex flex-col items-center">
          <SkeletonBox className="h-6 w-44" />
          <SkeletonBox className="h-28 w-28 rounded-full" />
          <SkeletonBox className="h-4 w-52" />
          <SkeletonBox className="h-16 w-full rounded-2xl mt-4" />
        </div>

        {/* Summary Card Skeleton */}
        <div className="lg:col-span-2 bg-canvas rounded-3xl p-8 border border-ink/5 space-y-4">
          <SkeletonBox className="h-7 w-56" />
          <div className="space-y-3 pt-2">
            <SkeletonBox className="h-5 w-full" />
            <SkeletonBox className="h-5 w-5/6" />
            <SkeletonBox className="h-5 w-4/5" />
            <SkeletonBox className="h-5 w-3/4" />
          </div>
        </div>
      </div>

      {/* Red Flags Panel Skeleton */}
      <div className="bg-canvas rounded-3xl p-8 border border-ink/5 space-y-4">
        <SkeletonBox className="h-7 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <SkeletonBox className="h-40 w-full rounded-3xl" />
          <SkeletonBox className="h-40 w-full rounded-3xl" />
          <SkeletonBox className="h-40 w-full rounded-3xl" />
        </div>
      </div>
    </div>
  );
}
