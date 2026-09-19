import { FC } from 'react';
import { VerificationStatus } from '../types';

export const StatusBadge: FC<{ status: VerificationStatus }> = ({ status }) => {
  const styles: Record<VerificationStatus, { bg: string; text: string; dot: string; border: string }> = {
    'VERIFIED': { bg: 'bg-emerald-950/60', text: 'text-emerald-400', dot: 'bg-emerald-400', border: 'border-emerald-700/40' },
    'SUSPICIOUS': { bg: 'bg-amber-950/60', text: 'text-amber-400', dot: 'bg-amber-400', border: 'border-amber-700/40' },
    'HIGH RISK': { bg: 'bg-rose-950/60', text: 'text-rose-400', dot: 'bg-rose-400', border: 'border-rose-700/40' },
    'CRITICAL': { bg: 'bg-red-950/80', text: 'text-red-300 animate-pulse', dot: 'bg-red-500', border: 'border-red-600' }
  };

  const current = styles[status] || styles['SUSPICIOUS'];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wider uppercase border ${current.bg} ${current.text} ${current.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${current.dot}`} />
      {status}
    </span>
  );
};
