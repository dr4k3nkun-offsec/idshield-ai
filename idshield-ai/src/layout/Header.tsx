import { FC, useState } from 'react';
import { ShieldCheck, Bell, Search, Cpu, UploadCloud } from 'lucide-react';

interface HeaderProps {
  onNavigateToScreen?: () => void;
}

export const Header: FC<HeaderProps> = ({ onNavigateToScreen }) => {
  const [officerSession] = useState(() => {
    const raw = sessionStorage.getItem('idshield_session');
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.clearance) {
          return parsed;
        }
      } catch {
        // Fallback to initial state
      }
    }
    return {
      badgeId: 'INV-7029',
      name: 'Gov. Lead Investigator',
      clearance: 'L3',
    };
  });

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between select-none">
      {/* Brand & Platform Architecture */}
      <div className="flex items-center gap-3">
        <div className="relative h-9 w-9 rounded-md bg-slate-900 border border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.25)] flex items-center justify-center text-cyan-400">
          <ShieldCheck className="w-5 h-5" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-mono font-bold tracking-wider text-white uppercase">
              IDSHIELD <span className="text-cyan-400">AI</span>
            </h1>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
              v2.4-PROD
            </span>
          </div>
          <p className="text-[10px] font-mono text-slate-400 leading-tight">
            Identity Fraud Intelligence Platform
          </p>
        </div>
      </div>

      {/* Telemetry Controls & Officer Identity */}
      <div className="flex items-center gap-4">
        {/* Dossier Search Input */}
        <div className="hidden md:flex items-center relative">
          <Search className="w-3.5 h-3.5 absolute left-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search doc ID, hash, or audit key..."
            className="w-72 bg-slate-900/80 border border-slate-800 rounded-md pl-9 pr-8 py-1.5 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition"
          />
          <kbd className="absolute right-2 px-1.5 py-0.5 text-[9px] font-mono text-slate-500 bg-slate-800/60 border border-slate-700/50 rounded">
            /
          </kbd>
        </div>

        {/* Inference Cluster Telemetry */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900/80 border border-slate-800 font-mono text-[11px]">
          <Cpu className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span className="text-slate-500">ENGINE:</span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            ONLINE (CUDA-01)
          </span>
        </div>

        {/* Tactical Screen Action Trigger */}
        {onNavigateToScreen && (
          <button
            onClick={onNavigateToScreen}
            className="px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 rounded-md text-xs font-mono font-semibold tracking-wider uppercase transition-all shadow-[0_0_12px_rgba(6,182,212,0.15)] flex items-center gap-1.5 active:scale-95"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Screen Unit</span>
          </button>
        )}

        {/* Audit Alerts */}
        <button 
          aria-label="Security Audit Alerts"
          className="relative p-2 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-cyan-400 hover:border-slate-700 transition"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.9)]" />
        </button>

        {/* Dynamically Resolved Officer Dossier Badge */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-800">
          <div className="relative w-8 h-8 rounded-md bg-gradient-to-tr from-cyan-950 to-slate-900 border border-cyan-500/50 flex items-center justify-center text-xs font-mono font-bold text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
            {officerSession.clearance}
          </div>
          <div className="hidden sm:block text-left font-mono">
            <div className="text-xs font-semibold text-slate-200 truncate max-w-[150px]">
              {officerSession.name}
            </div>
            <div className="text-[10px] text-cyan-400 flex items-center gap-1">
              <span>{officerSession.badgeId}</span>
              <span className="text-slate-600">|</span>
              <span className="text-emerald-400">CLR-{officerSession.clearance}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
