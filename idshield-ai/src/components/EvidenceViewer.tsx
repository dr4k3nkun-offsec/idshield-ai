import React, { useState } from 'react';
import { EvidenceRegion } from '../types';
import { Eye, EyeOff, Search } from 'lucide-react';

interface EvidenceViewerProps {
  regions: EvidenceRegion[];
  imageUrl?: string;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ regions, imageUrl }) => {
  const [overlaysActive, setOverlaysActive] = useState(true);
  const [selectedRegion, setSelectedRegion] = useState<EvidenceRegion | null>(null);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      {/* Control Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white">Side-by-Side Computer Vision Evidence Inspector</h3>
        </div>
        <button
          onClick={() => setOverlaysActive(!overlaysActive)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
            overlaysActive
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
              : 'bg-slate-800 text-slate-400 border border-slate-700'
          }`}
        >
          {overlaysActive ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          {overlaysActive ? 'Overlays Active' : 'Overlays Hidden'}
        </button>
      </div>

      {/* Side-by-Side Dual Viewports */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
        {/* Left: Raw Upload */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider">Original Uploaded Document Scan</span>
            <span className="font-mono text-[10px]">RAW RGB PIXELS</span>
          </div>
          <div className="w-full min-h-[380px] bg-slate-950 rounded-lg flex items-center justify-center p-3 border border-slate-800/80">
            {imageUrl ? (
              <img
                src={imageUrl}
                alt="Original Document Scan"
                className="max-h-[460px] max-w-full object-contain rounded shadow-lg"
              />
            ) : (
              <span className="text-xs text-slate-500">No Image Preview Available</span>
            )}
          </div>
        </div>

        {/* Right: Neural Overlay with Tight Wrapper */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-cyan-400">
              AI Neural Inference Overlay
            </span>
            <span className="font-mono text-[10px]">CALIBRATED BOUNDS</span>
          </div>
          <div className="w-full min-h-[380px] bg-slate-950 rounded-lg flex items-center justify-center p-3 border border-slate-800/80">
            {imageUrl ? (
              /* The inline-block container matches the rendered image dimensions */
              <div className="relative inline-block max-w-full max-h-[460px]">
                <img
                  src={imageUrl}
                  alt="Inference Overlay View"
                  className="max-h-[460px] max-w-full object-contain block rounded"
                />

                {/* Overlays anchored strictly to the image canvas */}
                {overlaysActive &&
                  regions.map((r) => {
                    const isSelected = selectedRegion?.id === r.id;
                    const borderColor =
                      r.type === 'qr_forgery'
                        ? 'border-rose-500 bg-rose-500/20'
                        : r.type === 'pixel_splice'
                        ? 'border-amber-500 bg-amber-500/20'
                        : 'border-cyan-400 bg-cyan-400/15';

                    return (
                      <div
                        key={r.id}
                        onClick={() => setSelectedRegion(r)}
                        style={{
                          left: `${r.x}%`,
                          top: `${r.y}%`,
                          width: `${r.width}%`,
                          height: `${r.height}%`,
                        }}
                        className={`absolute border-2 cursor-pointer transition-all ${borderColor} ${
                          isSelected ? 'ring-2 ring-white z-20' : 'z-10'
                        }`}
                      >
                        <span
                          className={`absolute -top-5 left-0 px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase rounded whitespace-nowrap ${
                            r.type === 'qr_forgery'
                              ? 'bg-rose-600 text-white'
                              : r.type === 'pixel_splice'
                              ? 'bg-amber-600 text-black'
                              : 'bg-cyan-600 text-white'
                          }`}
                        >
                          {r.label} ({r.confidence}%)
                        </span>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <span className="text-xs text-slate-500">Awaiting document upload</span>
            )}
          </div>
        </div>
      </div>

      {/* Detected Evidence Summary Cards */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <div className="text-xs text-slate-400 uppercase font-semibold mb-2">
          Detected Evidence Regions ({regions.length})
        </div>
        {regions.length === 0 ? (
          <div className="text-xs text-slate-500 italic">No localized manipulation regions flagged.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {regions.map((r) => (
              <div
                key={r.id}
                onClick={() => setSelectedRegion(r)}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                  selectedRegion?.id === r.id
                    ? 'bg-slate-800 border-cyan-500'
                    : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between font-bold mb-1">
                  <span className="text-slate-200">{r.label}</span>
                  <span className="font-mono text-cyan-400">{r.confidence}% Conf.</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">{r.explanation}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
