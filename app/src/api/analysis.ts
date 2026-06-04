// 分析API客户端
import { fetchJSON } from './portfolio';

export interface AnalysisReport {
  id: number;
  symbol: string;
  report_type: string;
  title: string;
  summary: string;
  verdict: string;
  confidence: number;
  price_target?: number;
  risk_level: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export const analysisApi = {
  getReports: (params?: { symbol?: string; industry?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.symbol) q.set('symbol', params.symbol);
    if (params?.industry) q.set('industry', params.industry);
    if (params?.limit) q.set('limit', String(params.limit));
    return fetchJSON<AnalysisReport[]>(`/api/analysis?${q.toString()}`);
  },
  getLatestBySymbol: (symbol: string) => fetchJSON<AnalysisReport>(`/api/analysis/by-symbol/${symbol}/latest`),
  createReport: (body: Partial<AnalysisReport>) => fetchJSON<AnalysisReport>('/api/analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
};
