import React from 'react';

export const Banner: React.FC = () => {
  return (
    <div className="w-full bg-zinc-900 border-b border-zinc-800 px-4 py-2 text-xs">
      <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded font-mono text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            DEMO MODE
          </span>
          <span className="text-zinc-300 font-medium">
            TrustDesk Synthetic Demonstration
          </span>
          <span className="text-zinc-500 hidden sm:inline">|</span>
          <span className="text-zinc-400 hidden sm:inline">
            Technical demonstration on synthetic data. Not a regulated banking system.
          </span>
        </div>
        <div className="flex items-center gap-3 text-zinc-400 font-mono text-[11px]">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Streaming API (SSE)
          </span>
          <span className="text-zinc-600">•</span>
          <span>Zero-Key Mock LLM</span>
        </div>
      </div>
    </div>
  );
};
