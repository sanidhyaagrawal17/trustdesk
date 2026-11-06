import React from 'react';
import { ChannelType } from '../types';

interface ChannelToggleProps {
  channel: ChannelType;
  bearerToken: string;
  onChannelChange: (channel: ChannelType) => void;
  onBearerTokenChange: (token: string) => void;
  disabled?: boolean;
}

export const ChannelToggle: React.FC<ChannelToggleProps> = ({
  channel,
  bearerToken,
  onChannelChange,
  onBearerTokenChange,
  disabled = false,
}) => {
  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-3 text-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-zinc-400 font-medium text-xs uppercase tracking-wider">
            Execution Channel:
          </span>
          <div className="inline-flex rounded-md p-0.5 bg-zinc-950 border border-zinc-800">
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChannelChange('untrusted')}
              className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                channel === 'untrusted'
                  ? 'bg-zinc-800 text-zinc-100 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              } disabled:opacity-50`}
            >
              Untrusted (Public)
            </button>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onChannelChange('trusted')}
              className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                channel === 'trusted'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              } disabled:opacity-50`}
            >
              Trusted (Internal)
            </button>
          </div>
        </div>

        {channel === 'untrusted' ? (
          <div className="text-xs text-zinc-500 font-mono">
            Mode: Restricted tools • Full 5-step PII masking • Anonymous access
          </div>
        ) : (
          <div className="flex items-center gap-2 flex-1 sm:max-w-md">
            <input
              type="password"
              placeholder="Enter Bearer token (TRUSTED_CHANNEL_SECRET)..."
              value={bearerToken}
              disabled={disabled}
              onChange={(e) => onBearerTokenChange(e.target.value)}
              className="w-full px-2.5 py-1 text-xs bg-zinc-950 border border-zinc-800 rounded font-mono text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
            <span className="text-[10px] text-zinc-500 font-mono whitespace-nowrap hidden md:inline">
              HMAC SHA-256
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
