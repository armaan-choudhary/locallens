import React from 'react';
import { CheckCircle } from 'lucide-react';
import ProgressBar from '../ui/ProgressBar';

interface IngestionProgressProps {
  filename: string;
  currentPage: number;
  totalPages: number;
  stage: string;
}

const stageLabel: Record<string, string> = {
  extracting: 'Extracting text with PyPDF2…',
  ocr:        'Running Tesseract OCR on image pages…',
  embedding:  'Generating embeddings…',
  indexing:   'Writing vectors to Milvus…',
  done:       'Complete',
  error:      'Error — see log below',
};

/**
 * Component displaying real-time progress of the document ingestion pipeline.
 */
const IngestionProgress: React.FC<IngestionProgressProps> = ({
  filename,
  currentPage,
  totalPages,
  stage,
}) => {
  const isDone  = stage === 'done';
  const isError = stage === 'error';
  const pct     = totalPages > 0 ? Math.min((currentPage / totalPages) * 100, 100) : 0;

  return (
    <div className="w-full rounded-10 bg-surface border border-border p-5 mb-4 shadow-xl">
      <div className="flex items-center justify-between mb-5">
        <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.2em]">
          Ingestion Pipeline
        </div>
        {isDone && (
          <div className="flex items-center gap-1.5 text-success text-[12px] font-medium animate-fade-in">
            <CheckCircle className="w-[14px] h-[14px]" />
            All tasks complete
          </div>
        )}
      </div>

      <div className="text-[14px] font-semibold text-white truncate mb-6" title={filename}>
        {filename}
      </div>

      <div className="mb-6">
        <ProgressBar 
          progress={isDone ? 100 : pct}
          isIndeterminate={!isDone && !isError && totalPages === 0}
          color={isError ? 'error' : isDone ? 'success' : 'accent'}
          size="md"
          label={stageLabel[stage] || stage}
          showPercentage={totalPages > 0}
        />
      </div>

      {totalPages > 0 && !isDone && (
        <div className="flex justify-end">
          <div className="px-2 py-0.5 rounded-4 bg-raised border border-border font-mono text-[10px] text-muted5">
            PAGE {currentPage} OF {totalPages}
          </div>
        </div>
      )}
    </div>
  );
};

export default IngestionProgress;
