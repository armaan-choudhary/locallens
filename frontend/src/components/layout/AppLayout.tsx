import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import {
  getDocuments, getSessions, getSessionDocs,
  addDocToSession, removeDocFromSession,
  addDocsToSessionBulk, clearSessionDocs,
} from '../../api/client';
import type { Document, ChatSession } from '../../types';
import Sidebar from './Sidebar';

export interface AppLayoutContext {
  documents: Document[];
  docsLoading: boolean;
  fetchDocs: () => Promise<void>;
  sessions: ChatSession[];
  fetchSessions: () => Promise<void>;
  currentSessionId: string | undefined;
  setCurrentSessionId: (id: string | undefined) => void;
  sessionDocIds: Set<string>;
  handleToggleDoc: (docId: string) => Promise<void>;
  handleBulkChange: (ids: Set<string>) => void;
}

import { createContext, useContext } from 'react';
export const AppLayoutCtx = createContext<AppLayoutContext | null>(null);
export const useAppLayout = () => {
  const ctx = useContext(AppLayoutCtx);
  if (!ctx) throw new Error('useAppLayout must be used within AppLayout');
  return ctx;
};

const AppLayout: React.FC = () => {
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionIdState] = useState<string | undefined>(
    () => localStorage.getItem('currentSessionId') || undefined
  );
  const [sessionDocIds, setSessionDocIds] = useState<Set<string>>(new Set());

  const fetchDocs = useCallback(async () => {
    setDocsLoading(true);
    const docs = await getDocuments();
    setDocuments(docs);
    setDocsLoading(false);
  }, []);

  const fetchSessions = useCallback(async () => {
    const sess = await getSessions();
    setSessions(sess);
  }, []);

  const fetchSessionDocs = useCallback(async (sid: string) => {
    const ids = await getSessionDocs(sid);
    setSessionDocIds(new Set(ids));
  }, []);

  const setCurrentSessionId = useCallback((id: string | undefined) => {
    setCurrentSessionIdState(id);
    if (id) {
      localStorage.setItem('currentSessionId', id);
    } else {
      localStorage.removeItem('currentSessionId');
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchDocs();
    fetchSessions();
  }, [fetchDocs, fetchSessions]);

  // When session changes, load its docs (or clear)
  useEffect(() => {
    if (currentSessionId) {
      fetchSessionDocs(currentSessionId);
    } else {
      setSessionDocIds(new Set());
    }
  }, [currentSessionId, fetchSessionDocs]);

  const handleToggleDoc = useCallback(async (docId: string) => {
    if (!currentSessionId) return;
    const isIn = sessionDocIds.has(docId);
    if (isIn) {
      await removeDocFromSession(currentSessionId, docId);
    } else {
      await addDocToSession(currentSessionId, docId);
    }
    setSessionDocIds(prev => {
      const s = new Set(prev);
      if (isIn) s.delete(docId); else s.add(docId);
      return s;
    });
  }, [currentSessionId, sessionDocIds]);

  const handleBulkChange = useCallback((ids: Set<string>) => {
    setSessionDocIds(ids);
  }, []);

  // When selecting a session from sidebar, navigate to query page
  const handleSelectSession = useCallback((id: string | undefined) => {
    setCurrentSessionId(id);
    navigate('/query');
  }, [setCurrentSessionId, navigate]);

  const ctx: AppLayoutContext = {
    documents,
    docsLoading,
    fetchDocs,
    sessions,
    fetchSessions,
    currentSessionId,
    setCurrentSessionId,
    sessionDocIds,
    handleToggleDoc,
    handleBulkChange,
  };

  return (
    <AppLayoutCtx.Provider value={ctx}>
      <div className="flex h-screen overflow-hidden">
        <Sidebar
          documents={documents}
          loading={docsLoading}
          onRefreshDocs={fetchDocs}
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onRefreshSessions={fetchSessions}
          sessionDocIds={sessionDocIds}
          onToggleDoc={handleToggleDoc}
          onBulkChange={handleBulkChange}
        />
        <Outlet />
      </div>
    </AppLayoutCtx.Provider>
  );
};

export default AppLayout;
