import { FC } from 'react';
import { RiskFactor } from '../types';

export const RiskWaterfall: FC<{ factors: RiskFactor[]; totalScore: number }> = ({ factors, totalScore }) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div>
          <h4 className="text-sm font-semibold text-white">Explainable Risk Engine Matrix</h4>
          <p className="text-xs text-slate-400">Additive multi-signal heuristic weights</p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 uppercase">Calculated Index</span>
          <div className="text-lg font-bold text-rose-400">{totalScore} <span className="text-xs text-slate-500">/ 100</span></div>
        </div>
      </div>

      <div className="space-y-2.5">
        {factors.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between text-xs bg-slate-950/40 p-2.5 rounded-lg border border-slate-850">
            <div className="flex flex-col">
              <span className="font-medium text-slate-200">{item.signal}</span>
              <span className="text-[11px] text-slate-400">{item.description}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded font-mono font-bold ${
                item.weight > 0 ? 'bg-rose-950/60 text-rose-400 border border-rose-800/40' : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
              }`}>
                {item.weight > 0 ? `+${item.weight}` : item.weight}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
