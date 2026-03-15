import React, { useState, useEffect } from 'react';
import { getDocuments, ingestFiles, getIngestionStatus } from '../api/client';
import type { Document, IngestionStatus } from '../types';
import Sidebar from '../components/layout/Sidebar';
import DropZone from '../components/ingest/DropZone';
import FileQueue from '../components/ingest/FileQueue';
import IngestionProgress from '../components/ingest/IngestionProgress';
import LogPanel from '../components/ingest/LogPanel';
import Button from '../components/shared/Button';

const IngestPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [queuedFiles, setQueuedFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<IngestionStatus | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    let interval: number;
    if (jobId && isIngesting) {
      interval = window.setInterval(async () => {
        const currentStatus = await getIngestionStatus(jobId);
        if (currentStatus) {
          setStatus(currentStatus);
          if (currentStatus.stage === 'done' || currentStatus.stage === 'error') {
            setIsIngesting(false);
            setJobId(null);
            fetchDocuments();
          }
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [jobId, isIngesting]);

  const fetchDocuments = async () => {
    setLoading(true);
    const docs = await getDocuments();
    setDocuments(docs);
    setLoading(false);
  };

  const handleFilesSelected = (files: File[]) => {
    setQueuedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index: number) => {
    setQueuedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const startIngestion = async () => {
    if (queuedFiles.length === 0) return;
    
    setIsIngesting(true);
    const result = await ingestFiles(queuedFiles);
    if (result) {
      setJobId(result.job_id);
      setQueuedFiles([]);
    } else {
      setIsIngesting(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden pt-[48px]">
      <Sidebar documents={documents} loading={loading} />
      
      <main className="flex-1 overflow-y-auto p-8 max-w-[900px]">
        <div className="mb-8">
          <h1 className="font-inter font-medium text-[22px] text-white">Ingest Documents</h1>
          <p className="font-inter font-normal text-[13px] text-muted7 mt-1">
            Upload and index your local files for semantic search and private analysis.
          </p>
        </div>

        {!isIngesting ? (
          <>
            <DropZone onFilesSelected={handleFilesSelected} />
            <FileQueue files={queuedFiles} onRemove={removeFile} />
            {queuedFiles.length > 0 && (
              <Button 
                variant="primary" 
                className="w-full mt-4 h-[38px]"
                onClick={startIngestion}
              >
                Start Ingestion
              </Button>
            )}
          </>
        ) : (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <IngestionProgress 
              filename={status?.filename || queuedFiles[0]?.name || 'document'} 
              currentPage={status?.current_page || 0}
              totalPages={status?.total_pages || 0}
              stage={status?.stage || 'Starting...'}
            />
            <LogPanel logs={status?.log_lines || []} />
          </div>
        )}
      </main>
    </div>
  );
};

export default IngestPage;
