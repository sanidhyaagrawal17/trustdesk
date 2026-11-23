import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MetricsDrawer } from '../MetricsDrawer';

describe('MetricsDrawer', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('unwraps the nested { metrics, storage_adapters } envelope from /api/metrics', async () => {
    const mockFetch = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input);
      if (url.includes('/api/metrics')) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              metrics: {
                total_requests: 7,
                requests_by_channel: { untrusted: 5, trusted: 2 },
                intents_classified: { faq_lookup: 5, injection_refusal: 2 },
                injection_attempts: 2,
                pii_masked_count: { aadhaar: 1, phone: 2 },
                average_latency_ms: 14.5,
              },
              storage_adapters: {
                session_store: 'in-memory',
                audit_logger: 'sqlite',
              },
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
          )
        );
      }
      return Promise.resolve(
        new Response(
          JSON.stringify({
            status: 'healthy',
            service: 'TrustDesk',
            environment: 'synthetic_demonstration',
            regulatory_notice: 'Synthetic demo',
            storage_adapters: {
              session_store: 'in-memory',
              audit_logger: 'sqlite',
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );
    });

    render(<MetricsDrawer isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('7')).toBeInTheDocument();
      expect(screen.getByText('14.5ms')).toBeInTheDocument();
      expect(screen.getByText('faq_lookup')).toBeInTheDocument();
    });
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
