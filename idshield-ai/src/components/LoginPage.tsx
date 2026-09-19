import React, { useState } from 'react';
import { 
  Shield, 
  Key, 
  User, 
  Lock, 
  AlertTriangle, 
  Eye, 
  EyeOff, 
  Terminal, 
  UserPlus, 
  CheckCircle2, 
  Cpu, 
  Radio 
} from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: (officer: { badgeId: string; name: string; clearance: string }) => void;
}

const CLEARANCE_MAP: Record<string, string> = {
  L1: 'Verification Observer',
  L2: 'Forensic Examiner',
  L3: 'Gov. Lead Investigator',
  L4: 'Autonomous Syndicate Admin',
};

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [badgeId, setBadgeId] = useState('INV-7029');
  const [password, setPassword] = useState('');
  const [agencyKey, setAgencyKey] = useState('');
  const [clearanceLevel, setClearanceLevel] = useState('L3');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Dynamic backend resolution: localhost vs Render cloud
  const isLocalhost = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  const API_BASE = (
    import.meta.env.VITE_API_URL || 
    (isLocalhost ? 'http://127.0.0.1:8000' : 'https://idshield-backend-eiu9.onrender.com')
  ).replace(/\/$/, '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setIsSubmitting(true);

    const endpoint = isRegisterMode 
      ? `${API_BASE}/api/auth/register` 
      : `${API_BASE}/api/auth/token`;

    const payload = isRegisterMode
      ? { badgeId, password, clearanceLevel, agencySecretKey: agencyKey }
      : { badgeId, password, clearanceLevel };

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication handshake rejected by cluster authority.');
      }

      if (isRegisterMode) {
        setSuccessMsg(data.message || 'Authorization granted. Credential record sealed.');
        setIsRegisterMode(false);
        setPassword('');
        setAgencyKey('');
      } else {
        // Persist valid active session token for ScreeningPage and other modules
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('idshield_token', data.access_token);
          sessionStorage.setItem('access_token', data.access_token);
          sessionStorage.setItem('token', data.access_token);
        }

        onLoginSuccess({
          badgeId: data.officer.badgeId,
          name: CLEARANCE_MAP[data.officer.clearance] || data.officer.name,
          clearance: data.officer.clearance,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Connection failure to active auth cluster.';
      setErrorMsg(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-slate-950 cyber-grid flex items-center justify-center p-4 overflow-hidden select-none">
      {/* Background Ambient Radial Glow */}
      <div className="absolute w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-[140px] pointer-events-none" />

      {/* Main Tactical SOC Authentication Module */}
      <div className="relative w-full max-w-md soc-card hud-corners rounded-sm p-7 z-10 shadow-[0_0_60px_-15px_rgba(0,0,0,0.9)] border border-slate-800">
        
        {/* Top Hardware Telemetry Header */}
        <div className="flex items-center justify-between pb-3.5 mb-6 border-b border-slate-800/80 text-[10px] font-mono">
          <div className="flex items-center space-x-2">
            <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span className="text-slate-400 tracking-wider">GATEWAY:</span>
            <span className="text-cyan-300 font-semibold">{isLocalhost ? 'ONLINE // 8000' : 'CLOUD // LIVE'}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-emerald-400 font-semibold">ENCLAVE SECURE</span>
          </div>
        </div>

        {/* Console Branding */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="relative flex items-center justify-center w-13 h-13 p-3 rounded-lg bg-slate-950 border border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.2)] mb-3">
            <Shield className="w-7 h-7 text-cyan-400" />
            <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          </div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-display font-bold tracking-widest text-slate-100">
              IDSHIELD <span className="text-cyan-400">AI</span>
            </h1>
            <span className="px-1.5 py-0.5 text-[9px] font-mono font-semibold bg-cyan-950/90 text-cyan-400 border border-cyan-500/40 rounded">
              v2.4-PROD
            </span>
          </div>
          <p className="text-[11px] font-mono text-slate-500 tracking-tight mt-1">
            Forensic Identity & Syndicate Threat Detection Console
          </p>
        </div>

        {/* Hardware-Style Mode Switcher */}
        <div className="flex rounded bg-slate-950/90 p-1 border border-slate-800/90 mb-5 font-mono text-[11px]">
          <button
            type="button"
            onClick={() => { setIsRegisterMode(false); setErrorMsg(''); setSuccessMsg(''); }}
            className={`flex-1 py-1.5 rounded transition-all font-semibold uppercase tracking-wider ${
              !isRegisterMode 
                ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.15)]' 
                : 'text-slate-500 hover:text-slate-300 border border-transparent'
            }`}
          >
            Access Session
          </button>
          <button
            type="button"
            onClick={() => { setIsRegisterMode(true); setErrorMsg(''); setSuccessMsg(''); }}
            className={`flex-1 py-1.5 rounded transition-all font-semibold uppercase tracking-wider ${
              isRegisterMode 
                ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.15)]' 
                : 'text-slate-500 hover:text-slate-300 border border-transparent'
            }`}
          >
            Register Profile
          </button>
        </div>

        {/* Security Telemetry Alerts */}
        {errorMsg && (
          <div className="mb-4 flex items-start space-x-2 p-2.5 rounded bg-rose-950/40 border border-rose-500/40 text-rose-300 text-[11px] font-mono">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="mb-4 flex items-start space-x-2 p-2.5 rounded bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-[11px] font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Badge ID Input */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[10px] font-mono tracking-wider text-slate-400 uppercase">
                Investigator Badge ID
              </label>
              <span className="text-[9px] font-mono text-slate-600">[STATION_HANDLE]</span>
            </div>
            <div className="relative">
              <User className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
              <input
                type="text"
                required
                value={badgeId}
                onChange={(e) => setBadgeId(e.target.value)}
                placeholder="e.g., INV-7029"
                className="w-full pl-9 pr-3 py-2 bg-slate-950/80 border border-slate-800 rounded text-xs text-slate-200 font-mono focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 focus:outline-none transition-all placeholder-slate-600"
              />
            </div>
          </div>

          {/* Agency Secret Key (Register Mode Only) */}
          {isRegisterMode && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] font-mono tracking-wider text-amber-400 uppercase">
                  Agency Authorization Secret Key
                </label>
                <span className="text-[9px] font-mono text-amber-500/60">[RESTRICTED]</span>
              </div>
              <div className="relative">
                <Key className="absolute left-3 top-2.5 w-3.5 h-3.5 text-amber-500" />
                <input
                  type="password"
                  required
                  value={agencyKey}
                  onChange={(e) => setAgencyKey(e.target.value)}
                  placeholder="Master Authorization Key"
                  className="w-full pl-9 pr-3 py-2 bg-slate-950/80 border border-amber-500/40 rounded text-xs text-amber-200 font-mono focus:border-amber-400 focus:ring-1 focus:ring-amber-400/20 focus:outline-none transition-all placeholder-amber-700/50"
                />
              </div>
            </div>
          )}

          {/* Passcode Input */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[10px] font-mono tracking-wider text-slate-400 uppercase">
                {isRegisterMode ? 'New Access Passphrase' : 'Security Clearance Key'}
              </label>
              <span className="text-[9px] font-mono text-slate-600">[ENCRYPTED_PBKDF2]</span>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter clearance passphrase"
                className="w-full pl-9 pr-10 py-2 bg-slate-950/80 border border-slate-800 rounded text-xs text-slate-200 font-mono focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 focus:outline-none transition-all placeholder-slate-600"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition-colors"
              >
                {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Clearance Level Selector */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[10px] font-mono tracking-wider text-slate-400 uppercase">
                Station Clearance Profile
              </label>
              <span className="text-[9px] font-mono text-cyan-500/70">LEVEL: {clearanceLevel}</span>
            </div>
            <select
              value={clearanceLevel}
              onChange={(e) => setClearanceLevel(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950/80 border border-slate-800 rounded text-xs text-slate-200 font-mono focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 focus:outline-none transition-all"
            >
              <option value="L1">Level 1: Verification Observer</option>
              <option value="L2">Level 2: Forensic Examiner</option>
              <option value="L3">Level 3: Gov. Lead Investigator (Full Access)</option>
              <option value="L4">Level 4: Autonomous Syndicate Admin</option>
            </select>
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 py-2.5 px-4 bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/40 hover:border-cyan-400 text-cyan-300 font-mono text-xs font-semibold uppercase tracking-wider rounded transition-all shadow-[0_0_15px_rgba(6,182,212,0.15)] flex items-center justify-center space-x-2 active:scale-98 disabled:opacity-50 cursor-pointer"
          >
            {isSubmitting ? (
              <span className="animate-spin h-3.5 w-3.5 border-2 border-cyan-400 border-t-transparent rounded-full" />
            ) : isRegisterMode ? (
              <>
                <UserPlus className="w-3.5 h-3.5 text-cyan-400" />
                <span>Register Clearance Profile</span>
              </>
            ) : (
              <>
                <Key className="w-3.5 h-3.5 text-cyan-400" />
                <span>Initialize Secure Session</span>
              </>
            )}
          </button>
        </form>

        {/* Footer Audit Signature */}
        <div className="mt-6 pt-3.5 border-t border-slate-800/70 flex items-center justify-between text-[10px] font-mono text-slate-500">
          <div className="flex items-center space-x-1.5">
            <Terminal className="w-3 h-3 text-cyan-500" />
            <span>NODE: KALI-CLUSTER-01</span>
          </div>
          <div className="flex items-center space-x-1 text-slate-500">
            <Cpu className="w-3 h-3 text-slate-600" />
            <span>TLS_AES_256_GCM</span>
          </div>
        </div>

      </div>
    </div>
  );
};