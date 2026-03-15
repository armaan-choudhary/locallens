import React, { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading: boolean;
  docCount: number;
  chunkCount: number;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, loading, docCount, chunkCount }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query.trim());
    }
  };

  return (
    <div className="w-full mb-8">
      <form onSubmit={handleSubmit} className="relative group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything about your documents..."
          className="w-full h-[48px] bg-raised border border-border rounded-8 px-4 pr-[90px] text-[14px] text-white placeholder-muted4 focus:border-muted5 focus:outline-none transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="absolute right-[6px] top-1/2 -translate-y-1/2 h-[36px] px-[14px] bg-raised border border-border rounded-6 text-[13px] text-muted10 hover:bg-border hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      
      <div className="font-mono text-[12px] text-muted4 mt-2">
        {docCount} documents · {chunkCount} chunks
      </div>
    </div>
  );
};

export default SearchBar;
