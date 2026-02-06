'use client';

import type { ReactNode } from 'react';

interface SummaryCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  gradient: 'blue' | 'green' | 'orange' | 'red' | 'purple';
  trend?: { value: number; label: string };
}

const GRADIENT_MAP = {
  blue: 'card-gradient-blue',
  green: 'card-gradient-green',
  orange: 'card-gradient-orange',
  red: 'card-gradient-red',
  purple: 'card-gradient-blue',
} as const;

const ICON_COLOR_MAP = {
  blue: 'text-brand-500 bg-brand-500/10',
  green: 'text-emerald-500 bg-emerald-500/10',
  orange: 'text-orange-500 bg-orange-500/10',
  red: 'text-red-500 bg-red-500/10',
  purple: 'text-purple-500 bg-purple-500/10',
} as const;

const VALUE_COLOR_MAP = {
  blue: 'text-brand-600 dark:text-brand-400',
  green: 'text-emerald-600 dark:text-emerald-400',
  orange: 'text-orange-600 dark:text-orange-400',
  red: 'text-red-600 dark:text-red-400',
  purple: 'text-purple-600 dark:text-purple-400',
} as const;

export default function SummaryCard({ label, value, icon, gradient, trend }: SummaryCardProps) {
  return (
    <div
      className={`${GRADIENT_MAP[gradient]} rounded-2xl p-5 border border-[var(--border-primary)] card-hover relative overflow-hidden`}
      role="region"
      aria-label={`${label}: ${value}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div
          className={`w-10 h-10 rounded-xl flex items-center justify-center ${ICON_COLOR_MAP[gradient]}`}
          aria-hidden="true"
        >
          {icon}
        </div>
        {trend && (
          <span
            className={`text-xs font-semibold px-2 py-1 rounded-full ${
              trend.value >= 0
                ? 'text-emerald-600 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/30'
                : 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30'
            }`}
            aria-label={`Trend: ${trend.value >= 0 ? '+' : ''}${trend.value}% ${trend.label}`}
          >
            {trend.value >= 0 ? '+' : ''}{trend.value}%
          </span>
        )}
      </div>
      <div className={`text-3xl font-bold font-mono mb-1 ${VALUE_COLOR_MAP[gradient]}`}>
        {value}
      </div>
      <p className="text-sm text-[var(--text-secondary)] font-medium">
        {label}
      </p>
    </div>
  );
}
