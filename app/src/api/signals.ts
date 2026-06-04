// 信号API客户端
import { fetchJSON } from './portfolio';

export interface TradingSignal {
  id: number;
  symbol: string;
  signal_type: string;
  action: string;
  direction: string;
  strength: number;
  price_entry?: number;
  price_target?: number;
  price_stop?: number;
  confidence: number;
  rationale: string;
  status: string;
  created_at: string;
  triggered_at?: string;
}

export const signalsApi = {
  getSignals: (params?: { status?: string; symbol?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
    if (params?.symbol) q.set('symbol', params.symbol);
    if (params?.limit) q.set('limit', String(params.limit));
    return fetchJSON<TradingSignal[]>(`/api/signals?${q.toString()}`);
  },
  createSignal: (body: Partial<TradingSignal>) => fetchJSON<TradingSignal>('/api/signals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
  updateStatus: (id: number, status: string) => fetchJSON<TradingSignal>(`/api/signals/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  }),
};
