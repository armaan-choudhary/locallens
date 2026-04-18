import React, { useCallback, useState, useRef } from 'react';
import { UploadCloud, FolderOpen, FileText } from 'lucide-react';

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
}

/**
 * Handles PDF and directory selection for ingestion.
 */
const DropZone: React.FC<DropZoneProps> = ({ onFilesSelected }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  /**
   * Processes dropped items, supporting both files and directory recursion.
   */
  const processItems = (items: DataTransferItemList) => {
    const files: File[] = [];
    const promises: Promise<void>[] = [];

    const traverseItem = (item: any): Promise<void> => {
      return new Promise((resolve) => {
        if (item.isFile) {
          item.file((f: File) => {
            if (f.name.toLowerCase().match(/\.(pdf|png|jpe?g)$/)) files.push(f);
            resolve();
          });
        } else if (item.isDirectory) {
          const reader = item.createReader();
          reader.readEntries(async (entries: any[]) => {
            await Promise.all(entries.map(traverseItem));
            resolve();
          });
        } else {
          resolve();
        }
      });
    };

    for (let i = 0; i < items.length; i++) {
      const entry = items[i].webkitGetAsEntry?.();
      if (entry) promises.push(traverseItem(entry));
    }

    Promise.all(promises).then(() => {
      if (files.length > 0) onFilesSelected(files);
    });
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      processItems(e.dataTransfer.items);
    } else if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files).filter(f =>
        f.name.toLowerCase().match(/\.(pdf|png|jpe?g)$/)
      );
      if (files.length > 0) onFilesSelected(files);
    }
  }, [onFilesSelected]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files).filter(f =>
        f.name.toLowerCase().match(/\.(pdf|png|jpe?g)$/)
      );
      if (files.length > 0) onFilesSelected(files);
      e.target.value = '';
    }
  }, [onFilesSelected]);

  return (
    <div
      className={`
        relative w-full rounded-12 border-1.5 transition-all duration-300
        flex flex-col items-center justify-center gap-6 py-16
        ${isDragOver
          ? 'border-accent bg-accentDim shadow-glow'
          : 'border-dashed border-border bg-card hover:border-accent hover:bg-cardHi'}
      `}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,application/pdf,image/png,image/jpeg"
        className="hidden"
        onChange={handleFileInput}
      />
      <input
        ref={folderInputRef}
        type="file"
        multiple
        className="hidden"
        // @ts-expect-error
        webkitdirectory=""
        directory=""
        onChange={handleFileInput}
      />

      <div className={`
        w-16 h-16 rounded-16 flex items-center justify-center transition-all duration-500
        ${isDragOver ? 'bg-accent text-[#F0E8EF] scale-110 shadow-glow' : 'bg-card border border-border text-textMuted'}
      `}>
        <UploadCloud className={`w-7 h-7 ${isDragOver ? 'animate-pulse' : ''}`} />
      </div>

      <div className="text-center">
        <div className="text-[15px] font-semibold text-textPrimary mb-2">
          Drop PDFs or Images here to ingest
        </div>
        <div className="text-[13px] text-textSecondary max-w-[320px] mx-auto leading-relaxed">
          LocalLens will recursively index all documents for semantic search.
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="px-4 py-2 rounded-8 bg-accent text-[#F0E8EF] text-[12px] font-bold hover:bg-accentLight shadow-glow transition-colors flex items-center gap-2"
        >
          <FileText className="w-3.5 h-3.5" />
          Select Files
        </button>
        <button
          onClick={() => folderInputRef.current?.click()}
          className="px-4 py-2 rounded-8 bg-card border border-border text-textSecondary text-[12px] font-bold shadow-sm hover:text-textPrimary hover:bg-cardHi transition-colors flex items-center gap-2"
        >
          <FolderOpen className="w-3.5 h-3.5" />
          Select Folder
        </button>
      </div>

      <div className="font-mono text-[9px] text-textMuted uppercase tracking-[0.2em] mt-2">
        PDF & Image Format · OCR Enabled · Local Privacy
      </div>
    </div>
  );
};

export default DropZone;
