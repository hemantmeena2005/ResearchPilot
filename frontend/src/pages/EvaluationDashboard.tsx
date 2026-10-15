import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { 
  BarChart3, 
  Clock, 
  Loader2,
  RefreshCw
} from 'lucide-react';

export const EvaluationDashboard: React.FC = () => {
  const { data: summary, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['evaluation-summary'],
    queryFn: api.getEvaluationSummary,
  });

  const modes = [
    { key: 'vector_only', label: 'Vector Only (FAISS)', color: 'text-blue-400', border: 'border-blue-500/30' },
    { key: 'hybrid', label: 'Hybrid (FAISS + BM25 RRF)', color: 'text-indigo-400', border: 'border-indigo-500/30' },
    { key: 'hybrid_rerank', label: 'Hybrid + Cross-Encoder', color: 'text-emerald-400', border: 'border-emerald-500/30' },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-[#0b0f19]">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-purple-400" />
            Evaluation Suite & Retrieval Benchmarks
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Empirical measurements comparing vector-only, BM25 hybrid fusion, and Cross-Encoder reranking over research test cases.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition border border-slate-700 shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          <span>{isFetching ? 'Running Benchmark...' : 'Re-run Benchmark'}</span>
        </button>
      </div>

      {isLoading ? (
        <div className="p-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-purple-500" />
          <p className="text-xs text-slate-400 mt-3">Computing retrieval metrics and empirical rankings...</p>
        </div>
      ) : summary ? (
        <div className="space-y-6">
          {/* Comparative Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {modes.map((m) => {
              const recall = summary.mean_recall_at_k[m.key] ?? 0;
              const mrr = summary.mean_mrr[m.key] ?? 0;
              const faith = summary.mean_faithfulness[m.key] ?? 0;
              const lat = summary.mean_latency_ms[m.key] ?? 0;

              return (
                <div
                  key={m.key}
                  className={`bg-[#10172a] border ${m.border} rounded-2xl p-6 space-y-5 shadow-lg relative overflow-hidden`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-bold ${m.color}`}>{m.label}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                      k = 5
                    </span>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Recall@5</span>
                        <span className="font-mono font-bold text-white">{(recall * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-blue-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${recall * 100}%` }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Mean Reciprocal Rank (MRR)</span>
                        <span className="font-mono font-bold text-white">{mrr.toFixed(3)}</span>
                      </div>
                      <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${mrr * 100}%` }}
                        ></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Passage Faithfulness</span>
                        <span className="font-mono font-bold text-white">{(faith * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${faith * 100}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" /> Latency
                      </span>
                      <span className="font-mono font-semibold text-slate-200">{lat.toFixed(1)} ms</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Test Cases Log Table */}
          <div className="bg-[#10172a] border border-slate-800 rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200">
              Evaluated Benchmark Test Cases ({summary.experiments.length} runs)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 font-mono border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Mode</th>
                    <th className="py-2.5 px-3">Research Question</th>
                    <th className="py-2.5 px-3">Recall@5</th>
                    <th className="py-2.5 px-3">MRR</th>
                    <th className="py-2.5 px-3">Faithfulness</th>
                    <th className="py-2.5 px-3">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {summary.experiments.map((exp, i) => (
                    <tr key={i} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 font-mono text-blue-400">{exp.mode}</td>
                      <td className="py-2.5 px-3 max-w-md truncate">{exp.question}</td>
                      <td className="py-2.5 px-3 font-mono">{(exp.recall_at_k * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono">{exp.mrr.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-mono">{(exp.faithfulness * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono">{exp.latency_ms.toFixed(1)}ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
