import React from 'react';
import type { CitationCard as CitationType } from '../../types';
import CitationCard from './CitationCard';

interface CitationPanelProps {
  citations: CitationType[];
}

const CitationPanel: React.FC<CitationPanelProps> = ({ citations }) => {
  return (
    <div className="flex flex-col">
      <div className="font-mono text-[11px] text-muted4 uppercase tracking-[0.08em] mb-4">
        Sources
      </div>
      
      <div className="flex flex-col">
        {citations.map((citation, i) => (
          <CitationCard key={i} citation={citation} />
        ))}
        {citations.length === 0 && (
          <div className="text-muted4 text-[13px]">No references found.</div>
        )}
      </div>
    </div>
  );
};

export default CitationPanel;
