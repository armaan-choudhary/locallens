import React from 'react';
import type { CitationCard as CitationType } from '../../types';
import CitationCard from './CitationCard';
import { BookOpen } from 'lucide-react';

interface CitationPanelProps {
  citations: CitationType[];
}

const CitationPanel: React.FC<CitationPanelProps> = ({ citations }) => {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-[12px] h-[12px] text-textMuted" />
        <span className="font-mono text-[9px] text-textMuted uppercase tracking-[0.12em]">
          Sources — {citations.length}
        </span>
      </div>

      {citations.length === 0 ? (
        <div className="text-textMuted text-[13px] italic">No citations found.</div>
      ) : (
        <div>
          {citations.map((c, i) => (
            <CitationCard key={i} citation={c} index={i} />
          ))}
        </div>
      )}
    </div>
  );
};

export default CitationPanel;
