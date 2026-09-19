import { useState, FC } from 'react';
import { DashboardLayout } from './layout/DashboardLayout';
import { OverviewPage } from './pages/OverviewPage';
import { ScreeningPage } from './pages/ScreeningPage';
import { AnalysisResultPage } from './pages/AnalysisResultPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ReportModal } from './pages/ReportModal';
import { LoginPage } from './components/LoginPage';
import { DetailedAnalysis } from './types';

export interface OfficerSession {
  badgeId: string;
  name: string;
  clearance: string;
}

export const App: FC = () => {
  const [currentUser, setCurrentUser] = useState<OfficerSession | null>(() => {
    const saved = sessionStorage.getItem('idshield_session');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [isReportOpen, setIsReportOpen] = useState<boolean>(false);
  const [activeInspection, setActiveInspection] = useState<DetailedAnalysis | null>(null);

  const handleLoginSuccess = (officer: OfficerSession) => {
    sessionStorage.setItem('idshield_session', JSON.stringify(officer));
    setCurrentUser(officer);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('idshield_session');
    setCurrentUser(null);
    setActiveInspection(null);
    setCurrentTab('overview');
  };

  const handleAnalysisSuccess = (result: DetailedAnalysis) => {
    setActiveInspection(result);
    setCurrentTab('analysis');
  };

  const handleAuditDocument = (doc?: DetailedAnalysis) => {
    if (doc) {
      setActiveInspection(doc);
    }
    setCurrentTab('analysis');
  };

  // Gatekeeper: Render LoginPage if unauthenticated
  if (!currentUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <DashboardLayout 
      currentTab={currentTab} 
      setCurrentTab={setCurrentTab}
    >
      {currentTab === 'overview' && (
        <OverviewPage 
          onNavigateToInspection={handleAuditDocument}
          onNavigateToUpload={() => setCurrentTab('screen')}
        />
      )}

      {currentTab === 'screen' && (
        <ScreeningPage onAnalysisSuccess={handleAnalysisSuccess} />
      )}

      {currentTab === 'analysis' && (
        <AnalysisResultPage
          doc={activeInspection}
          onBack={() => setCurrentTab('overview')}
          onOpenReport={() => setIsReportOpen(true)}
          onNavigateToUpload={() => setCurrentTab('screen')}
        />
      )}

      {currentTab === 'analytics' && <AnalyticsPage />}

      {(currentTab === 'suspicious' || currentTab === 'evidence' || currentTab === 'history') && (
        <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-xl space-y-3">
          <h3 className="text-base font-bold text-white capitalize">{currentTab} Queue</h3>
          <p className="text-xs text-slate-400">
            {activeInspection 
              ? `Active audit record: ${activeInspection.id}` 
              : 'No active documents queued in this category.'}
          </p>
          {activeInspection && (
            <button
              onClick={() => setCurrentTab('analysis')}
              className="px-4 py-2 rounded-lg bg-cyan-500 text-slate-950 text-xs font-bold hover:bg-cyan-400 transition-colors"
            >
              Open Active Dossier ({activeInspection.status})
            </button>
          )}
        </div>
      )}

      {currentTab === 'settings' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Investigator Security Profile
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Active session metadata and station credentials
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg bg-rose-950/60 border border-rose-500/50 text-rose-400 text-xs font-mono font-semibold hover:bg-rose-900/60 transition-colors"
            >
              Terminate Session (Logout)
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <span className="block text-[10px] font-mono text-slate-500 uppercase">Operator</span>
              <span className="text-xs font-mono text-slate-200">{currentUser.name}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <span className="block text-[10px] font-mono text-slate-500 uppercase">Badge Number</span>
              <span className="text-xs font-mono text-cyan-400">{currentUser.badgeId}</span>
            </div>
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <span className="block text-[10px] font-mono text-slate-500 uppercase">Security Clearance</span>
              <span className="text-xs font-mono text-emerald-400">Level {currentUser.clearance}</span>
            </div>
          </div>

          <h3 className="text-sm font-bold text-white uppercase tracking-wider pt-2">
            System Heuristic Configuration
          </h3>
          <div className="space-y-2 text-xs text-slate-400">
            <div className="flex justify-between p-3 bg-slate-950 rounded border border-slate-800">
              <span>Tampering Threshold Sensitivity</span>
              <span className="font-mono text-cyan-400">0.85 (Strict)</span>
            </div>
            <div className="flex justify-between p-3 bg-slate-950 rounded border border-slate-800">
              <span>Cryptographic QR Validation</span>
              <span className="font-mono text-emerald-400">Enforced</span>
            </div>
            <div className="flex justify-between p-3 bg-slate-950 rounded border border-slate-800">
              <span>Inference Engine Worker Threads</span>
              <span className="font-mono text-slate-200">16 CUDA Cores</span>
            </div>
          </div>
        </div>
      )}

      {isReportOpen && activeInspection && (
        <ReportModal
          doc={activeInspection}
          onClose={() => setIsReportOpen(false)}
        />
      )}
    </DashboardLayout>
  );
};

export default App;
