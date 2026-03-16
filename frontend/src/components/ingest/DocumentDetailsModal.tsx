import React, { useEffect, useState } from 'react';
import { X, FileText, Image as ImageIcon, Calendar, Layers, ExternalLink, Loader2 } from 'lucide-react';
import { getDocumentDetails } from '../../api/client';

interface DocumentDetailsModalProps {
  docId: string | null;
  onClose: () => void;
}

/**
 * Modal for displaying detailed document insights, including text chunks and images.
 */
const DocumentDetailsModal: React.FC<DocumentDetailsModalProps> = ({ docId, onClose }) => {
  const [details, setDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chunks' | 'images'>('chunks');

  useEffect(() => {
    if (docId) {
      setLoading(true);
      getDocumentDetails(docId).then(data => {
        setDetails(data);
        setLoading(false);
      });
    } else {
      setDetails(null);
    }
  }, [docId]);

  if (!docId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-md" onClick={onClose} />
      
      <div className="relative w-full max-w-[800px] h-[85vh] bg-surface border border-border rounded-20 shadow-2xl flex flex-col overflow-hidden animate-fade-in">
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4">
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
            <p className="text-muted4 font-mono text-[11px] uppercase tracking-widest">Loading document insights...</p>
          </div>
        ) : details ? (
          <>
            <div className="px-6 py-5 border-b border-border bg-surface/50 backdrop-blur-xl">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-10 bg-raised border border-border flex items-center justify-center text-accent">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-white text-[16px] font-medium leading-tight mb-1">{details.metadata.filename}</h3>
                    <div className="flex items-center gap-3 font-mono text-[10px] text-muted4 uppercase tracking-wider">
                       <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(details.metadata.ingested_at).toLocaleDateString()}</span>
                       <span className="flex items-center gap-1"><Layers className="w-3 h-3" /> {details.metadata.page_count} Pages</span>
                    </div>
                  </div>
                </div>
                <button onClick={onClose} className="p-2 rounded-full hover:bg-raised text-muted5 hover:text-white transition-all">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="flex border-b border-border px-6">
              <button 
                onClick={() => setActiveTab('chunks')}
                className={`px-4 py-3 text-[13px] font-medium transition-colors relative ${activeTab === 'chunks' ? 'text-accent' : 'text-muted5 hover:text-muted11'}`}
              >
                Text Samples
                {activeTab === 'chunks' && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-accent" />}
              </button>
              <button 
                onClick={() => setActiveTab('images')}
                className={`px-4 py-3 text-[13px] font-medium transition-colors relative ${activeTab === 'images' ? 'text-accent' : 'text-muted5 hover:text-muted11'}`}
              >
                Extracted Images ({details.images.length})
                {activeTab === 'images' && <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-accent" />}
              </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-base/30">
              {activeTab === 'chunks' ? (
                <div className="space-y-4">
                  {details.chunks.map((chunk: any, i: number) => (
                    <div key={chunk.chunk_id} className="bg-raised/30 border border-border p-4 rounded-10">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-[9px] text-muted4 uppercase">Chunk {i+1} · Page {chunk.page_number}</span>
                        <span className="font-mono text-[8px] px-1.5 py-0.5 rounded bg-surface border border-border text-muted5 uppercase">{chunk.source}</span>
                      </div>
                      <p className="text-[12px] text-muted11 font-mono leading-relaxed line-clamp-4">{chunk.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  {details.images.map((img: any) => (
                    <div key={img.image_id} className="group relative bg-raised/30 border border-border rounded-10 overflow-hidden flex flex-col">
                      <div className="aspect-video bg-black/40 flex items-center justify-center overflow-hidden">
                        <img 
                          src={`/api/images/${img.image_id}`} 
                          alt="Region" 
                          className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-500"
                        />
                      </div>
                      <div className="p-3 border-t border-border flex items-center justify-between">
                        <span className="font-mono text-[9px] text-muted4 uppercase">Page {img.page_number}</span>
                        <button className="text-muted4 hover:text-accent transition-colors">
                          <ExternalLink className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                  {details.images.length === 0 && (
                    <div className="col-span-2 py-12 flex flex-col items-center justify-center text-center opacity-40">
                      <ImageIcon className="w-12 h-12 mb-4 text-muted4" />
                      <p className="text-[14px] text-muted4">No images or diagrams were detected in this document.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};

export default DocumentDetailsModal;
