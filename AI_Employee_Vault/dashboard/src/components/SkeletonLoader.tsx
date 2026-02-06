'use client';

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

function Skeleton({ className = '', style }: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={style}
      role="status"
      aria-label="Loading..."
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-2xl p-5 border border-[var(--border-primary)] animate-fade-in">
      <div className="flex items-start justify-between mb-3">
        <Skeleton className="w-10 h-10 rounded-xl" />
        <Skeleton className="w-12 h-6 rounded-full" />
      </div>
      <Skeleton className="w-20 h-8 mb-2" />
      <Skeleton className="w-28 h-4" />
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 p-4 rounded-xl border border-[var(--border-secondary)]">
      <Skeleton className="w-3 h-3 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="w-3/4 h-4" />
        <Skeleton className="w-1/2 h-3" />
      </div>
      <Skeleton className="w-16 h-6 rounded-full" />
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="rounded-2xl p-6 border border-[var(--border-primary)]">
      <Skeleton className="w-40 h-6 mb-6" />
      <div className="flex items-end gap-2 h-48">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t-md"
            style={{ height: `${30 + Math.random() * 70}%` } as React.CSSProperties}
          />
        ))}
      </div>
    </div>
  );
}

export function SkeletonDashboard() {
  return (
    <div className="space-y-6 animate-fade-in" role="status" aria-label="Loading dashboard">
      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>

      {/* Chart */}
      <SkeletonChart />

      {/* List */}
      <div className="rounded-2xl p-6 border border-[var(--border-primary)] space-y-3">
        <Skeleton className="w-32 h-6 mb-4" />
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    </div>
  );
}

export default Skeleton;
