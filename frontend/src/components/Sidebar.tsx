import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Compass, 
  Files, 
  MessageSquare, 
  GitCompare, 
  BarChart3, 
  Sparkles
} from 'lucide-react';

interface SidebarProps {
  docCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ docCount = 0 }) => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: Compass },
    { to: '/documents', label: 'Document Library', icon: Files, badge: docCount > 0 ? docCount : undefined },
    { to: '/workspace', label: 'Research Workspace', icon: MessageSquare },
    { to: '/comparison', label: 'Paper Comparison', icon: GitCompare },
    { to: '/evaluation', label: 'Evaluation & Benchmarks', icon: BarChart3 },
  ];

  return (
    <aside className="w-64 bg-[#0d1322] border-r border-slate-800 flex flex-col h-screen shrink-0 select-none">
      {/* Brand header */}
      <div className="p-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-slate-100 text-base tracking-tight flex items-center gap-1.5">
            ResearchPilot
          </h1>
          <p className="text-xs text-slate-400 font-mono">v0.1.0 • Evidence Grounded</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer system info */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40 text-xs text-slate-500 space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            FAISS & BM25
          </span>
          <span className="text-slate-400">Local</span>
        </div>
        <div className="flex items-center justify-between">
          <span>LLM Inference</span>
          <span className="text-blue-400 font-mono">Groq Llama-3.3</span>
        </div>
      </div>
    </aside>
  );
};
