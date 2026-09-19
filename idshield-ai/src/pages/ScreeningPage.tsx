import { useState, useRef, FC, ChangeEvent } from 'react';
import { StageStatus, DetailedAnalysis } from '../types';
import { 
  UploadCloud, 
  Camera, 
  File, 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  ShieldCheck, 
  ArrowRight 
} from 'lucide-react';

const INITIAL_STAGES: StageStatus[] = [
  { id: 'upload', label: 'Payload Receiving & Hash Check', state: 'pending' },
  { id: 'preprocessing', label: 'Image Rectification & ELA Normalization', state: 'pending' },
  { id: 'ocr', label: 'Deep OCR & Key-Value Extraction', state: 'pending' },
  { id: 'classification', label: 'Document Template Classifier', state: 'pending' },
  { id: 'tampering', label: 'Splice & Pixel Anomaly Detection', state: 'pending' },
  { id: 'layout', label: 'Microprint & Layout Structural Check', state: 'pending' },
  { id: 'qr', label: 'Cryptographic QR Code Validation', state: 'pending' },
  { id: 'biometric', label: 'Face Quality & Photo Integrity Check', state: 'pending' },
  { id: 'risk', label: 'Explainable Multi-Signal Risk Engine', state: 'pending' },
  { id: 'decision', label: 'Final Forensic Verdict Synthesis', state: 'pending' }
];

export const ScreeningPage: FC<{ onAnalysisSuccess: (analysis: DetailedAnalysis) => void }> = ({ onAnalysisSuccess }) => {
  const [stages, setStages] = useState<StageStatus[]>(INITIAL_STAGES);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<globalThis.File | null>(null);
  const [analyzedResult, setAnalyzedResult] = useState<DetailedAnalysis | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Dynamic backend resolution: connects to local backend when on localhost, and Render on Vercel
  const isLocalhost = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  const API_BASE = (
    import.meta.env.VITE_API_URL || 
    (isLocalhost ? 'http://127.0.0.1:8000' : 'https://idshield-backend-eiu9.onrender.com')
  ).replace(/\/$/, '');

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setErrorMessage(null);
      processRealDocument(file);
    }
  };

  const processRealDocument = async (file: globalThis.File) => {
    setIsProcessing(true);
    setAnalyzedResult(null);

    // Progressive stage animation
    INITIAL_STAGES.forEach((_, idx) => {
      setTimeout(() => {
        setStages((prev) =>
          prev.map((stage, i) => {
            if (i < idx) return { ...stage, state: 'completed' };
            if (i === idx) return { ...stage, state: 'processing' };
            return { ...stage, state: 'pending' };
          })
        );
      }, (idx + 1) * 200);
    });

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Retrieve authenticated officer session token dynamically
      const authToken = 
        localStorage.getItem('access_token') ||
        localStorage.getItem('token') ||
        localStorage.getItem('idshield_token') ||
        sessionStorage.getItem('access_token') ||
        sessionStorage.getItem('token') ||
        '';

      if (!authToken) {
        throw new Error('Authentication session missing or expired. Please return to login.');
      }

      const response = await fetch(`${API_BASE}/api/documents/screen`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData,
      });

      if (!response.ok) {
        const errDetail = await response.text();
        throw new Error(`Server returned HTTP ${response.status}: ${errDetail || response.statusText}`);
      }

      const data: DetailedAnalysis = await response.json();

      setTimeout(() => {
        setStages((prev) => prev.map((s) => ({ ...s, state: 'completed' })));
        setAnalyzedResult(data);
        setIsProcessing(false);
      }, 2200);

    } catch (err: any) {
      console.error(err);
      setErrorMessage(err.message || `Failed to connect to AI backend at ${API_BASE}. Is uvicorn running?`);
      setIsProcessing(false);
      setStages((prev) => prev.map((s) => ({ ...s, state: 'failed' })));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Identity Document Upload & Screening Engine</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Execute real-time optical character recognition, digital watermark verification, and convolutional tampering analysis.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-950/80 border border-rose-700 text-rose-300 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          {errorMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Upload Zone */}
        <div className="lg:col-span-7 space-y-4">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/png, image/jpeg, image/jpg"
            className="hidden"
          />

          <div
            onClick={() => !isProcessing && fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-700 hover:border-cyan-500/60 bg-slate-900/60 rounded-2xl p-8 flex flex-col items-center justify-center text-center transition cursor-pointer"
          >
            <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-base font-semibold text-white mb-1">Upload Identity Document</h3>
            <p className="text-xs text-slate-400 max-w-sm mb-4 leading-relaxed">
              Click anywhere in this box to select an image from your computer (Aadhaar, PAN, Passport, Driving License).
            </p>

            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                disabled={isProcessing}
                className="px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition flex items-center gap-2 shadow-lg shadow-cyan-950 disabled:opacity-50"
              >
                <File className="w-4 h-4" />
                Select File & Run AI Verification
              </button>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                disabled={isProcessing}
                className="px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center gap-2"
              >
                <Camera className="w-4 h-4 text-cyan-400" />
                Hardware Scanner / Camera
              </button>
            </div>

            <div className="mt-6 flex items-center gap-4 text-[11px] text-slate-500 border-t border-slate-800/80 pt-4">
              <span>Max file size: 25MB</span>
              <span>•</span>
              <span className="flex items-center gap-1 text-slate-400">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> End-to-End TLS Encrypted
              </span>
            </div>
          </div>

          {selectedFile && (
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded bg-slate-800 flex items-center justify-center text-cyan-400">
                  <File className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white">{selectedFile.name}</div>
                  <div className="text-[10px] text-slate-400">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • {selectedFile.type}
                  </div>
                </div>
              </div>
              <span className="text-xs font-mono text-cyan-400 font-bold">
                {isProcessing ? 'Inspecting Live...' : 'Inspection Ready'}
              </span>
            </div>
          )}
        </div>

        {/* Verification Pipeline Progress */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="text-sm font-semibold text-white">AI Analysis Pipeline Execution</h3>
              <span className="text-[11px] font-mono text-cyan-400">10 Verification Checks</span>
            </div>

            <div className="space-y-2.5">
              {stages.map((stage, idx) => (
                <div
                  key={stage.id}
                  className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-950/40 border border-slate-850"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 text-[10px] flex items-center justify-center font-mono font-bold">
                      {idx + 1}
                    </span>
                    <span className={`${
                      stage.state === 'processing' ? 'text-cyan-300 font-semibold' : stage.state === 'completed' ? 'text-slate-300' : 'text-slate-500'
                    }`}>
                      {stage.label}
                    </span>
                  </div>

                  <div>
                    {stage.state === 'pending' && <span className="text-[10px] text-slate-600 uppercase font-mono">Pending</span>}
                    {stage.state === 'processing' && (
                      <span className="flex items-center gap-1 text-[10px] text-cyan-400 font-mono">
                        <Loader2 className="w-3 h-3 animate-spin" /> RUNNING
                      </span>
                    )}
                    {stage.state === 'completed' && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    )}
                    {stage.state === 'failed' && (
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 mt-4">
            <button
              type="button"
              onClick={() => analyzedResult && onAnalysisSuccess(analyzedResult)}
              disabled={!analyzedResult || isProcessing}
              className={`w-full py-2.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
                analyzedResult && !isProcessing
                  ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 cursor-pointer shadow-lg shadow-cyan-950'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              Open Complete Forensic Analysis <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};