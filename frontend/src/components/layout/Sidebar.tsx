import React, { useState } from 'react';
import type { Document } from '../../types';
import { Trash2, Loader2 } from 'lucide-react';
import { deleteDocument } from '../../api/client';

interface SidebarProps {
  documents: Document[];
  loading: boolean;
  onRefresh?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ documents, loading, onRefresh }) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to remove this indexed document? This will delete all associated chunks and vectors.')) {
      return;
    }

    setDeletingId(docId);
    const success = await deleteDocument(docId);
    setDeletingId(null);

    if (success && onRefresh) {
      onRefresh();
    }
  };

  return (
    <aside className="w-[220px] h-full border-r border-border p-5 flex flex-col relative shrink-0 overflow-hidden">
      <div className="font-mono text-[11px] text-muted4 uppercase tracking-[0.08em] mb-3">
        Indexed Documents
      </div>
      
      <div className="flex-1 overflow-y-auto overflow-x-hidden pr-1">
        {loading ? (
          <div className="text-muted4 text-[13px] italic">Loading...</div>
        ) : documents.length === 0 ? (
          <div className="text-muted4 text-[13px]">No documents indexed</div>
        ) : (
          <div className="flex flex-col">
            {documents.map((doc) => (
              <div key={doc.doc_id} className="py-2 border-b border-raised group transition-colors relative">
                <div className="flex justify-between items-start pr-6">
                  <div className="text-muted10 text-[13px] font-medium truncate mb-1" title={doc.filename}>
                    {doc.filename}
                  </div>
                </div>
                <div className="font-mono text-[11px] text-muted4 uppercase">
                  {doc.chunk_count} chunks · {doc.page_count} pages
                </div>
                
                <button
                  onClick={(e) => handleDelete(doc.doc_id, e)}
                  disabled={deletingId === doc.doc_id}
                  className="absolute right-0 top-2 opacity-0 group-hover:opacity-100 transition-opacity text-muted4 hover:text-white focus:outline-none"
                  title="Remove document"
                >
                  {deletingId === doc.doc_id ? (
                    <Loader2 className="w-[14px] h-[14px] animate-spin" />
                  ) : (
                    <Trash2 className="w-[14px] h-[14px]" />
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="pt-4 mt-auto border-t border-border">
        <div className="font-mono text-[11px] text-muted4 uppercase">
          Milvus · PostgreSQL
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
