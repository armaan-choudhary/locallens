import React from 'react';
import { CheckCircle } from 'lucide-react';

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
    <div className="w-full rounded-10 bg-surface border border-border p-5 mb-4">
      {/* Header row */}
      <div className="flex items-center justify-between mb-4">
        <div className="font-mono text-[11px] text-muted5 uppercase tracking-[0.1em]">
          Pipeline Status
        </div>
        {isDone && (
          <div className="flex items-center gap-1.5 text-success text-[12px] font-medium">
            <CheckCircle className="w-[13px] h-[13px]" />
            Done
          </div>
        )}
      </div>

      {/* Filename */}
      <div className="text-[13px] font-medium text-muted11 truncate mb-4" title={filename}>
        {filename}
      </div>

      {/* Progress bar */}
      <div className="progress-track mb-3">
        {isDone ? (
          <div className="progress-fill" style={{ width: '100%' }} />
        ) : isError ? (
          <div className="h-full bg-error rounded-[1px]" style={{ width: `${pct || 30}%` }} />
        ) : totalPages > 0 ? (
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        ) : (
          <div className="progress-fill progress-fill-indeterminate" />
        )}
      </div>

      {/* Stage label + page count */}
      <div className="flex items-center justify-between">
        <div className={`font-mono text-[11px] ${isError ? 'text-error' : 'text-muted6'}`}>
          {stageLabel[stage] || stage}
        </div>
        {totalPages > 0 && !isDone && (
          <div className="font-mono text-[11px] text-muted4">
            pg {currentPage} / {totalPages}
          </div>
        )}
      </div>
    </div>
  );
};

export default IngestionProgress;
