import React, { useState, useEffect, useRef } from 'react';
import { getDocuments, queryDocs } from '../api/client';
import type { Document, QueryResult } from '../types';
import Sidebar from '../components/layout/Sidebar';
import SearchBar from '../components/query/SearchBar';
import AnswerPanel from '../components/query/AnswerPanel';
import CitationPanel from '../components/query/CitationPanel';

// ── Staged progress bar ──────────────────────────────────────────────────────
// Advances through 3 pipeline stages automatically; never reaches 100% until
// the parent signals completion (component unmounts).
const STAGES = [
  { label: 'Retrieving chunks…',     target: 28, duration: 1800 },
  { label: 'Generating answer…',     target: 72, duration: 6000 },
  { label: 'Verifying citations…',   target: 92, duration: 2400 },
];

interface ProgressBarProps { query: string; }

const ProgressBar: React.FC<ProgressBarProps> = ({ query }) => {
  const [pct, setPct]     = useState(0);
  const [stage, setStage] = useState(0);
  const raf               = useRef<number>(0);
  const start             = useRef<number>(0);
  const prevPct           = useRef<number>(0);

  useEffect(() => {

    const runStage = (idx: number, from: number) => {
      if (idx >= STAGES.length) return;
      const { target, duration } = STAGES[idx];
      setStage(idx);
      start.current = performance.now();
      prevPct.current = from;

      const tick = (now: number) => {
        const elapsed = now - start.current;
        const t       = Math.min(elapsed / duration, 1);
        // ease-out quad
        const eased   = 1 - (1 - t) * (1 - t);
        const next    = prevPct.current + (target - prevPct.current) * eased;
        setPct(next);
        if (t < 1) {
          raf.current = requestAnimationFrame(tick);
        } else {
          runStage(idx + 1, target);
        }
      };
      raf.current = requestAnimationFrame(tick);
    };

    runStage(0, 0);
    return () => cancelAnimationFrame(raf.current);
  }, []);

  const label = STAGES[Math.min(stage, STAGES.length - 1)].label;

  return (
    <div className="w-full max-w-[480px] flex flex-col gap-4">
      {/* Query echo */}
      {query && (
        <div className="font-mono text-[11px] text-muted5 text-center truncate px-2">
          &ldquo;{query}&rdquo;
        </div>
      )}

      {/* Track */}
      <div className="w-full h-[2px] bg-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            background: 'linear-gradient(90deg, #7c6af7, #a78bfa)',
            transition: 'width 60ms linear',
          }}
        />
      </div>

      {/* Stage label + pct */}
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] text-muted6">{label}</span>
        <span className="font-mono text-[11px] text-muted4">{Math.round(pct)}%</span>
      </div>
    </div>
  );
};

const SUGGESTIONS = [
  'What are the key findings across all documents?',
  'Summarise the compliance requirements',
  'Find all mentions of data encryption',
];

const QueryPage: React.FC = () => {
  const [documents, setDocuments]     = useState<Document[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [searching, setSearching]     = useState(false);
  const [result, setResult]           = useState<QueryResult | null>(null);
  const [lastQuery, setLastQuery]     = useState('');

  useEffect(() => { fetchDocs(); }, []);

  const fetchDocs = async () => {
    const docs = await getDocuments();
    setDocuments(docs);
    setDocsLoading(false);
  };

  const handleSearch = async (query: string) => {
    setSearching(true);
    setLastQuery(query);
    const r = await queryDocs(query);
    if (r) setResult(r);
    setSearching(false);
  };

  const totalChunks = documents.reduce((a, d) => a + d.chunk_count, 0);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar documents={documents} loading={docsLoading} onRefresh={fetchDocs} />

      <main className="flex-1 overflow-y-auto px-10 py-9 flex flex-col max-w-[1280px]">
        {/* Full-width search bar */}
        <SearchBar
          onSearch={handleSearch}
          loading={searching}
          docCount={documents.length}
          chunkCount={totalChunks}
        />

        {/* Empty / loading / result states */}
        {!result && !searching && (
          <div className="flex flex-col gap-[10px] animate-fade-in">
            <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em] mb-1">
              Suggestions
            </div>
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSearch(s)}
                className="flex items-start gap-3 text-left group focus:outline-none"
              >
                <span className="text-muted4 text-[13px] mt-[2px] shrink-0 group-hover:text-accent transition-colors">→</span>
                <span className="text-[13px] text-muted6 group-hover:text-muted11 transition-colors leading-snug">
                  {s}
                </span>
              </button>
            ))}
          </div>
        )}

        {searching && !result && (
          <div className="flex-1 flex flex-col items-center justify-center gap-6 animate-fade-in select-none">
            <ProgressBar query={lastQuery} />
          </div>
        )}

        {result && (
          <div className="flex gap-8 mt-2">
            {/* Answer — left 58% */}
            <div className="w-[58%] min-w-0">
              <AnswerPanel
                answer={result.answer}
                verified={result.verified}
                latency={result.latency_seconds}
                flaggedSentences={result.flagged_sentences}
              />
            </div>

            {/* Citations — right 42%, with divider */}
            <div className="w-[42%] min-w-0 border-l border-border pl-8">
              <CitationPanel citations={result.citations} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default QueryPage;
