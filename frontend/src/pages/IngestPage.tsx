import React, { useState, useEffect } from 'react';
import { getDocuments, ingestFiles, getIngestionStatus } from '../api/client';
import type { Document, IngestionStatus } from '../types';
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

  useEffect(() => { fetchDocuments(); }, []);

  // Poll status
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

  const handleFilesSelected = (files: File[]) => {
    setQueuedFiles(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...files.filter(f => !names.has(f.name))];
    });
  };

  const removeFile = (index: number) => {
    setQueuedFiles(prev => prev.filter((_, i) => i !== index));
  };

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
      <Sidebar documents={documents} loading={docsLoading} onRefresh={fetchDocuments} />

      <main className="flex-1 overflow-y-auto px-10 py-9 max-w-[860px]">
        {/* Header */}
        <div className="mb-7">
          <h1 className="text-[22px] font-semibold text-white tracking-[-0.01em]">
            Ingest Documents
          </h1>
          <p className="text-[13px] text-muted7 mt-1 leading-relaxed">
            Drop individual PDFs or an entire folder. PyPDF2 extracts text;
            Tesseract handles image-only pages via OCR.
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
                  w-full mt-5 h-[42px] rounded-10 bg-accent hover:bg-accentLight
                  text-[13px] font-medium text-white
                  shadow-[0_0_24px_rgba(124,106,247,0.2)]
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

        {/* After-done summary reflow */}
        {!isIngesting && status?.stage === 'done' && (
          <div className="mt-6 p-4 rounded-10 border border-[rgba(52,211,153,0.2)] bg-[rgba(52,211,153,0.05)] animate-fade-in">
            <div className="text-[13px] font-medium text-success mb-1">
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
