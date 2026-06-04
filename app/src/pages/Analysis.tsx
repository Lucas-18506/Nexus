import { useEffect, useState, useMemo } from 'react';
import { analysisApi, type AnalysisReport } from '../api/analysis';
import {
  Search, Loader2, Filter, FileText, ChevronRight,
} from 'lucide-react';

function verdictBg(v: string): string {
  if (v?.includes('buy') || v?.includes('强')) return 'bg-emerald-50 text-[#10B981] border-emerald-200';
  if (v?.includes('avoid') || v?.includes('空')) return 'bg-red-50 text-[#EF4444] border-red-200';
  return 'bg-yellow-50 text-[#F59E0B] border-yellow-200';
}

export default function Analysis() {
  const [reports, setReports] = useState<AnalysisReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');

  useEffect(() => {
    analysisApi.getReports({ limit: 50 })
      .then(setReports)
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, []);

  const types = useMemo(() => {
    const set = new Set(reports.map(r => r.report_type));
    return Array.from(set);
  }, [reports]);

  const risks = useMemo(() => {
    const set = new Set(reports.map(r => r.risk_level));
    return Array.from(set);
  }, [reports]);

  const filtered = useMemo(() => {
    let list = [...reports];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(r =>
        r.symbol.toLowerCase().includes(q) ||
        r.title.toLowerCase().includes(q) ||
        r.summary.toLowerCase().includes(q)
      );
    }
    if (typeFilter !== 'all') list = list.filter(r => r.report_type === typeFilter);
    if (riskFilter !== 'all') list = list.filter(r => r.risk_level === riskFilter);
    return list;
  }, [reports, search, typeFilter, riskFilter]);

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
        <h1 className="text-2xl font-bold text-slate-900">分析报告</h1>
        <span className="text-sm text-slate-500">共 {reports.length} 份报告</span>
      </div>

      {/* 筛选栏 */}
      <div className="flex flex-wrap items-center gap-3 bg-white rounded-lg border border-slate-200 p-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="搜索股票、标题..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-[#10B981]"
          />
        </div>

        <div className="flex items-center gap-1">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-500 mr-1">类型</span>
          <button
            onClick={() => setTypeFilter('all')}
            className={`px-2 py-1 rounded text-xs font-medium ${typeFilter === 'all' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
          >全部</button>
          {types.map(t => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-2 py-1 rounded text-xs font-medium ${typeFilter === t ? 'bg-[#10B981] text-white' : 'bg-slate-100 text-slate-600'}`}
            >{t}</button>
          ))}
        </div>

        <div className="flex items-center gap-1">
          <span className="text-xs text-slate-500 mr-1">风险</span>
          <button
            onClick={() => setRiskFilter('all')}
            className={`px-2 py-1 rounded text-xs font-medium ${riskFilter === 'all' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}
          >全部</button>
          {risks.map(r => (
            <button
              key={r}
              onClick={() => setRiskFilter(r)}
              className={`px-2 py-1 rounded text-xs font-medium ${riskFilter === r ? 'bg-[#10B981] text-white' : 'bg-slate-100 text-slate-600'}`}
            >{r}</button>
          ))}
        </div>
      </div>

      {/* 报告列表 */}
      <div className="space-y-3">
        {filtered.map(r => (
          <div key={r.id} className="card hover:shadow-md transition-shadow cursor-pointer group">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5 text-slate-500" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-slate-900">{r.symbol}</span>
                  <span className={`text-xs px-2 py-0.5 rounded border ${verdictBg(r.verdict)}`}>
                    {r.verdict}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-500">
                    {r.report_type}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-500">
                    风险: {r.risk_level}
                  </span>
                </div>
                <h3 className="text-sm font-medium text-slate-700 mt-1">{r.title}</h3>
                <p className="text-sm text-slate-500 mt-1 line-clamp-2">{r.summary}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                  <span>置信度: {Math.round(r.confidence * 100)}%</span>
                  {r.price_target && <span>目标价: ${r.price_target}</span>}
                  <span>{new Date(r.created_at).toLocaleDateString('zh-CN')}</span>
                  <div className="ml-auto flex items-center gap-1 text-[#10B981]">
                    查看详情 <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            没有找到匹配的分析报告
          </div>
        )}
      </div>
    </div>
  );
}
