import React from 'react';
import { X } from 'lucide-react';

interface FileQueueProps {
  files: File[];
  onRemove: (index: number) => void;
}

const FileQueue: React.FC<FileQueueProps> = ({ files, onRemove }) => {
  if (files.length === 0) return null;

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="mt-8">
      <div className="font-mono text-[11px] text-muted4 uppercase tracking-[0.08em] mb-2">
        Ingestion Queue
      </div>
      <div className="flex flex-col">
        {files.map((file, i) => (
          <div key={i} className="flex items-center py-2.5 border-b border-border">
            <div className="flex-1 text-muted10 text-[13px] truncate pr-4">
              {file.name}
            </div>
            <div className="font-mono text-[12px] text-muted5 mr-3 shrink-0">
              {formatSize(file.size)}
            </div>
            <button 
              onClick={(e) => { e.stopPropagation(); onRemove(i); }}
              className="text-muted4 hover:text-muted10 transition-colors focus:outline-none"
            >
              <X className="w-4.5 h-4.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileQueue;
