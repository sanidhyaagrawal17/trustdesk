import React, { useState, useRef, useEffect } from 'react';
import { Banner } from './components/Banner';
import { ChannelToggle } from './components/ChannelToggle';
import { ChatMessageItem } from './components/ChatMessageItem';
import { ChatInput } from './components/ChatInput';
import { MetricsDrawer } from './components/MetricsDrawer';
import { ChatMessage, ChannelType } from './types';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [channel, setChannel] = useState<ChannelType>('untrusted');
  const [bearerToken, setBearerToken] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [metricsOpen, setMetricsOpen] = useState<boolean>(false);

  const sessionIdRef = useRef<string>(
    `session-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 7)}`
  );
  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  const handleSendMessage = async (rawQuery: string) => {
    if (isStreaming || !rawQuery.trim()) return;

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `asst-${Date.now()}`;

    const userMsg: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content: rawQuery,
      channel,
      timestamp: Date.now(),
    };

    const initialAsstMsg: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      channel,
      timestamp: Date.now(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, initialAsstMsg]);
    setIsStreaming(true);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (channel === 'trusted' && bearerToken.trim()) {
        headers['Authorization'] = `Bearer ${bearerToken.trim()}`;
      }

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: rawQuery,
          session_id: sessionIdRef.current,
          channel,
        }),
      });

      if (response.status === 401) {
        const errorData = await response.json().catch(() => ({ detail: 'Unauthorized' }));
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: `Channel Authorization Failure (HTTP 401): ${
                    errorData.detail || 'Missing or invalid Bearer token for trusted channel.'
                  }`,
                  isStreaming: false,
                  fallback_triggered: true,
                }
              : msg
          )
        );
        setIsStreaming(false);
        return;
      }

      if (!response.ok || !response.body) {
        throw new Error(`HTTP Error ${response.status}: Failed to establish SSE stream`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      const processEventBlock = (eventBlock: string) => {
        if (!eventBlock.trim()) return;

        let eventType = 'message';
        let dataStr = '';

        const lines = eventBlock.split(/\r?\n/);
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('event:')) {
            eventType = trimmed.slice(6).trim();
          } else if (trimmed.startsWith('data:')) {
            const val = trimmed.slice(5).trim();
            dataStr = dataStr ? `${dataStr}\n${val}` : val;
          }
        }

        if (!dataStr) return;

        try {
          const parsed = JSON.parse(dataStr);

          if (eventType === 'token') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + (parsed.token || '') }
                  : msg
              )
            );
          } else if (eventType === 'metadata') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      trace_id: parsed.trace_id,
                      retriever_used: parsed.retriever_used,
                      grounding_score: parsed.grounding_score,
                      is_grounded: parsed.is_grounded,
                      fallback_triggered: parsed.fallback_triggered,
                      injection_detected: parsed.injection_detected,
                    }
                  : msg
              )
            );
          } else if (eventType === 'done') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
              )
            );
          }
        } catch (e) {
          console.warn('[SSE Parse Error]', e, eventBlock);
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // Handle both CRLF (\r\n\r\n) and LF (\n\n) SSE block delimiters
        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() || '';

        for (const eventBlock of events) {
          processEventBlock(eventBlock);
        }
      }

      // Process any trailing event block when stream completes
      if (buffer.trim()) {
        processEventBlock(buffer);
      }
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `Network / Gateway Error: ${err.message || 'Stream interrupted'}.`,
                isStreaming: false,
                fallback_triggered: true,
              }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
        )
      );
    }
  };

  const handleClearChat = () => {
    if (isStreaming) return;
    setMessages([]);
    sessionIdRef.current = `session-${Date.now().toString(36)}-${Math.random()
      .toString(36)
      .substring(2, 7)}`;
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      {/* Top Banner */}
      <Banner />

      {/* Main Header */}
      <header className="border-b border-zinc-800 bg-zinc-950/70 backdrop-blur-md px-4 py-3 shrink-0">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center font-mono font-bold text-blue-400 text-sm">
              TD
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold tracking-wide text-zinc-100">
                  TrustDesk
                </h1>
                <span className="font-mono text-[10px] text-zinc-400 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded">
                  v0.1.0-synthetic
                </span>
              </div>
              <p className="text-[11px] text-zinc-500 font-mono">
                LangGraph Agent • Dual-Mode Storage • 5-Step PII Guardrail
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] text-zinc-500 hidden md:inline">
              Session: {sessionIdRef.current.substring(0, 16)}...
            </span>
            <button
              type="button"
              onClick={handleClearChat}
              disabled={isStreaming || messages.length === 0}
              className="px-2.5 py-1 text-xs font-medium rounded text-zinc-400 hover:text-zinc-200 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 transition-colors disabled:opacity-40"
            >
              Reset Session
            </button>
            <button
              type="button"
              onClick={() => setMetricsOpen(true)}
              className="px-2.5 py-1 text-xs font-medium rounded bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/20 transition-colors flex items-center gap-1.5"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
              Runtime Telemetry
            </button>
          </div>
        </div>
      </header>

      {/* Main Chat Workspace */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 flex flex-col min-h-0">
        {/* Channel Selection Bar */}
        <div className="pb-3 shrink-0">
          <ChannelToggle
            channel={channel}
            bearerToken={bearerToken}
            onChannelChange={setChannel}
            onBearerTokenChange={setBearerToken}
            disabled={isStreaming}
          />
        </div>

        {/* Message Thread */}
        <div
          ref={chatScrollRef}
          className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent min-h-0"
        >
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-zinc-500 space-y-3">
              <div className="w-12 h-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center font-mono text-zinc-400 text-lg">
                TD
              </div>
              <div className="max-w-md space-y-1">
                <h3 className="text-zinc-200 text-sm font-semibold">
                  Synthetic Loan-FAQ Conversational Assistant
                </h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Demonstrates real LangGraph agent loops, dense ChromaDB retrieval with TF-IDF fallback,
                  5-step PII masking (Luhn card, Aadhaar, mobile, PAN, email), heuristic injection defense,
                  and SSE token streaming.
                </p>
              </div>
              <div className="text-[11px] font-mono text-zinc-600">
                Notice: All numbers and rates are synthetic demonstration data.
              </div>
            </div>
          ) : (
            messages.map((msg) => <ChatMessageItem key={msg.id} message={msg} />)
          )}
        </div>

        {/* Bottom Input Area */}
        <div className="pt-2 shrink-0 border-t border-zinc-900">
          <ChatInput onSendMessage={handleSendMessage} disabled={isStreaming} />
        </div>
      </main>

      {/* Telemetry Drawer */}
      <MetricsDrawer isOpen={metricsOpen} onClose={() => setMetricsOpen(false)} />
    </div>
  );
};
