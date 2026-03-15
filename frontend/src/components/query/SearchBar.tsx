import React, { useState, useRef, useEffect } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading: boolean;
  docCount: number;
  chunkCount: number;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, loading, docCount, chunkCount }) => {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus on mount
  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) onSearch(query.trim());
  };

  return (
    <div className="w-full mb-8">
      <form onSubmit={handleSubmit} className="relative">
        {/* Search icon */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
          {loading
            ? <Loader2 className="w-[16px] h-[16px] text-accent animate-spin" />
            : <Search className="w-[16px] h-[16px] text-muted5" />
          }
        </div>

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything about your documents…"
          className="
            search-input w-full h-[52px] bg-raised border border-border rounded-10
            pl-11 pr-[110px] text-[14px] text-white placeholder-muted5
            transition-all duration-200
          "
        />

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="
            absolute right-[6px] top-1/2 -translate-y-1/2
            h-[40px] px-5 bg-accent hover:bg-accentLight
            rounded-8 text-[13px] font-medium text-white
            disabled:opacity-40 disabled:cursor-not-allowed
            transition-all duration-150
            shadow-[0_0_20px_rgba(124,106,247,0.25)]
          "
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {/* Context line */}
      <div className="font-mono text-[11px] text-muted4 mt-2 pl-1">
        {docCount} document{docCount !== 1 ? 's' : ''} · {chunkCount} chunks indexed
      </div>
    </div>
  );
};

export default SearchBar;
