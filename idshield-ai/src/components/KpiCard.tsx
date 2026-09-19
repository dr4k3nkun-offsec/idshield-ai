import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface KpiCardProps {
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
  subtext: string;
  icon: React.ReactNode;
  sensorCode?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  change,
  isPositive,
  subtext,
  icon,
  sensorCode,
}) => {
  // Derives a tactical sensor node identifier if none provided
  const nodeTag = sensorCode || `NODE-${label.slice(0, 3).toUpperCase()}`;

  return (
    <div className="soc-card hud-corners rounded-sm p-4 transition-all duration-200 group border border-slate-800/80 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.12)]">
      {/* Top Telemetry Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/60 mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono text-slate-500 tracking-widest uppercase">
            {nodeTag}
          </span>
          <span className="inline-block w-1 h-1 rounded-full bg-slate-700 group-hover:bg-cyan-400 transition-colors" />
        </div>
        <div className="p-1.5 rounded bg-slate-950/90 border border-slate-800/90 text-cyan-400 group-hover:border-cyan-500/40 group-hover:shadow-[0_0_10px_rgba(6,182,212,0.2)] transition-all">
          {icon}
        </div>
      </div>

      {/* Primary Value & Tactical Label */}
      <div className="space-y-1">
        <span className="block text-[10px] font-mono tracking-wider uppercase text-slate-400">
          {label}
        </span>
        <div className="flex items-baseline space-x-2">
          <span className="text-3xl font-mono font-bold tracking-tight text-slate-100 tabular-nums">
            {value}
          </span>
        </div>
      </div>

      {/* Telemetry Status Footer */}
      <div className="mt-3.5 pt-2.5 border-t border-slate-800/40 flex items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-1.5 truncate">
          <span
            className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
              isPositive
                ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-400'
                : 'bg-rose-950/60 border-rose-500/30 text-rose-400'
            }`}
          >
            {isPositive ? (
              <TrendingUp className="w-3 h-3 mr-1 shrink-0" />
            ) : (
              <TrendingDown className="w-3 h-3 mr-1 shrink-0" />
            )}
            {change}
          </span>
          <span className="text-[11px] text-slate-500 truncate">{subtext}</span>
        </div>

        <div className="hidden sm:flex items-center space-x-1 text-[9px] text-slate-500 tracking-widest uppercase shrink-0">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>SYNC</span>
        </div>
      </div>
    </div>
  );
};
