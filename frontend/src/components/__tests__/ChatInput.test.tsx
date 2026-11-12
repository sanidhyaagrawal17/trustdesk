import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { axe } from 'jest-axe';
import { ChatInput } from '../ChatInput';

describe('ChatInput Component', () => {
  it('updates text state and fires onSendMessage on Enter keypress', () => {
    const handleSend = vi.fn();
    render(<ChatInput onSendMessage={handleSend} />);

    const textarea = screen.getByLabelText(/Ask a loan question/i);
    fireEvent.change(textarea, { target: { value: 'What is the LTV limit?' } });
    expect(textarea).toHaveValue('What is the LTV limit?');

    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
    expect(handleSend).toHaveBeenCalledWith('What is the LTV limit?');
    expect(textarea).toHaveValue('');
  });

  it('allows multi-line entry with Shift+Enter without sending', () => {
    const handleSend = vi.fn();
    render(<ChatInput onSendMessage={handleSend} />);

    const textarea = screen.getByLabelText(/Ask a loan question/i);
    fireEvent.change(textarea, { target: { value: 'Line 1' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
    expect(handleSend).not.toHaveBeenCalled();
  });

  it('populates and sends message when clicking a sample query button', () => {
    const handleSend = vi.fn();
    render(<ChatInput onSendMessage={handleSend} />);

    const sampleBtn = screen.getByRole('button', { name: 'FAQ Query' });
    fireEvent.click(sampleBtn);
    expect(handleSend).toHaveBeenCalledWith('What is the synthetic home loan interest rate and minimum tenure?');
  });

  it('shows Stop button during active streaming and triggers onStopStreaming', () => {
    const handleSend = vi.fn();
    const handleStop = vi.fn();

    render(
      <ChatInput
        onSendMessage={handleSend}
        onStopStreaming={handleStop}
        isStreaming={true}
      />
    );

    const stopBtn = screen.getByRole('button', { name: /Stop/i });
    expect(stopBtn).toBeInTheDocument();
    fireEvent.click(stopBtn);
    expect(handleStop).toHaveBeenCalledTimes(1);
  });

  it('disables input when disabled prop is passed', () => {
    render(<ChatInput onSendMessage={() => {}} disabled={true} />);

    const textarea = screen.getByLabelText(/Ask a loan question/i);
    expect(textarea).toBeDisabled();
  });

  it('passes automated axe accessibility audit with 0 violations', async () => {
    const { container } = render(
      <ChatInput
        onSendMessage={() => {}}
        onStopStreaming={() => {}}
        isStreaming={false}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
