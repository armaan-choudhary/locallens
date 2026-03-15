import React, { useCallback, useState } from 'react';
import { UploadCloud } from 'lucide-react';

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
}

const DropZone: React.FC<DropZoneProps> = ({ onFilesSelected }) => {
  const [isDragOver, setIsDragOver] = useState(false);

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
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
      if (files.length > 0) onFilesSelected(files);
    }
  }, [onFilesSelected]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(Array.from(e.target.files));
    }
  }, [onFilesSelected]);

  return (
    <div
      className={`
        relative w-full h-[200px] rounded-10 border-1.5 transition-all
        flex flex-col items-center justify-center gap-[10px] cursor-pointer
        ${isDragOver 
          ? 'border-solid border-muted7 bg-raised' 
          : 'border-dashed border-border bg-surface hover:border-muted5 hover:bg-raised'}
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
      />
      <UploadCloud className="w-8 h-8 text-muted4" />
      <div className="text-[14px] text-muted10">Drop your PDFs here</div>
      <div className="text-[13px] text-muted5 group-hover:underline">or click to browse</div>
    </div>
  );
};

export default DropZone;
