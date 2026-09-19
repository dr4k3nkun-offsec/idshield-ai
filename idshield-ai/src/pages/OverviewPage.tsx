import { useState, useEffect, FC } from 'react';
import { KpiCard } from '../components/KpiCard';
import { StatusBadge } from '../components/StatusBadge';
import { DetailedAnalysis } from '../types';
import { 
  FileCheck2, 
  ShieldAlert, 
  AlertTriangle, 
  Activity, 
  Timer, 
  CheckCircle2, 
  ArrowUpRight,
  Trash2,
  Inbox
} from 'lucide-react';

interface StatsState {
  scanned: { value: string; change: string; isPositive: boolean };
  verified: { value: string; change: string; isPositive: boolean };
  suspicious: { value: string; change: string; isPositive: boolean };
  highRisk: { value: string; change: string; isPositive: boolean };
  avgRiskScore: { value: string; change: string; isPositive: boolean };
  accuracy: { value: string; change: string; isPositive: boolean };
  processingTime: { value: string; change: string; isPositive: boolean };
  recentDocuments: DetailedAnalysis[];
}

const DEFAULT_STATS: StatsState = {
  scanned: { value: '0', change: '0', isPositive: true },
  verified: { value: '0', change: '0%', isPositive: true },
  suspicious: { value: '0', change: '0%', isPositive: false },
  highRisk: { value: '0', change: '0%', isPositive: false },
  avgRiskScore: { value: '0.0', change: 'Live', isPositive: true },
  accuracy: { value: '0%', change: 'Active', isPositive: true },
  processingTime: { value: '0.0s', change: 'Live', isPositive: true },
  recentDocuments: []
};

