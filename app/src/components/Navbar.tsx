import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  BarChart3,
  Activity,
  Settings,
} from 'lucide-react';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/portfolio', icon: Briefcase, label: '持仓' },
  { to: '/analysis', icon: BarChart3, label: '分析' },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-14">
          <div className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-[#10B981]" />
            <span className="font-bold text-lg text-slate-900">Nexus</span>
          </div>
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const active = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? 'bg-emerald-50 text-[#10B981]'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </div>
          <button className="p-2 rounded-lg hover:bg-slate-50 text-slate-500">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>
    </nav>
  );
}
