import React from 'react';

export const RiskGauge: React.FC<{ score: number }> = ({ score }) => {
  const getRiskColor = (val: number) => {
    if (val <= 30) return '#34d399';
    if (val <= 60) return '#fbbf24';
    if (val <= 80) return '#fb7185';
    return '#f43f5e';
  };

  const color = getRiskColor(score);
  const circumference = 2 * Math.PI * 46;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex flex-col items-center justify-center">
      <svg className="w-40 h-40 transform -rotate-90" viewBox="0 0 108 108">
        <circle cx="54" cy="54" r="46" stroke="#18243e" strokeWidth="8" fill="transparent" />
        <circle
          cx="54"
          cy="54"
          r="46"
          stroke={color}
          strokeWidth="9"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="text-4xl font-extrabold text-white tracking-tighter">{score}</span>
        <span className="text-[10px] uppercase font-semibold text-slate-400">/ 100 Risk</span>
      </div>
    </div>
  );
};
