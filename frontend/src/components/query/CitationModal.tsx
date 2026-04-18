import React from 'react';
import { X, BookOpen, ExternalLink } from 'lucide-react';
import type { CitationCard as CitationType } from '../../types';
import CitationCard from './CitationCard';

interface CitationModalProps {
  isOpen: boolean;
  onClose: () => void;
  citations: CitationType[];
}

/** Modal component for displaying source citations and references */
const CitationModal: React.FC<CitationModalProps> = ({ isOpen, onClose, citations }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-md animate-fade-in" 
        onClick={onClose}
      />
      
      <div className="relative w-full max-w-[700px] h-[80vh] bg-base border border-border rounded-20 shadow-2xl flex flex-col overflow-hidden animate-zoom-in">
        <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-base/80 backdrop-blur-xl sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-8 bg-card border border-border flex items-center justify-center shadow-sm">
              <BookOpen className="w-4 h-4 text-textPrimary" />
            </div>
            <div>
              <h3 className="text-textPrimary text-[15px] font-medium">Source Citations</h3>
              <p className="text-textMuted text-[11px] font-mono uppercase tracking-wider">{citations.length} References Found</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-full hover:bg-card text-textMuted hover:text-textPrimary transition-all"
          >
            <X className="w-5 5-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
          {citations.map((c, i) => (
            <div key={i} className="group relative">
               <CitationCard citation={c} index={i} />
            </div>
          ))}
          
          {citations.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-12 h-12 rounded-full bg-card flex items-center justify-center mb-4 shadow-sm">
                <ExternalLink className="w-6 h-6 text-textMuted opacity-20" />
              </div>
              <p className="text-textMuted text-[14px]">No specific citations were mapped for this response.</p>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-border bg-base/80 flex justify-end">
          <button 
            onClick={onClose}
            className="px-5 py-2 rounded-10 bg-card border border-border text-textSecondary text-[13px] font-medium hover:bg-cardHi transition-all hover:border-textMuted"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default CitationModal;
