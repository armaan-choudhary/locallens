/**
 * OnboardingPage Component
 * Provides the initial entry point for users to understand LocalLens features
 * and begin the document ingestion process.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDocuments } from '../api/client';

const features = [
  {
    emoji: '🔒',
    title: '100% Offline',
    desc:  'No data leaves your device. Every model and index runs locally.',
  },
  {
    emoji: '📎',
    title: 'Verified Citations',
    desc:  'Every answer traced to exact page & chunk coordinates.',
  },
  {
    emoji: '🖼',
    title: 'Text + Images',
    desc:  'CLIP embeddings + Tesseract OCR — multimodal retrieval.',
  },
];

const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);

  /**
   * Check for existing documents to determine if onboarding is necessary.
   */
  useEffect(() => {
    getDocuments().then(docs => {
      if (docs && docs.length > 0) navigate('/ingest');
      else setChecking(false);
    });
  }, [navigate]);

  if (checking) return null;

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4 animate-fade-in">
      <div className="w-full max-w-[440px]">

        <div className="flex justify-center mb-8">
          <span className="font-mono text-[10px] text-accent uppercase tracking-[0.2em] px-3 py-1 border border-white/20 rounded-full bg-accentDim">
            LocalLens
          </span>
        </div>

        <h1 className="text-[32px] font-semibold text-white leading-[1.2] tracking-[-0.02em] text-center mb-3">
          Your documents,<br />answered privately.
        </h1>
        <p className="text-[14px] text-muted7 text-center leading-relaxed mb-10 max-w-[340px] mx-auto">
          Semantic search, multimodal RAG, and verified citations — all on your machine.
        </p>

        <div className="border border-border rounded-12 overflow-hidden mb-8">
          {features.map((f, i) => (
            <div
              key={i}
              className={`
                flex items-center gap-4 px-5 py-[18px]
                ${i < features.length - 1 ? 'border-b border-border' : ''}
              `}
            >
              <div className="w-9 h-9 rounded-8 bg-raised border border-border flex items-center justify-center text-[16px] shrink-0">
                {f.emoji}
              </div>
              <div>
                <div className="text-[14px] font-medium text-muted14 mb-[2px]">{f.title}</div>
                <div className="text-[12px] text-muted6 leading-snug">{f.desc}</div>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={() => navigate('/ingest')}
          className="
            w-full h-[46px] rounded-10 bg-accent hover:bg-accentLight
            text-[14px] font-medium text-base
            shadow-glow
            transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-base
          "
        >
          Import Your First PDF →
        </button>

        <div className="mt-5 text-center font-mono text-[11px] text-muted4 tracking-[0.04em]">
          No accounts · No API keys · No internet
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;
