import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Upload, Search, Database, CheckSquare, Square } from 'lucide-react';
import type { Document } from '../../types';
import { Trash2, Loader2, MessageSquare, Plus } from 'lucide-react';
import { deleteDocument, deleteSession, createSession, getSessionDocs, addDocToSession, removeDocFromSession } from '../../api/client';
import type { ChatSession } from '../../types';

interface SidebarProps {
  documents: Document[];
  loading: boolean;
  onRefreshDocs?: () => void;
  sessions: ChatSession[];
  currentSessionId?: string;
  onSelectSession: (id: string | undefined) => void;
  onRefreshSessions: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  documents, 
  loading, 
  onRefreshDocs, 
  sessions, 
  currentSessionId, 
  onSelectSession,
  onRefreshSessions 
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [deletingId, setDeletingId] = React.useState<string | null>(null);
  const [deletingSessionId, setDeletingSessionId] = React.useState<string | null>(null);

  // Per-session doc scope
  const [sessionDocIds, setSessionDocIds] = useState<Set<string>>(new Set());
  const [togglingDocId, setTogglingDocId] = useState<string | null>(null);

  useEffect(() => {
    if (currentSessionId) {
      getSessionDocs(currentSessionId).then(ids => setSessionDocIds(new Set(ids)));
    } else {
      setSessionDocIds(new Set());
    }
  }, [currentSessionId]);

