import React from 'react';
import { AlertTriangle } from 'lucide-react';

const HallucinationWarning: React.FC = () => (
  <div className="
    flex items-start gap-3 mb-4 p-3 rounded-8
    bg-[rgba(251,191,36,0.06)] border border-[rgba(251,191,36,0.18)]
    border-l-2 border-l-warning
  ">
    <AlertTriangle className="w-[14px] h-[14px] text-warning shrink-0 mt-[1px]" />
    <p className="text-[13px] text-warning leading-snug">
      Parts of this answer could not be fully verified against source documents.
      Flagged sentences are underlined.
    </p>
  </div>
);

export default HallucinationWarning;
