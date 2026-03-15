import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { getDocuments } from './api/client';
import type { Document } from './types';
import Topbar from './components/layout/Topbar';
import OnboardingPage from './pages/OnboardingPage';
import IngestPage from './pages/IngestPage';
import QueryPage from './pages/QueryPage';

const App: React.FC = () => {
  const [documents, setDocuments] = useState<Document[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDocs = async () => {
      const docs = await getDocuments();
      setDocuments(docs);
      setLoading(false);
    };
    fetchDocs();
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-base">
        <div className="font-mono text-[12px] text-muted4 animate-pulse uppercase tracking-widest">
          Initializing LocalLens
        </div>
      </div>
    );
  }

  const hasDocs = documents && documents.length > 0;

  return (
    <Router>
      <div className="bg-base min-h-screen text-muted10 font-inter">
        <Routes>
          <Route 
            path="/" 
            element={hasDocs ? <Navigate to="/ingest" replace /> : <OnboardingPage />} 
          />
          <Route 
            path="/ingest" 
            element={<><Topbar /><IngestPage /></>} 
          />
          <Route 
            path="/query" 
            element={<><Topbar /><QueryPage /></>} 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
