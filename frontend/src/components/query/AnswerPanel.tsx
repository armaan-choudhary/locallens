import React, { useState, useMemo } from 'react';
import { Copy, Check, AlertTriangle, ShieldCheck, Info } from 'lucide-react';
import HallucinationWarning from './HallucinationWarning';
import type { SupportScore } from '../../types';

/** Sanitizes answer text by removing LLM-specific artifacts and thinking blocks */
function sanitiseAnswer(text: string): string {
  return text
    .replace(/<think>[\s\S]*?<\/think>/gi, '')
    .replace(/—\s*source:\s*\S+,\s*page\s*\d+/gi, '')
    .replace(/\[Image found on page \d+ of .+?—.+?\]/gi, '')
    .replace(/\[Insert answer here\]['""]?/gi, '')
    // Strip markdown bold/italic/heading markers
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/__(.+?)__/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

interface AnswerPanelProps {
  answer: string;
  verified: boolean;
  latency: number;
  flaggedSentences: string[];
  supportScores?: SupportScore[];
  isStreaming?: boolean;
}

/** Displays the generated answer with verification status and confidence levels */
const AnswerPanel: React.FC<AnswerPanelProps> = ({
  answer,
  verified,
  latency,
  flaggedSentences,
  supportScores = [],
  isStreaming = false
}) => {
  const [copied, setCopied] = useState(false);
  const cleanAnswer = useMemo(() => sanitiseAnswer(answer), [answer]);

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanAnswer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const confidence = useMemo(() => {
    if (supportScores.length === 0) return null;
    const avg = supportScores.reduce((a, b) => a + b.score, 0) / supportScores.length;
    return Math.round(avg * 100);
  }, [supportScores]);

  /** Render a single sentence with optional highlighting */
  const renderSentence = (sentence: string, key: string) => {
    const trimmed = sentence.trim();
    if (!trimmed) return null;

    const scoreObj = supportScores.find(s =>
      trimmed.toLowerCase().includes(s.sentence.toLowerCase()) ||
      s.sentence.toLowerCase().includes(trimmed.toLowerCase())
    );

    const isFlagged = flaggedSentences.some(
      s => trimmed.toLowerCase().includes(s.toLowerCase()) && trimmed.length > 10
    );

    let bgClass = "";
    let title = "";

    if (scoreObj) {
      const s = scoreObj.score;
      if (s > 0.7) bgClass = "hover:bg-white/5";
      else if (s > 0.4) bgClass = "hover:bg-white/5";
      else bgClass = "bg-white/5 hover:bg-white/10";
      title = `Support Score: ${Math.round(s * 100)}%`;
    } else if (isFlagged) {
      bgClass = "bg-white/10";
      title = "Potentially unverified statement";
    }

    return (
      <span
        key={key}
        className={`transition-colors rounded-2 px-0.5 cursor-help ${bgClass}`}
        title={title}
      >
        {sentence}{" "}
      </span>
    );
  };

  const renderAnswer = () => {
    if (!cleanAnswer) return null;

    // Split into paragraphs first (preserve structure), then sentences within each
    const paragraphs = cleanAnswer.split(/\n\n+/);
    const hasAnalysis = flaggedSentences.length > 0 || supportScores.length > 0;

    return (
      <>
        {paragraphs.map((para, pIdx) => {
          // Handle single-newline breaks within a paragraph (numbered list items)
          const lines = para.split(/\n/);

          return (
            <div key={pIdx} style={{ marginBottom: '0.75em' }}>
              {lines.map((line, lIdx) => {
                const trimmedLine = line.trim();
                if (!trimmedLine) return null;

                if (!hasAnalysis) {
                  return <div key={lIdx}>{trimmedLine}</div>;
                }

                // Split line into sentences for highlighting
                const sentences = trimmedLine.split(/(?<=[.!?])\s+/);
                return (
                  <div key={lIdx}>
                    {sentences.map((s, sIdx) =>
                      renderSentence(s, `${pIdx}-${lIdx}-${sIdx}`)
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </>
    );
  };

  return (
    <div className="flex flex-col animate-fade-up">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[9px] text-muted7 uppercase tracking-[0.12em]">
            Answer
          </span>
          {verified ? (
            <span className="flex items-center gap-1 font-mono text-[9px] text-white">
              <ShieldCheck className="w-[10px] h-[10px]" /> verified
            </span>
          ) : (
            <span className="flex items-center gap-1 font-mono text-[9px] text-muted11">
              <AlertTriangle className="w-[10px] h-[10px]" /> unverified
            </span>
          )}
        </div>

        {confidence !== null && !isStreaming && (
          <div className="flex items-center gap-2 px-2 py-0.5 rounded-4 bg-raised border border-border">
            <span className="font-mono text-[9px] text-muted7 uppercase">Confidence</span>
            <span className={`font-mono text-[10px] font-bold ${confidence > 70 ? 'text-white' : confidence > 40 ? 'text-muted11' : 'text-muted7'}`}>
              {confidence}%
            </span>
          </div>
        )}
      </div>

      {!verified && !isStreaming && <HallucinationWarning />}

      <div className="answer-text leading-[1.8] text-[15px]" style={{ whiteSpace: 'pre-line' }}>
        {renderAnswer()}
      </div>

      {!isStreaming && (
        <div className="mt-8 flex items-center justify-between border-t border-border pt-4">
          <div className="flex items-center gap-4">
            <div className="font-mono text-[11px] text-muted7">
              {latency > 0 ? `${latency.toFixed(1)}s` : 'Real-time'} &nbsp;·&nbsp; LOCALLENS-LOCAL-01
            </div>
            {supportScores.length > 0 && (
              <div className="group relative flex items-center gap-1 cursor-help">
                <Info className="w-3 h-3 text-muted7" />
                <span className="font-mono text-[9px] text-muted7 uppercase border-b border-muted7/30 border-dotted">Analysis Active</span>
                <div className="absolute bottom-full left-0 mb-2 w-48 p-2 bg-surface border border-border rounded-8 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-[10px] text-muted11 leading-normal">
                  Sentences are cross-referenced with your documents. Hover over text to see support levels.
                </div>
              </div>
            )}
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-muted9 hover:text-muted11 transition-colors focus:outline-none"
          >
            {copied
              ? <Check className="w-[13px] h-[13px] text-white" />
              : <Copy className="w-[13px] h-[13px]" />
            }
            <span className="text-[12px]">{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default AnswerPanel;
