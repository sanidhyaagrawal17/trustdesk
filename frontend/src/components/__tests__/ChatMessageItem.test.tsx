import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import { ChatMessageItem } from '../ChatMessageItem';
import { ChatMessage } from '../../types';

describe('ChatMessageItem Component', () => {
  it('renders user query accurately with role formatting', () => {
    const userMsg: ChatMessage = {
      id: 'msg-1',
      role: 'user',
      content: 'What is the synthetic home loan interest rate?',
      channel: 'untrusted',
      timestamp: Date.now(),
    };

    render(<ChatMessageItem message={userMsg} />);
    expect(screen.getByText('User Query')).toBeInTheDocument();
    expect(screen.getByText('What is the synthetic home loan interest rate?')).toBeInTheDocument();
    expect(screen.getByText('untrusted')).toBeInTheDocument();
  });

  it('renders assistant response with chroma retriever and grounding score metadata', () => {
    const assistantMsg: ChatMessage = {
      id: 'msg-2',
      role: 'assistant',
      content: 'The interest rate starts at 8.5% p.a.',
      channel: 'trusted',
      trace_id: 'tr-abc-123',
      retriever_used: 'chroma',
      grounding_score: 0.92,
      is_grounded: true,
      timestamp: Date.now(),
    };

    render(<ChatMessageItem message={assistantMsg} />);
    expect(screen.getByText('TrustDesk Assistant')).toBeInTheDocument();
    expect(screen.getByText('The interest rate starts at 8.5% p.a.')).toBeInTheDocument();
    expect(screen.getByText('tr-abc-123')).toBeInTheDocument();
    expect(screen.getByText(/Retriever: chroma/i)).toBeInTheDocument();
    expect(screen.getByText(/Grounding: 92% \(Verified\)/i)).toBeInTheDocument();
  });

  it('displays streaming pulse indicator when isStreaming is true', () => {
    const streamingMsg: ChatMessage = {
      id: 'msg-3',
      role: 'assistant',
      content: 'Synthesizing response...',
      isStreaming: true,
      timestamp: Date.now(),
    };

    const { container } = render(<ChatMessageItem message={streamingMsg} />);
    const pulseIndicator = container.querySelector('.animate-pulse');
    expect(pulseIndicator).not.toBeNull();
    // Metadata section should be hidden during streaming
    expect(screen.queryByText(/Retriever:/i)).toBeNull();
  });

  it('displays heuristic refusal pill when injection is detected', () => {
    const refusalMsg: ChatMessage = {
      id: 'msg-4',
      role: 'assistant',
      content: 'I cannot process prompt injection attempts.',
      injection_detected: true,
      timestamp: Date.now(),
    };

    render(<ChatMessageItem message={refusalMsg} />);
    expect(screen.getByText(/Heuristic Screening: Refusal Triggered/i)).toBeInTheDocument();
  });

  it('passes automated axe accessibility audit with 0 violations', async () => {
    const msg: ChatMessage = {
      id: 'msg-5',
      role: 'assistant',
      content: 'Accessible content test block.',
      trace_id: 'tr-test-axe',
      retriever_used: 'networkx',
      grounding_score: 0.85,
      is_grounded: true,
      timestamp: Date.now(),
    };

    const { container } = render(<ChatMessageItem message={msg} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
