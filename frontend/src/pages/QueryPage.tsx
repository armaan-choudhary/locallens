import React, { useState, useEffect, useRef } from 'react';
import { 
  queryDocsStream, getSessionMessages, createSession, searchByImage,
  addDocsToSessionBulk,
} from '../api/client';
import type { ChatMessage, CitationCard as CitationType, SupportScore } from '../types';
import { useAppLayout } from '../components/layout/AppLayout';
import AnswerPanel from '../components/query/AnswerPanel';
import CitationModal from '../components/query/CitationModal';
import SearchBar from '../components/query/SearchBar';
import { MessageSquare, BookOpen } from 'lucide-react';

const STAGES = [
  { label: 'Retrieving chunks…',     target: 28, duration: 1800 },
  { label: 'Generating answer…',     target: 72, duration: 6000 },
  { label: 'Verifying citations…',   target: 92, duration: 2400 },
];

const QueryProgressBar: React.FC = () => {
  const [pct, setPct] = useState(0);
  const [stage, setStage] = useState(0);
  const raf = useRef<number>(0);
  const start = useRef<number>(performance.now());
  const prevPct = useRef<number>(0);

  useEffect(() => {
    const runStage = (idx: number, from: number) => {
      if (idx >= STAGES.length) return;
      const { target, duration } = STAGES[idx];
      setStage(idx);
      start.current = performance.now();
      prevPct.current = from;

      const tick = (now: number) => {
        const elapsed = now - start.current;
        const t = Math.min(elapsed / duration, 1);
        const eased = 1 - (1 - t) * (1 - t);
        const next = prevPct.current + (target - prevPct.current) * eased;
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

  return (
    <div className="w-full max-w-[400px] flex flex-col gap-3 py-4">
      <div className="w-full h-[2px] bg-border rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-accent transition-all duration-300" style={{ width: `${pct}%` }} />
      </div>
      <div className="flex items-center justify-between font-mono text-[10px] text-muted5">
        <span>{STAGES[Math.min(stage, STAGES.length - 1)].label}</span>
        <span>{Math.round(pct)}%</span>
      </div>
    </div>
  );
};

const QueryPage: React.FC = () => {
  const {
    documents,
    currentSessionId, setCurrentSessionId,
    sessionDocIds, handleToggleDoc,
    fetchSessions,
  } = useAppLayout();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [searching, setSearching] = useState(false);

  /** Response streaming state */
  const [streamingAnswer, setStreamingAnswer] = useState<string>('');
  const [streamingFlagged, setStreamingFlagged] = useState<string[]>([]);
  const [streamingScores, setStreamingScores] = useState<SupportScore[]>([]);
  const [streamingVerified, setStreamingVerified] = useState<boolean>(true);

  /** UI interaction state */
  const [modalOpen, setModalOpen] = useState(false);
  const [activeCitations, setActiveCitations] = useState<CitationType[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const fetchMessages = async (sid: string) => {
    const msgs = await getSessionMessages(sid);
    setMessages(msgs);
  };

  // Load messages when session changes
  useEffect(() => {
    if (currentSessionId) {
      fetchMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, searching, streamingAnswer]);

  /** Orchestrate streaming RAG query */
  const handleSearch = async (query: string) => {
    if (!query.trim()) return;

    let sid = currentSessionId;
    if (!sid) {
      const res = await createSession(query.slice(0, 30) + (query.length > 30 ? '...' : ''));
      if (res) {
        sid = res.session_id;
        setCurrentSessionId(sid);
        await fetchSessions();

        if (sessionDocIds.size > 0) {
          await addDocsToSessionBulk(sid, Array.from(sessionDocIds));
        }
      } else return;
    }

    const userMsg: ChatMessage = {
      message_id: 'temp-user-' + Date.now(),
      session_id: sid!,
      role: 'user',
      content: query,
      scoped_docs: Array.from(sessionDocIds),
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setSearching(true);

    setStreamingAnswer('');
    setStreamingFlagged([]);
    setStreamingScores([]);
    setStreamingVerified(true);

    await queryDocsStream(query, sid, (data) => {
      if (data.answer) setStreamingAnswer(data.answer);
      if (data.flagged_sentences) setStreamingFlagged(data.flagged_sentences);
      if (data.support_scores) setStreamingScores(data.support_scores);
      if (data.verified !== undefined) setStreamingVerified(data.verified);
      if (data.done) {
        setSearching(false);
        setStreamingAnswer('');
        if (sid) fetchMessages(sid);
      }
    });
  };

  /** Process image-based semantic retrieval */
  const handleImageSearch = async (file: File) => {
    let sid = currentSessionId;
    if (!sid) {
      const res = await createSession("Image Search Result");
      if (res) {
        sid = res.session_id;
        setCurrentSessionId(sid);
        await fetchSessions();
      } else return;
    }

    const userMsg: ChatMessage = {
      message_id: 'temp-user-' + Date.now(),
      session_id: sid!,
      role: 'user',
      content: "[Image Uploaded for Search]",
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setSearching(true);

    const res = await searchByImage(file, sid);
    setSearching(false);
    if (res && sid) fetchMessages(sid);
  };

  const openCitations = (citations: CitationType[]) => {
    setActiveCitations(citations);
    setModalOpen(true);
  };

  const totalChunks = documents.reduce((a, d) => a + d.chunk_count, 0);

  return (
    <main className="flex-1 flex flex-col relative min-w-0">
      <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-8">
        <div className="max-w-[720px] mx-auto flex flex-col gap-10">
          {messages.length === 0 && !searching && (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center animate-fade-in">
              <div className="w-12 h-12 rounded-12 bg-raised flex items-center justify-center mb-6">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-white text-[18px] font-medium mb-2">How can I help you today?</h2>
              <p className="text-muted4 text-[13px] max-w-[400px]">
                Ask questions about your {documents.length} indexed documents ({totalChunks.toLocaleString()} chunks).
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.message_id} className="flex flex-col gap-4 animate-fade-in">
              {msg.role === 'user' ? (
                <div className="flex flex-col items-end gap-2">
                  <div className="bg-raised px-4 py-2.5 rounded-16 rounded-tr-4 max-w-[85%] text-[14px] text-muted11 leading-relaxed border border-border/50">
                    {msg.content}
                  </div>
                  {msg.scoped_docs && msg.scoped_docs.length > 0 && (
                    <div className="flex flex-wrap justify-end gap-1.5 max-w-[85%]">
                      {msg.scoped_docs.map(docId => {
                        const doc = documents.find(d => d.doc_id === docId);
                        if (!doc) return null;
                        return (
                          <div key={docId} className="px-2 py-0.5 rounded-4 bg-white/5 border border-white/5 text-[10px] font-mono text-muted5">
                            @{doc.filename}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  <div className="flex-1 min-w-0">
                    <AnswerPanel
                      answer={msg.content}
                      verified={msg.verified ?? true}
                      latency={0}
                      flaggedSentences={msg.flagged_sentences ?? []}
                      supportScores={msg.support_scores ?? []}
                    />
                  </div>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => openCitations(msg.citations!)}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-8 bg-raised/30 border border-border hover:bg-raised transition-all text-muted9 hover:text-white group"
                      >
                        <BookOpen className="w-[12px] h-[12px] group-hover:text-white" />
                        <span className="text-[11px] font-medium font-mono uppercase tracking-wider">
                          View {msg.citations.length} Sources
                        </span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {(searching || streamingAnswer) && (
            <div className="flex flex-col gap-4 animate-fade-in">
              <div className="flex-1 min-w-0">
                <AnswerPanel
                  answer={streamingAnswer}
                  verified={streamingVerified}
                  latency={0}
                  flaggedSentences={streamingFlagged}
                  supportScores={streamingScores}
                  isStreaming={searching && !streamingAnswer}
                />
              </div>
              {searching && !streamingAnswer && (
                <div className="flex flex-col items-center py-4">
                  <QueryProgressBar />
                </div>
              )}
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="border-t border-border bg-surface/50 backdrop-blur-xl px-6 py-6 pb-8">
        <div className="max-w-[720px] mx-auto relative">
          <SearchBar
            onSearch={handleSearch}
            onImageSearch={handleImageSearch}
            loading={searching}
            docCount={documents.length}
            chunkCount={totalChunks}
            documents={documents}
            sessionDocIds={sessionDocIds}
            onToggleDoc={handleToggleDoc}
          />
        </div>
        <div className="mt-4 flex justify-center gap-6">
          <div className="font-mono text-[10px] text-muted7 uppercase tracking-widest flex items-center gap-1.5 grayscale opacity-50">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            {documents.length} Files Available
          </div>
          <div className="font-mono text-[10px] text-muted7 uppercase tracking-widest flex items-center gap-1.5 grayscale opacity-50">
            <span className="w-1.5 h-1.5 rounded-full bg-white/40" />
            Local Mode
          </div>
        </div>
      </div>

      <CitationModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        citations={activeCitations}
      />
    </main>
  );
};

export default QueryPage;
