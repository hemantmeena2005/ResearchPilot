import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { 
  UploadCloud, 
  Trash2, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Search,
  BookOpen,
  User
} from 'lucide-react';

export const DocumentLibrary: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: api.getDocuments,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: () => {
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      setUploadError(err.message || 'Failed to process document');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setUploadError('Only PDF files are permitted.');
        return;
      }
      uploadMutation.mutate(file);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const term = search.toLowerCase();
    const title = (doc.title || doc.original_filename).toLowerCase();
    const authors = (doc.authors || '').toLowerCase();
    return title.includes(term) || authors.includes(term);
  });

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-[#0b0f19]">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-500" />
            Document Library
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload scientific papers. Text, sections, and page numbers are preserved and indexed with SentenceTransformers and BM25.
          </p>
        </div>

        {/* Upload Button */}
        <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition shadow-lg shadow-blue-600/30">
          {uploadMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <UploadCloud className="w-4 h-4" />
          )}
          <span>{uploadMutation.isPending ? 'Indexing Paper...' : 'Upload Research PDF'}</span>
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            disabled={uploadMutation.isPending}
            onChange={handleFileUpload}
          />
        </label>
      </div>

      {uploadError && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Search and Filters */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search uploaded papers by title, author, or keyword..."
          className="w-full pl-10 pr-4 py-2 bg-[#10172a] border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
        />
      </div>

      {/* Documents Grid / Table */}
      {isLoading ? (
        <div className="flex items-center justify-center p-16">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="p-12 border border-dashed border-slate-800 rounded-2xl text-center space-y-3 bg-[#10172a]/30">
          <FileText className="w-10 h-10 mx-auto text-slate-600 stroke-[1.5]" />
          <h4 className="text-sm font-medium text-slate-300">No documents found</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Upload PDF research papers to start indexing text, vectorizing chunks, and asking grounded questions.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc) => (
            <div
              key={doc.id}
              className="bg-[#10172a] border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <span className="p-2 rounded-lg bg-blue-500/10 text-blue-400 shrink-0">
                    <FileText className="w-5 h-5" />
                  </span>
                  <button
                    onClick={() => deleteMutation.mutate(doc.id)}
                    title="Delete Paper"
                    className="text-slate-500 hover:text-red-400 p-1 rounded-lg transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-slate-200 line-clamp-2 leading-snug">
                    {doc.title || doc.original_filename}
                  </h4>
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5 line-clamp-1">
                    <User className="w-3 h-3 text-slate-600 shrink-0" />
                    <span>{doc.authors || 'Unknown authors'}</span>
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800/80 mt-4 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-3">
                  <span>{doc.page_count} pages</span>
                  <span>•</span>
                  <span>{doc.chunk_count} chunks</span>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
                  <CheckCircle2 className="w-3 h-3" /> Indexed
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
