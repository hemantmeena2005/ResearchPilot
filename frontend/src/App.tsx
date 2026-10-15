import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { DocumentLibrary } from './pages/DocumentLibrary';
import { ResearchWorkspace } from './pages/ResearchWorkspace';
import { PaperComparison } from './pages/PaperComparison';
import { EvaluationDashboard } from './pages/EvaluationDashboard';
import { api } from './services/api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 30,
    },
  },
});

const AppShell: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);
  const queryClient = useQueryClient();
  const location = useLocation();
  const navigate = useNavigate();

  // Extract active conversation id from query param if on workspace
  const searchParams = new URLSearchParams(location.search);
  const currentConversationId = location.pathname === '/workspace' ? searchParams.get('c') : null;

  const { data: documents = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: api.getDocuments,
  });

  const { data: conversations = [] } = useQuery({
    queryKey: ['conversations'],
    queryFn: api.getConversations,
  });

  const deleteChatMutation = useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (currentConversationId === deletedId) {
        navigate('/workspace');
      }
    },
  });

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0b0f19] text-slate-100 antialiased selection:bg-blue-500/30">
      <Sidebar 
        docCount={documents.length} 
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={(id) => {
          navigate(id ? `/workspace?c=${id}` : '/workspace');
        }}
        onNewChat={() => {
          navigate('/workspace');
        }}
        onDeleteChat={(id) => deleteChatMutation.mutate(id)}
      />
      <main className="flex-1 flex overflow-hidden">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/documents" element={<DocumentLibrary />} />
          <Route path="/workspace" element={<ResearchWorkspace />} />
          <Route path="/comparison" element={<PaperComparison />} />
          <Route path="/evaluation" element={<EvaluationDashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
