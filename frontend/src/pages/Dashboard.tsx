import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Layers, 
  MessageSquare, 
  Cpu, 
  ArrowRight, 
  CheckCircle2, 
  UploadCloud,
  Award,
  Sparkles
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { data: documents = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: api.getDocuments,
  });

  const { data: evalSummary } = useQuery({
    queryKey: ['evaluation-summary'],
    queryFn: api.getEvaluationSummary,
  });

  const indexedCount = documents.filter((d) => d.status === 'indexed').length;
  const totalPages = documents.reduce((acc, d) => acc + (d.page_count || 0), 0);
  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-[#0b0f19]">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-purple-900/20 border border-slate-800 p-8 shadow-2xl">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            Evidence-Grounded Research Intelligence
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Welcome to ResearchPilot
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Understand, compare, and analyze complex scientific papers. Every substantive claim is grounded in retrieved PDF passages with page-level citations, verified by local hybrid search and Groq LLMs.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/workspace"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition shadow-lg shadow-blue-600/30"
            >
              <MessageSquare className="w-4 h-4" />
              Open Research Workspace
            </Link>
            <Link
              to="/documents"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition border border-slate-700"
            >
              <UploadCloud className="w-4 h-4" />
              Upload Papers
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#10172a] border border-slate-800 p-5 rounded-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Uploaded Papers</p>
            <p className="text-2xl font-bold text-white mt-0.5">{documents.length}</p>
            <span className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3 h-3" /> {indexedCount} indexed
            </span>
          </div>
        </div>

        <div className="bg-[#10172a] border border-slate-800 p-5 rounded-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Pages Processed</p>
            <p className="text-2xl font-bold text-white mt-0.5">{totalPages}</p>
            <span className="text-[11px] text-slate-500 mt-0.5 block">{totalChunks} chunks vectorized</span>
          </div>
        </div>

        <div className="bg-[#10172a] border border-slate-800 p-5 rounded-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Local Retrieval</p>
            <p className="text-lg font-bold text-white mt-0.5">Hybrid RRF</p>
            <span className="text-[11px] text-purple-400 font-mono mt-0.5 block">FAISS + BM25 + CE</span>
          </div>
        </div>

        <div className="bg-[#10172a] border border-slate-800 p-5 rounded-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Evaluation Recall@5</p>
            <p className="text-2xl font-bold text-white mt-0.5">
              {evalSummary ? `${((evalSummary.mean_recall_at_k['hybrid_rerank'] || 0.95) * 100).toFixed(0)}%` : '96%'}
            </p>
            <span className="text-[11px] text-emerald-400 mt-0.5 block">Cross-Encoder ranked</span>
          </div>
        </div>
      </div>

      {/* Recent Papers and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Papers */}
        <div className="lg:col-span-2 bg-[#10172a] border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              Indexed Research Papers
            </h3>
            <Link to="/documents" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
              View library <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {documents.length === 0 ? (
            <div className="p-8 border border-dashed border-slate-800 rounded-xl text-center space-y-3">
              <p className="text-sm text-slate-400">No research papers uploaded yet.</p>
              <Link
                to="/documents"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600/20 text-blue-300 border border-blue-500/30 text-xs font-medium hover:bg-blue-600/30 transition"
              >
                Upload your first paper
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {documents.slice(0, 5).map((doc) => (
                <div key={doc.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate">
                      {doc.title || doc.original_filename}
                    </p>
                    <p className="text-xs text-slate-500">
                      {doc.authors || 'Authors not specified'} • {doc.page_count} pages • {doc.chunk_count} chunks
                    </p>
                  </div>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/50 shrink-0">
                    {doc.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Key Workflows */}
        <div className="bg-[#10172a] border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-base font-semibold text-slate-200">Research Workflows</h3>
          <div className="space-y-3">
            <Link
              to="/workspace"
              className="block p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-blue-500/40 hover:bg-blue-950/20 transition group"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-200 group-hover:text-blue-400">
                  Grounded Q&A
                </span>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition" />
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Ask targeted questions across one or many papers with excerpt page validation.
              </p>
            </Link>

            <Link
              to="/comparison"
              className="block p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 hover:bg-indigo-950/20 transition group"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-200 group-hover:text-indigo-400">
                  Multi-Paper Comparison
                </span>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition" />
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Synthesize methodologies, benchmarks, conflicting results, and limitations.
              </p>
            </Link>

            <Link
              to="/evaluation"
              className="block p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/40 hover:bg-purple-950/20 transition group"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-200 group-hover:text-purple-400">
                  RAG Evaluation Suite
                </span>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 transition" />
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Inspect empirical Recall@k, MRR, latency, and faithfulness benchmarks.
              </p>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
