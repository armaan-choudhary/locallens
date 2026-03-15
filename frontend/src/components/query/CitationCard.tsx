import React, { useState } from 'react';
import type { CitationCard as CitationType } from '../../types';
import Badge from '../shared/Badge';

interface CitationCardProps {
  citation: CitationType;
}

const CitationCard: React.FC<CitationCardProps> = ({ citation }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-surface border border-border border-l-2 border-l-muted5 rounded-8 p-3 mb-2 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="font-mono text-[12px] text-muted7 truncate max-w-[140px]" title={citation.doc_name}>
          {citation.doc_name}
        </div>
        <div className="flex gap-2">
          <Badge>pg. {citation.page_number}</Badge>
          <Badge>{citation.source_type}</Badge>
        </div>
      </div>

      <div className={`font-mono text-[12px] text-muted5 leading-[1.6] ${!isExpanded ? 'line-clamp-3' : ''}`}>
        {citation.chunk_text || 'Image reference at the specified page coordinates.'}
      </div>
      
      {citation.chunk_text && citation.chunk_text.length > 200 && (
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-muted4 text-[12px] mt-1 text-left hover:text-muted10 transition-colors focus:outline-none"
        >
          {isExpanded ? 'show less' : 'show more'}
        </button>
      )}

      {citation.bbox && (
        <div className="font-mono text-[11px] text-muted4 mt-2">
          bbox  {citation.bbox[0]} · {citation.bbox[1]} · {citation.bbox[2]} · {citation.bbox[3]}
        </div>
      )}
    </div>
  );
};

export default CitationCard;
