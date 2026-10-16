import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Compass, 
  Files, 
  MessageSquare, 
  GitCompare, 
  BarChart3, 
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Plus,
  History,
  Trash2
} from 'lucide-react';
import type { Conversation } from '../types';

interface SidebarProps {
  docCount?: number;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  conversations?: Conversation[];
  currentConversationId?: string | null;
  onSelectConversation?: (id: string | null) => void;
  onNewChat?: () => void;
  onDeleteChat?: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  docCount = 0,
  isCollapsed = false,
  onToggleCollapse,
  conversations = [],
  currentConversationId = null,
  onSelectConversation,
  onNewChat,
  onDeleteChat,
}) => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: Compass },
    { to: '/documents', label: 'Document Library', icon: Files, badge: docCount > 0 ? docCount : undefined },
    { to: '/workspace', label: 'Research Workspace', icon: MessageSquare },
    { to: '/comparison', label: 'Paper Comparison', icon: GitCompare },
    { to: '/evaluation', label: 'Evaluation & Benchmarks', icon: BarChart3 },
  ];

  return (
    <aside 
      className={`${
        isCollapsed ? 'w-16' : 'w-64'
      } bg-[#0d1322] border-r border-slate-800 flex flex-col h-screen shrink-0 select-none transition-all duration-300 relative group/sidebar`}
    >
      {/* Brand header */}
      <div className={`p-4 border-b border-slate-800 flex items-center ${isCollapsed ? 'justify-center' : 'justify-between gap-3'}`}>
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          {!isCollapsed && (
            <div className="truncate">
              <h1 className="font-bold text-slate-100 text-sm tracking-tight">
                ResearchPilot
              </h1>
              <p className="text-[10px] text-slate-400 font-mono">v0.1.0 • Evidence</p>
            </div>
          )}
        </div>

        {/* Collapse toggle button */}
        {onToggleCollapse && !isCollapsed && (
          <button
            onClick={onToggleCollapse}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            title="Collapse Sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="px-2.5 py-3 space-y-1 overflow-y-auto shrink-0 border-b border-slate-800/80">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={isCollapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center ${
                  isCollapsed ? 'justify-center px-2 py-2' : 'justify-between px-3 py-2'
                } rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span className="truncate">{item.label}</span>}
              </div>
              {!isCollapsed && item.badge !== undefined && (
                <span className="px-1.5 py-0.2 text-[10px] rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Embedded Sessions / Research History */}
      {!isCollapsed ? (
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="p-3 border-b border-slate-800/60 flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <History className="w-3 h-3 text-blue-400" />
              Chat History
            </span>
            {onNewChat && (
              <button
                onClick={onNewChat}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-medium transition shadow-sm"
                title="Start a new chat session"
              >
                <Plus className="w-3 h-3" />
                <span>New</span>
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-500">
                No past chats yet.
              </div>
            ) : (
              conversations.map((conv) => {
                const isActive = conv.id === currentConversationId;
                return (
                  <NavLink
                    key={conv.id}
                    to={`/workspace?c=${conv.id}`}
                    onClick={() => onSelectConversation?.(conv.id)}
                    className={`group px-2.5 py-2 rounded-lg text-xs font-medium cursor-pointer transition flex items-center justify-between gap-1.5 ${
                      isActive
                        ? 'bg-blue-600/15 text-blue-300 border border-blue-500/30'
                        : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
                      <span className="truncate">{conv.title || 'Untitled Session'}</span>
                    </div>
                    {onDeleteChat && (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          onDeleteChat(conv.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5 rounded transition"
                        title="Delete chat"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </NavLink>
                );
              })
            )}
          </div>
        </div>
      ) : (
        /* Collapsed Icon Bar for New Chat */
        <div className="flex-1 flex flex-col items-center pt-3 gap-2 overflow-y-auto">
          {onNewChat && (
            <button
              onClick={onNewChat}
              className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition shadow-sm"
              title="New Chat"
            >
              <Plus className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Expand button if collapsed */}
      {isCollapsed && onToggleCollapse && (
        <div className="p-2 border-t border-slate-800/80 flex justify-center">
          <button
            onClick={onToggleCollapse}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition w-full flex items-center justify-center"
            title="Expand Sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Footer system info */}
      {!isCollapsed && (
        <div className="p-3.5 border-t border-slate-800/80 bg-slate-900/40 text-[11px] text-slate-500 space-y-1">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Pinecone Vector DB
            </span>
            <span className="text-emerald-400 font-mono text-[10px]">Cloud</span>
          </div>
          <div className="flex items-center justify-between">
            <span>LLM Inference</span>
            <span className="text-blue-400 font-mono text-[10px]">Groq OSS</span>
          </div>
        </div>
      )}
    </aside>
  );
};
