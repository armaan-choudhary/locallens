import React, { useEffect, useState, memo, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Upload, Search, Database, CheckSquare, Square, Globe, Trash2, Loader2, MessageSquare, Plus, Info } from 'lucide-react';
import type { Document, ChatSession } from '../../types';
import { 
  deleteDocument, deleteSession, createSession, 
  addDocToSession, removeDocFromSession,
  addDocsToSessionBulk, clearSessionDocs 
} from '../../api/client';
import DocumentDetailsModal from '../ingest/DocumentDetailsModal';
import ProgressBar from '../ui/ProgressBar';

interface SidebarProps {
  documents?: Document[];
  loading?: boolean;
  onRefreshDocs?: () => void;
  sessions?: ChatSession[];
  currentSessionId?: string;
  onSelectSession?: (id: string | undefined) => void;
  onRefreshSessions?: () => void;
  sessionDocIds: Set<string>;
  onToggleDoc: (doc_id: string) => Promise<void>;
  onBulkChange: (ids: Set<string>) => void;
}

/** Individual document item in the sidebar */
const DocItem = memo(({ doc, isScoped, isGlobalMode, isDisabled, onToggle, onDelete, onInfo, deletingId }: any) => {
  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async (e: any) => {
    setIsToggling(true);
    await onToggle(doc.doc_id, e);
    setIsToggling(false);
  };

  return (
    <div className={`
      group relative rounded-6 px-2 py-[8px] transition-colors flex items-start gap-2 
      ${isScoped && !isGlobalMode ? 'bg-white/10' : 'hover:bg-raised'}
      ${isDisabled && !isScoped ? 'opacity-40 grayscale-[0.5]' : ''}
    `}>
      <button
        onClick={handleToggle}
        disabled={isDisabled || isToggling}
        className={`mt-[1px] shrink-0 transition-colors focus:outline-none 
          ${isScoped && !isGlobalMode ? 'text-white' : 'text-muted4 hover:text-white'}`}
      >
        {isToggling ? <Loader2 className="w-[13px] h-[13px] animate-spin" /> :
         isScoped && !isGlobalMode ? <CheckSquare className="w-[13px] h-[13px]" /> : <Square className="w-[13px] h-[13px]" />}
      </button>
      <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onInfo(doc.doc_id)}>
        <div className={`text-[12px] font-medium truncate pr-5 ${isScoped && !isGlobalMode ? 'text-white' : 'text-muted11'}`} title={doc.filename}>
          {doc.filename}
        </div>
        <div className="font-mono text-[10px] text-muted4 mt-[2px] flex items-center gap-2">
          <span>{doc.chunk_count}ch · {doc.page_count}pg</span>
          <Info className="w-2.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-white" />
        </div>
      </div>
      <button
        onClick={(e) => onDelete(doc.doc_id, e)}
        disabled={deletingId === doc.doc_id}
        className="absolute right-1 top-2 opacity-0 group-hover:opacity-100 transition-opacity text-muted4 hover:text-white focus:outline-none"
      >
        {deletingId === doc.doc_id ? <Loader2 className="w-[13px] h-[13px] animate-spin" /> : <Trash2 className="w-[13px] h-[13px]" />}
      </button>
    </div>
  );
});

