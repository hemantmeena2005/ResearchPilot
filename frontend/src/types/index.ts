export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  title: string | null;
  authors: string | null;
  publication_year: number | null;
  status: 'processing' | 'indexed' | 'failed';
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface CitationItem {
  document_id: string;
  document_title: string;
  filename: string;
  page_number: number;
  chunk_id: string;
  excerpt: string;
  relevance_score?: number | null;
  claim_association?: string | null;
}

export interface ResearchQueryResponse {
  answer: string;
  query_category: string;
  citations: CitationItem[];
  is_evidence_sufficient: boolean;
  latency_ms: number;
  retrieval_mode: string;
  rewritten_query?: string | null;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
  conversation_id?: string | null;
}

export interface PaperComparisonAspect {
  aspect: string;
  comparison_summary: string;
  per_paper_breakdown: Record<string, string>;
  citations: CitationItem[];
}

export interface PaperCompareResponse {
  title: string;
  document_summaries: Record<string, string>;
  aspects: PaperComparisonAspect[];
  agreements: string[];
  contradictions: string[];
  open_questions: string[];
  latency_ms: number;
}

export interface ResearchGapItem {
  title: string;
  gap_description: string;
  evidence_and_rationale: string;
  source_papers: string[];
  citations: CitationItem[];
}

export interface GapAnalysisResponse {
  research_directions: ResearchGapItem[];
  methodology_caveats: string[];
  latency_ms: number;
}

export interface PaperSummaryResponse {
  document_id: string;
  title: string;
  problem_statement: string;
  main_contribution: string;
  proposed_method: string;
  experimental_results: string;
  author_acknowledged_limitations: string[];
  inferred_limitations: string[];
  future_work: string[];
  citations: CitationItem[];
}

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  query_category?: string | null;
  citations: CitationItem[];
  is_evidence_sufficient: boolean;
  latency_ms?: number | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  selected_doc_ids: string[];
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}

export interface EvaluationSummary {
  total_evaluations: number;
  modes_evaluated: string[];
  mean_recall_at_k: Record<string, number>;
  mean_mrr: Record<string, number>;
  mean_citation_correctness: Record<string, number>;
  mean_faithfulness: Record<string, number>;
  mean_latency_ms: Record<string, number>;
  experiments: Array<{
    mode: string;
    question: string;
    recall_at_k: number;
    mrr: number;
    faithfulness: number;
    latency_ms: number;
    retrieved_count: number;
  }>;
}
