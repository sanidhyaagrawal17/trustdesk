import React from 'react';
import { ChatMessage } from '../types';

interface ChatMessageItemProps {
  message: ChatMessage;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex flex-col gap-2 py-3 px-4 rounded-xl transition-colors ${
        isUser
          ? 'bg-zinc-900/60 border border-zinc-800/80 ml-8 sm:ml-16'
          : 'bg-zinc-950/80 border border-zinc-800 mr-8 sm:mr-16'
      }`}
    >
      <div className="flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center gap-2">
          <span
            className={`font-semibold tracking-wide uppercase text-[11px] ${
              isUser ? 'text-zinc-300' : 'text-blue-400'
            }`}
          >
            {isUser ? 'User Query' : 'TrustDesk Assistant'}
          </span>
          {message.channel && (
            <span className="font-mono text-[10px] text-zinc-500 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">
              {message.channel}
            </span>
          )}
        </div>

        {message.trace_id && (
          <span
            className="font-mono text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
            title="Trace ID (recorded in audit log)"
          >
            {message.trace_id}
          </span>
        )}
      </div>

      <div className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap font-sans">
        {message.content}
        {message.isStreaming && (
          <span className="inline-block w-1.5 h-4 ml-1 bg-blue-500 animate-pulse align-middle" />
        )}
      </div>

      {!isUser && !message.isStreaming && (
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-zinc-900/80 text-[11px] font-mono">
          {message.retriever_used && message.retriever_used !== 'none' && (
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${
                message.retriever_used === 'chroma'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}
            >
              <span className="w-1 h-1 rounded-full bg-current"></span>
              Retriever: {message.retriever_used}
            </span>
          )}

          {typeof message.grounding_score === 'number' && (
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${
                message.is_grounded
                  ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                  : 'bg-zinc-800/80 text-zinc-400 border-zinc-700/50'
              }`}
            >
              Grounding: {(message.grounding_score * 100).toFixed(0)}%
              {message.is_grounded ? ' (Verified)' : ' (Low overlap)'}
            </span>
          )}

          {message.fallback_triggered && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Fallback Invoked
            </span>
          )}

          {message.injection_detected && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
              Heuristic Screening: Refusal Triggered
            </span>
          )}
        </div>
      )}
    </div>
  );
};
