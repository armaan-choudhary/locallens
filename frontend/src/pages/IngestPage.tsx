import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDocuments, ingestFiles, getIngestionStatus, getSessions } from '../api/client';
import type { Document, IngestionStatus, ChatSession } from '../types';
import Sidebar from '../components/layout/Sidebar';
import DropZone from '../components/ingest/DropZone';
import FileQueue from '../components/ingest/FileQueue';
import IngestionProgress from '../components/ingest/IngestionProgress';
import LogPanel from '../components/ingest/LogPanel';

const IngestPage: React.FC = () => {
  const [documents, setDocuments]   = useState<Document[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [queuedFiles, setQueuedFiles] = useState<File[]>([]);
  const [jobId, setJobId]           = useState<string | null>(null);
  const [status, setStatus]         = useState<IngestionStatus | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [sessions, setSessions]       = useState<ChatSession[]>([]);

  const navigate = useNavigate();

  useEffect(() => { 
    fetchDocuments(); 
    fetchSessions();
  }, []);

  /** Monitor ingestion status via polling */
  useEffect(() => {
    if (!jobId || !isIngesting) return;
    const id = window.setInterval(async () => {
      const s = await getIngestionStatus(jobId);
      if (s) {
        setStatus(s);
        if (s.stage === 'done' || s.stage === 'error') {
          setIsIngesting(false);
          setJobId(null);
          fetchDocuments();
        }
      }
    }, 1000);
    return () => clearInterval(id);
  }, [jobId, isIngesting]);

  const fetchDocuments = async () => {
    setDocsLoading(true);
    const docs = await getDocuments();
    setDocuments(docs);
    setDocsLoading(false);
  };

  const fetchSessions = async () => {
    const sess = await getSessions();
    setSessions(sess);
  };

  const handleSelectSession = (id: string | undefined) => {
    if (id) {
      localStorage.setItem('currentSessionId', id);
    } else {
      localStorage.removeItem('currentSessionId');
    }
    navigate('/query');
  };

  /** Append unique files to selection queue */
  const handleFilesSelected = (files: File[]) => {
    setQueuedFiles(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...files.filter(f => !names.has(f.name))];
    });
  };

  const removeFile = (index: number) => {
    setQueuedFiles(prev => prev.filter((_, i) => i !== index));
  };

  /** Trigger document processing pipeline */
  const startIngestion = async () => {
    if (queuedFiles.length === 0) return;
    setIsIngesting(true);
    setStatus(null);
    const result = await ingestFiles(queuedFiles);
    if (result) {
      setJobId(result.job_id);
      setQueuedFiles([]);
    } else {
      setIsIngesting(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar 
        documents={documents} 
        loading={docsLoading} 
        onRefreshDocs={fetchDocuments}
        sessions={sessions}
        onRefreshSessions={fetchSessions}
        onSelectSession={handleSelectSession}
        sessionDocIds={new Set()}
        onToggleDoc={async () => {}}
        onBulkChange={() => {}}
      />

      <main className="flex-1 overflow-y-auto px-10 py-9 max-w-[860px]">
        <div className="mb-7">
          <h1 className="text-[22px] font-semibold text-white tracking-[-0.01em]">
            Ingest Documents
          </h1>
          <p className="text-[13px] text-muted7 mt-1 leading-relaxed">
            Extract text from PDFs and images via OCR for local indexing.
          </p>
        </div>

        {!isIngesting ? (
          <div className="animate-fade-up">
            <DropZone onFilesSelected={handleFilesSelected} />
            <FileQueue files={queuedFiles} onRemove={removeFile} />

            {queuedFiles.length > 0 && (
              <button
                onClick={startIngestion}
                className="
                  w-full mt-5 h-[42px] rounded-10 bg-white hover:bg-muted11
                  text-[13px] font-medium text-black
                  shadow-[0_0_24px_rgba(255,255,255,0.05)]
                  transition-all duration-150 focus:outline-none
                "
              >
                ▶&nbsp; Start Ingestion — {queuedFiles.length} file{queuedFiles.length > 1 ? 's' : ''}
              </button>
            )}
          </div>
        ) : (
          <div className="animate-fade-up">
            <IngestionProgress
              filename={status?.filename || queuedFiles[0]?.name || 'document'}
              currentPage={status?.current_page || 0}
              totalPages={status?.total_pages || 0}
              stage={status?.stage || 'extracting'}
            />
            <LogPanel logs={status?.log_lines || []} />
          </div>
        )}

        {!isIngesting && status?.stage === 'done' && (
          <div className="mt-6 p-4 rounded-10 border border-white/10 bg-white/5 animate-fade-in">
            <div className="text-[13px] font-medium text-white mb-1">
              ✓ Ingestion complete
            </div>
            <div className="font-mono text-[11px] text-muted6">
              {status.log_lines[status.log_lines.length - 1] || ''}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default IngestPage;
