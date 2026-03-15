import React, { useState, useEffect } from 'react';
import { getDocuments, queryDocs } from '../api/client';
import type { Document, QueryResult } from '../types';
import Sidebar from '../components/layout/Sidebar';
import SearchBar from '../components/query/SearchBar';
import AnswerPanel from '../components/query/AnswerPanel';
import CitationPanel from '../components/query/CitationPanel';

const QueryPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    const docs = await getDocuments();
    setDocuments(docs);
    setLoading(false);
  };

  const handleSearch = async (query: string) => {
    setSearchLoading(true);
    const queryResult = await queryDocs(query);
    if (queryResult) {
      setResult(queryResult);
    }
    setSearchLoading(false);
  };

  const suggestions = [
    'What are the key findings across all documents?',
    'Summarize the compliance requirements',
    'Find all mentions of data encryption'
  ];

  const totalChunks = documents.reduce((acc, doc) => acc + doc.chunk_count, 0);

  return (
    <div className="flex h-screen overflow-hidden pt-[48px]">
      <Sidebar documents={documents} loading={loading} />
      
      <main className="flex-1 overflow-y-auto p-8 max-w-[1200px] flex flex-col">
        <SearchBar 
          onSearch={handleSearch} 
          loading={searchLoading} 
          docCount={documents.length}
          chunkCount={totalChunks}
        />

        {!result && !searchLoading ? (
          <div className="mt-10 flex flex-col gap-3 animate-in fade-in slide-in-from-top-4 duration-700">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSearch(s)}
                className="flex items-start gap-3 group focus:outline-none"
              >
                <span className="text-muted4 text-[13px] mt-[1px]">→</span>
                <span className="text-muted5 text-[13px] group-hover:text-muted10 transition-colors text-left">
                  {s}
                </span>
              </button>
            ))}
          </div>
        ) : searchLoading && !result ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="font-mono text-[14px] text-muted4 animate-pulse">
              Consulting local models...
            </div>
          </div>
        ) : result ? (
          <div className="mt-8 flex gap-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
            <div className="w-[58%]">
              <AnswerPanel 
                answer={result.answer}
                verified={result.verified}
                latency={result.latency_seconds}
                flaggedSentences={result.flagged_sentences}
              />
            </div>
            <div className="w-[42%] border-l border-border pl-8">
              <CitationPanel citations={result.citations} />
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
};

export default QueryPage;
