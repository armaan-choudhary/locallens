import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { getDocuments } from './api/client';
import type { Document } from './types';
import OnboardingPage from './pages/OnboardingPage';
import IngestPage from './pages/IngestPage';
import QueryPage from './pages/QueryPage';

const App: React.FC = () => {
  const [documents, setDocuments] = useState<Document[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDocuments()
      .then(docs => setDocuments(docs))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-base gap-4">
        <div className="w-6 h-6 rounded-full border-2 border-border border-t-accent animate-spin" />
        <div className="font-mono text-[11px] text-muted4 uppercase tracking-[0.15em] animate-pulse-slow">
          Initializing LocalLens
        </div>
      </div>
    );
  }

  const hasDocs = documents && documents.length > 0;

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="bg-base min-h-screen text-muted9 font-inter">
        <Routes>
          <Route
            path="/"
            element={hasDocs ? <Navigate to="/ingest" replace /> : <OnboardingPage />}
          />
          <Route path="/ingest" element={<IngestPage />} />
          <Route path="/query"  element={<QueryPage />} />
          <Route path="*"       element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
