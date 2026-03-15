import React, { useCallback, useState } from 'react';
import { UploadCloud, FolderOpen } from 'lucide-react';

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
}

const DropZone: React.FC<DropZoneProps> = ({ onFilesSelected }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const processItems = (items: DataTransferItemList) => {
    const files: File[] = [];
    const promises: Promise<void>[] = [];

    const traverseItem = (item: FileSystemEntry): Promise<void> => {
      return new Promise((resolve) => {
        if (item.isFile) {
          (item as FileSystemFileEntry).file((f) => {
            if (f.name.toLowerCase().endsWith('.pdf')) files.push(f);
            resolve();
          });
        } else if (item.isDirectory) {
          const reader = (item as FileSystemDirectoryEntry).createReader();
          reader.readEntries(async (entries) => {
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
        f.name.toLowerCase().endsWith('.pdf')
      );
      if (files.length > 0) onFilesSelected(files);
    }
  }, [onFilesSelected]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files).filter(f =>
        f.name.toLowerCase().endsWith('.pdf')
      );
      if (files.length > 0) onFilesSelected(files);
      e.target.value = '';
    }
  }, [onFilesSelected]);

  return (
    <div
      className={`
        relative w-full rounded-10 border-1.5 transition-all duration-200 cursor-pointer
        flex flex-col items-center justify-center gap-3 py-12
        ${isDragOver
          ? 'drop-zone-active border-solid border-accent bg-accentDim'
          : 'border-dashed border-border bg-surface hover:border-muted4 hover:bg-raised'}
      `}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-input')?.click()}
    >
      <input
        id="file-input"
        type="file"
        multiple
        accept=".pdf"
        className="hidden"
        onChange={handleFileInput}
        // @ts-expect-error – webkitdirectory is non-standard
        webkitdirectory=""
        directory=""
      />

      <div className={`
        w-12 h-12 rounded-10 flex items-center justify-center transition-colors
        ${isDragOver ? 'bg-accent/20' : 'bg-raised border border-border'}
      `}>
        <UploadCloud className={`w-5 h-5 ${isDragOver ? 'text-accent' : 'text-muted6'}`} />
      </div>

      <div className="text-center">
        <div className="text-[14px] font-medium text-muted11 mb-1">
          Drop PDFs or a folder here
        </div>
        <div className="text-[12px] text-muted5">
          or <span className="text-muted9 underline underline-offset-2">browse files</span>
        </div>
      </div>

      <div className="flex items-center gap-4 mt-1">
        <div className="flex items-center gap-[6px] text-muted4 text-[11px] font-mono">
          <FolderOpen className="w-[12px] h-[12px]" />
          folder import supported
        </div>
        <span className="text-muted3 text-[11px]">·</span>
        <div className="text-muted4 text-[11px] font-mono">PDF only · up to 100 MB</div>
      </div>
    </div>
  );
};

export default DropZone;
