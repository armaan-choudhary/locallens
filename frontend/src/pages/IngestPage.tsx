import React, { useState, useEffect } from 'react';
import { ingestFiles, getIngestionStatus } from '../api/client';
import type { IngestionStatus } from '../types';
import { useAppLayout } from '../components/layout/AppLayout';
import DropZone from '../components/ingest/DropZone';
import FileQueue from '../components/ingest/FileQueue';
import IngestionProgress from '../components/ingest/IngestionProgress';
import LogPanel from '../components/ingest/LogPanel';

const IngestPage: React.FC = () => {
  const { fetchDocs } = useAppLayout();
  
  const [queuedFiles, setQueuedFiles] = useState<File[]>([]);
  const [jobId, setJobId]           = useState<string | null>(null);
  const [status, setStatus]         = useState<IngestionStatus | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);

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
          // Refresh the global document list once finished
          fetchDocs();
        }
      }
    }, 1000);
    return () => clearInterval(id);
  }, [jobId, isIngesting, fetchDocs]);

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
    <main className="flex-1 overflow-y-auto px-10 py-9 max-w-[860px]">
      <div className="mb-7">
        <h1 className="text-[22px] font-semibold text-textPrimary tracking-[-0.01em]">
          Ingest Documents
        </h1>
        <p className="text-[13px] text-textSecondary mt-1 leading-relaxed">
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
                w-full mt-5 h-[42px] rounded-10 bg-accent hover:bg-accentLight
                text-[13px] font-medium text-[#F0E8EF]
                shadow-glow
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
        <div className="mt-6 p-4 rounded-10 border border-border bg-cardHi animate-fade-in shadow-sm">
          <div className="text-[13px] font-medium text-textPrimary mb-1">
            ✓ Ingestion complete
          </div>
          <div className="font-mono text-[11px] text-textMuted">
            {status.log_lines[status.log_lines.length - 1] || ''}
          </div>
        </div>
      )}
    </main>
  );
};

export default IngestPage;
