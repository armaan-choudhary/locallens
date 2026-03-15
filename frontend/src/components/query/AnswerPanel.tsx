import React, { useState } from 'react';
import { Copy, Check, AlertTriangle, ShieldCheck } from 'lucide-react';
import HallucinationWarning from './HallucinationWarning';

/** Client-side safety net — strips residual LLM artefacts */
function sanitiseAnswer(text: string): string {
  return text
    // Remove raw source-label echoes: "— source: foo.pdf, page 7"
    .replace(/—\s*source:\s*\S+,\s*page\s*\d+/gi, '')
    // Remove image placeholder echoes
    .replace(/\[Image found on page \d+ of .+?—.+?\]/gi, '')
    // Remove template leftovers
    .replace(/\[Insert answer here\]['""]?/gi, '')
    // Collapse double spaces / artefact spacing
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

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
  flaggedSentences,
}) => {
  const [copied, setCopied] = useState(false);
  const cleanAnswer = sanitiseAnswer(answer);

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanAnswer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderAnswer = () => {
    if (flaggedSentences.length === 0) {
      return <span>{cleanAnswer}</span>;
    }

    const parts = cleanAnswer.split(/([.!?]\s+)/);
    return (
      <>
        {parts.map((part, i) => {
          const isFlagged = flaggedSentences.some(
            s => typeof s === 'string' && s.toLowerCase().includes(part.trim().toLowerCase()) && part.trim().length > 10
          );
          return (
            <span key={i} className={isFlagged ? 'flagged' : ''}>
              {part}
            </span>
          );
        })}
      </>
    );
  };

  return (
    <div className="flex flex-col animate-fade-up">
      {/* Section label */}
      <div className="flex items-center gap-2 mb-4">
        <span className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em]">
          Answer
        </span>
        {verified ? (
          <span className="flex items-center gap-1 font-mono text-[9px] text-success">
            <ShieldCheck className="w-[10px] h-[10px]" /> verified
          </span>
        ) : (
          <span className="flex items-center gap-1 font-mono text-[9px] text-warning">
            <AlertTriangle className="w-[10px] h-[10px]" /> unverified
          </span>
        )}
      </div>

      {!verified && <HallucinationWarning />}

      {/* Answer body */}
      <div className="answer-text">{renderAnswer()}</div>

      {/* Footer */}
      <div className="mt-8 flex items-center justify-between border-t border-border pt-4">
        <div className="font-mono text-[11px] text-muted4">
          {latency.toFixed(1)}s &nbsp;·&nbsp; LOCALLENS-LOCAL-01
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-muted5 hover:text-muted11 transition-colors focus:outline-none"
        >
          {copied
            ? <Check className="w-[13px] h-[13px] text-success" />
            : <Copy className="w-[13px] h-[13px]" />
          }
          <span className="text-[12px]">{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
    </div>
  );
};

export default AnswerPanel;
