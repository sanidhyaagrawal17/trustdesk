export type ChannelType = 'untrusted' | 'trusted';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  trace_id?: string;
  retriever_used?: string;
  grounding_score?: number;
  is_grounded?: boolean;
  fallback_triggered?: boolean;
  injection_detected?: boolean;
  channel?: ChannelType;
  timestamp: number;
  isStreaming?: boolean;
}

export interface RuntimeMetrics {
  total_requests: number;
  requests_by_channel: Record<string, number>;
  intents_classified: Record<string, number>;
  injection_attempts: number;
  pii_masked_count: Record<string, number>;
  average_latency_ms: number;
}

export interface SystemHealth {
  status: string;
  service: string;
  environment: string;
  regulatory_notice: string;
  storage_adapters: {
    session_store: string;
    audit_logger: string;
  };
}
