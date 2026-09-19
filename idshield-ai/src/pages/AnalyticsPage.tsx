import { useState, useEffect, FC } from 'react';
import { 
  ShieldAlert, 
  FileText, 
  Cpu, 
  AlertTriangle, 
  Inbox, 
  Repeat, 
  Fingerprint, 
  TrendingUp, 
  Layers,
  ArrowUpRight 
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar
} from 'recharts';

interface AnalyticsData {
  totalQuarantined: number;
  mostForged: string;
  topVector: string;
  avgInference: string;
  tamperingVectors: { technique: string; count: number; pct: number }[];
  typeDistribution: { type: string; count: number; share: number }[];
  suspiciousCases?: Array<{
    id: string;
    docType: string;
    status: string;
    riskScore: number;
    tamperingDetected: boolean;
    faceConsistency: number;
  }>;
  topIndicators?: Array<{ indicator: string; count: number }>;
  repeatedIdentifiers?: Array<{ value: string; type: string; caseCount: number }>;
  riskTrend?: Array<{ idx: number; score: number }>;
}

export const AnalyticsPage: FC<{
  onInspectDoc?: (docId: string) => void;
}> = ({ onInspectDoc }) => {
  const [data, setData] = useState<AnalyticsData>({
    totalQuarantined: 0,
    mostForged: 'None',
    topVector: 'None',
    avgInference: '0.0s',
    tamperingVectors: [],
    typeDistribution: [],
    suspiciousCases: [],
    topIndicators: [],
    repeatedIdentifiers: [],
    riskTrend: []
  });

  useEffect(() => {
    let isMounted = true;
    const fetchAnalytics = async () => {
      try {
        const res = await fetch('/api/analytics');
        if (res.ok) {
          const json = await res.json();
          if (isMounted) setData(json);
        }
      } catch {
        // Keeps defaults if connection fails
      }
    };
    fetchAnalytics();
    return () => { isMounted = false; };
  }, []);

  const hasData = (data.tamperingVectors && data.tamperingVectors.length > 0) || 
                  (data.typeDistribution && data.typeDistribution.length > 0) ||
                  data.totalQuarantined > 0;

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Fraud Analytics & Detection Patterns</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Macro analysis of synthetic fraud attacks, forgery mechanisms, and geographical screening loads.
          </p>
        </div>
      </div>

      {/* 2. Stat Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Total Forgeries Quarantined</span>
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white mb-1">{data.totalQuarantined}</div>
          <div className="text-[11px] text-slate-500">Live flagged count</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Most Forged Credential</span>
            <FileText className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white mb-1">{data.mostForged}</div>
          <div className="text-[11px] text-slate-500">Primary threat vector</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Top Tampering Technique</span>
            <AlertTriangle className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white mb-1 truncate">{data.topVector}</div>
          <div className="text-[11px] text-slate-500">Dominant manipulation style</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Engine Inference Avg</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white mb-1">{data.avgInference}</div>
          <div className="text-[11px] text-slate-500">Local pipeline latency</div>
        </div>
      </div>

      {!hasData ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center flex flex-col items-center justify-center">
          <Inbox className="w-10 h-10 text-slate-600 mb-2" />
          <h4 className="text-sm font-semibold text-white">No Telemetry Recorded</h4>
          <p className="text-xs text-slate-400 max-w-sm">
            Statistical charts will generate dynamically once documents are screened through the engine.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Column (8 Cols): Tables and Visuals */}
          <div className="lg:col-span-8 space-y-6">
            {/* Investigation Queue Table */}
            {data.suspiciousCases && data.suspiciousCases.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    <h2 className="text-sm font-semibold text-white">
                      Active Investigation Queue — High & Critical Risk Quarantined Dossiers
                    </h2>
                  </div>
                  <span className="text-xs font-mono text-rose-300 bg-rose-950/60 border border-rose-800/80 px-2 py-0.5 rounded">
                    {data.suspiciousCases.length} Cases
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-[11px] font-mono uppercase text-slate-400 bg-slate-950/40">
                        <th className="px-4 py-3">Dossier ID</th>
                        <th className="px-4 py-3">Document</th>
                        <th className="px-4 py-3">Risk Index</th>
                        <th className="px-4 py-3">12x12 ELA</th>
                        <th className="px-4 py-3">Biometrics</th>
                        <th className="px-4 py-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {data.suspiciousCases.map((c) => (
                        <tr key={c.id} className="hover:bg-slate-800/30 transition">
                          <td className="px-4 py-3 text-cyan-400 font-bold">{c.id}</td>
                          <td className="px-4 py-3 text-slate-300">{c.docType}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              c.status === 'CRITICAL' 
                                ? 'bg-rose-950 border-rose-800 text-rose-300' 
                                : 'bg-amber-950 border-amber-800 text-amber-300'
                            }`}>
                              {c.riskScore}/100 [{c.status}]
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {c.tamperingDetected ? (
                              <span className="text-rose-400 font-bold">DETECTED</span>
                            ) : (
                              <span className="text-slate-500">CLEAN</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-slate-400">{c.faceConsistency}%</td>
                          <td className="px-4 py-3 text-right">
                            {onInspectDoc && (
                              <button
                                onClick={() => onInspectDoc(c.id)}
                                className="text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1 cursor-pointer"
                              >
                                Inspect <ArrowUpRight className="w-3 h-3" />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Recurring Tampering Indicators Bar Chart */}
            {data.topIndicators && data.topIndicators.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Fingerprint className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-sm font-semibold text-white">Recurring Forensic Tampering Signatures</h2>
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.topIndicators} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                    <XAxis type="number" stroke="#64748b" fontSize={10} allowDecimals={false} />
                    <YAxis 
                      dataKey="indicator" 
                      type="category" 
                      width={220} 
                      stroke="#94a3b8" 
                      fontSize={10} 
                      tickFormatter={(v: string) => (v.length > 35 ? v.slice(0, 35) + '…' : v)} 
                    />
                    <Tooltip contentStyle={{ background: '#020617', border: '1px solid #1e293b', fontSize: 11, color: '#fff' }} />
                    <Bar dataKey="count" fill="#ef4444" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Chronological Risk Progression */}
            {data.riskTrend && data.riskTrend.length > 1 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-sm font-semibold text-white">Risk Index Progression (Recent Screenings)</h2>
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={data.riskTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="idx" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} />
                    <Tooltip contentStyle={{ background: '#020617', border: '1px solid #1e293b', fontSize: 11, color: '#fff' }} />
                    <Line type="monotone" dataKey="score" stroke="#06b6d4" strokeWidth={2.5} dot={{ r: 3, fill: '#06b6d4' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Right Column (4 Cols): Categorical Distributions & Identity Collisions */}
          <div className="lg:col-span-4 space-y-6">
            {/* Repeated Identifiers (Trans-Border Syndicate Rings) */}
            {data.repeatedIdentifiers && data.repeatedIdentifiers.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <Repeat className="w-4 h-4 text-amber-400" />
                  <h2 className="text-sm font-semibold text-white">Repeated Identity Tokens</h2>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Identities or credential numbers detected appearing across multiple independent dossiers.
                </p>

                <div className="space-y-2 pt-1">
                  {data.repeatedIdentifiers.map((item, i) => (
                    <div key={i} className="p-2.5 bg-slate-950/80 border border-slate-800/80 rounded-lg flex items-center justify-between text-xs font-mono">
                      <div>
                        <div className="text-slate-200 font-bold">{item.value}</div>
                        <span className="text-[10px] text-slate-500 uppercase">{item.type.replace('_', ' ')}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/80 border border-amber-800 text-amber-300">
                        {item.caseCount}× collisions
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Detected Tampering Vectors Breakdown */}
            {data.tamperingVectors && data.tamperingVectors.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-white mb-1">Detected Tampering Vectors</h3>
                <p className="text-xs text-slate-400 mb-4">Breakdown by detected alteration techniques</p>

                <div className="space-y-3 text-xs">
                  {data.tamperingVectors.map((row, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-slate-300">
                        <span>{row.technique} ({row.count})</span>
                        <span className="font-mono font-bold text-cyan-400">{row.pct}%</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div style={{ width: `${row.pct}%` }} className="bg-cyan-500 h-full rounded-full transition-all" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Document Classification Distribution */}
            {data.typeDistribution && data.typeDistribution.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-white mb-1">Document Classification</h3>
                <p className="text-xs text-slate-400 mb-4">Volume processed by credential category</p>

                <div className="space-y-3 text-xs">
                  {data.typeDistribution.map((row, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-slate-300">
                        <span>{row.type} ({row.count})</span>
                        <span className="font-mono font-bold text-emerald-400">{row.share}%</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div style={{ width: `${row.share}%` }} className="bg-emerald-500 h-full rounded-full transition-all" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
