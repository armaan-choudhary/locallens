import React from 'react';
import { AlertTriangle } from 'lucide-react';

/** Warning banner for potentially unverified content */
const HallucinationWarning: React.FC = () => (
  <div className="
    flex items-start gap-3 mb-4 p-3 rounded-8
    bg-warning/10 border border-warning/30
    border-l-2 border-l-warning
  ">
    <AlertTriangle className="w-[14px] h-[14px] text-warning shrink-0 mt-[1px]" />
    <p className="text-[13px] text-textSecondary leading-snug">
      Parts of this answer could not be fully verified against source documents.
      Flagged sentences are highlighted.
    </p>
  </div>
);

export default HallucinationWarning;
