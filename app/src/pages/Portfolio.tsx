import { useEffect, useState, useMemo } from 'react';
import { portfolioApi, type Position } from '../api/portfolio';
import {
  TrendingUp, TrendingDown, Search, Loader2,
  ArrowUpDown, Filter
} from 'lucide-react';
import {
  LineChart, Line,
  ResponsiveContainer
} from 'recharts';

// 迷你折线图（模拟）
function MiniChart({ color }: { color: string }) {
  const data = useMemo(() =>
    Array.from({ length: 20 }, (_, i) => ({
      x: i,
      y: 100 + Math.random() * 30 - 15 + (i * (Math.random() - 0.4) * 2)
    })),
    []
  );
  return (
    <ResponsiveContainer width={80} height={30}>
      <LineChart data={data}>
        <Line type="monotone" dataKey="y" stroke={color} strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default function Portfolio() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'ticker' | 'pnl' | 'weight'>('pnl');
  const [marketFilter, setMarketFilter] = useState<string>('all');

  useEffect(() => {
    portfolioApi.getPositions()
      .then(setPositions)
      .catch(() => setPositions([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = [...positions];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(p =>
        p.ticker.toLowerCase().includes(q) ||
        p.name.toLowerCase().includes(q) ||
        (p.name_cn?.includes(q))
      );
    }
    if (marketFilter !== 'all') {
      list = list.filter(p => p.market === marketFilter);
    }
    list.sort((a, b) => {
      if (sortBy === 'ticker') return a.ticker.localeCompare(b.ticker);
      if (sortBy === 'pnl') return (b.unrealized_pnl || 0) - (a.unrealized_pnl || 0);
      if (sortBy === 'weight') return (b.weight_pct || 0) - (a.weight_pct || 0);
      return 0;
    });
    return list;
  }, [positions, search, sortBy, marketFilter]);

  // 汇总
  const totalValue = positions.reduce((s, p) => s + (p.quantity * (p.current_price || p.avg_cost)), 0);
  const totalPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || 0), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-[#10B981]" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">持仓管理</h1>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-slate-500">总持仓: <b className="text-slate-900">{positions.length}</b></span>
          <span className="text-slate-500">总市值: <b className="text-slate-900">${totalValue.toLocaleString()}</b></span>
          <span className={totalPnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}>
            总盈亏: {totalPnl >= 0 ? '+' : ''}${totalPnl.toLocaleString()}
          </span>
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="flex items-center gap-3 bg-white rounded-lg border border-slate-200 p-2">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="搜索股票..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-[#10B981]"
          />
        </div>
        <div className="flex items-center gap-1 text-sm">
          <Filter className="w-4 h-4 text-slate-400" />
          {['all', 'US', 'HK', 'CN'].map(m => (
            <button
              key={m}
              onClick={() => setMarketFilter(m)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                marketFilter === m
                  ? 'bg-[#10B981] text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {m === 'all' ? '全部' : m}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1 text-sm ml-auto">
          <ArrowUpDown className="w-4 h-4 text-slate-400" />
          {[
            { key: 'pnl', label: '盈亏' },
            { key: 'weight', label: '权重' },
            { key: 'ticker', label: '代码' }
          ].map(s => (
            <button
              key={s.key}
              onClick={() => setSortBy(s.key as any)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                sortBy === s.key
                  ? 'bg-slate-800 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* 表格 */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-500">标的</th>
              <th className="px-4 py-3 text-right font-medium text-slate-500">数量</th>
              <th className="px-4 py-3 text-right font-medium text-slate-500">成本</th>
              <th className="px-4 py-3 text-right font-medium text-slate-500">现价</th>
              <th className="px-4 py-3 text-right font-medium text-slate-500">盈亏</th>
              <th className="px-4 py-3 text-right font-medium text-slate-500">收益率</th>
              <th className="px-4 py-3 text-right font-medium text-slate-500">权重</th>
              <th className="px-4 py-3 text-center font-medium text-slate-500">趋势</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(p => {
              const pnl = p.unrealized_pnl || 0;
              const pct = p.total_return_pct || 0;
              const isGain = pnl >= 0;
              return (
                <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900">{p.ticker}</span>
                      <span className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">{p.market}</span>
                    </div>
                    <div className="text-xs text-slate-400">{p.name_cn || p.name}</div>
                  </td>
                  <td className="px-4 py-3 text-right">{p.quantity}</td>
                  <td className="px-4 py-3 text-right">${p.avg_cost.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right">${(p.current_price || p.avg_cost).toFixed(2)}</td>
                  <td className={`px-4 py-3 text-right font-medium ${isGain ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                    <div className="flex items-center justify-end gap-1">
                      {isGain ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                      {isGain ? '+' : ''}{pnl.toFixed(0)}
                    </div>
                  </td>
                  <td className={`px-4 py-3 text-right ${isGain ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                    {isGain ? '+' : ''}{pct.toFixed(1)}%
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600">
                    {p.weight_pct?.toFixed(1) || '-'}%
                  </td>
                  <td className="px-4 py-3">
                    <MiniChart color={isGain ? '#10B981' : '#EF4444'} />
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                  暂无持仓数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
