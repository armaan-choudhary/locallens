import React from 'react';
import { AlertTriangle } from 'lucide-react';

/** Warning banner for potentially unverified content */
const HallucinationWarning: React.FC = () => (
  <div className="
    flex items-start gap-3 mb-4 p-3 rounded-8
    bg-white/5 border border-white/10
    border-l-2 border-l-white
  ">
    <AlertTriangle className="w-[14px] h-[14px] text-white shrink-0 mt-[1px]" />
    <p className="text-[13px] text-muted11 leading-snug">
      Parts of this answer could not be fully verified against source documents.
      Flagged sentences are highlighted.
    </p>
  </div>
);

export default HallucinationWarning;
