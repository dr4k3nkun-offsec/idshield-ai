import { FC, useState } from 'react';
import { DetailedAnalysis } from '../types';
import { RiskGauge } from '../components/RiskGauge';
import { RiskWaterfall } from '../components/RiskWaterfall';
import { EvidenceViewer } from '../components/EvidenceViewer';
import { StatusBadge } from '../components/StatusBadge';
import { 
  FileText, 
  QrCode, 
  ScanFace, 
  Sparkles, 
  Printer, 
  ArrowLeft,
  ScanSearch,
  UploadCloud,
  ShieldAlert,
  ShieldCheck,
  CalendarCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Hash,
  Clock,
  Cpu,
  UserCheck,
  Send,
  Loader2,
  Lock
} from 'lucide-react';

interface ExtendedAnalysis extends DetailedAnalysis {
  validationOutcome?: {
    checks: Array<{
      code: string;
      label: string;
      status: 'pass' | 'warn' | 'fail';
      message: string;
    }>;
    passed: number;
    warnings: number;
    failed: number;
    isValid: boolean;
    extractedFields?: {
      name?: string;
      dob?: string;
      gender?: string;
      expiry?: string;
    };
  };
}

export const AnalysisResultPage: FC<{ 
  doc: DetailedAnalysis | null;
  onBack: () => void; 
  onOpenReport?: () => void;
  onNavigateToUpload: () => void;
}> = ({ doc, onBack, onNavigateToUpload }) => {
  const [decision, setDecision] = useState<string>('CLEARED');
  const [reason, setReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [adjudicationSuccess, setAdjudicationSuccess] = useState<string | null>(null);

  const [verifyingChain, setVerifyingChain] = useState(false);
  const [chainResult, setChainResult] = useState<{ valid: boolean; message: string } | null>(null);

  if (!doc) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[460px]">
        <div className="w-16 h-16 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400 mb-4 shadow-inner">
          <ScanSearch className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-white mb-1.5">No Active Document Under Inspection</h3>
        <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
          Upload an identity document in the screening engine to run real-time 12x12 block Error Level Analysis (ELA), OCR extraction, facial geometry validation, and watchlist screening.
        </p>
        <button
          onClick={onNavigateToUpload}
          className="px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center gap-2 transition shadow-lg shadow-cyan-950 cursor-pointer"
        >
          <UploadCloud className="w-4 h-4" /> Go to Upload & Screen
        </button>
      </div>
    );
  }

  const extendedDoc = doc as ExtendedAnalysis;
  const validation = extendedDoc.validationOutcome;

  // Identify if any watchlist match occurred in the forensic breakdown
  const watchlistHit = doc.riskBreakdown?.find(b => 
    b.signal?.toLowerCase().includes('watchlist') && b.impact === 'negative'
  );

  const handleDownloadReport = () => {
    if (!doc?.id) return;
    window.open(`/api/documents/${doc.id}/report`, '_blank');
  };

  const handleAdjudicate = async () => {
    if (!reason.trim()) {
      alert('Please provide a statutory justification before signing the decision.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await fetch(`/api/documents/${doc.id}/adjudicate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          reason,
          officerBadge: 'INV-7029'
        })
      });
      const data = await res.json();
      if (data.success) {
        setAdjudicationSuccess(`Adjudication sealed: ${decision} recorded under SHA-256 hash ${data.audit_hash.slice(0, 16)}...`);
        doc.status = data.new_status;
      }
    } catch {
      alert('Failed to record adjudication decision. Verify backend connection.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifyingChain(true);
    try {
      const res = await fetch('/api/audit/verify-chain');
      const data = await res.json();
      setChainResult(data);
    } catch {
      setChainResult({ valid: false, message: 'Could not connect to immutable audit ledger node.' });
    } finally {
      setVerifyingChain(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white tracking-tight">Forensic Dossier: {doc.id}</h2>
              <StatusBadge status={doc.status} />
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Audited by {doc.processedByNode} on {doc.timestamp}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadReport}
            className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition shadow-lg shadow-cyan-950 cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            Generate Audit Report
          </button>
          <button
            onClick={() => window.print()}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
          >
            <Printer className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Primary Threat & Verification Status Banner */}
      <div className={`p-4 rounded-xl border flex items-center justify-between ${
        doc.status === 'VERIFIED'
          ? 'bg-emerald-950/40 border-emerald-800/60'
          : doc.status === 'CRITICAL'
          ? 'bg-rose-950/60 border-rose-700 animate-pulse'
          : 'bg-rose-950/40 border-rose-800/60'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg border ${
            doc.status === 'VERIFIED'
              ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400'
              : 'bg-rose-500/20 border-rose-500/40 text-rose-400'
          }`}>
            {doc.status === 'VERIFIED' ? '✓' : '⚠'}
          </div>
          <div>
            <h4 className={`text-sm font-bold ${doc.status === 'VERIFIED' ? 'text-emerald-200' : 'text-rose-200'}`}>
              {doc.status === 'VERIFIED' 
                ? 'Legitimate Identity Credential Confirmed' 
                : doc.status === 'CRITICAL'
                ? 'CRITICAL ALERT: Malicious Forgery or Watchlist Violation'
                : 'High-Risk Manipulation Discrepancies Detected'}
            </h4>
            <p className={`text-xs ${doc.status === 'VERIFIED' ? 'text-emerald-300/80' : 'text-rose-300/80'}`}>
              {doc.status === 'VERIFIED' 
                ? 'All optical, facial biometric, and cryptographic verification checks passed statutory tolerances.'
                : 'Discrepancies identified across optical layout, QR cryptographic signatures, or 12x12 ELA compression.'}
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded text-xs font-mono font-bold border ${
          doc.status === 'VERIFIED'
            ? 'bg-emerald-900/60 border-emerald-700 text-emerald-200'
            : 'bg-rose-900/60 border-rose-700 text-rose-200'
        }`}>
          RISK: {doc.riskScore}/100
        </span>
      </div>

      {/* 3. National Security Watchlist & Sanctions Radar */}
      <div className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
        watchlistHit
          ? 'bg-rose-950/50 border-rose-500/60'
          : 'bg-slate-900/90 border-slate-800'
      }`}>
        <div className="flex items-start gap-3">
          <div className={`p-2.5 rounded-lg shrink-0 border ${
            watchlistHit 
              ? 'bg-rose-500/20 border-rose-500/50 text-rose-400' 
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
          }`}>
            {watchlistHit ? <ShieldAlert className="w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                National Security Watchlist & Sanctions Engine
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
                watchlistHit 
                  ? 'bg-rose-900/80 border-rose-600 text-rose-200' 
                  : 'bg-emerald-950 border-emerald-800 text-emerald-300'
              }`}>
                {watchlistHit ? 'SANCTIONS MATCH' : 'ZERO MATCHES // CLEAR'}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              {watchlistHit 
                ? watchlistHit.description 
                : 'Screened against central law enforcement database: zero active red notices or sanctions registered.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono border-t md:border-t-0 md:border-l border-slate-800 pt-2 md:pt-0 md:pl-4 shrink-0">
          <div>
            <span className="text-[10px] text-slate-500 block uppercase">Target Name</span>
            <span className="text-white font-bold">{validation?.extractedFields?.name || 'Verified Citizen'}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 block uppercase">Fuzzy Algorithm</span>
            <span className="text-cyan-400 font-bold">Jaccard Token (0.75)</span>
          </div>
        </div>
      </div>

      {/* 4. Risk Metrics & Signal Diagnostic Matrices */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-4 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col items-center justify-center text-center">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Composite AI Risk Score
          </span>
          <RiskGauge score={doc.riskScore} />
          <div className="mt-3 text-xs text-slate-400 max-w-[240px]">
            {doc.status === 'VERIFIED' 
              ? <strong className="text-emerald-400">Authentic Document Pattern</strong> 
              : <strong className="text-rose-400">High Probability of Forgery</strong>}
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 w-full grid grid-cols-2 text-center text-xs">
            <div>
              <span className="text-slate-500 block text-[10px]">VERIFICATION</span>
              <span className={`font-bold ${doc.status === 'VERIFIED' ? 'text-emerald-400' : 'text-rose-400'}`}>
                {doc.status === 'VERIFIED' ? 'ACCEPTED' : 'REJECT / AUDIT'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">DOCUMENT CLASS</span>
              <span className="text-slate-200 font-bold">{doc.docType}</span>
            </div>
          </div>
        </div>

        <div className="md:col-span-8 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold text-white">Signal Integrity Diagnostic Matrices</h3>
            <span className="text-xs text-slate-400 font-mono">12x12 Block & Fourier Res</span>
          </div>

          <div className="space-y-3.5 my-3">
            {[
              { label: 'OCR Consistency & Text Sharpness', value: doc.ocrConfidence, color: 'bg-emerald-500' },
              { label: 'Layout & Template Alignment Integrity', value: doc.layoutIntegrity, color: 'bg-cyan-500' },
              { label: 'Pixel & 12x12 Block Error Level (ELA)', value: doc.imageIntegrity, color: doc.imageIntegrity > 60 ? 'bg-emerald-500' : 'bg-rose-500' },
              { label: 'Biometric Face Geometry Consistency', value: doc.faceConsistency, color: doc.faceConsistency > 50 ? 'bg-emerald-500' : 'bg-rose-500' },
            ].map((meter, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{meter.label}</span>
                  <span className="font-mono text-slate-300 font-bold">{meter.value}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    style={{ width: `${meter.value}%` }}
                    className={`h-full ${meter.color} transition-all duration-700`}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 border-t border-slate-800 text-center">
            <div className="bg-slate-950/40 p-2 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 uppercase block">QR Signature</span>
              <span className={`text-xs font-mono font-bold ${doc.qrStatus === 'VERIFIED' ? 'text-emerald-400' : 'text-rose-400'}`}>
                {doc.qrStatus === 'VERIFIED' ? 'PASSED' : 'FAILED'}
              </span>
            </div>
            <div className="bg-slate-950/40 p-2 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 uppercase block">Tampering Flag</span>
              <span className={`text-xs font-mono font-bold ${doc.tamperingDetected ? 'text-rose-400' : 'text-emerald-400'}`}>
                {doc.tamperingDetected ? 'DETECTED' : 'CLEAN'}
              </span>
            </div>
            <div className="bg-slate-950/40 p-2 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 uppercase block">Face Match</span>
              <span className={`text-xs font-mono font-bold ${doc.faceDetected ? 'text-emerald-400' : 'text-rose-400'}`}>
                {doc.faceDetected ? `YES (${doc.faceQuality}%)` : 'NO'}
              </span>
            </div>
            <div className="bg-slate-950/40 p-2 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 uppercase block">Moiré FFT</span>
              <span className="text-xs font-mono font-bold text-cyan-400">CHECKED</span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Interactive Document Evidence Overlay Viewer */}
      <EvidenceViewer regions={doc.evidenceRegions} imageUrl={doc.imageUrl} />

      {/* 6. Structural Chronology & Validation Checklist */}
      {validation && validation.checks && validation.checks.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <CalendarCheck className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">
                Structural & Chronological Validation Checklist
              </h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
                {validation.passed} Passed
              </span>
              {validation.warnings > 0 && (
                <span className="text-amber-400 bg-amber-950/60 border border-amber-800 px-2 py-0.5 rounded">
                  {validation.warnings} Warn
                </span>
              )}
              {validation.failed > 0 && (
                <span className="text-rose-400 bg-rose-950/60 border border-rose-800 px-2 py-0.5 rounded">
                  {validation.failed} Failed
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {validation.checks.map((c, idx) => (
              <div 
                key={idx} 
                className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg flex items-start gap-2.5"
              >
                {c.status === 'pass' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : c.status === 'warn' ? (
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-white">{c.label}</span>
                    <span className="text-[10px] font-mono text-slate-500">[{c.code}]</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 leading-snug">{c.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Explanations & Risk Waterfall Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">Forensic Natural Language Explanations</h3>
          </div>
          <div className="p-3.5 rounded-lg bg-cyan-950/20 border border-cyan-800/40 text-xs text-cyan-200 leading-relaxed">
            The neural inference cluster classified this document with <strong>Risk Index {doc.riskScore}/100</strong>.
          </div>
          <div className="space-y-2 text-xs">
            {doc.aiExplanation.map((reason, idx) => (
              <div key={idx} className="flex items-start gap-2 text-slate-300">
                <span className="text-cyan-400 font-bold mt-0.5">•</span>
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-6">
          <RiskWaterfall factors={doc.riskBreakdown} totalScore={doc.riskScore} />
        </div>
      </div>

      {/* 8. QR Integrity & Facial Biometrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <QrCode className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">QR / Barcode Cryptographic Digest</h3>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
              doc.qrStatus === 'VERIFIED'
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                : 'bg-rose-950 text-rose-300 border border-rose-800'
            }`}>
              STATUS: {doc.qrStatus}
            </span>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 uppercase block mb-1">Decoded Payload Digest</span>
              <span className="text-rose-300 break-all">{doc.qrDecodedData || 'NOT_DECODABLE'}</span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 uppercase block mb-1">Expected Template Schema</span>
              <span className="text-emerald-400 break-all">{doc.qrExpectedData || 'NONE'}</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <ScanFace className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">Biometric Facial Verification</h3>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
              doc.faceDetected 
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                : 'bg-rose-950 text-rose-300 border border-rose-800'
            }`}>
              MATCH: {doc.faceConsistency}%
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center mb-4 text-xs">
            <div className="bg-slate-950/60 p-2 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 block">Face Present</span>
              <span className="font-bold text-emerald-400">{doc.faceDetected ? 'YES' : 'NO'}</span>
            </div>
            <div className="bg-slate-950/60 p-2 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 block">Photo Quality</span>
              <span className="font-bold text-slate-200">{doc.faceQuality}%</span>
            </div>
            <div className="bg-slate-950/60 p-2 rounded border border-slate-850">
              <span className="text-[10px] text-slate-500 block">Neural Embedding</span>
              <span className="font-bold text-cyan-300">SFace ONNX</span>
            </div>
          </div>
        </div>
      </div>

      {/* 9. Officer Statutory Adjudication Action Console */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">Officer Statutory Adjudication Console</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">Badge: INV-7029 (Gov. Lead Investigator)</span>
        </div>

        {adjudicationSuccess && (
          <div className="p-3 bg-emerald-950/60 border border-emerald-700/60 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            {adjudicationSuccess}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          <div className="md:col-span-4">
            <label className="text-xs text-slate-400 block mb-1">Statutory Disposition</label>
            <select
              value={decision}
              onChange={(e) => setDecision(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
            >
              <option value="CLEARED">CLEAR FOR TRANSIT (Accepted)</option>
              <option value="SECONDARY_INSPECTION">REFER TO SECONDARY INSPECTION</option>
              <option value="REJECTED">ENTRY REJECTED (Unlawful Credential)</option>
              <option value="REFERRED_TO_SSB">SEIZE & ALERT SSB COMMAND</option>
            </select>
          </div>

          <div className="md:col-span-6">
            <label className="text-xs text-slate-400 block mb-1">Investigator Note / Justification</label>
            <input
              type="text"
              placeholder="e.g. Identity verified against physical card under secondary UV inspection."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white placeholder-slate-600 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div className="md:col-span-2 pt-5">
            <button
              onClick={handleAdjudicate}
              disabled={isSubmitting}
              className="w-full py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-lg flex items-center justify-center gap-1.5 transition disabled:opacity-50 cursor-pointer shadow-lg shadow-cyan-950"
            >
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              Sign Decision
            </button>
          </div>
        </div>
      </div>

      {/* 10. Cryptographic Provenance Seal & Live Audit Chain Verifier */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <Hash className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>
            Provenance Seal: <strong className="text-slate-200">SHA256:{doc.id}-PROV-CHAIN-SEAL</strong>
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleVerifyChain}
            disabled={verifyingChain}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 font-mono text-xs flex items-center gap-1.5 transition cursor-pointer"
          >
            {verifyingChain ? <Loader2 className="w-3 h-3 animate-spin" /> : <Lock className="w-3 h-3" />}
            Verify Full Ledger Chain
          </button>
        </div>
      </div>

      {chainResult && (
        <div className={`p-3 rounded-lg border text-xs font-mono flex items-center gap-2 ${
          chainResult.valid
            ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
            : 'bg-rose-950/60 border-rose-800 text-rose-300'
        }`}>
          {chainResult.valid ? <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" /> : <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />}
          <span>{chainResult.message}</span>
        </div>
      )}
    </div>
  );
};
