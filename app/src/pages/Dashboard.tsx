import { useEffect, useState } from 'react';
import { portfolioApi, type HealthScore, type RiskMetrics, type CorrelationPair } from '../api/portfolio';
import { analysisApi, type AnalysisReport } from '../api/analysis';
import { signalsApi, type TradingSignal } from '../api/signals';
import {
  Heart, TrendingUp, AlertTriangle, Zap,
  ChevronRight, Loader2, BarChart3
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

// ── 工具函数 ──
function scoreColor(score: number): string {
  if (score >= 80) return '#10B981';
  if (score >= 60) return '#F59E0B';
  return '#EF4444';
}

function riskColor(val: number, type: 'sharpe' | 'drawdown'): string {
  if (type === 'sharpe') {
    if (val >= 1.5) return '#10B981';
    if (val >= 0.5) return '#F59E0B';
    return '#EF4444';
  }
  // drawdown: lower is better
  if (val <= 10) return '#10B981';
  if (val <= 20) return '#F59E0B';
  return '#EF4444';
}

function verdictColor(v: string): string {
  if (v?.includes('buy') || v?.includes('强')) return '#10B981';
  if (v?.includes('hold') || v?.includes('中')) return '#F59E0B';
  if (v?.includes('avoid') || v?.includes('空')) return '#EF4444';
  return '#6B7280';
}

// ── 主组件 ──
export default function Dashboard() {
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [risk, setRisk] = useState<RiskMetrics | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationPair[]>([]);
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [reports, setReports] = useState<AnalysisReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [h, r, c, s, a] = await Promise.all([
          portfolioApi.getHealthScore().catch(() => null),
          portfolioApi.getRiskMetrics().catch(() => null),
          portfolioApi.getCorrelation().catch(() => ({ high_correlation_pairs: [] as CorrelationPair[] })),
          signalsApi.getSignals({ limit: 5 }).catch(() => []),
          analysisApi.getReports({ limit: 5 }).catch(() => []),
        ]);
        setHealth(h);
        setRisk(r);
        setCorrelation(c?.high_correlation_pairs || []);
        setSignals(s);
        setReports(a);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-[#10B981]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card bg-red-50 border-red-200 text-red-700 text-center py-12">
        <AlertTriangle className="w-10 h-10 mx-auto mb-3" />
        加载失败：{error}
      </div>
    );
  }

  // 雷达图数据
  const radarData = health ? [
    { subject: 'AI集中度', A: health.ai_concentration_score, full: 100 },
    { subject: '港股占比', A: health.hk_weight_score, full: 100 },
    { subject: '亏损控制', A: health.high_loss_count_score, full: 100 },
    { subject: '防御资产', A: health.defensive_ratio_score, full: 100 },
    { subject: '现金预留', A: health.cash_reserve_score, full: 100 },
    { subject: '集中度风险', A: health.concentration_risk_score, full: 100 },
  ] : [];

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">仪表盘</h1>
        <span className="text-sm text-slate-500">
          {new Date().toLocaleString('zh-CN')}
        </span>
      </div>

      {/* 顶部三卡片：健康评分 + 夏普 + 回撤 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 健康评分 */}
        <div className="card relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Heart className="w-5 h-5 text-[#10B981]" />
              <span className="font-semibold text-slate-700">组合健康评分</span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
              {health?.risk_level || '-'}
            </span>
          </div>
          <div className="text-4xl font-bold" style={{ color: scoreColor(health?.total_score || 0) }}>
            {health?.total_score ?? '-'}
            <span className="text-lg text-slate-400">/100</span>
          </div>
          {health && (
            <div className="mt-3 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                  <Radar dataKey="A" stroke="#10B981" fill="#10B981" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* 夏普比率 */}
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-[#10B981]" />
            <span className="font-semibold text-slate-700">夏普比率</span>
          </div>
          <div className="text-3xl font-bold" style={{ color: riskColor(risk?.sharpe_ratio || 0, 'sharpe') }}>
            {risk?.sharpe_ratio?.toFixed(2) ?? '-'}
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {risk && risk.sharpe_ratio >= 1.5 ? '优秀' : risk && risk.sharpe_ratio >= 0.5 ? '一般' : '较差'}
          </p>
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">年化收益</span>
              <span className="font-medium">{risk?.annual_return?.toFixed(1) ?? '-'}%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">波动率</span>
              <span className="font-medium">{risk?.volatility?.toFixed(1) ?? '-'}%</span>
            </div>
          </div>
        </div>

        {/* 最大回撤 */}
        <div className="card">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-[#F59E0B]" />
            <span className="font-semibold text-slate-700">最大回撤</span>
          </div>
          <div className="text-3xl font-bold" style={{ color: riskColor(risk?.max_drawdown || 0, 'drawdown') }}>
            {risk?.max_drawdown?.toFixed(1) ?? '-'}%
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {risk && risk.max_drawdown <= 10 ? '风险可控' : risk && risk.max_drawdown <= 20 ? '注意风险' : '高风险'}
          </p>
          <div className="mt-4">
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all"
                style={{
                  width: `${Math.min((risk?.max_drawdown || 0) / 30 * 100, 100)}%`,
                  backgroundColor: riskColor(risk?.max_drawdown || 0, 'drawdown')
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 第二行：相关性矩阵 + 最新信号 + 最新分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 高相关性风险 */}
        <div className="card">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-5 h-5 text-[#F59E0B]" />
            <span className="font-semibold text-slate-700">高相关性风险</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-50 text-[#F59E0B]">
              {correlation.length} 对
            </span>
          </div>
          {correlation.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">暂无高相关性标的对</p>
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={correlation.slice(0, 6)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <YAxis type="category" dataKey="symbol_a" width={60} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
                  <Bar dataKey="correlation" radius={[0, 4, 4, 0]}>
                    {correlation.slice(0, 6).map((_, i) => (
                      <Cell key={i} fill="#F59E0B" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className="mt-2 space-y-1 max-h-32 overflow-auto">
            {correlation.slice(0, 5).map((pair, i) => (
              <div key={i} className="flex items-center justify-between text-sm py-1 px-2 rounded bg-slate-50">
                <span className="text-slate-600">{pair.symbol_a} ↔ {pair.symbol_b}</span>
                <span className="font-medium text-[#F59E0B]">{(pair.correlation * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* 最新信号 */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-[#EF4444]" />
              <span className="font-semibold text-slate-700">最新信号</span>
            </div>
            <span className="text-xs text-slate-400">{signals.length} 条</span>
          </div>
          <div className="space-y-2 max-h-72 overflow-auto">
            {signals.length === 0 ? (
              <p className="text-sm text-slate-400 py-4 text-center">暂无信号</p>
            ) : (
              signals.map((s) => (
                <div key={s.id} className="flex items-start gap-2 p-2 rounded-lg bg-slate-50">
                  <div
                    className="w-2 h-2 rounded-full mt-1.5 shrink-0"
                    style={{ backgroundColor: s.direction === 'long' ? '#10B981' : '#EF4444' }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1">
                      <span className="font-medium text-sm">{s.symbol}</span>
                      <span className="text-xs px-1.5 rounded bg-white border text-slate-500">{s.signal_type}</span>
                    </div>
                    <p className="text-xs text-slate-500 truncate">{s.rationale}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-400">置信度 {Math.round(s.confidence * 100)}%</span>
                      <span className="text-xs px-1.5 rounded" style={{
                        backgroundColor: s.status === 'active' ? '#10B98120' : '#EF444420',
                        color: s.status === 'active' ? '#10B981' : '#EF4444'
                      }}>
                        {s.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 最新分析 */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-[#10B981]" />
              <span className="font-semibold text-slate-700">最新分析</span>
            </div>
            <span className="text-xs text-slate-400">{reports.length} 条</span>
          </div>
          <div className="space-y-2 max-h-72 overflow-auto">
            {reports.length === 0 ? (
              <p className="text-sm text-slate-400 py-4 text-center">暂无分析报告</p>
            ) : (
              reports.map((r) => (
                <div key={r.id} className="p-2 rounded-lg bg-slate-50 group cursor-pointer hover:bg-slate-100 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">{r.symbol}</span>
                    <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500" />
                  </div>
                  <p className="text-xs text-slate-500 truncate mt-0.5">{r.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs font-medium px-1.5 rounded" style={{
                      backgroundColor: verdictColor(r.verdict) + '20',
                      color: verdictColor(r.verdict)
                    }}>
                      {r.verdict}
                    </span>
                    <span className="text-xs text-slate-400">
                      置信度 {Math.round(r.confidence * 100)}%
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
