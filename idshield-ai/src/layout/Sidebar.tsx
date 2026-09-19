import React from 'react';
import { 
  LayoutDashboard, 
  ScanSearch, 
  UploadCloud, 
  History, 
  AlertOctagon, 
  BarChart3, 
  ShieldAlert, 
  FileText, 
  Settings 
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'screen', label: 'Upload & Screen', icon: UploadCloud },
    { id: 'analysis', label: 'Detailed Inspection', icon: ScanSearch },
    { id: 'suspicious', label: 'Suspicious Queue', icon: AlertOctagon },
    { id: 'analytics', label: 'Risk Analytics', icon: BarChart3 },
    { id: 'evidence', label: 'Evidence Center', icon: ShieldAlert },
    { id: 'reports', label: 'Audit Reports', icon: FileText },
    { id: 'history', label: 'Verification History', icon: History },
    { id: 'settings', label: 'System Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between p-3 select-none">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[10px] uppercase font-bold tracking-wider text-slate-500">
          Operational Modules
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 text-left ${
                isActive
                  ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/50 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-850 text-xs">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-semibold text-slate-300">Live AI Engine</span>
          <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> READY
          </span>
        </div>
        <div className="text-[10px] text-slate-500">
          OpenCV + ELA + Tesseract pipeline active on port 8000
        </div>
      </div>
    </aside>
  );
};
