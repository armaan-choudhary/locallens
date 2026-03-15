import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Upload, Search, Database } from 'lucide-react';
import type { Document } from '../../types';
import { Trash2, Loader2 } from 'lucide-react';
import { deleteDocument } from '../../api/client';

interface SidebarProps {
  documents: Document[];
  loading: boolean;
  onRefresh?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ documents, loading, onRefresh }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [deletingId, setDeletingId] = React.useState<string | null>(null);

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Remove this document and all its indexed data?')) return;
    setDeletingId(docId);
    const ok = await deleteDocument(docId);
    setDeletingId(null);
    if (ok && onRefresh) onRefresh();
  };

  const navItems = [
    { path: '/ingest', label: 'Ingest', icon: Upload },
    { path: '/query',  label: 'Search', icon: Search },
  ];

  return (
    <aside className="w-[220px] h-full bg-surface border-r border-border flex flex-col shrink-0 overflow-hidden">
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

      {/* Doc list */}
      <div className="px-3 pt-4 pb-2">
        <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em] px-1 mb-2">
          Indexed Documents
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-3">
        {loading ? (
          <div className="text-muted5 text-[12px] italic px-1">Loading…</div>
        ) : documents.length === 0 ? (
          <div className="text-muted4 text-[12px] px-1">No documents yet.</div>
        ) : (
          <div className="flex flex-col gap-[2px]">
            {documents.map((doc) => (
              <div
                key={doc.doc_id}
                className="group relative rounded-6 px-2 py-[8px] hover:bg-raised transition-colors"
              >
                <div
                  className="text-muted11 text-[12px] font-medium truncate pr-5"
                  title={doc.filename}
                >
                  {doc.filename}
                </div>
                <div className="font-mono text-[10px] text-muted4 mt-[2px]">
                  {doc.chunk_count}ch · {doc.page_count}pg
                </div>
                <button
                  onClick={(e) => handleDelete(doc.doc_id, e)}
                  disabled={deletingId === doc.doc_id}
                  className="absolute right-1 top-2 opacity-0 group-hover:opacity-100 transition-opacity text-muted4 hover:text-error focus:outline-none"
                  title="Remove document"
                >
                  {deletingId === doc.doc_id
                    ? <Loader2 className="w-[13px] h-[13px] animate-spin" />
                    : <Trash2 className="w-[13px] h-[13px]" />
                  }
                </button>
              </div>
            ))}
          </div>
        )}
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
