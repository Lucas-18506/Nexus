// 持仓API客户端
const API_BASE = import.meta.env.VITE_API_BASE || '';

export async function fetchJSON<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, opts);
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
  const data = await res.json();
  if (!data.success) throw new Error(data.message || 'API error');
  return data.data;
}

export interface Position {
  id: number;
  ticker: string;
  market: string;
  name: string;
  name_cn?: string;
  quantity: number;
  avg_cost: number;
  current_price?: number;
  currency: string;
  sector?: string;
  industry?: string;
  position_type: string;
  unrealized_pnl?: number;
  realized_pnl?: number;
  total_return_pct?: number;
  weight_pct?: number;
  tags?: string[];
  analyst_rating?: string;
  target_price?: number;
  stop_loss?: number;
}

export interface HealthScore {
  total_score: number;
  ai_concentration_score: number;
  hk_weight_score: number;
  high_loss_count_score: number;
  defensive_ratio_score: number;
  cash_reserve_score: number;
  concentration_risk_score: number;
  risk_level: string;
  details: Record<string, any>;
}

export interface RiskMetrics {
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  annual_return: number;
  risk_free_rate: number;
}

export interface CorrelationPair {
  symbol_a: string;
  symbol_b: string;
  correlation: number;
}

export interface CorrelationMatrix {
  matrix: CorrelationPair[];
  top_pairs: CorrelationPair[];
  high_correlation_pairs: CorrelationPair[];
}

export const portfolioApi = {
  getPositions: () => fetchJSON<Position[]>('/api/portfolio/positions'),
  getHealthScore: () => fetchJSON<HealthScore>('/api/portfolio/health-score'),
  getRiskMetrics: () => fetchJSON<RiskMetrics>('/api/portfolio/risk-metrics'),
  getCorrelation: () => fetchJSON<CorrelationMatrix>('/api/portfolio/correlation'),
};
