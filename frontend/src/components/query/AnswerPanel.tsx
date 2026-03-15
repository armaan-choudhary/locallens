import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import HallucinationWarning from './HallucinationWarning';

interface AnswerPanelProps {
  answer: string;
  verified: boolean;
  latency: number;
  flaggedSentences: string[];
}

const AnswerPanel: React.FC<AnswerPanelProps> = ({ 
  answer, 
  verified, 
  latency, 
  flaggedSentences 
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Basic sentence highlighting logic
  // This is a naive implementation; ideally we'd use a more robust text matching or splitting
  // For the prompt requirement: "Flagged sentences inside the answer text get border-bottom: 1px solid #52525b only."

  return (
    <div className="flex flex-col">
      <div className="font-mono text-[11px] text-muted4 uppercase tracking-[0.08em] mb-4">
        Answer
      </div>

      {!verified && <HallucinationWarning />}

      <div className="text-[14px] text-muted14 leading-[1.75] font-inter whitespace-pre-wrap">
        {flaggedSentences.length === 0 ? answer : (
          answer.split(/([.!?]\s+)/).map((part, i) => {
            const isFlagged = flaggedSentences.some(s => s.toLowerCase().includes(part.trim().toLowerCase()) && part.trim().length > 10);
            return (
              <span key={i} className={isFlagged ? 'border-b border-muted5' : ''}>
                {part}
              </span>
            );
          })
        )}
      </div>

      <div className="mt-8 flex items-center justify-between">
        <div className="font-mono text-[12px] text-muted4">
          · {latency.toFixed(1)}s
        </div>
        <button 
          onClick={handleCopy}
          className="flex items-center gap-2 text-muted5 hover:text-muted10 transition-colors focus:outline-none"
        >
          {copied ? <Check className="w-[13px] h-[13px]" /> : <Copy className="w-[13px] h-[13px]" />}
          <span className="text-[13px]">{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
    </div>
  );
};

export default AnswerPanel;
