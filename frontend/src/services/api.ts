import type {
  Document,
  ResearchQueryResponse,
  PaperCompareResponse,
  GapAnalysisResponse,
  PaperSummaryResponse,
  Conversation,
  EvaluationSummary,
} from '../types';

// Use VITE_API_URL if configured, otherwise fall back to relative path '/api/v1'
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') + '/api/v1';

export const api = {
  // Document Operations
  async getDocuments(): Promise<Document[]> {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to upload document' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async deleteDocument(documentId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
  },

  // Research Query Operations
  async queryResearch(params: {
    query: string;
    document_ids?: string[];
    conversation_id?: string;
    retrieval_mode?: string;
    top_k?: number;
  }): Promise<ResearchQueryResponse> {
    const res = await fetch(`${API_BASE}/research/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Query failed' }));
      throw new Error(err.detail || 'Query request failed');
    }
    return res.json();
  },

  // Research Intelligence Operations
  async comparePapers(documentIds: string[], focusAspects?: string[]): Promise<PaperCompareResponse> {
    const res = await fetch(`${API_BASE}/research/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_ids: documentIds, focus_aspects: focusAspects }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Comparison failed' }));
      throw new Error(err.detail || 'Comparison request failed');
    }
    return res.json();
  },

  async summarizePaper(documentId: string): Promise<PaperSummaryResponse> {
    const res = await fetch(`${API_BASE}/research/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Summary failed' }));
      throw new Error(err.detail || 'Summary request failed');
    }
    return res.json();
  },

  async analyzeGaps(documentIds: string[]): Promise<GapAnalysisResponse> {
    const res = await fetch(`${API_BASE}/research/gap-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_ids: documentIds }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Gap analysis failed' }));
      throw new Error(err.detail || 'Gap analysis request failed');
    }
    return res.json();
  },

  // Conversations
  async getConversations(): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE}/conversations`);
    if (!res.ok) throw new Error('Failed to fetch conversations');
    return res.json();
  },

  async getConversation(id: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/conversations/${id}`);
    if (!res.ok) throw new Error('Failed to fetch conversation');
    return res.json();
  },

  async createConversation(title?: string, selectedDocIds?: string[]): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, selected_doc_ids: selectedDocIds }),
    });
    if (!res.ok) throw new Error('Failed to create conversation');
    return res.json();
  },

  async deleteConversation(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete conversation');
  },

  // Evaluation
  async getEvaluationSummary(): Promise<EvaluationSummary> {
    const res = await fetch(`${API_BASE}/evaluation/summary`);
    if (!res.ok) throw new Error('Failed to fetch evaluation metrics');
    return res.json();
  },
};
