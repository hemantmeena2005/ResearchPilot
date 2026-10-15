import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { PaperCompareResponse, GapAnalysisResponse } from '../types';
import { 
  GitCompare, 
  Sparkles, 
  Check, 
  AlertCircle, 
  Lightbulb, 
  Loader2, 
  HelpCircle,
  Layers
} from 'lucide-react';

export const PaperComparison: React.FC = () => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<PaperCompareResponse | null>(null);
  const [gapResult, setGapResult] = useState<GapAnalysisResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'compare' | 'gaps'>('compare');

  const { data: documents = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: api.getDocuments,
  });

  const compareMutation = useMutation({
    mutationFn: () => api.comparePapers(selectedIds),
    onSuccess: (data) => setComparisonResult(data),
  });

  const gapMutation = useMutation({
    mutationFn: () => api.analyzeGaps(selectedIds),
    onSuccess: (data) => setGapResult(data),
  });

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleRunComparison = () => {
    if (selectedIds.length < 2) return;
    compareMutation.mutate();
    gapMutation.mutate();
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-[#0b0f19]">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-indigo-400" />
            Multi-Paper Comparative Analysis & Research Gaps
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Compare methodologies, evaluation benchmarks, contradictory claims, and explore candidate research directions.
          </p>
        </div>

        <button
          onClick={handleRunComparison}
          disabled={selectedIds.length < 2 || compareMutation.isPending}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold transition shadow-lg shadow-indigo-600/30"
        >
          {compareMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          <span>Compare Selected Papers ({selectedIds.length})</span>
        </button>
      </div>

      {/* Paper Selection Checklist */}
      <div className="bg-[#10172a] border border-slate-800 rounded-xl p-5 space-y-3">
        <h4 className="text-xs font-semibold text-slate-300">
          Select at least 2 papers to compare:
        </h4>
        {documents.length < 2 ? (
          <p className="text-xs text-slate-500">
            Please upload at least 2 papers in the Document Library to unlock comparative intelligence.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {documents.map((doc) => {
              const isSelected = selectedIds.includes(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => toggleSelect(doc.id)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition flex items-start gap-2.5 ${
                    isSelected
                      ? 'bg-indigo-950/30 border-indigo-500/80 text-slate-100 ring-1 ring-indigo-500/40'
                      : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded border mt-0.5 flex items-center justify-center shrink-0 ${
                      isSelected
                        ? 'bg-indigo-600 border-indigo-500 text-white'
                        : 'border-slate-700 bg-slate-950'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium truncate">{doc.title || doc.original_filename}</p>
                    <p className="text-[11px] text-slate-500 truncate">{doc.authors || 'Authors'}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Tabs */}
      {(comparisonResult || gapResult) && (
        <div className="flex border-b border-slate-800 text-sm font-medium gap-6">
          <button
            onClick={() => setActiveTab('compare')}
            className={`pb-3 transition flex items-center gap-2 ${
              activeTab === 'compare'
                ? 'text-indigo-400 border-b-2 border-indigo-500'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Structured Comparison</span>
          </button>
          <button
            onClick={() => setActiveTab('gaps')}
            className={`pb-3 transition flex items-center gap-2 ${
              activeTab === 'gaps'
                ? 'text-indigo-400 border-b-2 border-indigo-500'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lightbulb className="w-4 h-4" />
            <span>Candidate Research Gaps</span>
          </button>
        </div>
      )}

      {/* Results View */}
      {compareMutation.isPending && (
        <div className="p-12 text-center bg-[#10172a] rounded-xl border border-slate-800 space-y-3">
          <Loader2 className="w-6 h-6 animate-spin mx-auto text-indigo-400" />
          <p className="text-sm font-medium text-slate-300">
            Synthesizing comparative methodology matrix across {selectedIds.length} papers...
          </p>
        </div>
      )}

      {activeTab === 'compare' && comparisonResult && (
        <div className="space-y-6">
          {/* Aspects Comparison Cards */}
          <div className="grid grid-cols-1 gap-4">
            {comparisonResult.aspects.map((aspect, idx) => (
              <div key={idx} className="bg-[#10172a] border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h4 className="text-sm font-bold text-indigo-300 tracking-wide uppercase">
                    {aspect.aspect}
                  </h4>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {aspect.comparison_summary}
                </p>

                {/* Per-Paper Breakdown Table/Grid */}
                {aspect.per_paper_breakdown && Object.keys(aspect.per_paper_breakdown).length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                    {Object.entries(aspect.per_paper_breakdown).map(([paper, desc], i) => (
                      <div key={i} className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/80 text-xs">
                        <span className="font-semibold text-slate-400 block mb-1">{paper}</span>
                        <p className="text-slate-300">{desc}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Agreements, Contradictions, Open Questions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#10172a] border border-slate-800 rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <Check className="w-4 h-4" /> Consensuses & Agreements
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                {comparisonResult.agreements.map((a, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{a}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-[#10172a] border border-slate-800 rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" /> Conflicting Findings
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                {comparisonResult.contradictions.map((c, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-[#10172a] border border-slate-800 rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4" /> Open Questions
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                {comparisonResult.open_questions.map((q, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-purple-500 font-bold">•</span>
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'gaps' && gapResult && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4">
            {gapResult.research_directions.map((gap, idx) => (
              <div key={idx} className="bg-[#10172a] border border-slate-800 rounded-xl p-6 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-400" />
                    {gap.title}
                  </h4>
                  <span className="text-[11px] font-mono px-2.5 py-0.5 rounded bg-indigo-950/60 text-indigo-400 border border-indigo-800/40">
                    Hypothesis
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {gap.gap_description}
                </p>
                <div className="bg-slate-950/50 p-3.5 rounded-lg border border-slate-800/60 text-xs text-slate-400 space-y-1">
                  <span className="font-semibold text-slate-300 block">Supporting Literature Rationale:</span>
                  <p>{gap.evidence_and_rationale}</p>
                </div>
              </div>
            ))}
          </div>

          {gapResult.methodology_caveats.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 text-amber-300 text-xs space-y-1">
              <span className="font-semibold block flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5" />
                Literature Boundary Caveat:
              </span>
              <p>
                {gapResult.methodology_caveats.join(' ')}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
