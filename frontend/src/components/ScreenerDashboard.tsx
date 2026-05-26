"use client";
import React from 'react';
import { useRouter } from 'next/navigation';
import { useAnalysisContext } from '@/context/AnalysisContext';
import MarketTickerBar from "@/components/MarketTickerBar";
import ScreenerTable from "@/components/ScreenerTable";
import BreakingNews from "@/components/BreakingNews";
import MarketSentimentPanel from "@/components/MarketSentimentPanel";

export function ScreenerDashboard() {
  const router = useRouter();
  const { setTicker, analyzeTicker } = useAnalysisContext();
  return (
    <>
      <main className="pt-[120px] px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto pb-32 flex flex-col gap-8">
        {/* Section A: Market Pulse */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75" />
            </div>
            <span className="text-xs tracking-widest text-neutral-500">
              LIVE · REFRESHES EVERY 30S
            </span>
          </div>
          <MarketTickerBar />
        </section>

        {/* Top Row: Sentiment & News */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Section B: Market Sentiment */}
          <section className="md:col-span-1">
            <MarketSentimentPanel />
          </section>

          {/* Section C: News */}
          <section className="md:col-span-2">
            <BreakingNews />
          </section>
        </div>

        <header className="mt-8 mb-6 flex justify-between items-end border-b border-glass-border-dim pb-4">
          <div>
            <h1 className="font-headline-md text-headline-md italic text-primary">Screener</h1>
            <p className="text-on-surface-variant mt-2">142 Stocks Matched</p>
          </div>
          <div className="flex gap-4">
            <button className="liquid-glass-strong px-6 py-2 rounded-full font-label-caps text-label-caps text-primary hover:opacity-80 transition-opacity flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">filter_list</span>
              Filter
            </button>
            <button className="px-6 py-2 rounded-full border border-white/20 font-label-caps text-label-caps text-primary hover:bg-white/5 transition-all">
              Export
            </button>
          </div>
        </header>

        <ScreenerTable
          onAnalyze={(ticker) => {
            setTicker(ticker);
            analyzeTicker(ticker);
            router.push('/overview');
          }}
        />
      </main>
    </>
  );
}
