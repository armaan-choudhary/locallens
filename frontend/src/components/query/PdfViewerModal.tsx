import React, { useState, useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, Loader2, FileWarning, ZoomIn, ZoomOut } from 'lucide-react';

interface PdfViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  docId: string;
  docName: string;
  pageNumber: number;
}

/**
 * Lightweight PDF page viewer that renders a specific page as an image.
 * Allows navigating between pages to see surrounding context.
 */
const PdfViewerModal: React.FC<PdfViewerModalProps> = ({ isOpen, onClose, docId, docName, pageNumber }) => {
  const [currentPage, setCurrentPage] = useState(pageNumber);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [zoom, setZoom] = useState(1);

  // Reset state when modal opens with new props
  useEffect(() => {
    if (isOpen) {
      setCurrentPage(pageNumber);
      setLoading(true);
      setError(false);
      setZoom(1);
    }
  }, [isOpen, pageNumber, docId]);

  if (!isOpen) return null;

  const imgSrc = `/api/documents/${docId}/page/${currentPage}`;

  const handlePrev = () => {
    if (currentPage > 1) {
      setCurrentPage(p => p - 1);
      setLoading(true);
      setError(false);
    }
  };

  const handleNext = () => {
    setCurrentPage(p => p + 1);
    setLoading(true);
    setError(false);
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-lg animate-fade-in"
        onClick={onClose}
      />

      <div className="relative w-full max-w-[900px] h-[90vh] bg-base border border-border rounded-20 shadow-2xl flex flex-col overflow-hidden animate-zoom-in">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-base/80 backdrop-blur-xl shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded-8 bg-accent/10 border border-accent/20 flex items-center justify-center shrink-0">
              <span className="text-accent text-[12px] font-bold font-mono">{currentPage}</span>
            </div>
            <div className="min-w-0">
              <h3 className="text-textPrimary text-[14px] font-medium truncate">{docName}</h3>
              <p className="text-textMuted text-[10px] font-mono uppercase tracking-wider">
                Page {currentPage} · Source View
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Zoom controls */}
            <button
              onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}
              className="p-1.5 rounded-6 hover:bg-card text-textMuted hover:text-textPrimary transition-all"
              title="Zoom out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-[10px] font-mono text-textMuted min-w-[40px] text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom(z => Math.min(3, z + 0.25))}
              className="p-1.5 rounded-6 hover:bg-card text-textMuted hover:text-textPrimary transition-all"
              title="Zoom in"
            >
              <ZoomIn className="w-4 h-4" />
            </button>

            <div className="w-px h-5 bg-border mx-1" />

            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-card text-textMuted hover:text-textPrimary transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Page content */}
        <div className="flex-1 overflow-auto custom-scrollbar bg-[#1a1a1a] flex items-start justify-center p-6">
          {loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 z-10">
              <Loader2 className="w-8 h-8 text-accent animate-spin" />
              <p className="text-textMuted font-mono text-[10px] uppercase tracking-widest">
                Rendering page {currentPage}…
              </p>
            </div>
          )}

          {error ? (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <FileWarning className="w-12 h-12 text-textMuted opacity-30" />
              <p className="text-textMuted text-[13px] text-center max-w-[300px]">
                Could not render this page. The source PDF may no longer be available on disk.
              </p>
              <p className="text-textMuted text-[11px] font-mono">
                Re-ingest the document to restore source viewing.
              </p>
            </div>
          ) : (
            <img
              key={`${docId}-${currentPage}`}
              src={imgSrc}
              alt={`Page ${currentPage}`}
              className="rounded-8 shadow-2xl transition-transform duration-300"
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'top center',
                opacity: loading ? 0 : 1,
                transition: 'opacity 0.3s ease, transform 0.3s ease',
              }}
              onLoad={() => setLoading(false)}
              onError={() => {
                setLoading(false);
                setError(true);
              }}
            />
          )}
        </div>

        {/* Navigation footer */}
        <div className="px-6 py-3 border-t border-border bg-base/80 backdrop-blur-xl flex items-center justify-between shrink-0">
          <button
            onClick={handlePrev}
            disabled={currentPage <= 1}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-8 bg-card border border-border text-textSecondary text-[12px] font-medium hover:bg-cardHi transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Previous
          </button>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-textMuted">
              Page
            </span>
            <input
              type="number"
              min={1}
              value={currentPage}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (val > 0) {
                  setCurrentPage(val);
                  setLoading(true);
                  setError(false);
                }
              }}
              className="w-[48px] px-2 py-1 rounded-6 bg-card border border-border text-textPrimary text-[12px] font-mono text-center focus:outline-none focus:border-accent/50"
            />
          </div>

          <button
            onClick={handleNext}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-8 bg-card border border-border text-textSecondary text-[12px] font-medium hover:bg-cardHi transition-all"
          >
            Next
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PdfViewerModal;
