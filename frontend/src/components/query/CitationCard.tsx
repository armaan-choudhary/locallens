import React, { useState } from 'react';
import type { CitationCard as CitationType } from '../../types';
import { Eye } from 'lucide-react';

interface CitationCardProps {
  citation: CitationType;
  index: number;
  onViewSource?: (docId: string, docName: string, pageNumber: number) => void;
}

const CitationCard: React.FC<CitationCardProps> = ({ citation, index, onViewSource }) => {
  const [expanded, setExpanded] = useState(false);

  const isImage = citation.source_type === 'image';
  const hasBbox = citation.bbox && citation.bbox.some(v => v !== 0);

  // Sanitise chunk text: trim, fix missing space after hyphenated line breaks
  const rawText  = (citation.chunk_text || '').trim();
  const chunkText = rawText
    .replace(/([a-z])-\n([a-z])/g, '$1$2')   // dehyphenate line breaks
    .replace(/\s{2,}/g, ' ')                   // collapse multiple spaces
    .replace(/^\s*ples of /i, 'Examples of ')  // fix orphaned word starts
    .trim();

  const isLong = chunkText.length > 320;

  // Abbreviate long filenames — keep extension
  const fname = citation.doc_name || 'Unknown';
  const displayName = fname.length > 40
    ? fname.slice(0, 18) + '…' + fname.slice(-12)
    : fname;

  const canViewSource = !!citation.doc_id && !!onViewSource;

  return (
    <div
      className="citation-card bg-card border border-border rounded-10 p-4 mb-3 animate-fade-up"
      style={{ animationDelay: `${index * 55}ms`, animationFillMode: 'both' }}
    >
      {/* Header row */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <span className={`
          font-mono text-[9px] uppercase tracking-[0.12em]
          px-[7px] py-[2px] rounded-4 border shrink-0
          ${isImage
            ? 'bg-[rgba(52,211,153,0.08)] text-success border-[rgba(52,211,153,0.2)]'
            : 'bg-accentDim text-accentLight border-[rgba(124,106,247,0.2)]'}
        `}>
          {isImage ? 'OCR / IMG' : 'TEXT'}
        </span>

        <span
          className="text-[12px] font-medium text-textSecondary truncate flex-1 min-w-0"
          title={fname}
        >
          {displayName}
        </span>

        <span className="font-mono text-[10px] text-textMuted shrink-0">
          pg {citation.page_number}
        </span>
      </div>

      {/* Chunk text block */}
      {chunkText && !isImage && (
        <div className={`
          font-mono text-[11px] leading-[1.75] text-textSecondary
          bg-cardHi border border-border rounded-6 px-3 py-[10px] mb-2
          ${!expanded && isLong ? 'max-h-[90px] overflow-hidden' : ''}
        `}>
          {chunkText}
        </div>
      )}

      {isImage && citation.image_id && (
        <div className="mb-3 rounded-8 overflow-hidden border border-border bg-black/20 group-hover:border-accent/30 transition-colors">
          <img 
            src={`/api/images/${citation.image_id}`} 
            alt="Extracted Region" 
            className="w-full h-auto object-contain max-h-[300px] hover:scale-[1.02] transition-transform duration-500"
            loading="lazy"
          />
        </div>
      )}

      {!chunkText && !isImage && (
        <div className="font-mono text-[11px] text-textMuted italic mb-2 px-1">
          No text chunk available.
        </div>
      )}

      {isLong && (
        <button
          onClick={() => setExpanded(v => !v)}
          className="
            text-[11px] text-textMuted hover:text-textPrimary
            transition-colors focus:outline-none mb-2 block
          "
        >
          {expanded ? '↑ collapse' : '↓ show more'}
        </button>
      )}

      {/* Footer: Bbox + View Source */}
      <div className="flex items-center justify-between mt-1">
        {/* Bbox row — only for verified image sources */}
        {hasBbox && citation.bbox ? (
          <div className="font-mono text-[9px] text-textMuted tracking-[0.04em]">
            BBOX &nbsp;
            {[
              `x₀=${Math.round(citation.bbox[0])}`,
              `y₀=${Math.round(citation.bbox[1])}`,
              `x₁=${Math.round(citation.bbox[2])}`,
              `y₁=${Math.round(citation.bbox[3])}`,
            ].join('  ')}
          </div>
        ) : <div />}

        {/* View Source button */}
        {canViewSource && (
          <button
            onClick={() => onViewSource!(citation.doc_id!, citation.doc_name, citation.page_number)}
            className="
              flex items-center gap-1.5 px-2.5 py-1 rounded-6
              bg-accent/8 border border-accent/15
              text-accent text-[10px] font-medium font-mono uppercase tracking-wider
              hover:bg-accent/15 hover:border-accent/30 transition-all
              group
            "
            title={`View page ${citation.page_number} in ${fname}`}
          >
            <Eye className="w-3 h-3 group-hover:scale-110 transition-transform" />
            View Source
          </button>
        )}
      </div>
    </div>
  );
};

export default CitationCard;
