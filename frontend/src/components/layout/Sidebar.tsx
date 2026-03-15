import React from 'react';
import type { Document } from '../../types';

interface SidebarProps {
  documents: Document[];
  loading: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ documents, loading }) => {
  return (
    <aside className="w-[220px] h-full border-r border-border p-5 flex flex-col relative shrink-0">
      <div className="font-mono text-[11px] text-muted4 uppercase tracking-[0.08em] mb-3">
        Indexed Documents
      </div>
      
      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        {loading ? (
          <div className="text-muted4 text-[13px] italic">Loading...</div>
        ) : documents.length === 0 ? (
          <div className="text-muted4 text-[13px]">No documents indexed</div>
        ) : (
          <div className="flex flex-col">
            {documents.map((doc) => (
              <div key={doc.doc_id} className="py-2 border-b border-raised group transition-colors">
                <div className="text-muted10 text-[13px] font-medium truncate mb-1" title={doc.filename}>
                  {doc.filename}
                </div>
                <div className="font-mono text-[11px] text-muted4 uppercase">
                  {doc.chunk_count} chunks · {doc.page_count} pages
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="pt-4 mt-auto">
        <div className="font-mono text-[11px] text-muted4 uppercase">
          Milvus · PostgreSQL
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
