import React, { useState, useEffect, useRef } from 'react';
import { getDocuments, queryDocs, getSessions, getSessionMessages, createSession } from '../api/client';
import type { Document, ChatSession, ChatMessage, CitationCard as CitationType } from '../types';
import Sidebar from '../components/layout/Sidebar';
import AnswerPanel from '../components/query/AnswerPanel';
import CitationModal from '../components/query/CitationModal';
import { MessageSquare, Send, Loader2, BookOpen } from 'lucide-react';

const STAGES = [
  { label: 'Retrieving chunks…',     target: 28, duration: 1800 },
  { label: 'Generating answer…',     target: 72, duration: 6000 },
  { label: 'Verifying citations…',   target: 92, duration: 2400 },
];

const ProgressBar: React.FC = () => {
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
  const [documents, setDocuments] = useState<Document[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const [docsLoading, setDocsLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [inputQuery, setInputQuery] = useState('');

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [activeCitations, setActiveCitations] = useState<CitationType[]>([]);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchDocs();
    fetchSessions();
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      fetchMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, searching]);

  const fetchDocs = async () => {
    const docs = await getDocuments();
    setDocuments(docs);
    setDocsLoading(false);
  };

  const fetchSessions = async () => {
    const sess = await getSessions();
    setSessions(sess);
  };

  const fetchMessages = async (sid: string) => {
    const msgs = await getSessionMessages(sid);
    setMessages(msgs);
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;
    
    let sid = currentSessionId;
    if (!sid) {
      const res = await createSession(query.slice(0, 30) + (query.length > 30 ? '...' : ''));
      if (res) {
        sid = res.session_id;
        setCurrentSessionId(sid);
        await fetchSessions();
      } else return;
    }

    const userMsg: ChatMessage = {
      message_id: 'temp-user-' + Date.now(),
      session_id: sid,
      role: 'user',
      content: query,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setSearching(true);
    setInputQuery('');

    const r = await queryDocs(query, sid);
    if (r) {
      await fetchMessages(sid);
    }
    setSearching(false);
  };

  const openCitations = (citations: CitationType[]) => {
    setActiveCitations(citations);
    setModalOpen(true);
  };

  const totalChunks = documents.reduce((a, d) => a + d.chunk_count, 0);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar 
        documents={documents} 
        loading={docsLoading} 
        onRefreshDocs={fetchDocs}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onRefreshSessions={fetchSessions}
      />

      <main className="flex-1 flex flex-col relative min-w-0">
        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-8">
          <div className="max-w-[720px] mx-auto flex flex-col gap-10">
            {messages.length === 0 && !searching && (
              <div className="flex flex-col items-center justify-center h-[60vh] text-center animate-fade-in">
                <div className="w-12 h-12 rounded-12 bg-raised flex items-center justify-center mb-6">
                  <MessageSquare className="w-6 h-6 text-accent" />
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
                  <div className="flex justify-end">
                    <div className="bg-raised px-4 py-2.5 rounded-16 rounded-tr-4 max-w-[85%] text-[14px] text-muted11 leading-relaxed border border-border/50">
                      {msg.content}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-4">
                    <div className="flex-1 min-w-0">
                      <AnswerPanel
                        answer={msg.content}
                        verified={true}
                        latency={0}
                        flaggedSentences={[]}
                      />
                    </div>
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={() => openCitations(msg.citations!)}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-8 bg-raised/30 border border-border hover:bg-raised transition-all text-muted5 hover:text-white group"
                        >
                          <BookOpen className="w-[12px] h-[12px] group-hover:text-accent" />
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

            {searching && (
              <div className="flex flex-col gap-4 animate-fade-in">
                <div className="flex justify-end">
                  <div className="bg-raised px-4 py-2.5 rounded-16 rounded-tr-4 text-[14px] text-muted11">
                    {inputQuery || "Generating..."}
                  </div>
                </div>
                <div className="flex flex-col items-center py-4">
                  <ProgressBar />
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Persistent Input Bar */}
        <div className="border-t border-border bg-surface/50 backdrop-blur-xl px-6 py-6 pb-8">
          <div className="max-w-[720px] mx-auto relative">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch(inputQuery)}
              placeholder="Ask a follow-up or start a new quest..."
              className="w-full bg-raised/50 border border-border rounded-12 py-3.5 pl-4 pr-12 text-[14px] text-white placeholder:text-muted4 focus:outline-none focus:border-accent/40 focus:bg-raised/80 transition-all shadow-sm"
              disabled={searching}
            />
            <button
              onClick={() => handleSearch(inputQuery)}
              disabled={searching || !inputQuery.trim()}
              className={`
                absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-8 transition-all
                ${inputQuery.trim() ? 'bg-accent text-white shadow-lg' : 'text-muted4 grayscale'}
              `}
            >
              {searching ? (
                <Loader2 className="w-[18px] h-[18px] animate-spin" />
              ) : (
                <Send className="w-[18px] h-[18px]" />
              )}
            </button>
          </div>
          <div className="mt-4 flex justify-center gap-6">
            <div className="font-mono text-[10px] text-muted4 uppercase tracking-widest flex items-center gap-1.5 grayscale opacity-50">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              {documents.length} Docs Indexed
            </div>
            <div className="font-mono text-[10px] text-muted4 uppercase tracking-widest flex items-center gap-1.5 grayscale opacity-50">
              <span className="w-1.5 h-1.5 rounded-full bg-success" />
              Local Mode
            </div>
          </div>
        </div>
      </main>

      {/* Citation Modal */}
      <CitationModal 
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        citations={activeCitations}
      />
    </div>
  );
};

export default QueryPage;
