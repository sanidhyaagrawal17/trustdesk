import { describe, it, expect } from 'vitest';
import { render, act } from '@testing-library/react';
import React, { useState } from 'react';
import { ChatMessage } from '../../types';

// Render tracking registers
let rawCounts: Record<string, number> = {};
let memoCounts: Record<string, number> = {};

// Unmemoized component: spys on render without any props other than `message`
const RawItem: React.FC<{ message: ChatMessage }> = ({ message }) => {
  rawCounts[message.id] = (rawCounts[message.id] || 0) + 1;
  return <div>{message.content}</div>;
};

// Memoized component (identical to ChatMessageItem in App.tsx)
const MemoItem = React.memo<{ message: ChatMessage }>(({ message }) => {
  memoCounts[message.id] = (memoCounts[message.id] || 0) + 1;
  return <div>{message.content}</div>;
});

describe('ChatMessageItem Re-render Profiling (A/B Test)', () => {
  it('measures render counts with and without React.memo across async streaming token ticks', async () => {
    const INITIAL_MESSAGES: ChatMessage[] = [
      { id: 'msg-1', role: 'user', content: 'What is the LTV ratio?', channel: 'untrusted', timestamp: 1 },
      { id: 'msg-2', role: 'assistant', content: 'Synthetic loan LTV is 80%.', channel: 'untrusted', timestamp: 2 },
      { id: 'msg-3', role: 'user', content: 'What about 30 year tenure?', channel: 'untrusted', timestamp: 3 },
      { id: 'msg-4', role: 'assistant', content: '', isStreaming: true, channel: 'untrusted', timestamp: 4 },
    ];

    const TOKENS = ['Maximum ', 'tenure ', 'is ', '300 ', 'months.'];

    // --- TEST A: WITHOUT React.memo ---
    rawCounts = {};
    let updateRaw: (t: string) => void = () => {};

    function RawContainer() {
      const [msgs, setMsgs] = useState<ChatMessage[]>(INITIAL_MESSAGES);
      updateRaw = (t: string) => {
        setMsgs((prev) =>
          prev.map((m) => (m.id === 'msg-4' ? { ...m, content: m.content + t } : m))
        );
      };
      return (
        <div>
          {msgs.map((m) => (
            <RawItem key={m.id} message={m} />
          ))}
        </div>
      );
    }

    const { unmount: unmountRaw } = render(<RawContainer />);

    // Simulate 5 async chunks arriving across separate event loop ticks (as in real fetch reader.read() loop)
    for (const token of TOKENS) {
      await act(async () => {
        updateRaw(token);
        await new Promise((r) => setTimeout(r, 10));
      });
    }

    unmountRaw();

    // --- TEST B: WITH React.memo ---
    memoCounts = {};
    let updateMemo: (t: string) => void = () => {};

    function MemoContainer() {
      const [msgs, setMsgs] = useState<ChatMessage[]>(INITIAL_MESSAGES);
      updateMemo = (t: string) => {
        setMsgs((prev) =>
          prev.map((m) => (m.id === 'msg-4' ? { ...m, content: m.content + t } : m))
        );
      };
      return (
        <div>
          {msgs.map((m) => (
            <MemoItem key={m.id} message={m} />
          ))}
        </div>
      );
    }

    const { unmount: unmountMemo } = render(<MemoContainer />);

    // Stream the same 5 async chunks
    for (const token of TOKENS) {
      await act(async () => {
        updateMemo(token);
        await new Promise((r) => setTimeout(r, 10));
      });
    }

    unmountMemo();

    console.log('\n================ RE-RENDER PROFILING RESULTS ================');
    console.log(`Streamed: 5 distinct async token chunks into msg-4`);
    console.log('WITHOUT React.memo:');
    console.log(`  msg-1 renders: ${rawCounts['msg-1']} (1 mount + 5 re-renders)`);
    console.log(`  msg-2 renders: ${rawCounts['msg-2']} (1 mount + 5 re-renders)`);
    console.log(`  msg-3 renders: ${rawCounts['msg-3']} (1 mount + 5 re-renders)`);
    console.log(`  msg-4 renders: ${rawCounts['msg-4']} (1 mount + 5 active token renders)`);
    console.log(`  Total prior message renders: ${rawCounts['msg-1'] + rawCounts['msg-2'] + rawCounts['msg-3']}`);

    console.log('\nWITH React.memo:');
    console.log(`  msg-1 renders: ${memoCounts['msg-1']} (1 mount + 0 re-renders)`);
    console.log(`  msg-2 renders: ${memoCounts['msg-2']} (1 mount + 0 re-renders)`);
    console.log(`  msg-3 renders: ${memoCounts['msg-3']} (1 mount + 0 re-renders)`);
    console.log(`  msg-4 renders: ${memoCounts['msg-4']} (1 mount + 5 active token renders)`);
    console.log(`  Total prior message renders: ${memoCounts['msg-1'] + memoCounts['msg-2'] + memoCounts['msg-3']}`);
    console.log('=============================================================\n');

    // Without memo: all prior messages re-render on every token chunk (1 mount + 5 chunks = 6 renders)
    expect(rawCounts['msg-1']).toBe(6);
    expect(rawCounts['msg-2']).toBe(6);
    expect(rawCounts['msg-3']).toBe(6);
    expect(rawCounts['msg-4']).toBe(6);

    // With memo: prior messages stay at 1 render (mount only), skipping all 5 chunk updates!
    expect(memoCounts['msg-1']).toBe(1);
    expect(memoCounts['msg-2']).toBe(1);
    expect(memoCounts['msg-3']).toBe(1);
    expect(memoCounts['msg-4']).toBe(6);
  });
});
