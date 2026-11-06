import React, { useEffect, useState } from 'react';
import { RuntimeMetrics, SystemHealth } from '../types';

interface MetricsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MetricsDrawer: React.FC<MetricsDrawerProps> = ({ isOpen, onClose }) => {
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDiagnostics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [mRes, hRes] = await Promise.all([
        fetch('/api/metrics'),
        fetch('/api/health'),
      ]);

      if (mRes.ok) {
        const mData = await mRes.json();
        setMetrics(mData);
      }
      if (hRes.ok) {
        const hData = await hRes.json();
        setHealth(hData);
      }
    } catch (err) {
      setError('Unable to connect to backend telemetry service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDiagnostics();
      const timer = setInterval(fetchDiagnostics, 6000);
      return () => clearInterval(timer);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-zinc-950 border-l border-zinc-800 p-5 shadow-2xl z-50 overflow-y-auto font-sans flex flex-col justify-between">
      <div className="space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div>
            <h2 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider">
              Runtime Telemetry
            </h2>
            <p className="text-xs text-zinc-400">Live operational & audit metrics</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-100 p-1 rounded hover:bg-zinc-900 transition-colors text-sm"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="p-3 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono">
            {error}
          </div>
        )}

        {/* System & Storage Adapters */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3 space-y-2">
          <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            System Adapters (Dual-Mode)
          </div>
          <div className="text-xs space-y-1.5 font-mono text-zinc-300">
            <div className="flex justify-between items-center">
              <span className="text-zinc-500">Service:</span>
              <span>{health?.service || 'trustdesk-api'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-zinc-500">Environment:</span>
              <span className="text-amber-400">{health?.environment || 'synthetic-demo'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-zinc-500">Session Store:</span>
              <span className="text-emerald-400">
                {health?.storage_adapters?.session_store || 'in-memory (dual-mode)'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-zinc-500">Audit Logger:</span>
              <span className="text-emerald-400">
                {health?.storage_adapters?.audit_logger || 'sqlite (dual-mode)'}
              </span>
            </div>
          </div>
        </div>

        {/* Core Metrics */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3 space-y-2">
          <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            Request Traffic
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800/80">
              <div className="text-zinc-500 text-[10px]">TOTAL CALLS</div>
              <div className="text-lg font-bold text-zinc-100">
                {metrics?.total_requests ?? 0}
              </div>
            </div>
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800/80">
              <div className="text-zinc-500 text-[10px]">AVG LATENCY</div>
              <div className="text-lg font-bold text-blue-400">
                {(metrics?.average_latency_ms ?? 0).toFixed(1)}ms
              </div>
            </div>
          </div>
          <div className="text-xs font-mono space-y-1 pt-1 text-zinc-400">
            <div className="flex justify-between">
              <span>Untrusted Channel:</span>
              <span className="text-zinc-200">
                {metrics?.requests_by_channel?.untrusted ?? 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Trusted Channel:</span>
              <span className="text-zinc-200">
                {metrics?.requests_by_channel?.trusted ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* Security & Masking Stats */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3 space-y-2">
          <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            Security & PII Masking
          </div>
          <div className="text-xs font-mono space-y-1 text-zinc-300">
            <div className="flex justify-between">
              <span className="text-zinc-500">Heuristic Injections Blocked:</span>
              <span className="text-rose-400 font-bold">
                {metrics?.injection_attempts ?? 0}
              </span>
            </div>
            <div className="pt-2 border-t border-zinc-800/80 space-y-1 text-zinc-400">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wider">
                Masked PII Tokens:
              </div>
              {Object.entries(metrics?.pii_masked_count || {}).map(([key, count]) => (
                <div key={key} className="flex justify-between">
                  <span className="capitalize">{key}:</span>
                  <span className="text-zinc-200">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Intent Distribution */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3 space-y-2">
          <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            Intents Handled
          </div>
          <div className="text-xs font-mono space-y-1 text-zinc-300">
            {Object.entries(metrics?.intents_classified || {}).length === 0 ? (
              <div className="text-zinc-500 italic text-[11px]">No requests recorded yet</div>
            ) : (
              Object.entries(metrics?.intents_classified || {}).map(([intent, count]) => (
                <div key={intent} className="flex justify-between items-center">
                  <span className="text-zinc-400">{intent}</span>
                  <span className="px-1.5 py-0.5 rounded bg-zinc-950 border border-zinc-800 text-zinc-200">
                    {count}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-zinc-800 text-center space-y-2">
        <button
          type="button"
          onClick={fetchDiagnostics}
          disabled={loading}
          className="w-full py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white rounded border border-zinc-800 text-xs font-medium transition-colors"
        >
          {loading ? 'Refreshing telemetry...' : 'Refresh Metrics'}
        </button>
        <p className="text-[10px] text-zinc-500 font-mono">
          Data sourced from dual-mode in-memory & SQLite telemetry collectors
        </p>
      </div>
    </div>
  );
};
