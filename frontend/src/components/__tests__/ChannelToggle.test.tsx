import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { axe } from 'jest-axe';
import { ChannelToggle } from '../ChannelToggle';

describe('ChannelToggle Component', () => {
  it('renders untrusted channel as default active state', () => {
    const handleChannelChange = vi.fn();
    const handleBearerTokenChange = vi.fn();

    render(
      <ChannelToggle
        channel="untrusted"
        bearerToken=""
        onChannelChange={handleChannelChange}
        onBearerTokenChange={handleBearerTokenChange}
      />
    );

    const untrustedBtn = screen.getByRole('button', { name: /Untrusted \(Public\)/i });
    expect(untrustedBtn).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText(/Full 5-step PII masking/i)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Enter Bearer token/i)).toBeNull();
  });

  it('renders Bearer token input when switched to trusted channel', () => {
    const handleChannelChange = vi.fn();
    const handleBearerTokenChange = vi.fn();

    render(
      <ChannelToggle
        channel="trusted"
        bearerToken="secret-test-token"
        onChannelChange={handleChannelChange}
        onBearerTokenChange={handleBearerTokenChange}
      />
    );

    const trustedBtn = screen.getByRole('button', { name: /Trusted \(Internal\)/i });
    expect(trustedBtn).toHaveAttribute('aria-pressed', 'true');

    const input = screen.getByPlaceholderText(/Enter Bearer token/i);
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('secret-test-token');

    fireEvent.change(input, { target: { value: 'new-token' } });
    expect(handleBearerTokenChange).toHaveBeenCalledWith('new-token');
  });

  it('invokes channel switch callback on button click', () => {
    const handleChannelChange = vi.fn();
    const handleBearerTokenChange = vi.fn();

    render(
      <ChannelToggle
        channel="untrusted"
        bearerToken=""
        onChannelChange={handleChannelChange}
        onBearerTokenChange={handleBearerTokenChange}
      />
    );

    const trustedBtn = screen.getByRole('button', { name: /Trusted \(Internal\)/i });
    fireEvent.click(trustedBtn);
    expect(handleChannelChange).toHaveBeenCalledWith('trusted');
  });

  it('passes automated axe accessibility audit with 0 violations', async () => {
    const { container } = render(
      <ChannelToggle
        channel="trusted"
        bearerToken="test-token"
        onChannelChange={() => {}}
        onBearerTokenChange={() => {}}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