export const OverviewPage: FC<{ 
  onNavigateToInspection: (doc?: DetailedAnalysis) => void;
  onNavigateToUpload: () => void;
}> = ({ onNavigateToInspection, onNavigateToUpload }) => {
  const [stats, setStats] = useState<StatsState>(DEFAULT_STATS);

  // Dynamic backend resolution: localhost vs Render cloud
  const isLocalhost = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  const API_BASE = (
    import.meta.env.VITE_API_URL || 
    (isLocalhost ? 'http://127.0.0.1:8000' : 'https://idshield-backend-eiu9.onrender.com')
  ).replace(/\/$/, '');

  const getAuthToken = () => {
    return (
      localStorage.getItem('access_token') ||
      localStorage.getItem('token') ||
      localStorage.getItem('idshield_token') ||
      sessionStorage.getItem('access_token') ||
      sessionStorage.getItem('token') ||
      ''
    );
  };

  const handleClearHistory = async () => {
    try {
      const authToken = getAuthToken();
      const res = await fetch(`${API_BASE}/api/documents/clear`, { 
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (res.ok) {
        setStats(DEFAULT_STATS);
      } else {
        const err = await res.text();
        console.error('Failed to clear records:', err);
      }
    } catch (err) {
      console.error('Clear request error:', err);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadStats = async () => {
      try {
        const authToken = getAuthToken();
        const headers: Record<string, string> = {};
        if (authToken) {
          headers['Authorization'] = `Bearer ${authToken}`;
        }

        const res = await fetch(`${API_BASE}/api/dashboard/stats`, { headers });
        if (res.ok) {
          const data = await res.json();
          if (isMounted) {
            setStats(data);
          }
        }
      } catch {
        // Backend not reached, keeps defaults
      }
    };

    loadStats();

    return () => {
      isMounted = false;
    };
  }, [API_BASE]);

  const totalCount = parseInt(stats.scanned.value, 10) || 0;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Identity Fraud Intelligence Dashboard</h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time neural document classification, OCR validation, and synthetic forgery screening.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {totalCount > 0 && (
            <button
              onClick={handleClearHistory}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-950/60 border border-rose-800/60 text-rose-300 hover:bg-rose-900 transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" /> Clear Records
            </button>
          )}
          <button
            onClick={onNavigateToUpload}
            className="px-3.5 py-1.5 text-xs font-bold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition shadow-lg shadow-cyan-950 cursor-pointer"
          >
            + Upload New Document
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Documents Scanned"
          value={stats.scanned.value}
          change={stats.scanned.change}
          isPositive={stats.scanned.isPositive}
          subtext="total uploads"
          icon={<FileCheck2 className="w-5 h-5" />}
        />
        <KpiCard
          label="Verified Legitimate"
          value={stats.verified.value}
          change={stats.verified.change}
          isPositive={stats.verified.isPositive}
          subtext="clean records"
          icon={<CheckCircle2 className="w-5 h-5" />}
        />
        <KpiCard
          label="Suspicious Documents"
          value={stats.suspicious.value}
          change={stats.suspicious.change}
          isPositive={stats.suspicious.isPositive}
          subtext="requires review"
          icon={<ShieldAlert className="w-5 h-5" />}
        />
        <KpiCard
          label="Critical / High Risk"
          value={stats.highRisk.value}
          change={stats.highRisk.change}
          isPositive={stats.highRisk.isPositive}
          subtext="quarantined"
          icon={<AlertTriangle className="w-5 h-5" />}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          label="Average Risk Score"
          value={stats.avgRiskScore.value}
          change={stats.avgRiskScore.change}
          isPositive={stats.avgRiskScore.isPositive}
          subtext="aggregate index"
          icon={<Activity className="w-4 h-4" />}
        />
        <KpiCard
          label="Detection Accuracy"
          value={stats.accuracy.value}
          change={stats.accuracy.change}
          isPositive={stats.accuracy.isPositive}
          subtext="model precision"
          icon={<CheckCircle2 className="w-4 h-4" />}
        />
        <KpiCard
          label="Average Processing Time"
          value={stats.processingTime.value}
          change={stats.processingTime.change}
          isPositive={stats.processingTime.isPositive}
          subtext="per inference"
          icon={<Timer className="w-4 h-4" />}
        />
      </div>

      {/* Screenings Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Recent Document Screenings</h3>
            <p className="text-xs text-slate-400">Live screening log of uploaded credentials</p>
          </div>
          <span className="text-xs font-mono text-cyan-400 font-semibold">
            {stats.recentDocuments.length} Record(s)
          </span>
        </div>

        {stats.recentDocuments.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-slate-500 mb-3">
              <Inbox className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-white mb-1">No Documents Screened Yet</h4>
            <p className="text-xs text-slate-400 max-w-sm mb-4">
              Upload an identity document to perform real-time optical and cryptographic fraud analysis.
            </p>
            <button
              onClick={onNavigateToUpload}
              className="px-4 py-2 text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg transition cursor-pointer"
            >
              Screen First Document
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Document ID</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Subject Identifier</th>
                  <th className="py-3 px-4">Risk Score</th>
                  <th className="py-3 px-4">OCR Conf.</th>
                  <th className="py-3 px-4">Tampering</th>
                  <th className="py-3 px-4">QR Check</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {stats.recentDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-850/50 transition">
                    <td className="py-3 px-4 font-mono font-medium text-cyan-300">{doc.id}</td>
                    <td className="py-3 px-4 text-slate-200">{doc.docType}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{doc.subjectMaskedId}</td>
                    <td className="py-3 px-4">
                      <span className={`font-mono font-bold ${
                        doc.riskScore > 70 ? 'text-rose-400' : doc.riskScore > 30 ? 'text-amber-400' : 'text-emerald-400'
                      }`}>
                        {doc.riskScore}/100
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">{doc.ocrConfidence}%</td>
                    <td className="py-3 px-4">
                      {doc.tamperingDetected ? (
                        <span className="text-rose-400 font-medium">Detected</span>
                      ) : (
                        <span className="text-slate-400">Clean</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                        doc.qrStatus === 'VERIFIED' 
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/50' 
                          : 'bg-rose-950 text-rose-300 border border-rose-800/50'
                      }`}>
                        {doc.qrStatus}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">{doc.timestamp}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onNavigateToInspection(doc)}
                        className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-medium cursor-pointer"
                      >
                        Audit <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};