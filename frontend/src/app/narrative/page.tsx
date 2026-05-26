"use client";

import React from 'react';
import { useAnalysis } from '@/hooks/useAnalysis';
import NarrativeTimeline from '@/components/NarrativeTimeline';

export default function NarrativePage() {
  const { ticker, setTicker, isAnalyzing, analyzeTicker } = useAnalysis();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) analyzeTicker(ticker);
  };

  return (
    <main className="pt-24 pb-24 min-h-screen relative overflow-hidden">
      {/* Ambient Background Effect */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden flex items-center justify-center opacity-30">
        <div className="absolute w-[800px] h-[800px] rounded-full bg-primary/5 blur-[120px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"></div>
      </div>

      <div className="relative z-10 max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop space-y-gutter">
        {/* Ticker Search Bar Section */}
        <div className="flex flex-col items-center justify-center mb-16 text-center w-full max-w-3xl mx-auto pt-8">
          <form onSubmit={handleSearch} className="flex w-full gap-4 flex-col sm:flex-row">
            <input 
              className="flex-1 bg-surface-overlay border border-glass-border-dim rounded-full px-6 py-4 text-primary font-body-lg focus:outline-none focus:border-primary transition-colors w-full" 
              placeholder="Enter ticker symbol (e.g. AAPL, TSLA, NVDA)" 
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              disabled={isAnalyzing}
            />
            <button 
              type="submit"
              disabled={isAnalyzing}
              className="bg-[#4f46e5] hover:bg-[#4338ca] text-white font-label-caps text-label-caps px-8 py-4 sm:py-0 rounded-full transition-colors flex items-center justify-center whitespace-nowrap disabled:opacity-50"
            >
              {isAnalyzing ? (
                <span className="material-symbols-outlined animate-spin text-[20px]">sync</span>
              ) : (
                'Analyze'
              )}
            </button>
          </form>
        </div>

        <div className="bg-surface-overlay backdrop-blur-[50px] rounded-xl p-8 liquid-glass mt-gutter">
          <NarrativeTimeline ticker={ticker || "AAPL"} />
        </div>
      </div>
    </main>
  );
}
