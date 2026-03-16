import React from 'react';
import { X, FileText } from 'lucide-react';

interface FileQueueProps {
  files: File[];
  onRemove: (index: number) => void;
}

/**
 * Formats file size into human-readable strings.
 */
const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * Displays a list of files queued for ingestion with removal options.
 */
const FileQueue: React.FC<FileQueueProps> = ({ files, onRemove }) => {
  if (files.length === 0) return null;

  return (
    <div className="mt-4 flex flex-col gap-[6px]">
      <div className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em] mb-1">
        Queue — {files.length} file{files.length > 1 ? 's' : ''}
      </div>
      {files.map((file, i) => (
        <div
          key={i}
          className="flex items-center gap-3 bg-surface border border-border rounded-8 px-3 py-[9px] group"
        >
          <FileText className="w-[14px] h-[14px] text-muted5 shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-[13px] text-muted11 truncate font-medium">{file.name}</div>
            <div className="font-mono text-[10px] text-muted4 mt-[1px]">{formatBytes(file.size)}</div>
          </div>
          <button
            onClick={() => onRemove(i)}
            className="text-muted4 hover:text-error opacity-0 group-hover:opacity-100 transition-all focus:outline-none p-1"
            title="Remove"
          >
            <X className="w-[13px] h-[13px]" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default FileQueue;