  const handleToggleDoc = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!currentSessionId) return;
    setTogglingDocId(docId);
    const isIn = sessionDocIds.has(docId);
    if (isIn) {
      await removeDocFromSession(currentSessionId, docId);
      setSessionDocIds(prev => { const s = new Set(prev); s.delete(docId); return s; });
    } else {
      await addDocToSession(currentSessionId, docId);
      setSessionDocIds(prev => new Set([...prev, docId]));
    }
    setTogglingDocId(null);
  };

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Remove this document and all its indexed data?')) return;
    setDeletingId(docId);
    const ok = await deleteDocument(docId);
    setDeletingId(null);
    if (ok && onRefreshDocs) onRefreshDocs();
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this chat history?')) return;
    setDeletingSessionId(sessionId);
    const ok = await deleteSession(sessionId);
    if (ok) {
      if (sessionId === currentSessionId) onSelectSession(undefined);
      onRefreshSessions();
    }
    setDeletingSessionId(null);
  };

  const handleNewChat = async () => {
    const res = await createSession();
    if (res) {
      onRefreshSessions();
      onSelectSession(res.session_id);
      navigate('/query');
    }
  };

  const navItems = [
    { path: '/ingest', label: 'Ingest', icon: Upload },
    { path: '/query',  label: 'Search', icon: Search },
  ];

  return (
    <aside className="w-[240px] h-full bg-surface border-r border-border flex flex-col shrink-0 overflow-hidden">
      {/* Logo */}
      <div className="px-5 pt-5 pb-4 border-b border-border">
        <span className="font-mono text-[13px] font-medium text-white tracking-[0.06em] uppercase">
          LocalLens
        </span>
      </div>

      {/* Nav */}
      <nav className="px-3 pt-3 flex flex-col gap-[2px]">
        {navItems.map(({ path, label, icon: Icon }) => {
          const active = location.pathname === path;
          return (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`
                flex items-center gap-[10px] w-full px-3 py-[7px] rounded-8
                text-[13px] font-medium transition-all duration-150 text-left
                ${active
                  ? 'bg-accentDim text-white'
                  : 'text-muted7 hover:text-muted11 hover:bg-raised'}
              `}
            >
              <Icon
                className={`w-[14px] h-[14px] shrink-0 ${active ? 'text-accent' : 'text-muted5'}`}
              />
              {label}
            </button>
          );
        })}
      </nav>

      <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
        {/* Doc list */}
        <div className="px-3 pt-4 pb-2">
          <div className="flex items-center justify-between mb-2 px-1">
            <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em]">
              Documents
            </div>
            {currentSessionId && (
              <span className="font-mono text-[8px] text-accent uppercase tracking-wider">
                {sessionDocIds.size === 0 ? 'All' : `${sessionDocIds.size} selected`}
              </span>
            )}
          </div>

          {currentSessionId && (
            <div className="font-mono text-[9px] text-muted4 px-1 mb-2 leading-relaxed">
              Toggle docs for this chat. Unselected = searches all.
            </div>
          )}

          {loading ? (
            <div className="text-muted5 text-[12px] italic px-1">Loading…</div>
          ) : documents.length === 0 ? (
            <div className="text-muted4 text-[12px] px-1">No documents yet.</div>
          ) : (
            <div className="flex flex-col gap-[2px]">
              {documents.map((doc) => {
                const isScoped = currentSessionId ? sessionDocIds.has(doc.doc_id) : false;
                const isToggling = togglingDocId === doc.doc_id;
                return (
                  <div
                    key={doc.doc_id}
                    className={`group relative rounded-6 px-2 py-[8px] transition-colors flex items-start gap-2 ${isScoped ? 'bg-accentDim/30' : 'hover:bg-raised'}`}
                  >
                    {/* Checkbox toggle - only show when a session is active */}
                    {currentSessionId && (
                      <button
                        onClick={(e) => handleToggleDoc(doc.doc_id, e)}
                        disabled={isToggling}
                        className="mt-[1px] shrink-0 text-muted4 hover:text-accent transition-colors focus:outline-none"
                      >
                        {isToggling
                          ? <Loader2 className="w-[13px] h-[13px] animate-spin" />
                          : isScoped
                            ? <CheckSquare className="w-[13px] h-[13px] text-accent" />
                            : <Square className="w-[13px] h-[13px]" />
                        }
                      </button>
                    )}
                    <div className="flex-1 min-w-0">
                      <div
                        className={`text-[12px] font-medium truncate pr-5 ${isScoped ? 'text-white' : 'text-muted11'}`}
                        title={doc.filename}
                      >
                        {doc.filename}
                      </div>
                      <div className="font-mono text-[10px] text-muted4 mt-[2px]">
                        {doc.chunk_count}ch · {doc.page_count}pg
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDelete(doc.doc_id, e)}
                      disabled={deletingId === doc.doc_id}
                      className="absolute right-1 top-2 opacity-0 group-hover:opacity-100 transition-opacity text-muted4 hover:text-error focus:outline-none"
                    >
                      {deletingId === doc.doc_id
                        ? <Loader2 className="w-[13px] h-[13px] animate-spin" />
                        : <Trash2 className="w-[13px] h-[13px]" />
                      }
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Chat History */}
        <div className="px-3 pt-4 pb-2">
          <div className="flex items-center justify-between mb-2">
             <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em] px-1">
              Chat History
            </div>
            <button 
              onClick={handleNewChat}
              className="p-1 hover:bg-raised rounded-4 text-muted5 hover:text-accent transition-colors"
              title="New Chat"
            >
              <Plus className="w-[12px] h-[12px]" />
            </button>
          </div>
          <div className="flex flex-col gap-[2px]">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                onClick={() => onSelectSession(session.session_id)}
                className={`
                  group relative rounded-6 px-2 py-[8px] cursor-pointer transition-colors flex items-center gap-2
                  ${currentSessionId === session.session_id ? 'bg-raised' : 'hover:bg-raised/50'}
                `}
              >
                <MessageSquare className={`w-[12px] h-[12px] shrink-0 ${currentSessionId === session.session_id ? 'text-accent' : 'text-muted4'}`} />
                <div
                  className={`text-[12px] truncate pr-4 ${currentSessionId === session.session_id ? 'text-white' : 'text-muted7 group-hover:text-muted11'}`}
                >
                  {session.title}
                </div>
                <button
                  onClick={(e) => handleDeleteSession(session.session_id, e)}
                  disabled={deletingSessionId === session.session_id}
                  className="absolute right-1 opacity-0 group-hover:opacity-100 transition-opacity text-muted4 hover:text-error focus:outline-none"
                >
                  {deletingSessionId === session.session_id
                    ? <Loader2 className="w-[11px] h-[11px] animate-spin" />
                    : <Trash2 className="w-[11px] h-[11px]" />
                  }
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border mt-auto">
        <div className="flex items-center gap-2 text-muted4">
          <Database className="w-[11px] h-[11px]" />
          <span className="font-mono text-[10px] uppercase tracking-[0.08em]">
            Milvus · PostgreSQL
          </span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
