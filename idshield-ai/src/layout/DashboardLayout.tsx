import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
  currentTab: string;
  setCurrentTab: (tab: string) => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  currentTab,
  setCurrentTab,
}) => {
  return (
    <div className="min-h-screen w-full bg-slate-950 cyber-grid flex flex-col font-sans text-slate-200">
      {/* Tactical SOC Command Header */}
      <Header onNavigateToScreen={() => setCurrentTab('screen')} />

      {/* Workspace Body */}
      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950/80 backdrop-blur-[2px]">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
