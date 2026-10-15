import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { CitationDrawer } from '../components/CitationDrawer';
import type { CitationItem } from '../types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, 
  Sparkles, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Filter, 
  FileText, 
  Sliders, 
  Loader2,
  ShieldCheck,
  Plus,
  MessageSquare,
  Trash2,
  History
} from 'lucide-react';

export const ResearchWorkspace: React.FC = () => {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState('');
  const [retrievalMode, setRetrievalMode] = useState<'hybrid_rerank' | 'hybrid' | 'vector_only'>('hybrid_rerank');
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  const { data: documents = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: api.getDocuments,
  });

  const { data: conversations = [] } = useQuery({
    queryKey: ['conversations'],
    queryFn: api.getConversations,
  });

  const { data: currentConversation } = useQuery({
    queryKey: ['conversation', currentConversationId],
    queryFn: () => (currentConversationId ? api.getConversation(currentConversationId) : null),
    enabled: !!currentConversationId,
  });

  const newChatMutation = useMutation({
    mutationFn: (title?: string) => api.createConversation(title || 'New Research Session', selectedDocIds),
    onSuccess: (newConv) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setCurrentConversationId(newConv.id);
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (currentConversationId === deletedId) {
        setCurrentConversationId(null);
      }
    },
  });

  const queryMutation = useMutation({
    mutationFn: async (userQuery: string) => {
      let convId = currentConversationId;
      if (!convId) {
        // Automatically create a new session named after the user's question
        const title = userQuery.length > 35 ? userQuery.slice(0, 35) + '...' : userQuery;
        const newConv = await api.createConversation(title, selectedDocIds);
        convId = newConv.id;
        setCurrentConversationId(newConv.id);
        queryClient.invalidateQueries({ queryKey: ['conversations'] });
      }

      return api.queryResearch({
        query: userQuery,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        conversation_id: convId,
        retrieval_mode: retrievalMode,
        top_k: 8,
      });
    },
    onSuccess: (res) => {
      setQuery('');
      queryClient.invalidateQueries({ queryKey: ['conversation', currentConversationId] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (res.citations && res.citations.length > 0) {
        setSelectedCitation(res.citations[0]);
      }
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || queryMutation.isPending) return;
    queryMutation.mutate(query);
  };

  const handleStartNewChat = () => {
    newChatMutation.mutate('New Research Session');
  };

  const toggleDocSelection = (id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const suggestedQuestions = [
    "Explain the main contribution of this paper in simple terms.",
    "Compare the performance results reported by different papers.",
    "What datasets and evaluation metrics did the authors use?",
    "What limitations do the authors explicitly acknowledge?",
  ];

  const activeMessages = currentConversation?.messages || [];

  return (
    <div className="flex-1 flex overflow-hidden bg-[#0b0f19]">
      {/* Sessions / Chat History Drawer */}
      <div className="w-64 border-r border-slate-800 bg-[#0d1322] flex flex-col h-full shrink-0 select-none">
        <div className="p-3.5 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <History className="w-3.5 h-3.5 text-blue-400" />
            Sessions
          </span>
          <button
            onClick={handleStartNewChat}
            disabled={newChatMutation.isPending}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition shadow-sm"
          >
            <Plus className="w-3 h-3" />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              No previous chats. Start a new session or ask a question.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === currentConversationId;
              return (
                <div
                  key={conv.id}
                  onClick={() => setCurrentConversationId(conv.id)}
                  className={`group px-3 py-2.5 rounded-lg text-xs font-medium cursor-pointer transition flex items-center justify-between gap-2 ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{conv.title || 'Untitled Session'}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteChatMutation.mutate(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5 rounded transition"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat & Q&A Pane */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Control Bar */}
        <div className="px-6 py-3 border-b border-slate-800 bg-[#0d1322] flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-blue-400" />
              Retrieval Mode:
            </span>
            <div className="flex bg-slate-900 rounded-lg p-0.5 border border-slate-800">
              <button
                onClick={() => setRetrievalMode('hybrid_rerank')}
                className={`px-2.5 py-1 rounded-md transition ${
                  retrievalMode === 'hybrid_rerank'
                    ? 'bg-blue-600 text-white font-medium'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Hybrid + Rerank
              </button>
              <button
                onClick={() => setRetrievalMode('hybrid')}
                className={`px-2.5 py-1 rounded-md transition ${
                  retrievalMode === 'hybrid'
                    ? 'bg-blue-600 text-white font-medium'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Hybrid (FAISS+BM25)
              </button>
              <button
                onClick={() => setRetrievalMode('vector_only')}
                className={`px-2.5 py-1 rounded-md transition ${
                  retrievalMode === 'vector_only'
                    ? 'bg-blue-600 text-white font-medium'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Vector Only
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-400">
            <Filter className="w-3.5 h-3.5" />
            <span>Scope: {selectedDocIds.length === 0 ? 'All Documents' : `${selectedDocIds.length} Selected`}</span>
          </div>
        </div>

        {/* Content Area: Chat History & Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeMessages.length === 0 && !queryMutation.isPending && (
            <div className="max-w-2xl mx-auto py-12 text-center space-y-6">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto shadow-inner">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-slate-100">Evidence-Grounded Research Assistant</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Synthesize answers from indexed scientific literature with prominent headings, structured comparison tables, and page citations.
                </p>
              </div>

              {/* Scope filter pills */}
              {documents.length > 0 && (
                <div className="text-left bg-slate-900/60 border border-slate-800 p-4 rounded-xl space-y-2">
                  <span className="text-xs font-semibold text-slate-300">Target Paper Scope:</span>
                  <div className="flex flex-wrap gap-2">
                    {documents.map((d) => {
                      const isSelected = selectedDocIds.includes(d.id);
                      return (
                        <button
                          key={d.id}
                          onClick={() => toggleDocSelection(d.id)}
                          className={`text-xs px-2.5 py-1 rounded-lg border transition flex items-center gap-1.5 ${
                            isSelected
                              ? 'bg-blue-600/20 border-blue-500/60 text-blue-300'
                              : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-300'
                          }`}
                        >
                          <FileText className="w-3 h-3" />
                          <span className="max-w-[200px] truncate">{d.title || d.original_filename}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Sample prompts */}
              <div className="space-y-2 text-left">
                <p className="text-xs font-medium text-slate-500">Sample Research Questions:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setQuery(q);
                        queryMutation.mutate(q);
                      }}
                      className="p-3 text-xs text-slate-300 bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800 rounded-xl text-left transition"
                    >
                      "{q}"
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Render all messages in active thread */}
          {activeMessages.map((msg) => {
            if (msg.role === 'user') {
              return (
                <div key={msg.id} className="max-w-3xl mx-auto flex justify-end">
                  <div className="p-4 rounded-2xl bg-blue-600/15 border border-blue-500/30 text-sm font-medium text-slate-100 max-w-xl">
                    <span className="text-[10px] text-blue-400 uppercase tracking-wider font-semibold block mb-1">
                      User Query
                    </span>
                    {msg.content}
                  </div>
                </div>
              );
            }

            return (
              <div key={msg.id} className="max-w-3xl mx-auto space-y-3">
                <div className="p-6 rounded-2xl bg-[#10172a] border border-slate-800 space-y-4 shadow-xl">
                  {/* Header indicators */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800/80 text-xs">
                    <div className="flex items-center gap-2">
                      {msg.query_category && (
                        <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                          Category: {msg.query_category}
                        </span>
                      )}
                      {msg.is_evidence_sufficient ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400">
                          <CheckCircle className="w-3.5 h-3.5" /> Evidence Grounded
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-amber-400 font-semibold">
                          <AlertTriangle className="w-3.5 h-3.5" /> Insufficient Evidence Acknowledged
                        </span>
                      )}
                    </div>

                    {msg.latency_ms !== null && msg.latency_ms !== undefined && (
                      <span className="flex items-center gap-1 text-slate-500 font-mono text-xs">
                        <Clock className="w-3 h-3" /> {msg.latency_ms.toFixed(0)}ms
                      </span>
                    )}
                  </div>

                  {/* Markdown Answer with responsive table container */}
                  <div className="markdown-content">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        table: ({ node, ...props }) => (
                          <div className="markdown-table-wrapper">
                            <table {...props} />
                          </div>
                        )
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  {/* Citations Preview Banner */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span>{msg.citations.length} Grounded Excerpt Citations Available in Drawer</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {queryMutation.isPending && (
            <div className="max-w-3xl mx-auto p-8 rounded-2xl bg-[#10172a] border border-slate-800 space-y-4">
              <div className="flex items-center gap-3 text-blue-400 text-sm">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="font-medium">
                  Retrieving evidence across documents & generating grounded response...
                </span>
              </div>
              <div className="space-y-2 animate-pulse">
                <div className="h-4 bg-slate-800 rounded w-3/4"></div>
                <div className="h-4 bg-slate-800 rounded w-5/6"></div>
                <div className="h-4 bg-slate-800 rounded w-2/3"></div>
              </div>
            </div>
          )}
        </div>

        {/* Input Form */}
        <div className="p-4 border-t border-slate-800 bg-[#0d1322]">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto flex items-center gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a scientific research question across indexed papers..."
              disabled={queryMutation.isPending}
              className="flex-1 px-4 py-3 bg-[#10172a] border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
            <button
              type="submit"
              disabled={!query.trim() || queryMutation.isPending}
              className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-sm transition flex items-center gap-2 shadow-lg shadow-blue-600/30"
            >
              {queryMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span>Query</span>
            </button>
          </form>
        </div>
      </div>

      {/* Right Evidence Drawer */}
      <CitationDrawer
        citations={
          (activeMessages.length > 0 && activeMessages[activeMessages.length - 1].citations) || []
        }
        selectedCitation={selectedCitation}
        onSelectCitation={setSelectedCitation}
      />
    </div>
  );
};