/** Application sidebar for navigation and document/session management */
const Sidebar: React.FC<SidebarProps> = ({ 
  documents = [], loading = false, onRefreshDocs, 
  sessions = [], currentSessionId, onSelectSession = () => {}, onRefreshSessions = () => {},
  sessionDocIds = new Set(), onToggleDoc = async () => {}, onBulkChange = () => {}
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deletionProgress, setDeletionProgress] = useState(0);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [isBulkOperating, setIsBulkOperating] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const handleToggleDocInternal = useCallback(async (docId: string) => {
    if (!currentSessionId) return;
    await onToggleDoc(docId);
  }, [currentSessionId, onToggleDoc]);

  const handleGlobalSearch = useCallback(async () => {
    if (!currentSessionId) return;
    setIsBulkOperating(true);
    await clearSessionDocs(currentSessionId);
    onBulkChange(new Set());
    setIsBulkOperating(false);
  }, [currentSessionId, onBulkChange]);

  const handleSelectAll = useCallback(async () => {
    if (!currentSessionId) return;
    setIsBulkOperating(true);
    const allIds = documents.map(d => d.doc_id);
    await addDocsToSessionBulk(currentSessionId, allIds);
    onBulkChange(new Set(allIds));
    setIsBulkOperating(false);
  }, [currentSessionId, documents, onBulkChange]);

  const handleDelete = useCallback(async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Remove this document and all its indexed data?')) return;
    
    setDeletingId(docId);
    setDeletionProgress(0);
    
    const interval = setInterval(() => {
      setDeletionProgress(prev => Math.min(prev + (100 / 30), 90));
    }, 100);

    const ok = await deleteDocument(docId);
    
    clearInterval(interval);
    setDeletionProgress(100);
    
    setTimeout(() => {
      setDeletingId(null);
      setDeletionProgress(0);
      if (ok && onRefreshDocs) onRefreshDocs();
    }, 500);
  }, [onRefreshDocs]);

  const handleDeleteSession = useCallback(async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this chat history?')) return;
    setDeletingSessionId(sessionId);
    const ok = await deleteSession(sessionId);
    if (ok) {
      if (sessionId === currentSessionId) onSelectSession(undefined);
      onRefreshSessions();
    }
    setDeletingSessionId(null);
  }, [currentSessionId, onSelectSession, onRefreshSessions]);

  const handleNewChat = useCallback(async () => {
    const res = await createSession();
    if (res) {
      onRefreshSessions();
      onSelectSession(res.session_id);
      navigate('/query');
    }
  }, [onRefreshSessions, onSelectSession, navigate]);

  const isGlobalMode = !!(currentSessionId && sessionDocIds.size === 0);

  return (
    <>
      <aside className="w-[240px] h-full bg-surface border-r border-border flex flex-col shrink-0 overflow-hidden">
        <div className="px-5 pt-5 pb-4 border-b border-border">
          <span className="font-mono text-[13px] font-medium text-white tracking-[0.06em] uppercase">LocalLens</span>
        </div>

        <nav className="px-3 pt-3 flex flex-col gap-[2px]">
          {[
            { path: '/ingest', label: 'Ingest', icon: Upload },
            { path: '/query',  label: 'Search', icon: Search },
          ].map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path;
            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className={`flex items-center gap-[10px] w-full px-3 py-[7px] rounded-8 text-[13px] font-medium transition-all duration-150 text-left ${active ? 'bg-white/10 text-white' : 'text-muted7 hover:text-muted11 hover:bg-raised'}`}
              >
                <Icon className={`w-[14px] h-[14px] shrink-0 ${active ? 'text-white' : 'text-muted5'}`} />
                {label}
              </button>
            );
          })}
        </nav>

        <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
          {deletingId && (
            <div className="px-4 py-3 bg-white/5 border-b border-white/10 animate-fade-in">
              <ProgressBar 
                progress={deletionProgress} 
                label="Deleting..." 
                subLabel="Erasing indexed data"
                size="sm"
              />
            </div>
          )}
          <div className="px-3 pt-4 pb-2">
            <div className="flex items-center justify-between mb-2 px-1">
              <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em]">Documents</div>
              {currentSessionId && (
                <div className="flex items-center gap-2">
                  <button onClick={handleSelectAll} disabled={isBulkOperating} className="font-mono text-[8px] text-muted4 hover:text-white uppercase tracking-wider transition-colors">All</button>
                  <span className="text-muted4 opacity-30">|</span>
                  <button onClick={handleGlobalSearch} disabled={isBulkOperating} className="font-mono text-[8px] text-muted4 hover:text-white uppercase tracking-wider transition-colors">None</button>
                </div>
              )}
            </div>

            {currentSessionId && (
              <div className="px-1 mb-3">
                <button
                  data-testid="global-search-toggle"
                  onClick={handleGlobalSearch}
                  disabled={isBulkOperating}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-6 border transition-all text-left ${isGlobalMode ? 'bg-white/10 border-white/20 text-white' : 'bg-raised/30 border-border text-muted5 hover:border-muted4'}`}
                >
                  {isBulkOperating ? <Loader2 className="w-[12px] h-[12px] animate-spin" /> : <Globe className={`w-[12px] h-[12px] ${isGlobalMode ? 'text-white' : 'text-muted4'}`} />}
                  <span className="text-[11px] font-medium">Global Search</span>
                  {isGlobalMode && <span className="ml-auto font-mono text-[8px] uppercase tracking-tighter opacity-70 italic">Active</span>}
                </button>
              </div>
            )}

            {loading ? (
              <div className="text-muted5 text-[12px] italic px-1">Loading…</div>
            ) : documents.length === 0 ? (
              <div className="text-muted4 text-[12px] px-1">No documents yet.</div>
            ) : (
              <div className="flex flex-col gap-[2px]">
                {documents.map((doc) => (
                  <DocItem 
                    key={doc.doc_id}
                    doc={doc}
                    isScoped={sessionDocIds.has(doc.doc_id)}
                    isGlobalMode={isGlobalMode}
                    isDisabled={isBulkOperating}
                    onToggle={handleToggleDocInternal}
                    onDelete={handleDelete}
                    onInfo={setSelectedDocId}
                    deletingId={deletingId}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="px-3 pt-4 pb-2">
            <div className="flex items-center justify-between mb-2">
               <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em] px-1">Chat History</div>
              <button onClick={handleNewChat} className="p-1 hover:bg-raised rounded-4 text-muted5 hover:text-white transition-colors" title="New Chat"><Plus className="w-[12px] h-[12px]" /></button>
            </div>
            <div className="flex flex-col gap-[2px]">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  onClick={() => onSelectSession(session.session_id)}
                  className={`group relative rounded-6 px-2 py-[8px] cursor-pointer transition-colors flex items-center gap-2 ${currentSessionId === session.session_id ? 'bg-raised' : 'hover:bg-raised/50'}`}
                >
                  <MessageSquare className={`w-[12px] h-[12px] shrink-0 ${currentSessionId === session.session_id ? 'text-white' : 'text-muted4'}`} />
                  <div className={`text-[12px] truncate pr-4 ${currentSessionId === session.session_id ? 'text-white' : 'text-muted7 group-hover:text-muted11'}`}>{session.title}</div>
                  <button onClick={(e) => handleDeleteSession(session.session_id, e)} disabled={deletingSessionId === session.session_id} className="absolute right-1 opacity-0 group-hover:opacity-100 transition-opacity text-muted4 hover:text-white focus:outline-none">
                    {deletingSessionId === session.session_id ? <Loader2 className="w-[11px] h-[11px] animate-spin" /> : <Trash2 className="w-[11px] h-[11px]" />}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="px-5 py-4 border-t border-border mt-auto">
          <div className="flex items-center gap-2 text-muted4">
            <Database className="w-[11px] h-[11px]" />
            <span className="font-mono text-[10px] uppercase tracking-[0.08em]">Milvus · PostgreSQL</span>
          </div>
        </div>
      </aside>

      <DocumentDetailsModal 
        docId={selectedDocId} 
        onClose={() => setSelectedDocId(null)} 
      />
    </>
  );
};

export default Sidebar;
