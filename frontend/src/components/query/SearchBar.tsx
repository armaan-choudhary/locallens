import React, { useState, useRef, useEffect, memo, useCallback } from 'react';
import { Search, Loader2, FileText, Check, Image as ImageIcon, Camera } from 'lucide-react';
import type { Document } from '../../types';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onImageSearch: (file: File) => void;
  loading: boolean;
  docCount: number;
  chunkCount: number;
  documents: Document[];
  sessionDocIds: Set<string>;
  onToggleDoc: (docId: string) => void;
}

/** Individual document suggestion item in the mention dropdown */
const MentionItem = memo(({ doc, isSelected, isActive, onClick, onMouseEnter }: any) => (
  <button
    onClick={onClick}
    onMouseEnter={onMouseEnter}
    className={`w-full px-3 py-2.5 flex items-center gap-3 text-left transition-colors ${isActive ? 'bg-white/5' : 'hover:bg-raised/50'}`}
  >
    <div className={`w-7 h-7 rounded-6 flex items-center justify-center shrink-0 ${isSelected ? 'bg-white/10 text-white' : 'bg-raised text-muted4'}`}>
      {isSelected ? <Check className="w-3.5 h-3.5" /> : <FileText className="w-3.5 h-3.5" />}
    </div>
    <div className="flex-1 min-w-0">
      <div className={`text-[13px] truncate ${isSelected ? 'text-white font-medium' : 'text-muted11'}`}>{doc.filename}</div>
      <div className="text-[10px] text-muted4 font-mono truncate">{doc.chunk_count} chunks · {doc.page_count} pages</div>
    </div>
  </button>
));

/** Main search input component with support for @mentions and image search */
const SearchBar: React.FC<SearchBarProps> = ({ 
  onSearch, onImageSearch, loading, documents, sessionDocIds, onToggleDoc 
}) => {
  const [query, setQuery] = useState('');
  const [mentionQuery, setMentionQuery] = useState('');
  const [showMentions, setShowMentions] = useState(false);
  const [mentionIndex, setMentionIndex] = useState(-1);
  const [activeIndex, setActiveIndex] = useState(0);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const filteredDocs = React.useMemo(() => 
    documents.filter(d => d.filename.toLowerCase().includes(mentionQuery.toLowerCase())).slice(0, 8),
  [documents, mentionQuery]);

  const selectedDocs = React.useMemo(() => 
    documents.filter(d => sessionDocIds.has(d.doc_id)),
  [documents, sessionDocIds]);

  const selectDocument = useCallback((doc: Document) => {
    onToggleDoc(doc.doc_id);
    const cursor = inputRef.current?.selectionStart || 0;
    const before = query.slice(0, mentionIndex);
    const after = query.slice(cursor);
    setQuery(before.trim() + " " + after.trim());
    setShowMentions(false);
    inputRef.current?.focus();
  }, [onToggleDoc, query, mentionIndex]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query.trim());
      setQuery('');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageSearch(file);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showMentions) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex(prev => (prev + 1) % filteredDocs.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex(prev => (prev - 1 + filteredDocs.length) % filteredDocs.length);
      } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        if (filteredDocs[activeIndex]) selectDocument(filteredDocs[activeIndex]);
      } else if (e.key === 'Escape') {
        setShowMentions(false);
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    } else if (e.key === 'Backspace' && query === '' && sessionDocIds.size > 0) {
      const lastDoc = selectedDocs[selectedDocs.length - 1];
      if (lastDoc) onToggleDoc(lastDoc.doc_id);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    const cursor = e.target.selectionStart || 0;
    const textBefore = val.slice(0, cursor);
    const lastAt = textBefore.lastIndexOf('@');
    if (lastAt !== -1 && (lastAt === 0 || textBefore[lastAt - 1] === ' ')) {
      setMentionQuery(textBefore.slice(lastAt + 1));
      setMentionIndex(lastAt);
      setShowMentions(true);
      setActiveIndex(0);
    } else {
      setShowMentions(false);
    }
  };

  const isGlobalMode = sessionDocIds.size === 0;
  const placeholderText = isGlobalMode 
    ? "Ask anything about all documents..." 
    : "Ask a question...";

  return (
    <div className="w-full relative">
      <input 
        type="file" 
        ref={fileInputRef} 
        className="hidden" 
        accept="image/*" 
        onChange={handleFileChange} 
      />

      {showMentions && filteredDocs.length > 0 && (
        <div className="absolute bottom-full left-0 mb-2 w-[300px] bg-surface border border-border rounded-12 shadow-2xl overflow-hidden z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="px-3 py-2 border-b border-border bg-raised/30 flex items-center justify-between">
            <span className="font-mono text-[9px] text-white/40 uppercase tracking-widest">Select Scope</span>
            <span className="font-mono text-[8px] text-muted4 opacity-50">↑↓ to navigate</span>
          </div>
          <div className="max-h-[240px] overflow-y-auto custom-scrollbar">
            {filteredDocs.map((doc, i) => (
              <MentionItem
                key={doc.doc_id}
                doc={doc}
                isSelected={sessionDocIds.has(doc.doc_id)}
                isActive={i === activeIndex}
                onClick={() => selectDocument(doc)}
                onMouseEnter={() => setActiveIndex(i)}
              />
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="relative group">
        <div className="min-h-[52px] w-full bg-raised/50 border border-border rounded-12 flex flex-wrap items-center gap-2 py-2 px-4 focus-within:border-white/20 focus-within:bg-raised/80 transition-all shadow-sm">
          <div className="flex items-center gap-1.5 shrink-0 mr-1">
            {loading ? <Loader2 className="w-[18px] h-[18px] text-white animate-spin" /> : <Search className="w-[18px] h-[18px] text-muted5" />}
          </div>

          {selectedDocs.map(doc => (
            <div 
              key={doc.doc_id} 
              className="flex items-center gap-1.5 bg-white/10 border border-white/5 rounded-6 px-2 py-1 animate-fade-in"
            >
              <span className="text-[11px] font-medium text-white">@{doc.filename}</span>
              <button
                type="button"
                onClick={() => onToggleDoc(doc.doc_id)}
                className="text-white/40 hover:text-white transition-colors"
              >
                <Check className="w-2.5 h-2.5" />
              </button>
            </div>
          ))}
          
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={selectedDocs.length === 0 ? placeholderText : ""}
            className="flex-1 min-w-[120px] bg-transparent border-none py-1.5 text-[14px] text-white placeholder:text-muted4 focus:outline-none"
            disabled={loading}
          />

          <div className="flex items-center gap-1 ml-auto">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              title="Search by image"
              className="p-2 rounded-8 text-muted4 hover:text-white hover:bg-white/5 transition-all"
            >
              <Camera className="w-[18px] h-[18px]" />
            </button>
            
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className={`p-2 rounded-8 transition-all ${query.trim() ? 'bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.15)]' : 'text-muted4 grayscale'}`}
            >
              <Search className="w-[18px] h-[18px]" />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default SearchBar;
