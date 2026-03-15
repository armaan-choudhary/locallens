import React from 'react';

const HallucinationWarning: React.FC = () => {
  return (
    <div className="border-left-2 border-muted5 p-2 px-3 bg-surface font-inter text-[12px] text-muted7 mb-4 flex items-center gap-2">
      <span className="shrink-0">⚠</span>
      Some sentences could not be verified against source documents.
    </div>
  );
};

export default HallucinationWarning;
